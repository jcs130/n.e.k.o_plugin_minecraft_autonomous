"""Host speaking opportunities, separate from strategic acknowledgement and play."""

import hashlib
import json

from agent_mc_autonomy.commentary import commentary_changes

SPEAK = ("像正在玩游戏的主播，只选一个新重点说1—2句，总共约40个汉字，可有自然情绪。"
         "不要念背包清单、坐标、工具名、受理回执或‘先读取现场’等过程；不用先复述状态。"
         "行动未完成就只说打算，不说已完成。用户直接提问仍正常回答。")
QUIET = ("本轮没有到期的新解说重点。照常检查并确认策略，工具调用前后都不用出声；"
         "不要念背包清单、查询过程，也不说‘保持安静’。用户直接提问仍正常回答。")


def commentary_plan(plugin, settings, target, event, now, interval, *, review_id="", manual=False):
    identity = hashlib.sha256((settings.identity + target).encode()).hexdigest()[:24]
    path = plugin.data_path("presentation", identity + ".json")
    previous = load_commentary(path)
    if review_id and previous.get("review_id") == review_id:
        return path, previous, previous["commentary"]
    changed = commentary_changes(event, previous.get("baseline"))
    ready = now - previous.get("submitted_at", 0) >= (30 if manual else interval)
    retrying = now < previous.get("retry_after", 0)
    allowed = not retrying and (manual or bool(changed["topics"])) and (ready or changed["urgent"])
    note = {"allowed": allowed, "topics": changed["topics"], "urgent": changed["urgent"],
            "reason": "highlight" if allowed else ("unchanged" if not manual and not changed["topics"]
                                                     else "rate_limited"),
            "instruction": SPEAK if allowed else QUIET, "playback_verified": False}
    state = {**previous, "signature": event["signature"], "baseline": event["baseline"],
             "review_id": review_id, "commentary": note}
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
