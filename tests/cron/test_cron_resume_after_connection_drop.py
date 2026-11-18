"""A brief gateway connection drop must not turn an admitted cron fire into a false failure.

Specimen: g02-wake-driver-vigil 2026-11-17 05:19 and 19:26 EST. The firer's status poll lost its
gateway connection ("Gateway connection failed; no local fallback") during a short gateway stall,
raised CronExecutionUnknown and paused/alerted, while the owner finished and delivered the run.
"""
from contextlib import asynccontextmanager

import pytest

from cron import jobs, executions, scheduler_authority
from hermes_cli import gateway_client


def flaky_peer(monkeypatch, call, drops):
    """connect_gateway whose client raises a transport error on the first `drops` status calls."""
    state = {'drops': drops, 'connects': 0}

    class Peer:
        async def rpc(self, method, **params):
            if method == 'cron.status' and state['drops'] > 0:
                state['drops'] -= 1
                raise gateway_client.GatewayClientError('Gateway connection failed; no local fallback')
            return call(method, params)

    @asynccontextmanager
    async def connected():
        state['connects'] += 1
        yield Peer()

    monkeypatch.setattr(gateway_client, 'connect_gateway', connected)
    async def no_sleep(_):
        return None
    monkeypatch.setattr(scheduler_authority.asyncio, 'sleep', no_sleep)
    return state


def test_admitted_fire_survives_status_connection_drop(tmp_path, monkeypatch):
    with jobs.use_cron_store(tmp_path / 'cron'):
        job = jobs.create_job(prompt='report', schedule='every 1h', deliver='local')
        execution = executions.create_execution(job['id'], source='test')
        calls = []

        def call(method, params):
            calls.append(method)
            if method == 'cron.submit':
                return {'session_id': 's1', 'admission_id': 'a1'}
            assert method == 'cron.status'
            return {'status': 'terminal', 'result': [True, 'document', 'answer', None]}

        state = flaky_peer(monkeypatch, call, drops=2)
        result = scheduler_authority.run_canonical_job(job, execution_id=execution['id'])
        assert tuple(result) == (True, 'document', 'answer', None)
        assert calls.count('cron.submit') == 1, calls  # resumed observing; never re-submitted
        assert state['connects'] == 3


def test_drop_outlasting_resume_window_is_still_unknown(tmp_path, monkeypatch):
    with jobs.use_cron_store(tmp_path / 'cron'):
        job = jobs.create_job(prompt='report', schedule='every 1h', deliver='local')
        execution = executions.create_execution(job['id'], source='test')

        def call(method, params):
            if method == 'cron.submit':
                return {'session_id': 's1', 'admission_id': 'a1'}
            return {'status': 'started'}

        flaky_peer(monkeypatch, call, drops=10**6)
        monkeypatch.setattr(scheduler_authority, 'RESUME_WINDOW_S', 0.0)
        with pytest.raises(scheduler_authority.CronExecutionUnknown):
            scheduler_authority.run_canonical_job(job, execution_id=execution['id'])


def test_drop_before_admission_keeps_old_behaviour(tmp_path, monkeypatch):
    """No receipt yet: the firer cannot know whether the owner admitted it, so it must not resume."""
    with jobs.use_cron_store(tmp_path / 'cron'):
        job = jobs.create_job(prompt='report', schedule='every 1h', deliver='local')
        execution = executions.create_execution(job['id'], source='test')
        connects = {'n': 0}

        class Peer:
            async def rpc(self, method, **params):
                raise gateway_client.GatewayClientError('Gateway connection failed; no local fallback')

        @asynccontextmanager
        async def connected():
            connects['n'] += 1
            yield Peer()

        monkeypatch.setattr(gateway_client, 'connect_gateway', connected)
        with pytest.raises(scheduler_authority.CronExecutionUnknown):
            scheduler_authority.run_canonical_job(job, execution_id=execution['id'])
        assert connects['n'] == 1
