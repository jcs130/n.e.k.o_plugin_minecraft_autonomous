import importlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from agent_mc_autonomy.ownership import session_lease
from test_recent_context import prepare


def response(arguments, content='I need to inspect first.</think>'):
    call = SimpleNamespace(function=SimpleNamespace(name='submit_game_review', arguments=json.dumps(arguments)))
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason='tool_calls', message=SimpleNamespace(
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
    assert call['tool_choice']['function']['name'] == 'submit_game_review'
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
