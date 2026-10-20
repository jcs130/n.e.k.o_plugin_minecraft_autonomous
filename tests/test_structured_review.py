import importlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from agent_mc_autonomy.ownership import session_lease
from test_recent_context import prepare


def response(arguments, content='I need to inspect first.</think>', *, finish_reason='tool_calls'):
    call = SimpleNamespace(id='review-call', function=SimpleNamespace(name='submit_game_review', arguments=json.dumps(arguments)))
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(
        content=content, tool_calls=[call]))])


def configured(plugin, monkeypatch):
    port, snapshot, raw, settings, clock, save, host, push = prepare(plugin, monkeypatch)
    raw['heartbeat']['structured_reviews'] = True
    create = AsyncMock()
    plugin._test_review_gateway = SimpleNamespace(aclose=AsyncMock(), get_client=AsyncMock(return_value=SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create)))))
    monkeypatch.setattr(type(plugin.ctx), 'models', property(lambda _: plugin._test_review_gateway))
    port.observe(snapshot)
    return port, snapshot, raw, settings, clock, save, host, push, create


def test_model_prelude_never_enters_host_chat_or_voice(plugin_instance, monkeypatch, run_async):
    port, _, _, _, _, _, _, push, create = configured(plugin_instance, monkeypatch)
    create.return_value = response({'decision': 'continue', 'reason': 'Keep useful work',
                                      'spoken_text': '这片树林真漂亮，沿着河走走吧。'})
    speech = importlib.import_module(plugin_instance.__class__.__module__ + '.neko_speech')
    lines = []
    def enqueue(*args, **kwargs):
        lines.append(args[6])
        return {'status': 'enqueued'}
    monkeypatch.setattr(speech, 'enqueue_speech', enqueue)
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is True
    assert lines == ['这片树林真漂亮，沿着河走走吧。']
    assert create.await_count == 1
    call = create.await_args.kwargs
    assert call['model'] == 'decision' and call['stream'] is False
    assert call['tool_choice'] == 'auto'
    assert 'Synthetic' in json.dumps(call['messages'], ensure_ascii=False)
    assert 'Protect house' in json.dumps(call['messages'], ensure_ascii=False)
    plugin_instance._test_review_gateway.aclose.assert_awaited_once()
    assert all(call.kwargs['ai_behavior'] == 'read' for call in push.call_args_list)
    assert 'I need' not in json.dumps([call.kwargs for call in push.call_args_list], ensure_ascii=False)
    assert port.state()['review']['result']['acknowledged']


def test_free_text_cannot_replace_a_structured_decision(plugin_instance, monkeypatch, run_async):
    port, _, _, _, _, _, _, push, create = configured(plugin_instance, monkeypatch)
    create.return_value = SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop', message=SimpleNamespace(
        content='I need to inspect first.', tool_calls=[]))])
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is False
    assert result['reason'] == 'structured_review_invalid_response'
    assert not port.state()['review'].get('result')
    assert all(call.kwargs['ai_behavior'] == 'read' for call in push.call_args_list)
    assert not getattr(plugin_instance, '_speech_output_tasks', None)


@pytest.mark.parametrize('finish_reason', ['stop', 'tool_calls'])
def test_accepts_complete_structured_review_with_provider_stop(plugin_instance, monkeypatch, run_async, finish_reason):
    port, _, _, _, _, _, _, push, create = configured(plugin_instance, monkeypatch)
    create.return_value = response({'decision': 'continue', 'reason': 'Keep current work'},
                                   content=None, finish_reason=finish_reason)
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is True
    assert create.await_count == 1
    assert port.state()['review']['result']['acknowledged']
    assert not getattr(plugin_instance, '_speech_output_tasks', None)
    assert all(call.kwargs['ai_behavior'] == 'read' for call in push.call_args_list)


@pytest.mark.parametrize('finish_reason', ['length', 'content_filter', 'error', None])
def test_rejects_incomplete_review_even_with_a_tool_call(plugin_instance, monkeypatch, run_async, finish_reason):
    port, _, _, _, _, _, _, _, create = configured(plugin_instance, monkeypatch)
    create.return_value = response({'decision': 'continue', 'reason': 'Do not adopt truncated work'},
                                   content=None, finish_reason=finish_reason)
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is False
    assert result['reason'] == 'structured_review_invalid_response'
    assert not port.state()['review'].get('result')
    assert not getattr(plugin_instance, '_speech_output_tasks', None)


