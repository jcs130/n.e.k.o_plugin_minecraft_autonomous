"""Host speaking opportunities, separate from strategic acknowledgement and play."""

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from agent_mc_autonomy.commentary import commentary_changes

SPEAK = ("你正亲自在玩Minecraft，用自己的角色性格用中文边玩边聊1—2句。"
         "分享自然反应、好奇、心情或小打算；平静时也能轻松闲聊，不作汇报。"
         "不要念背包清单、坐标、工具名、受理回执或‘先读取现场’等过程；不用先复述状态。"
         "行动未完成就只说打算，不说已完成。用户直接提问仍正常回答。")
QUIET = ("这是策略交流的延续，可自然分享当前打算或感受；具体依据留在工具判断里。"
         "若同一判断已通过spoken_text排入语音，接话时推进话题，不复述那句打算。")


@lru_cache(maxsize=1)
def speaking_skill():
    return Path(__file__).with_name("skills").joinpath("gameplay-speaking.md").read_text(encoding="utf-8")


def commentary_delivery(note):
    """Load the bundled speaking skill into the existing main-brain tool turn."""
    return {"allowed": note["allowed"], "instruction": note["instruction"],
            "表达技能": speaking_skill(),
            **({"本轮重点证据": note["evidence"]} if note["allowed"] else {})}


def commentary_plan(plugin, settings, target, event, now, interval, *, review_id="", manual=False):
    identity = hashlib.sha256((settings.identity + target).encode()).hexdigest()[:24]
    path = plugin.data_path("presentation", identity + ".json")
    previous = load_commentary(path)
    episode = event["payload"].get("death_episode")
    review_key = hashlib.sha256(json.dumps([event["signature"], episode.get("id") if episode else None]).encode()).hexdigest()
    if review_id and previous.get("review_id") == review_id and previous.get("review_key") == review_key:
        return path, previous, previous["commentary"]
    changed = commentary_changes(event, previous.get("baseline"))
    new_death = bool(episode and episode.get("id") != previous.get("death_episode_id"))
    if new_death:
        changed = {"topics": ["死亡后的感想与复盘"], "urgent": True}
    opportunity = event["payload"].get("opportunity", {})
    if opportunity.get("kind") == "idle_presence":
        changed = {"topics": ["idle_presence"], "urgent": False}
    ready = now - previous.get("submitted_at", 0) >= (30 if manual else interval)
    retrying = now < previous.get("retry_after", 0)
    allowed = not retrying and (manual or bool(changed["topics"])) and (ready or changed["urgent"] or opportunity.get("kind") == "idle_presence")
    note = {"opportunity_id": opportunity.get("id", review_id), "allowed": allowed, "topics": changed["topics"], "urgent": changed["urgent"],
            "evidence": {"progress": event["payload"].get("progress", ""),
                         "task_outcome": event["payload"].get("task_outcome"),
                         "body_feedback": event["payload"].get("body_feedback", {}),
                         **({"death_episode": episode} if new_death else {})},
            "reason": "highlight" if allowed else ("unchanged" if not manual and not changed["topics"]
                                                     else "rate_limited"),
            "instruction": SPEAK if allowed else QUIET, "playback_verified": False}
    state = {**previous, "signature": event["signature"],
             "baseline": event["baseline"] if allowed else previous.get("baseline"),
             "review_id": review_id, "review_key": review_key, "commentary": note,
             "death_episode_id": episode["id"] if new_death and allowed else previous.get("death_episode_id")}
    return path, state, note


def load_commentary(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_commentary(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
