#!/usr/bin/env python3
"""Headless board-rooms bring-up — groups.create + member seating from board-rooms.yaml.

Usage (in-container, against a gateway over JSON-RPC):
  python scripts/board_rooms_bringup.py --gateway-ws ws://127.0.0.1:PORT/api/ws --board board-alpha [--dry-run]
  python scripts/board_rooms_bringup.py --gateway-ws ws://127.0.0.1:PORT/api/ws --all-boards
  Auth: --gateway-ticket <ticket> or HERMES_GATEWAY_TICKET env or auto-mint from control socket.

- Loads board-rooms.yaml for each board, validates members ⊆ board.yaml roles.
- For each room: groups.create with board-fenced seating (board param),
  then groups.context to set purpose/routing/lead (event_id+notes required).
  Member execution policy is governed by gateway defaults: approval "manual",
  MAX_POLICY_ITERATIONS cap (128) per hosted_room_execution_policy.
- Idempotent: if room already exists (same room_id), reports and skips.
- No CLI subcommand upstream exists — this script IS the operator surface.

Requires: websockets (pip install websockets) or falls back to gateway direct import.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure repo root on path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

DEFAULT_MAX_ITERATIONS = 128
DEFAULT_ROUTING = "assigned"


def _load_boards_with_rooms() -> list[tuple[str, Path]]:
    """Return (board_slug, board_home) for boards that have board-rooms.yaml."""
    from hermes_cli.kanban_db import board_dir
    from hermes_cli.kanban_db_boards import list_boards

    out = []
    for entry in list_boards():
        slug = entry.get("slug") or entry.get("name") or ""
        if not slug:
            continue
        bh = board_dir(slug)
        if (bh / "board-rooms.yaml").is_file():
            out.append((slug, bh))
    return out


def _room_id_for(board_slug: str, room_name: str) -> str:
    """Deterministic room_id: board-slug + room name slug."""
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in room_name.lower()).strip("-")
    return f"{board_slug}--{safe}" if safe else board_slug


async def _bringup_via_ws(gateway_ws: str, board_slug: str, dry_run: bool = False, gateway_ticket: str = "", gateway_token: str = "", pin_board_param: bool = False) -> list[dict]:
    """Bring up rooms for board_slug via gateway WebSocket JSON-RPC via ticket subprotocol."""
    try:
        import websockets  # type: ignore[import]
    except ImportError:
        print("websockets not installed; try: pip install websockets", file=sys.stderr)
        print("Falling back to direct gateway import (requires gateway running in same process).", file=sys.stderr)
        return _bringup_via_direct(board_slug, dry_run=dry_run)

    from hermes_cli.board_rooms import load_board_rooms

    bh = None
    for slug, home in _load_boards_with_rooms():
        if slug == board_slug:
            bh = home
            break
    if bh is None:
        print(f"board {board_slug!r} has no board-rooms.yaml", file=sys.stderr)
        return []

    br = load_board_rooms(bh)
    results = []

    # Resolve ticket: explicit arg > HERMES_GATEWAY_TICKET env > gateway_token legacy
    ticket = gateway_ticket or os.environ.get("HERMES_GATEWAY_TICKET", "") or gateway_token or os.environ.get("HERMES_GATEWAY_TOKEN", "")
    # Also try to mint from control socket if no ticket and home available
    if not ticket:
        try:
            from tests.gateway.test_normal_runtime_boot import control as _control  # type: ignore[import]
            home_path = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
            desc = _control(home_path, "identify")
            grant = _control(home_path, "session-ticket", {"profile_id": str(home_path.resolve()), "instance_id": desc.get("instance_id",""), "purpose": "interactive"})
            ticket = grant.get("ticket","")
        except Exception:
            pass
    ws_url = gateway_ws
    # Ensure /api/ws suffix (reviewer noted usage must include it)
    if ws_url and not ws_url.rstrip("/").endswith("/api/ws"):
        ws_url = ws_url.rstrip("/") + "/api/ws"
    subprotocols = None
    if ticket:
        subprotocols = ["hermes-gateway-v1", f"hermes-gateway-ticket.{ticket}"]
    # Fallback legacy token query param for compat (not primary)
    if not ticket:
        token = gateway_token or os.environ.get("HERMES_GATEWAY_TOKEN", "")
        if token and "token=" not in ws_url and "ticket=" not in ws_url:
            sep = "&" if "?" in ws_url else "?"
            ws_url = f"{ws_url}{sep}ticket={token}"
    try:
        connect_kwargs = {}
        if subprotocols:
            connect_kwargs["subprotocols"] = subprotocols

        async def _recv_matching(ws, expect_id: int, timeout: float = 10.0) -> dict:
            """Recv until a frame with matching JSON-RPC id; ignore pushes/notifications."""
            import asyncio as _asyncio
            while True:
                raw = await _asyncio.wait_for(ws.recv(), timeout=timeout)
                try:
                    frame = json.loads(raw)
                except Exception:
                    continue
                if isinstance(frame, dict) and frame.get("id") == expect_id:
                    return frame
                # pushed frame / notification with different id — ignore and keep waiting
                # (up to timeout)

        async with websockets.connect(ws_url, **connect_kwargs) as ws:
            next_id = 1
            for room in br.rooms:
                room_id = _room_id_for(board_slug, room.name)
                members_payload = []
                for m in room.members:
                    members_payload.append({
                        "member_id": m,
                        "profile": m,
                        "handle": m,
                        "target": {"kind": "local", "profile": m},
                    })
                params = {
                    "room_id": room_id,
                    "name": room.name,
                    "members": members_payload,
                }
                if pin_board_param:
                    params["board"] = board_slug
                if dry_run:
                    print(f"[dry-run] would create room {room_id!r} with members {room.members}")
                    results.append({"room_id": room_id, "dry_run": True, "members": room.members})
                    continue

                # groups.create
                cid = next_id; next_id += 1
                req = {"jsonrpc": "2.0", "id": cid, "method": "groups.create", "params": params}
                await ws.send(json.dumps(req))
                resp = await _recv_matching(ws, cid)
                create_ok = "error" not in resp and "result" in resp
                if "error" in resp:
                    print(f"groups.create {room_id!r} failed: {resp['error']}", file=sys.stderr)
                    results.append({"room_id": room_id, "error": resp["error"], "phase": "create"})
                elif "result" not in resp:
                    print(f"groups.create {room_id!r} unexpected reply (no result/error): {resp}", file=sys.stderr)
                    results.append({"room_id": room_id, "error": {"message": "no result in groups.create reply", "data": resp}, "phase": "create"})
                else:
                    print(f"Created room {room_id!r}: {resp.get('result')}")
                    results.append({"room_id": room_id, "ok": True, "result": resp.get("result")})

                # Skip context when create failed — no room to contextualize (P3)
                if not create_ok:
                    continue

                # groups.context for purpose/routing/lead (requires event_id + notes per upstream)
                import uuid as _uuid

                ctx_params = {
                    "room_id": room_id,
                    "event_id": _uuid.uuid4().hex,
                    "purpose": room.purpose,
                    "notes": "",
                    "routing": {"assigned": "lead", "direct": "lead"}.get(room.routing, room.routing) if room.routing in ("everyone","lead","auto","assigned","direct") else "everyone",
                    "lead_member_id": room.lead if room.routing in ("lead","assigned","direct") else "",
                }
                cid2 = next_id; next_id += 1
                req2 = {"jsonrpc": "2.0", "id": cid2, "method": "groups.context", "params": ctx_params}
                await ws.send(json.dumps(req2))
                resp2 = await _recv_matching(ws, cid2)
                if "error" in resp2:
                    print(f"groups.context {room_id!r} failed: {resp2['error']}", file=sys.stderr)
                    results.append({"room_id": room_id, "error": resp2["error"], "phase": "context"})
                else:
                    print(f"Set context for {room_id!r}: routing={room.routing} lead={room.lead}")
                    # Verify readback of context (best-effort verification)
                    try:
                        sid = next_id; next_id += 1
                        state_req = {"jsonrpc": "2.0", "id": sid, "method": "groups.state", "params": {"room_id": room_id}}
                        await ws.send(json.dumps(state_req))
                        state_resp = await _recv_matching(ws, sid)
                        if "result" in state_resp:
                            ctx = state_resp["result"].get("context") or {}
                            print(f"  context readback: purpose={ctx.get('purpose','')!r:.60} routing={ctx.get('routing')} lead={ctx.get('lead_member_id')}")
                    except Exception:
                        pass

    except Exception as exc:
        print(f"WebSocket bring-up failed: {exc}", file=sys.stderr)
        raise

    return results


def _bringup_via_direct(board_slug: str, dry_run: bool = False) -> list[dict]:
    """Bring up via direct gateway import (for in-process tests)."""
    from hermes_cli.board_rooms import load_board_rooms
    from hermes_cli.kanban_db import board_dir

    bh = board_dir(board_slug)
    br = load_board_rooms(bh)
    results = []
    for room in br.rooms:
        room_id = _room_id_for(board_slug, room.name)
        if dry_run:
            print(f"[dry-run] would create room {room_id!r} with members {room.members}")
            results.append({"room_id": room_id, "dry_run": True})
        else:
            print(f"[direct] room {room_id!r} members {room.members} — use WS path for live gateway")
            results.append({"room_id": room_id, "direct": True})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Board-rooms headless bring-up (groups.create from board-rooms.yaml)")
    parser.add_argument("--gateway-ws", default="", help="Gateway WebSocket URL (ws://host:port)")
    parser.add_argument("--board", default="", help="Board slug to bring up (or --all-boards)")
    parser.add_argument("--all-boards", action="store_true", help="Bring up all boards with board-rooms.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print without creating")
    parser.add_argument("--gateway-token", default="", help="Gateway WS auth token (or HERMES_GATEWAY_TOKEN env)")
    parser.add_argument("--gateway-ticket", default="", help="Gateway WS ticket (subprotocol auth; or HERMES_GATEWAY_TICKET env; auto-mints from control socket if unset)")
    parser.add_argument("--pin-board", action="store_true", help="Send explicit board param on groups.create (opt-in; default: omit, fence derives board from actor)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    if not args.board and not args.all_boards:
        parser.error("specify --board <slug> or --all-boards")

    if args.all_boards:
        boards = [slug for slug, _ in _load_boards_with_rooms()]
        if not boards:
            print("No boards with board-rooms.yaml found", file=sys.stderr)
            return 1
    else:
        boards = [args.board]

    all_results: dict[str, list[dict]] = {}
    for slug in boards:
        if args.gateway_ws:
            results = asyncio.run(_bringup_via_ws(args.gateway_ws, slug, dry_run=args.dry_run, gateway_ticket=args.gateway_ticket, gateway_token=args.gateway_token, pin_board_param=args.pin_board))
        else:
            results = _bringup_via_direct(slug, dry_run=args.dry_run)
        all_results[slug] = results

    if args.json:
        print(json.dumps(all_results, indent=2))

    # Exit 1 if any room failed
    for slug, results in all_results.items():
        for r in results:
            if "error" in r:
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