@pytest.mark.parametrize('budget', [3072, 8192])
def test_review_honors_configured_output_budget(plugin_instance, monkeypatch, run_async, budget):
    port, _, raw, _, _, _, _, _, create = configured(plugin_instance, monkeypatch)
    raw['autonomy']['max_output_tokens'] = budget
    create.return_value = response({'decision': 'continue', 'reason': 'Complete within the configured budget'})
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is True
    assert create.await_args.kwargs['max_completion_tokens'] == budget
    assert create.await_count == 1


def test_truncated_review_records_budget_failure_without_adoption(plugin_instance, monkeypatch, run_async):
    port, _, raw, _, _, _, _, _, create = configured(plugin_instance, monkeypatch)
    raw['autonomy']['max_output_tokens'] = 3072
    create.return_value = response({'decision': 'continue', 'reason': 'Never adopt partial reasoning'},
                                   finish_reason='length')
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['failure_category'] == 'output_budget_exhausted'
    assert result['max_output_tokens'] == 3072
    assert not result['main_brain_acknowledged']
    assert not port.state()['review'].get('result')
    assert not getattr(plugin_instance, '_speech_output_tasks', None)
    assert create.await_count == 1


@pytest.mark.parametrize('change', ['stop', 'generation', 'run', 'intent'])
def test_late_review_cannot_change_a_stopped_or_replaced_body(plugin_instance, monkeypatch, run_async, change):
    port, snapshot, _, _, _, save, _, _, create = configured(plugin_instance, monkeypatch)
    async def answer(**kwargs):
        if change == 'stop':
            plugin_instance._operator_state(True)
        elif change == 'generation':
            plugin_instance._generation += 1
        elif change == 'run':
            snapshot['native_run'] = 'other-run'
            save()
        else:
            port.mailbox.submit_user_intent('feedback', {'goal': 'New operator goal', 'mode': 'insert'},
                                           '11111111-1111-4111-8111-111111111111')
        return response({'decision': 'insert', 'reason': 'Try a different plan', 'goal': 'Old stale plan'})
    create.side_effect = answer
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is False
    assert result['reason'] == 'structured_review_superseded'
    assert not port.state()['review'].get('result')


def test_missing_gateway_does_not_fall_back_to_an_unfiltered_reply(plugin_instance, monkeypatch, run_async):
    port, _, _, _, _, _, _, push, _ = configured(plugin_instance, monkeypatch)
    plugin_instance._test_review_gateway = None
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['reason'] == 'structured_review_unavailable'
    assert not result['main_brain_acknowledged']
    assert all(call.kwargs['ai_behavior'] == 'read' for call in push.call_args_list)


def test_control_text_in_explicit_voice_is_not_speakable(plugin_module):
    speech = importlib.import_module(plugin_module.__name__ + '.neko_speech')
    assert speech.sanitize_speech('<think>I need to inspect first.</think>我们去找棵树吧。') == '我们去找棵树吧。'


def test_rejected_stage_choice_returns_actual_error_once(plugin_instance, monkeypatch, run_async):
    port, _, _, _, _, _, _, _, create = configured(plugin_instance, monkeypatch)
    first = response({'decision': 'revise', 'reason': 'Change the stage', 'goal': 'New stage'})
    first.choices[0].message.reasoning_content = 'Private provider reasoning; never transport as free text.'
    create.side_effect = [first,
                          response({'decision': 'continue', 'reason': 'No stage exists to revise'})]
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is True
    assert result['correction_attempts'] == 1
    assert create.await_count == 2
    messages = create.await_args.kwargs['messages']
    assert [m['role'] for m in messages] == ['system', 'user', 'user']
    correction = json.loads(messages[-1]['content'])
    assert correction['rejected_candidate']['decision'] == 'revise'
    assert correction['rejection']['error'] == 'no_active_review_stage'
    assert 'Private provider reasoning' not in json.dumps(messages)
    assert 'I need' not in json.dumps(messages)
    assert port.state()['last_decision']['decision'] == 'continue'
    assert port.mailbox.intent_revision() == 0


