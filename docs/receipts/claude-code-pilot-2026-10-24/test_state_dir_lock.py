"""QA-001 / QA-002: one authority per state dir, typed refusals at the CLI door.

QA-001: a server (``serve``) holds an advisory lock on the state dir; a
direct opener must refuse by name instead of writing a duplicate-seq record.
QA-002: a corrupt state log is a one-line typed error, never a traceback.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from metatron.cli.app import app
from metatron.lifecycle import LifecycleEngine, StateDirLocked, StateLogCorrupt
from metatron.lifecycle.state_log import LOG_NAME
from metatron.runtime import AppRuntime

runner = CliRunner()


def test_direct_engine_open_refused_while_server_holds_the_lock(tmp_path: Path) -> None:
    server = AppRuntime(state_dir=tmp_path, hold_lock=True)
    try:
        with pytest.raises(
            StateDirLocked, match=r"state-dir-locked \(a server owns it — pass --url\)"
        ):
            LifecycleEngine(root=tmp_path)
    finally:
        server.close()
    LifecycleEngine(root=tmp_path)  # lock released with the server


def test_cli_verb_refused_by_name_while_server_holds_the_lock(tmp_path: Path) -> None:
    server = AppRuntime(state_dir=tmp_path, hold_lock=True)
    try:
        res = runner.invoke(app, ["--state", str(tmp_path), "run"])
        assert res.exit_code == 1
        assert "state-dir-locked (a server owns it — pass --url)" in res.output
        assert "Traceback" not in res.output
        assert not (tmp_path / LOG_NAME).exists() or (tmp_path / LOG_NAME).read_text() == ""
    finally:
        server.close()


def test_cli_verb_against_corrupt_log_is_one_typed_line(tmp_path: Path) -> None:
    first = runner.invoke(app, ["--state", str(tmp_path), "run"])
    assert first.exit_code in (0, 1), first.output
    log = tmp_path / LOG_NAME
    lines = log.read_text().splitlines()
    assert lines, "setup: run must have written a state-log record"
    log.write_text("\n".join([*lines, lines[-1]]) + "\n")  # duplicate seq (QA-001 aftermath)

    res = runner.invoke(app, ["--state", str(tmp_path), "status"])
    assert res.exit_code == 1
    assert res.output.startswith("StateLogCorrupt:")
    assert "Traceback" not in res.output
    assert len(res.output.strip().splitlines()) == 1


def test_second_server_refused_and_failed_open_releases_the_lock(tmp_path: Path) -> None:
    first = AppRuntime(state_dir=tmp_path, hold_lock=True)
    try:
        with pytest.raises(StateDirLocked):
            AppRuntime(state_dir=tmp_path, hold_lock=True)
    finally:
        first.close()
    log = tmp_path / LOG_NAME
    log.write_text("not json\nnot json\n")  # garbage mid-log is not a torn tail
    with pytest.raises(StateLogCorrupt):
        AppRuntime(state_dir=tmp_path, hold_lock=True)
    log.unlink()
    AppRuntime(state_dir=tmp_path, hold_lock=True).close()  # corrupt open did not leak the lock