def test_rejected_review_correction_is_bounded(plugin_instance, monkeypatch, run_async):
    port, _, _, _, _, _, _, _, create = configured(plugin_instance, monkeypatch)
    create.return_value = response({'decision': 'revise', 'reason': 'Change the stage', 'goal': 'New stage'})
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is False
    assert result['decision_error'] == 'no_active_review_stage'
    assert result['correction_attempts'] == 1
    assert create.await_count == 2
    assert not port.state()['review'].get('choice')


def test_transport_timeout_does_not_retry_an_unknown_review(plugin_instance, monkeypatch, run_async):
    port, _, _, _, _, _, _, _, create = configured(plugin_instance, monkeypatch)
    create.side_effect = TimeoutError()
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['reason'] == 'structured_review_unavailable'
    assert create.await_count == 1
    assert result['failure_category'] == 'deadline_exceeded'
    assert not port.state()['review'].get('choice')


def test_review_wait_uses_remaining_native_lease(plugin_instance, monkeypatch, run_async):
    port, _, _, _, clock, _, _, _, create = configured(plugin_instance, monkeypatch)
    transport = importlib.import_module(plugin_instance.__class__.__module__ + '.neko_structured_review')
    actual_wait = transport.asyncio.wait_for
    waits = []
    async def wait_for(coro, timeout):
        waits.append(timeout)
        return await actual_wait(coro, timeout)
    monkeypatch.setattr(transport.asyncio, 'wait_for', wait_for)
    async def answer(**kwargs):
        clock[0] += 30  # A valid, slow inference must fit the offered lease.
        return response({'decision': 'continue', 'reason': 'Continue after the queued inference'})
    create.side_effect = answer
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is True
    assert 25 < waits[-1] <= 180
    assert create.await_count == 1


def test_correction_shares_original_review_deadline(plugin_instance, monkeypatch, run_async):
    port, _, _, _, clock, _, _, _, create = configured(plugin_instance, monkeypatch)
    transport = importlib.import_module(plugin_instance.__class__.__module__ + '.neko_structured_review')
    actual_wait = transport.asyncio.wait_for
    waits = []
    async def wait_for(coro, timeout):
        waits.append(timeout)
        return await actual_wait(coro, timeout)
    monkeypatch.setattr(transport.asyncio, 'wait_for', wait_for)
    async def answer(**kwargs):
        clock[0] += 10
        return response({'decision': 'revise', 'reason': 'Change stage', 'goal': 'New stage'} if create.await_count == 1
                        else {'decision': 'continue', 'reason': 'Continue original goal'})
    create.side_effect = answer
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is True
    assert waits[-1] == waits[-2] - 10
    assert 25 < waits[-1] <= 170
    assert create.await_count == 2


@pytest.mark.parametrize('change', ['stop', 'generation', 'run', 'intent'])
def test_corrected_review_rechecks_ownership(plugin_instance, monkeypatch, run_async, change):
    port, snapshot, _, _, _, save, _, _, create = configured(plugin_instance, monkeypatch)
    async def answer(**kwargs):
        if create.await_count == 1:
            return response({'decision': 'revise', 'reason': 'No stage', 'goal': 'New stage'})
        if change == 'stop':
            plugin_instance._operator_state(True)
        elif change == 'generation':
            plugin_instance._generation += 1
        elif change == 'run':
            snapshot['native_run'] = 'other-run'
            save()
        else:
            port.mailbox.submit_user_intent('feedback', {'goal': 'New operator goal', 'mode': 'insert'},
                                           '11111111-1111-4111-8111-111111111111')
        return response({'decision': 'continue', 'reason': 'Stale correction'})
    create.side_effect = answer
    with session_lease(port.directory):
        result = run_async(plugin_instance.game_decision_heartbeat()).value
    assert result['main_brain_acknowledged'] is False
    assert result['reason'] == 'structured_review_superseded'
    assert create.await_count == 2
    assert not port.state()['review'].get('choice')
