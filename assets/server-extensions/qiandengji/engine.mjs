var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __reExport = (target, mod, secondTarget) => (__copyProps(target, mod, "default"), secondTarget && __copyProps(secondTarget, mod, "default"));

// integrations/qiandengji/engine/cast-tool.ts
import { chatInputError } from "agent-mc-world/extension";
var QIANDENGJI_CAST_TOOL = {
  name: "mc_cast",
  tags: ["act"],
  description: "Cast one server-listed /mycli spell immediately, even during combat or retreat. This does not enter the task queue or take movement control. The reply only confirms sending; the server message and observed effects determine whether the spell worked. For planned timed movement, prepare the route first and queue the cast chat command with dependent flight steps in one mc_do group; do not start the timer while earlier queued work is still running. Pass only the arguments declared by the current server skill contract as separate tokens. This always sends /mycli cast <spell>; other server command namespaces must use mc_do chat with the exact observed usage. Use /mycli skills for current unlocks and /mycli capabilities for command contracts; historical spell lists do not prove current availability.",
  parameters: {
    type: "object",
    properties: {
      spell: {
        type: "string",
        pattern: "^[a-z][a-z0-9_:-]{0,63}$",
        description: "Skill ID from the current server listing, with its current unlock and target requirements."
      },
      arguments: {
        type: "array",
        items: { type: "string", minLength: 1, pattern: "^[^\\s\\u0000-\\u001f\\u007f-\\u009f\\u00a7<>]+$" },
        description: "Optional command arguments in server order, one token per item. No whitespace, control characters or <placeholder> text; read the spell description for required values."
      }
    },
    required: ["spell"]
  }
};
function invokeQiandengjiCast(port, args) {
  const inhibitReason = port.blockedReason?.() ?? null;
  const log = port.log ?? ((_name, _args, value) => value);
  if (inhibitReason) return { text: log("mc_cast", args, `[mc_cast \u672A\u53D1\u9001] ${inhibitReason}`), failed: true, endsTurn: true };
  const spell = args.spell;
  if (typeof spell !== "string" || !/^[a-z][a-z0-9_:-]{0,63}$/.test(spell)) {
    return { text: log("mc_cast", args, "[mc_cast \u5931\u8D25] spell \u5FC5\u987B\u662F\u670D\u52A1\u7AEF\u7ED9\u51FA\u7684\u82F1\u6587\u6280\u80FD ID"), failed: true };
  }
  const parameters2 = args.arguments === void 0 ? [] : args.arguments;
  if (!Array.isArray(parameters2) || !parameters2.every((value) => typeof value === "string" && value.length > 0 && !/[\s\u0000-\u001f\u007f-\u009f<>]/u.test(value))) {
    return { text: log(
      "mc_cast",
      args,
      "[mc_cast \u5931\u8D25] arguments \u5FC5\u987B\u662F\u72EC\u7ACB\u53C2\u6570\u8BCD\u7EC4\u6210\u7684\u6570\u7EC4\uFF0C\u4E0D\u80FD\u5305\u542B\u7A7A\u767D\u3001\u63A7\u5236\u7B26\u6216 <\u5360\u4F4D\u7B26>\uFF1B\u6309\u670D\u52A1\u7AEF\u8BF4\u660E\u586B\u5199\u5B9E\u9645\u503C"
    ), failed: true };
  }
  const command = `/mycli cast ${spell}${parameters2.length ? ` ${parameters2.join(" ")}` : ""}`;
  const inputError = chatInputError(command);
  if (inputError) return { text: log("mc_cast", args, `[mc_cast \u5931\u8D25] ${inputError}`), failed: true };
  const connection = port.connection();
  if (!connection) return { text: log("mc_cast", args, "[mc_cast \u5931\u8D25] \u8FD8\u6CA1\u8FDE\u4E0A\u670D\u52A1\u5668"), failed: true };
  const detail = port.skillDetail?.(spell);
  if (detail?.invocation === "command") {
    return {
      text: log(
        "mc_cast",
        args,
        `[mc_cast \u672A\u53D1\u9001] ${detail.name}\uFF08${spell}\uFF09\u7684\u672C\u8FDE\u63A5\u670D\u52A1\u7AEF\u547D\u4EE4\u662F ${detail.command}\uFF0C\u4E0D\u662F /mycli cast\u3002 \u7528 mc_do ${JSON.stringify({ steps: [{ skill: "chat", text: detail.command }] })}\uFF1B\u5148\u8BFB\u8BE5\u5165\u53E3\u7684\u76EE\u6807\u548C\u524D\u63D0\u3002\u672A\u9644\u52A0\u539F\u65BD\u6CD5\u53C2\u6570\u3001\u672A\u4EE3\u4E3A\u6267\u884C\u3002\u6765\u6E90 MC_RPG\uFF0C\u89C2\u6D4B ` + detail.observedAt
      ),
      failed: true,
      meta: { reason: "command-route-mismatch", skillId: spell, advertisedCommand: detail.command, dispatchStarted: false }
    };
  }
  const route = port.abilities.hasAbility(spell) ? null : port.commands.misplacedPrefix(command, "/mycli cast");
  if (route) {
    const example = JSON.stringify({ steps: [{ skill: "chat", text: route.suggestedCommand }] });
    return { text: log(
      "mc_cast",
      args,
      `[mc_cast \u672A\u53D1\u9001] \u672C\u5DE5\u5177\u56FA\u5B9A\u4F7F\u7528 /mycli cast\uFF1B\u670D\u52A1\u7AEF\u5DF2\u7ED9\u51FA ${route.id} \u7684\u53E6\u4E00\u6761\u547D\u4EE4\u7528\u6CD5\uFF1A${route.usage}\uFF08\u89C2\u6D4B ${new Date(route.observedAt).toISOString()}\uFF09\u3002 \u82E5\u4ECD\u8981\u6267\u884C\u8BE5\u64CD\u4F5C\uFF0C\u7528 mc_do ${example}\uFF1B\u5148\u6838\u5BF9\u670D\u52A1\u7AEF\u524D\u63D0\u3002\u8FD9\u91CC\u53EA\u7EA0\u6B63\u547D\u4EE4\u5165\u53E3\uFF0C\u672A\u4EE3\u66FF\u6267\u884C\uFF0C\u4E5F\u672A\u786E\u8BA4\u5B50\u547D\u4EE4\u3001\u53C2\u6570\u3001\u76EE\u6807\u6216\u8D44\u683C\u3002`
    ), failed: true };
  }
  const blocked = port.abilities.manualCastBlock(spell);
  if (blocked) {
    return {
      text: log("mc_cast", args, `[mc_cast \u6682\u7F13] ${blocked}\uFF1B\u8BE5\u6280\u80FD\u4EE5\u65B0\u7684\u670D\u52A1\u7AEF\u72B6\u6001\u4E3A\u51C6\uFF0C\u5176\u4ED6\u6280\u80FD\u548C\u52A8\u4F5C\u4ECD\u53EF\u9009\u62E9`),
      failed: true,
      endsTurn: true
    };
  }
  let sent = false;
  try {
    connection.send(command);
    sent = true;
    connection.published?.(command);
    port.abilities.noteManualCast(spell);
    return log("mc_cast", args, `[mc_cast] \u5DF2\u53D1\u9001 ${command}\uFF1B\u662F\u5426\u751F\u6548\u4EE5\u670D\u52A1\u7AEF\u56DE\u6267\u548C\u73B0\u573A\u72B6\u6001\u4E3A\u51C6`);
  } catch (error) {
    return {
      text: log("mc_cast", args, sent ? `[mc_cast] \u547D\u4EE4\u5DF2\u53D1\u9001\uFF0C\u4F46\u672C\u5730\u8BB0\u5F55\u5931\u8D25:${String(error)}\uFF1B\u6548\u679C\u4ECD\u672A\u77E5` : `[mc_cast \u5931\u8D25] \u53D1\u9001\u629B\u9519:${String(error)}\uFF1B\u7ED3\u679C\u672A\u77E5\uFF0C\u672A\u81EA\u52A8\u91CD\u8BD5`),
      failed: true,
      data: { commandSent: sent, outcomeUnknown: true, goal_completed: false }
    };
  }
}
function createQiandengjiCastTool(port) {
  return { ...QIANDENGJI_CAST_TOOL, handler: async (args) => invokeQiandengjiCast(port, args) };
}

// integrations/qiandengji/engine/portable-storage.ts
import { Vec3 } from "vec3";
import { itemCustomName, zhName, invCount, itemPredOf, invItemNamed, resolveAt, CONTAINER_FIND } from "agent-mc-world/extension";
function portableStorageMisuseNote(bot, steps) {
  if (!bot?.inventory?.items) return null;
  const portable = bot.inventory.items().find((item) => item.name === "player_head" && /背包|backpack|rucksack|satchel/i.test((itemCustomName(item) ?? "").replace(/§./g, "")));
  if (!portable) return null;
  const name = itemCustomName(portable) ?? zhName(portable.name);
  const opener = steps[0];
  if (opener?.skill === "use" && opener.item && !opener.at && invItemNamed(bot, opener.item) === portable) {
    for (const step of steps.slice(1)) {
      if (step.skill !== "stow" || step.into !== "open") continue;
      const held = invCount(bot, itemPredOf(bot, step.item, step.pick));
      if (held < step.count) {
        return `${name}\u7A97\u53E3\u91CC\u7684\u7269\u54C1\u8FD8\u4E0D\u5728\u968F\u8EAB\u680F\uFF1Bstow \u662F\u628A\u968F\u8EAB\u7269\u54C1\u653E\u8FDB\u7A97\u53E3\uFF0C\u5305\u91CC\u53EA\u6709${zhName(step.item)}\xD7${held}\uFF0C\u672C\u5355\u5374\u8981\u5B58\xD7${step.count}\u3002\u60F3\u6E05\u7A7A\u968F\u8EAB\u5BB9\u5668\uFF0C\u8BF7\u5728\u540C\u4E00\u5355\u7528 use item + take from:"open"\uFF0C\u518D\u53E6\u8D77\u4E00\u5355\u5B58\u8FDB\u5730\u9762\u7BB1\uFF1B\u539F\u961F\u5217\u4FDD\u7559`;
      }
    }
  }
  for (const step of steps) {
    if (step.skill === "stow" && itemPredOf(bot, step.item, step.pick)(portable.name, portable)) {
      return `${name}\u662F\u968F\u8EAB\u5BB9\u5668\uFF0C\u4E0D\u8981\u628A\u5B83\u5F53\u666E\u901A\u73A9\u5BB6\u5934\u5B58\u5165\u7BB1\u5B50\u3002\u8981\u6574\u7406\u5185\u5BB9\uFF0C\u5148\u5728\u540C\u4E00\u5355\u6267\u884C use item:${portable.name} + take from:"open"\uFF0C\u628A\u7269\u54C1\u53D6\u5230\u968F\u8EAB\u680F\uFF1B\u518D\u53E6\u8D77\u4E00\u5355 stow \u5230\u5730\u9762\u7BB1\u3002\u7A97\u53E3\u5728\u6BCF\u5355\u7ED3\u675F\u65F6\u81EA\u52A8\u5173\u95ED\uFF1B\u539F\u961F\u5217\u4FDD\u7559`;
    }
    if (step.skill === "use" && step.item && invItemNamed(bot, step.item) === portable && step.at) {
      try {
        const target = resolveAt(bot, step.at);
        const block = bot.blockAt?.(new Vec3(target.x, target.y, target.z));
        if (block && CONTAINER_FIND.includes(block.name)) {
          return `${name}\u70B9\u5730\u9762\u7BB1\u53EA\u4F1A\u6253\u5F00\u90A3\u4E2A\u7BB1\u5B50\uFF0C\u4E0D\u4F1A\u6574\u7406\u968F\u8EAB\u5BB9\u5668\u3002\u6253\u5F00\u5730\u9762\u7BB1\u7528 use at\uFF1B\u6253\u5F00\u968F\u8EAB\u5BB9\u5668\u7528 use item \u4E14\u4E0D\u5E26 at\uFF1B\u539F\u961F\u5217\u4FDD\u7559`;
        }
      } catch {
      }
    }
  }
  return null;
}

// integrations/qiandengji/engine/storage-trade-query.ts
var stashTakePrefix = /^\/mycli\s+arena\s+stash\s+take(?:\s|$)/i;
function stashTakeArguments(command) {
  const request = /^\/mycli[ \t]+arena[ \t]+stash[ \t]+take[ \t]+(\+?\d+)(?:[ \t]+(\+?\d+))?$/i.exec(command.trim());
  if (!request) return null;
  const slot = Number(request[1]);
  const limit = Number(request[2] ?? 64);
  return slot >= 1 && slot <= 540 && limit >= 1 && limit <= 64 ? { slot, limit } : null;
}
function stashTakeAdmission(steps) {
  const index = steps.findIndex((step) => {
    if (step.skill === "server_travel") return stashTakePrefix.test(step.command.trim());
    return step.skill === "chat" && stashTakePrefix.test(step.text.trim()) && !stashTakeArguments(step.text);
  });
  if (index < 0) return null;
  return `\u7B2C ${index + 1} \u6B65\u672A\u53D1\u9001\u3002\u7528 chat.text \u53D1\u9001 /mycli arena stash take <\u5168\u5C40\u7BB1\u69FD 1\u2013540> [\u6570\u91CF 1\u201364]\u3002\u5148\u7528 storage.stash \u67E5\u8BE2\u5BF9\u5E94\u9875\u7684\u7269\u54C1\u548C\u5B9E\u9645\u69FD\u53F7\u3002\u5F85\u5165\u7BB1\u7269\u54C1\u5148\u6309\u670D\u52A1\u7AEF\u56DE\u6267\u6253\u5F00\u6307\u5B9A\u9875\uFF0C\u518D\u67E5\u8BE2\u5DF2\u5165\u7BB1\u7684\u69FD\u53F7\u3002\u5F85\u9886\u5956\u52B1\u5217\u8868\u4E2D\u7684\u69FD\u53F7\u4E0D\u80FD\u7528\u4E8E\u53D6\u4E2A\u4EBA\u7BB1\u3002`;
}
function stashTakeArrival(command) {
  const request = stashTakeArguments(command);
  if (!request) return;
  const { slot, limit } = request;
  return (line) => {
    if (line === `MC_STASH_TAKE slot=${slot} moved=0 reason=empty`) return { rejected: `\u4E2A\u4EBA\u7BB1\u69FD ${slot} \u5DF2\u7A7A\uFF0C\u672A\u53D6\u51FA\u7269\u54C1\u3002` };
    const receipt = /^MC_STASH_TAKE slot=(\d{1,3}) id=minecraft:([a-z0-9_]+) moved=(\d{1,2})$/.exec(line);
    if (!receipt || Number(receipt[1]) !== slot) return null;
    const moved = Number(receipt[3]);
    if (moved > limit) return null;
    return moved ? { item: receipt[2], moved } : { rejected: `\u4E2A\u4EBA\u7BB1\u69FD ${slot} \u5B9E\u9645\u8F6C\u5165 0 \u4EF6\uFF0C\u5148\u68C0\u67E5\u968F\u8EAB\u5BB9\u91CF\u3002` };
  };
}
var object = (x) => !!x && typeof x === "object" && !Array.isArray(x);
var integer = (x, min = 0) => Number.isSafeInteger(x) && Number(x) >= min;
var noArgs = { type: "array", minItems: 0, maxItems: 0, items: { type: "string" } };
var pageArgs = (max, required = true) => ({
  type: "array",
  minItems: required ? 1 : 0,
  maxItems: 1,
  items: { type: "string", pattern: "^[1-9][0-9]{0,3}$", maxLength: 4, description: `\u9875\u7801 1\u2013${max}` }
});
var page = (args, max, optional = false) => optional && !args.length ? 1 : args.length === 1 && /^[1-9][0-9]{0,3}$/.test(args[0]) && Number(args[0]) <= max ? Number(args[0]) : null;
function json(text2, marker) {
  if (!text2.startsWith(marker + " ") || /[\r\n]/.test(text2)) return null;
  try {
    const value = JSON.parse(text2.slice(marker.length + 1));
    return object(value) ? value : null;
  } catch {
    return null;
  }
}
function itemRow(text2, marker) {
  if (/[\r\n]/.test(text2) || !text2.startsWith(marker + " ")) return null;
  const m = /^slot=(\d+) id=(minecraft:[a-z0-9_]+) count=(\d+) name=(.*?) enchants=(.*)$/.exec(text2.slice(marker.length + 1));
  return m && integer(Number(m[3]), 1) ? {
    slot: Number(m[1]),
    id: m[2],
    count: Number(m[3]),
    displayName: m[4] === "-" ? null : m[4],
    enchantments: m[5] === "-" ? null : m[5]
  } : null;
}
var pendingTrialRewards = {
  id: "trial.rewards",
  argumentsSchema: noArgs,
  maxReplyParts: 18,
  description: "\u53EA\u8BFB\u672C\u4EBA\u8BD5\u70BC\u5F85\u5165\u7BB1\u5956\u52B1\u4E0E\u53EF\u89C1\u7269\u54C1\u3002\u4E09\u4E2A\u8BA1\u6570\u5168\u96F6\u5373\u53EF\u7ED3\u675F\u672C\u6B21\u9886\u5956\u6838\u67E5\uFF1B\u5DF2\u5165\u7BB1\u7684\u5E93\u5B58\u53E6\u67E5 storage.overview\u3002\u67E5\u8BE2\u4E0D\u8017\u9B54\u529B\u3001\u4E0D\u6253\u5F00\u7A97\u53E3\u3002",
  command: (args) => args.length ? null : "/mycli arena rewards list",
  matchReply(text2, args, username, parts = []) {
    if (!username || args.length) return null;
    const item = itemRow(text2, "MC_REWARD");
    if (item) {
      const slot = item.slot;
      if (!integer(slot) || slot === 8 && item.id !== "minecraft:copper_ingot" || slot > 17 || parts.some((p) => object(p) && p.slot === slot)) return null;
      return { partial: true, data: item };
    }
    const summary = /^MC_REWARD_SUMMARY visible=(\d+) queuedBonus=(\d+) queuedPhotos=(\d+)$/.exec(text2);
    if (!summary || /[\r\n]/.test(text2)) return null;
    const [visible, queuedBonus, queuedPhotos] = summary.slice(1).map(Number);
    if (![visible, queuedBonus, queuedPhotos].every((n) => integer(n)) || visible !== parts.length || Math.min(9, queuedBonus) !== parts.filter((p) => object(p) && integer(p.slot, 9)).length) return null;
    return { ok: true, data: {
      source: "trial_pending_rewards",
      visible,
      queuedBonus,
      queuedPhotos,
      hasPending: visible > 0 || queuedBonus > 0 || queuedPhotos > 0,
      items: parts
    } };
  }
};
var stashOverview = {
  id: "storage.overview",
  description: "\u4E00\u6B21\u53EA\u8BFB\u67E5\u8BE2\u4E2A\u4EBA\u7BB1\u5168\u90E8\u5341\u9875\u7684\u5BB9\u91CF\u3001\u5DF2\u5B58\u6570\u91CF\u3001\u5F85\u5165\u7BB1\u5956\u52B1\uFF0C\u4EE5\u53CA\u5404\u7C7B\u7269\u54C1\u5728\u54EA\u51E0\u9875\u3002\u9700\u8981\u5177\u4F53\u5806\u65F6\u518D\u7528 storage.stash \u67E5\u5BF9\u5E94\u9875\u3002\u968F\u8EAB\u5927\u80CC\u5305\u53E6\u7528 Minepacks\u3002",
  argumentsSchema: noArgs,
  command: (args) => args.length ? null : "/mycli arena stash summary --json",
  matchReply(text2, args, username) {
    if (!username || args.length) return null;
    const value = json(text2, "MC_STASH_OVERVIEW");
    if (!value || value.schemaVersion !== 1 || value.scope !== "personal_stash" || value.pageCount !== 10 || value.pageSize !== 54 || value.capacity !== 540 || !integer(value.occupiedSlots) || !integer(value.freeSlots) || value.occupiedSlots + value.freeSlots !== value.capacity || !integer(value.totalItems, value.occupiedSlots) || !integer(value.pendingRewardEntries) || !object(value.categories)) return null;
    const categories = {};
    let itemCount = 0;
    let slotCount = 0;
    for (const [key, entry] of Object.entries(value.categories)) {
      if (!/^[a-z][a-z0-9_]*$/.test(key) || !object(entry) || !integer(entry.occupiedSlots) || !integer(entry.items, entry.occupiedSlots) || !Array.isArray(entry.pages) || entry.pages.some((p) => !integer(p, 1) || p > 10) || new Set(entry.pages).size !== entry.pages.length || entry.pages.length > entry.occupiedSlots || entry.occupiedSlots === 0 !== (entry.pages.length === 0) || entry.items === 0 !== (entry.occupiedSlots === 0)) return null;
      categories[key] = { items: entry.items, occupiedSlots: entry.occupiedSlots, pages: entry.pages };
      itemCount += entry.items;
      slotCount += entry.occupiedSlots;
    }
    if (!Object.keys(categories).length || itemCount !== value.totalItems || slotCount !== value.occupiedSlots) return null;
    return { ok: true, data: {
      source: "personal_stash",
      scope: "all_pages",
      pageCount: value.pageCount,
      pageSize: value.pageSize,
      capacity: value.capacity,
      occupiedSlots: slotCount,
      freeSlots: value.freeSlots,
      totalItems: itemCount,
      pendingRewardEntries: value.pendingRewardEntries,
      categories
    } };
  }
};
var tidyPreview = {
  id: "storage.tidy.preview",
  description: '\u4E00\u952E\u6574\u7406\u672C\u4EBA\u968F\u8EAB\u80CC\u5305\u524D\u5148\u770B\u9884\u8BA1\u80FD\u817E\u51E0\u683C\u3002\u9ED8\u8BA4\u53EA\u5408\u5806\uFF0Carguments:["discard-common"] \u540C\u65F6\u9884\u89C8\u666E\u901A\u6742\u7269\u7684\u79CD\u7C7B\u548C\u6570\u91CF\uFF0C\u4E24\u79CD\u67E5\u8BE2\u90FD\u4E0D\u6539\u7269\u54C1\u3002\u4ED3\u5E93\u548C Minepacks \u53E6\u67E5\u3002',
  argumentsSchema: {
    type: "array",
    minItems: 0,
    maxItems: 1,
    items: { type: "string", pattern: "^discard-common$", maxLength: 14 }
  },
  command: (args) => args.length === 0 ? "/mycli inventory tidy --dry-run --json" : args.length === 1 && args[0] === "discard-common" ? "/mycli inventory tidy --dry-run --discard-common --json" : null,
  matchReply(text2, args, username) {
    if (!username || args.length > 1 || args.length === 1 && args[0] !== "discard-common") return null;
    const v = json(text2, "MC_INVENTORY_TIDY");
    if (!v || v.schemaVersion !== 1 || v.action !== "tidy" || v.success !== true || v.reason !== "preview" || v.dryRun !== true || v.automatic !== false || v.changed !== false || v.serverOperator !== false || v.discardCommon !== (args.length === 1) || typeof v.requestId !== "string" || !v.requestId || typeof v.playerUuid !== "string" || !v.playerUuid || !integer(v.beforeOccupied) || Number(v.beforeOccupied) > 36 || !integer(v.afterOccupied) || !integer(v.freedSlots) || Number(v.beforeOccupied) - Number(v.afterOccupied) !== v.freedSlots || !integer(v.mergedItems) || !Array.isArray(v.discarded) || v.discarded.length > 27 || !v.discardCommon && v.discarded.length > 0 || !v.discarded.every((row) => object(row) && typeof row.id === "string" && /^minecraft:[a-z0-9_]+$/.test(row.id) && integer(row.count, 1))) return null;
    return { ok: true, data: {
      source: "inventory",
      dryRun: true,
      playerUuid: v.playerUuid,
      serverRequestId: v.requestId,
      beforeOccupied: v.beforeOccupied,
      projectedOccupied: v.afterOccupied,
      projectedFreedSlots: v.freedSlots,
      mergedItems: v.mergedItems,
      wouldDiscard: v.discarded.map((row) => ({ id: row.id, count: row.count }))
    } };
  }
};
var playerUuidPattern = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
var itemId = /^minecraft:[a-z0-9_]+$/;
var slots = (n) => integer(n) && Number(n) <= 36;
function inventoryBatchPreviews(playerUuid) {
  return ["clean", "store"].map((action) => ({
    id: `storage.${action}.preview`,
    description: action === "clean" ? "\u4E00\u952E\u6574\u7406\u672C\u4EBA\u968F\u8EAB\u80CC\u5305\u5E76\u6E05\u7406\u666E\u901A\u6742\u7269\u7684\u53EA\u8BFB\u9884\u89C8\u3002\u770B\u9884\u8BA1\u9500\u6BC1\u7684\u7269\u54C1\u3001\u5408\u5806\u6570\u91CF\u548C\u9884\u8BA1\u817E\u683C\uFF1B\u4E0D\u5220\u9664\u7269\u54C1\u3001\u4E0D\u5356\u88C5\u5907\u3002arguments:[]\u3002" : "\u4E00\u6B21\u9884\u89C8\u628A\u968F\u8EAB\u591A\u4F59\u7269\u8D44\u5B58\u5165\u5341\u9875\u4E2A\u4EBA\u7BB1\uFF0C\u67E5\u770B\u53EF\u8F6C\u5165\u7684\u7269\u54C1\u548C\u6570\u91CF\u3001\u9884\u8BA1\u817E\u683C\u3001\u5BB9\u91CF\u548C\u8FDC\u7A0B\u9B54\u529B\u8D39\u7528\u3002arguments:[]\u3002\u4E0D\u8F6C\u79FB\u3001\u4E0D\u6350\u732E\u3001\u4E0D\u6263\u8D39\u3002",
    argumentsSchema: noArgs,
    command: (args) => args.length ? null : `/mycli inventory ${action} --dry-run --json`,
    matchReply(text2, args, username) {
      if (args.length || !username || !playerUuid || !playerUuidPattern.test(playerUuid)) return null;
      const v = json(text2, "MC_INVENTORY_BATCH");
      if (!v || v.schemaVersion !== 1 || v.action !== action || typeof v.playerUuid !== "string" || v.playerUuid.toLowerCase() !== playerUuid.toLowerCase() || v.serverOperator === true || v.changed === true || v.outcomeUnknown === true || v.success !== true || v.reason !== "preview" || v.dryRun !== true || v.freedSlots !== 0 || !slots(v.plannedFreedSlots)) return null;
      const result = { action, playerUuid: v.playerUuid, dryRun: true, freedSlots: 0, plannedFreedSlots: v.plannedFreedSlots };
      if (action === "clean") {
        if (v.changed !== false || v.automatic !== false || v.discardCommon !== true || v.serverOperator !== false || typeof v.requestId !== "string" || !v.requestId || !slots(v.beforeOccupied) || !slots(v.afterOccupied) || v.beforeOccupied - v.afterOccupied !== v.plannedFreedSlots || !integer(v.mergedItems) || !Array.isArray(v.discarded) || v.discarded.length > 36 || !v.discarded.every((row) => object(row) && typeof row.id === "string" && itemId.test(row.id) && integer(row.count, 1))) return null;
        return { ok: true, data: {
          ...result,
          beforeOccupied: v.beforeOccupied,
          projectedOccupied: v.afterOccupied,
          plannedMergeItems: v.mergedItems,
          wouldDiscard: v.discarded.map(({ id: id2, count }) => ({ id: id2, count })),
          serverRequestId: v.requestId
        } };
      }
      if (v.moved !== 0 || v.manaSpent !== 0 || !integer(v.quotedMana) || !integer(v.leftForCapacity) || !integer(v.leftForUnavailableChest) || !integer(v.plannedItems) || !object(v.items)) return null;
      const items = Object.entries(v.items);
      if (items.length > 36 || !items.every(([id2, count]) => itemId.test(id2) && integer(count, 1)) || items.reduce((n, [, count]) => n + Number(count), 0) !== v.plannedItems || v.plannedFreedSlots > Number(v.plannedItems)) return null;
      return { ok: true, data: {
        ...result,
        moved: 0,
        manaSpent: 0,
        plannedItems: v.plannedItems,
        quotedMana: v.quotedMana,
        leftForCapacity: v.leftForCapacity,
        leftForUnavailableChest: v.leftForUnavailableChest,
        wouldStore: v.items
      } };
    }
  }));
}
function storage(kind) {
  const stash = kind === "stash";
  return {
    id: `storage.${kind}`,
    maxReplyParts: stash ? 54 : 36,
    description: stash ? '\u53EA\u8BFB\u4E2A\u4EBA\u4ED3\u5E93\u4E00\u9875\uFF0Carguments:["1".."10"]\uFF1B10\u9875\xD754\u683C\uFF0C\u4E0D\u662FMinepacks\u5927\u80CC\u5305\u3002\u4FDD\u7559\u5168\u5C40\u7BB1\u69FD1\u2013540\u3001\u5B9E\u9645\u7269\u54C1\u4E0E\u7A7A\u683C\uFF1B\u5176\u4ED6\u9875\u672A\u8BFB\uFF0C\u4E0D\u5168\u91CF\u5E38\u9A7B\u3002\u4E0D\u4F1A\u5F00\u7A97\u3001\u642C\u7269\u6216\u6263\u9B54\u529B\u3002\u5B58\u5165\u7528\u8EAB\u4F53\u547D\u4EE4 /mycli arena stash putslot <\u968F\u8EAB\u69FD0\u201335> <\u6570\u91CF>\uFF1B\u53D6\u51FA\u7528 stash take <\u5168\u5C40\u7BB1\u69FD> <\u6570\u91CF>\u3002' : "\u53EA\u8BFB\u672C\u4EBA\u968F\u8EAB\u80CC\u5305\u5404\u4E2A\u670D\u52A1\u7AEF\u69FD\u4F4D0\u201335\uFF0Carguments:[]\u3002\u7528\u4E8E\u4ED3\u50A8putslot\u548C\u56DE\u6536quote bag\uFF1B\u4E0D\u662FMineflayer\u7A97\u53E3\u69FD\u53F7\uFF0C\u4E0D\u542B\u76D4\u7532/\u526F\u624B\uFF0C\u4E0D\u505A\u642C\u8FD0\u3002",
    argumentsSchema: stash ? pageArgs(10) : noArgs,
    command: (args) => stash ? page(args, 10) === null ? null : `/mycli arena stash list ${args[0]}` : args.length ? null : "/mycli arena stash inventory",
    matchReply: (text2, args, username, parts = []) => {
      const p = stash ? page(args, 10) : args.length ? null : 1;
      if (!username || p === null) return null;
      const start = stash ? (p - 1) * 54 + 1 : 0, end = stash ? p * 54 : 35;
      const item = itemRow(text2, stash ? "MC_STASH" : "MC_INVENTORY");
      if (item) return integer(item.slot) && item.slot >= start && item.slot <= end && !parts.some((x) => object(x) && x.slot === item.slot) ? { partial: true, data: item } : null;
      if (!stash) return text2 === "MC_INVENTORY_SUMMARY slots=0-35" ? { ok: true, data: {
        source: "inventory",
        slotConvention: "Bukkit inventory 0\u201335",
        items: parts,
        occupied: parts.length,
        capacity: 36,
        freeSlots: 36 - parts.length,
        complete: true
      } } : null;
      const summary = /^MC_STASH_SUMMARY occupied=(\d+)\/54 page=(\d+) pages=10 capacity=540$/.exec(text2);
      if (!summary || Number(summary[1]) !== parts.length || Number(summary[2]) !== p) return null;
      return { ok: true, data: {
        source: "personal_stash",
        page: p,
        pages: 10,
        pageSize: 54,
        capacity: 540,
        occupiedOnPage: parts.length,
        freeSlotsOnPage: 54 - parts.length,
        slotRange: [start, end],
        items: parts,
        complete: true,
        scope: "requested_page_only",
        pendingRewards: null,
        note: "\u5176\u4ED6\u9875\u4E0E\u5F85\u5165\u7BB1\u5956\u52B1\u672A\u6838\u5B9E\uFF1B\u5F00\u7A97\u540E\u624D\u88C5\u5165\u5F85\u9886\u5956\u52B1\u3002putslot\u81EA\u52A8\u8DE8\u9875\u627E\u7A7A\u4F4D\uFF1Btake\u4F7F\u7528\u672C\u56DE\u6267\u7684\u5168\u5C40\u7BB1\u69FD\u3002"
      } };
    }
  };
}
function compactEconomy(value) {
  const { item, ...rest } = value;
  if (!object(item)) return { ...rest, item };
  const { serializedItemBase64: _binary, ...details } = item;
  return { ...rest, item: details };
}
function economy(kind) {
  const list = kind === "shop" || kind === "recycle";
  const action = list ? `${kind}_list` : kind;
  const id2 = kind === "recycle_status" ? "trade.recycle.status" : kind === "wallet" ? "trade.wallet" : `trade.${kind}.list`;
  return {
    id: id2,
    ...list ? { maxReplyParts: kind === "shop" ? 64 : 12 } : {},
    description: kind === "shop" ? "\u53EA\u8BFB\u91D1\u5E01\u5546\u57CE\u5B8C\u6574\u76EE\u5F55/\u6BCF\u4EFD\u6570\u91CF/\u5355\u4EF7\u3002arguments:[]\uFF1B\u4E70\u7269\u7528 /mycli trade shop buy <offerId> <\u4EFD\u6570>\uFF0C\u5546\u54C1\u5165\u4E2A\u4EBA\u7BB1/\u5F85\u5165\u7BB1\u961F\u5217\uFF1B\u67E5\u8BE2\u4E0D\u8D2D\u4E70\u3002" : kind === "recycle" ? '\u53EA\u8BFB\u53EF\u56DE\u6536\u88C5\u5907\uFF0Carguments:["\u9875\u78011\u201348"]\u3002\u5305\u542B10\u9875\u4E2A\u4EBA\u7BB1chest\u548C\u968F\u8EABbag\u7684\u771F\u5B9E\u69FD\u53F7\u3001\u540D\u79F0\u3001\u8010\u4E45\u3001\u9644\u9B54\u548C\u5355\u4EF7\u3002\u5148\u7528 /mycli trade recycle quote <source> <slot> <\u6570\u91CF> \u62A5\u4EF7\uFF0C\u518Dsell <quoteId>\uFF1B\u67E5\u8BE2\u4E0D\u51FA\u552E\u3002' : "\u53EA\u8BFB\u91D1\u5E01\u4F59\u989D/\u5F85\u5BF9\u8D26\u72B6\u6001\uFF0Carguments:[]\uFF1B\u91D1\u5E01\u4E0D\u662F\u968F\u8EAB\u7EFF\u5B9D\u77F3\u3002pending/unverified\u4E0D\u91CD\u8BD5\u4E70\u5356\uFF0C\u4FDD\u7559\u539F\u4EA4\u6613ID\u4E0E\u7269\u54C1\u8BC1\u636E\u3002",
    argumentsSchema: kind === "recycle" ? pageArgs(48) : noArgs,
    command: (args) => kind === "recycle" ? page(args, 48) === null ? null : `/mycli trade recycle list ${args[0]} --json` : args.length ? null : kind === "wallet" ? "/mycli arena wallet --json" : kind === "recycle_status" ? "/mycli trade recycle status --json" : "/mycli trade shop list --json",
    matchReply: (text2, args, username, parts = []) => {
      if (!username || (kind === "recycle" ? page(args, 48) === null : args.length)) return null;
      const value = json(text2, "MC_ARENA_ECONOMY");
      if (!value || value.schemaVersion !== 1 || value.queryOnly !== true || typeof value.success !== "boolean" || typeof value.requestId !== "string" || !value.requestId || value.requestId.length > 64) return null;
      if (!list) return value.action === action ? { ok: value.success, data: compactEconomy(value) } : null;
      if (parts.length && object(parts[0]) && value.requestId !== parts[0].requestId) return null;
      if (value.action === action && value.success === false && !parts.length) return { ok: false, data: compactEconomy(value) };
      if (value.success !== true) return null;
      if (value.action === action) {
        if (!object(value.item) || typeof value.item.id !== "string" || !integer(value.item.quantity, 1)) return null;
        const valid = kind === "shop" ? typeof value.offerId === "string" && integer(value.unitPrice) && !parts.some((x) => object(x) && x.offerId === value.offerId) : (value.source === "bag" && integer(value.slot) && value.slot <= 35 || value.source === "chest" && integer(value.slot, 1) && value.slot <= 540) && integer(value.unitPrice) && !parts.some((x) => object(x) && x.source === value.source && x.slot === value.slot);
        return valid ? { partial: true, data: compactEconomy(value) } : null;
      }
      if (value.action !== action + "_end") return null;
      if (kind === "shop" ? value.quantity !== parts.length : value.page !== Number(args[0]) || !integer(value.total) || !integer(value.pages, 1) || Math.min(12, Math.max(0, value.total - (Number(args[0]) - 1) * 12)) !== parts.length) return null;
      return { ok: true, data: { ...compactEconomy(value), complete: true, items: parts } };
    }
  };
}
function market(kind) {
  const idPattern = /^[A-Za-z0-9_-]{1,64}$/;
  const valid = (args) => kind === "info" ? args.length === 1 && idPattern.test(args[0]) : page(args, 1200, true) !== null;
  return {
    id: `trade.auction.${kind}`,
    description: `\u53EA\u8BFB\u73A9\u5BB6\u4EA4\u6613\u884C${kind === "mine" ? "\u672C\u4EBA\u6302\u5355" : kind === "info" ? "\u5546\u54C1\u8BE6\u60C5" : "\u76EE\u5F55"}\u3002${kind === "info" ? 'arguments:["\u5F53\u524D\u8FD4\u56DE\u7684\u5546\u54C1ID"]' : 'arguments:["\u9875\u7801"]\uFF0C\u9ED8\u8BA41\uFF0C\u6BCF\u98758\u9879'}\u3002buy\u6309\u6574\u5355\u8D2D\u4E70\uFF1Bsell <\u6574\u7EC4\u603B\u4EF7>\u5148\u62A5\u4EF7\uFF0Cconfirm\u624D\u4E0A\u67B6\uFF1Bcancel\u8FD4\u56DE\u4E2A\u4EBA\u7BB1\u3002\u6B64\u67E5\u8BE2\u4E0D\u4E70\u5356\u3001\u4E0D\u9886\u53D6\u3002`,
    argumentsSchema: kind === "info" ? {
      type: "array",
      minItems: 1,
      maxItems: 1,
      items: { type: "string", pattern: idPattern.source, maxLength: 64 }
    } : pageArgs(1200, false),
    command: (args) => valid(args) ? `/mycli trade auction ${kind} ${args[0] ?? "1"} --json` : null,
    matchReply: (text2, args, username) => {
      if (!username || !valid(args)) return null;
      const value = json(text2, "MC_MARKET");
      if (!value || value.success !== true || Object.hasOwn(value, "result") || Object.hasOwn(value, "quoteId")) return null;
      const matches = kind === "info" ? value.id === args[0] && typeof value.state === "string" && typeof value.name === "string" : value.page === page(args, 1200, true) && integer(value.pages, 1) && Array.isArray(value.listings) && value.listings.length <= 8;
      return matches ? { ok: true, data: value } : null;
    }
  };
}
var STORAGE_TRADE_QUERIES = [
  storage("inventory"),
  tidyPreview,
  stashOverview,
  storage("stash"),
  pendingTrialRewards,
  economy("shop"),
  economy("recycle"),
  economy("wallet"),
  economy("recycle_status"),
  market("list"),
  market("mine"),
  market("info")
];

// integrations/qiandengji/engine/native-rpg.ts
var object2 = (value) => !!value && typeof value === "object" && !Array.isArray(value);
var number = (value) => typeof value === "number" && Number.isFinite(value);
var nonnegative = (value) => number(value) && value >= 0;
var points = (value) => Number.isSafeInteger(value) && Number(value) >= 0;
var id = (value) => typeof value === "string" && /^[a-z][a-z0-9_:-]{0,63}$/i.test(value);
function readNativeTalentTree(value, at) {
  if (!object2(value) || !Number.isFinite(Date.parse(at)) || !points(value.talentPoints) || !object2(value.allocated) || Object.keys(value.allocated).length > 32 || !object2(value.nodes) || Object.keys(value.nodes).length > 128) return null;
  const allocated = {}, nodes = {};
  for (const [key, raw] of Object.entries(value.allocated)) {
    if (!id(key) || !Array.isArray(raw) || raw.length > 128 || !raw.every(id)) return null;
    allocated[key] = [...new Set(raw)];
  }
  for (const [key, raw] of Object.entries(value.nodes)) {
    if (!id(key) || !object2(raw) || raw.id !== key || !points(raw.cost) || !Array.isArray(raw.prerequisites) || raw.prerequisites.length > 32 || !raw.prerequisites.every(id)) return null;
    const text2 = (v, max) => typeof v === "string" && v.length <= max && !/[\u0000-\u001f\u007f]/.test(v) ? v : void 0;
    nodes[key] = {
      id: key,
      cost: raw.cost,
      prerequisites: [...new Set(raw.prerequisites)],
      ...text2(raw.displayName, 80) ? { displayName: text2(raw.displayName, 80) } : {},
      ...text2(raw.description, 512) ? { description: text2(raw.description, 512) } : {}
    };
  }
  return { observedAt: at, talentPoints: value.talentPoints, allocated, nodes };
}
function readNativeSkills(value, at, saved = false) {
  if (!object2(value) || !Number.isFinite(Date.parse(at))) return null;
  const ids = (values) => Array.isArray(values) && values.length <= 256 && values.every(id) ? [...new Set(values)] : null;
  const available = ids(value.available), common = ids(value.common);
  const learnable = ids(saved ? value.learnable : Array.isArray(value.learnable) ? value.learnable.map((v) => object2(v) ? v.id : null) : null);
  if (!available || !common || !learnable || !points(value.skillPoints)) return null;
  const node = (v) => {
    if (!object2(v) || !id(v.id) || !points(v.requiredLevel) || !points(v.cost)) return null;
    const bonuses = object2(v.permanentBonuses) && Object.keys(v.permanentBonuses).length <= 16 && Object.entries(v.permanentBonuses).every(([key, value2]) => id(key) && number(value2) && Math.abs(value2) <= 1e6) ? { ...v.permanentBonuses } : void 0;
    return {
      id: v.id,
      requiredLevel: v.requiredLevel,
      cost: v.cost,
      ...typeof v.displayName === "string" && v.displayName.length <= 80 && !/[\u0000-\u001f\u007f]/.test(v.displayName) ? { displayName: v.displayName } : {},
      ...typeof v.description === "string" && v.description.length <= 512 && !/[\u0000-\u001f\u007f]/.test(v.description) ? { description: v.description } : {},
      ...bonuses ? { permanentBonuses: bonuses } : {},
      ...id(v.grantedSpellId) ? { grantedSpellId: v.grantedSpellId } : {}
    };
  };
  const rawNodes = saved ? value.nodes : value.learnable;
  const parsed = (Array.isArray(rawNodes) ? rawNodes : []).map(node).filter((v) => v !== null);
  return {
    observedAt: at,
    available,
    common,
    learnable,
    skillPoints: value.skillPoints,
    ...parsed.length ? { nodes: parsed } : {},
    ...value.activeSpell === "" || id(value.activeSpell) ? { activeSpell: value.activeSpell } : {}
  };
}
function nativeRpgMessage(text2) {
  if (text2.length > 65536 || !text2.startsWith("MC_RPG ") || /[\r\n]/.test(text2)) return null;
  try {
    const value = JSON.parse(text2.slice(7));
    return object2(value) ? value : null;
  } catch {
    return null;
  }
}
function readNativeProfessionSkillInfo(value, at) {
  if (!object2(value) || (value.queryOnly ?? value.queryonly) !== true || !object2(value.skill) || typeof value.learned !== "boolean" || !Number.isFinite(Date.parse(at))) return null;
  const node = value.skill;
  if (!id(node.id) || value.id !== void 0 && value.id !== node.id) return null;
  const text2 = (v, limit) => typeof v === "string" && !!v.trim() && v.length <= limit && !/[\u0000-\u001f\u007f-\u009f\u00a7]/.test(v) ? v : null;
  const name = text2(value.name ?? node.displayName ?? node.displayname, 80);
  if (!name) return null;
  const level = node.requiredLevel ?? node.requiredlevel;
  const grants = value.grantedSpellId ?? node.grantedSpellId ?? node.grantedspellid;
  return {
    id: node.id,
    name,
    observedAt: at,
    classId: id(node.archetype) ? node.archetype.toLowerCase() : null,
    requiredLevel: points(level) ? level : null,
    learningPointCost: points(node.cost) ? node.cost : null,
    grantedSpellId: id(grants) ? grants : null,
    description: text2(node.description, 1024),
    requirements: text2(value.requirements, 1024),
    mana: nonnegative(value.mana) ? value.mana : null,
    cooldownMs: nonnegative(value.cooldownMs) ? value.cooldownMs : null,
    equipmentAccess: typeof value.equipmentAccess === "boolean" ? value.equipmentAccess : null,
    eligibilityAtQuery: {
      learned: value.learned,
      available: typeof value.available === "boolean" ? value.available : null,
      source: id(value.source) ? value.source : null
    }
  };
}
var NativeProfessionSkillBook = class {
  observations = /* @__PURE__ */ new Map();
  clear() {
    this.observations.clear();
  }
  has(skillId) {
    return this.observations.has(skillId);
  }
  observe(info) {
    const previous = this.observations.get(info.id);
    if (previous && Date.parse(previous.observedAt) > Date.parse(info.observedAt)) return;
    this.observations.delete(info.id);
    this.observations.set(info.id, info);
    if (this.observations.size > 64) this.observations.delete(this.observations.keys().next().value);
  }
  readout(skillId, abilities) {
    const info = this.observations.get(skillId);
    if (!info) return null;
    const newer = abilities && info.grantedSpellId && Date.parse(abilities.at) >= Date.parse(info.observedAt) ? { available: abilities.ids.includes(info.grantedSpellId), observedAt: abilities.at, source: abilities.source } : null;
    const superseded = newer && info.eligibilityAtQuery.available !== null && newer.available !== info.eligibilityAtQuery.available;
    return "[\u672C\u8FDE\u63A5\u804C\u4E1A\u6280\u80FD\u8BE6\u60C5\uFF1B\u5B66\u4E60\u4E0E\u88C5\u5907\u6765\u6E90\u53D6\u81EA\u67E5\u8BE2\u5F53\u65F6\uFF0C\u547D\u4E2D\u6548\u679C\u53E6\u67E5\u670D\u52A1\u5668\u56DE\u6267]\n" + JSON.stringify({
      ...info,
      eligibilityAtQuery: superseded ? null : info.eligibilityAtQuery,
      latestSpellAvailability: newer,
      effectVerified: null
    });
  }
};
function readNativeSkillDetail(value, at) {
  const text2 = (v, max) => typeof v === "string" && !!v.trim() && v.length <= max && !/[\u0000-\u001f\u007f-\u009f\u00a7]/.test(v);
  if (!object2(value) || value.schemaVersion !== 1 || !id(value.id) || !text2(value.name, 80) || !text2(value.command, 256) || !value.command.startsWith("/mycli ") || !Number.isFinite(Date.parse(at))) return null;
  const cast = `/mycli cast ${value.id}`;
  return {
    id: value.id,
    name: value.name,
    command: value.command,
    observedAt: at,
    source: "MC_RPG",
    invocation: value.command === cast || value.command.startsWith(cast + " ") ? "cast" : "command",
    mana: nonnegative(value.mana) ? value.mana : null,
    cooldownMs: nonnegative(value.cooldownMs) ? value.cooldownMs : null,
    cooldownRemainingMs: nonnegative(value.cooldownRemainingMs) ? value.cooldownRemainingMs : null,
    effect: text2(value.effect, 1024) ? value.effect : null,
    requires: text2(value.requires, 1024) ? value.requires : null,
    available: typeof value.available === "boolean" ? value.available : null
  };
}
function readNativeSkillInvocations(value, at) {
  if (!object2(value) || value.schemaVersion !== 1 || value.kind !== "skill_invocations" || value.queryOnly !== true || !Array.isArray(value.entries) || value.entries.length > 64) return null;
  const entries = value.entries.map((entry) => {
    if (object2(entry) && object2(entry.invocation)) {
      const route = entry.invocation;
      if (!id(entry.id) || route.kind !== "cast" && route.kind !== "command") return null;
      const detail = readNativeSkillDetail({ schemaVersion: 1, id: entry.id, name: entry.id, command: route.command }, at);
      return detail?.invocation === route.kind ? detail : null;
    }
    return readNativeSkillDetail(entry, at);
  });
  return entries.every((e) => e !== null) && new Set(entries.map((e) => e.id)).size === entries.length ? entries : null;
}
function guidance(value) {
  if (!object2(value)) return void 0;
  const text2 = (v, max) => typeof v === "string" && v.trim().length > 0 && v.length <= max && !/[\u0000-\u001f\u007f]/.test(v);
  if (!id(value.step) || !id(value.reason) || !text2(value.nextAction, 512)) return void 0;
  const command = (v) => text2(v, 180) && v.startsWith("/mycli ") ? v : void 0;
  const missing = Array.isArray(value.missing) && value.missing.length <= 12 && value.missing.every((v) => text2(v, 120)) ? [...value.missing] : null;
  return {
    step: value.step,
    reason: value.reason,
    nextAction: value.nextAction,
    ...command(value.nextCommand) ? { nextCommand: command(value.nextCommand) } : {},
    ...command(value.verifyCommand) ? { verifyCommand: command(value.verifyCommand) } : {},
    queryOnly: typeof value.queryOnly === "boolean" ? value.queryOnly : null,
    requiresWorldAction: typeof value.requiresWorldAction === "boolean" ? value.requiresWorldAction : null,
    missing
  };
}
function economy2(value) {
  if (!object2(value) || typeof value.available !== "boolean") return void 0;
  return { available: value.available, balance: value.available && number(value.balance) ? value.balance : null };
}
function mana(current, max) {
  return nonnegative(current) && nonnegative(max) && current <= max ? { current, max } : void 0;
}
function readNativeRpgStatus(value) {
  if (!object2(value) || value.authority !== "VortexRPG" || !id(value.class) || !points(value.level) || !nonnegative(value.xp) || !nonnegative(value.nextLevelXp) || !mana(value.mana, value.maxMana) || typeof value.preview !== "boolean" || !economy2(value.economy)) return null;
  const next = guidance(value.guide);
  return {
    available: true,
    classId: value.class,
    level: value.level,
    xp: value.xp,
    nextLevelXp: value.nextLevelXp,
    mana: mana(value.mana, value.maxMana),
    economy: economy2(value.economy),
    preview: value.preview,
    ...next ? { guidance: next } : {}
  };
}
function readNativeRpgPacket(channel, data) {
  if (channel !== "mcagent:state" || !Buffer.isBuffer(data) || data.length > 65536) return null;
  let payload2;
  try {
    payload2 = JSON.parse(data.toString("utf8"));
  } catch {
    return null;
  }
  if (!object2(payload2) || payload2.schemaVersion !== 1 || !object2(payload2.profession)) return null;
  const value = payload2.profession;
  if (value.backend !== "vortex" || typeof value.available !== "boolean") return null;
  if (!value.available) return { available: false };
  if (!(value.combat === "" || id(value.combat)) || !points(value.level) || !nonnegative(value.xp) || !points(value.skillPoints) || !(value.activeSkill === "" || id(value.activeSkill))) return null;
  const m = object2(value.mana) ? mana(value.mana.current, value.mana.max) : void 0;
  const skillIds = Array.isArray(value.abilities) && value.abilities.length <= 48 && value.abilities.every((a) => object2(a) && id(a.id)) ? [...new Set(value.abilities.map((a) => String(a.id).replace(/^mycli:/, "")))] : void 0;
  return {
    available: true,
    classId: value.combat || "none",
    level: value.level,
    xp: value.xp,
    skillPoints: value.skillPoints,
    activeSkill: value.activeSkill,
    ...m ? { mana: m } : {},
    economy: economy2(value.economy),
    ...skillIds ? { skillIds } : {}
  };
}
var names = {
  none: "\u672A\u9009\u804C\u4E1A",
  knight: "\u9A91\u58EB",
  mage: "\u6CD5\u5E08",
  ranger: "\u6E38\u4FA0",
  cleric: "\u7267\u5E08",
  beastmaster: "\u9A6F\u517D\u5E08",
  engineer: "\u5DE5\u7A0B\u5E08"
};
var NativeRpgState = class {
  profile = null;
  learning = null;
  skills = null;
  talents = null;
  abilitySnapshot = null;
  prepared = null;
  details = /* @__PURE__ */ new Map();
  professionInfo = new NativeProfessionSkillBook();
  signature = "";
  reset() {
    this.profile = null;
    this.learning = null;
    this.skills = null;
    this.talents = null;
    this.abilitySnapshot = null;
    this.prepared = null;
    this.details.clear();
    this.professionInfo.clear();
    this.signature = "";
  }
  preparedAbility() {
    return this.prepared && this.profile?.value.available && this.currentAbilities()?.ids.includes(this.prepared) ? this.prepared : null;
  }
  skillDetail(id2) {
    return this.details.get(id2) ?? null;
  }
  hasInvocationInfo(id2) {
    return id2 ? this.details.has(id2) : this.details.size > 0;
  }
  hasProfessionSkillInfo(skillId) {
    return this.professionInfo.has(skillId);
  }
  identity() {
    return this.profile ? { available: this.profile.value.available, classId: this.profile.value.classId } : null;
  }
  currentAbilities() {
    if (this.abilitySnapshot && (!this.skills || Date.parse(this.abilitySnapshot.at) >= Date.parse(this.skills.observedAt)))
      return { ...this.abilitySnapshot, source: "mcagent:state.profession" };
    return this.skills ? { ids: this.skills.available, at: this.skills.observedAt, source: "MC_RPG" } : null;
  }
  chat(text2, at = (/* @__PURE__ */ new Date()).toISOString()) {
    const value = nativeRpgMessage(text2);
    if (!value) return false;
    const tree = readNativeTalentTree(value, at);
    if (tree) {
      if (!this.profile?.value.available || !this.profile.value.classId || this.profile.value.classId === "none") return false;
      const changed = JSON.stringify(this.talents && { ...this.talents, observedAt: "" }) !== JSON.stringify({ ...tree, observedAt: "" });
      this.talents = tree;
      return changed;
    }
    const invocations = readNativeSkillInvocations(value, at);
    if (invocations) {
      for (const detail2 of invocations) {
        this.details.delete(detail2.id);
        this.details.set(detail2.id, detail2);
      }
      while (this.details.size > 64) this.details.delete(this.details.keys().next().value);
      return true;
    }
    const profile = readNativeRpgStatus(value);
    if (profile) return this.update(profile, at, "MC_RPG status");
    const skills = readNativeSkills(value, at);
    if (skills) {
      const changed = JSON.stringify(this.learning?.skills && { ...this.learning.skills, observedAt: "" }) !== JSON.stringify({ ...skills, observedAt: "" });
      this.learning = { points: skills.skillPoints, at, skills };
      this.skills = this.profile?.value.available ? skills : null;
      if (this.skills && skills.activeSpell !== void 0) this.prepared = skills.activeSpell || null;
      return changed;
    }
    const detail = readNativeSkillDetail(value, at);
    if (detail) {
      const old = this.details.get(detail.id);
      this.details.delete(detail.id);
      this.details.set(detail.id, detail);
      while (this.details.size > 64) this.details.delete(this.details.keys().next().value);
      return JSON.stringify(old && { ...old, observedAt: "" }) !== JSON.stringify({ ...detail, observedAt: "" });
    }
    const professionInfo = readNativeProfessionSkillInfo(value, at);
    if (professionInfo) this.professionInfo.observe(professionInfo);
    return false;
  }
  packet(channel, data, at = (/* @__PURE__ */ new Date()).toISOString()) {
    const profile = readNativeRpgPacket(channel, data);
    return profile ? this.update(profile, at, "mcagent:state.profession") : false;
  }
  update(value, at, source) {
    const prior = this.profile?.value;
    if (!value.available || prior?.classId !== value.classId) {
      this.learning = null;
      this.skills = null;
      this.talents = null;
      this.abilitySnapshot = null;
      this.prepared = null;
      this.details.clear();
      this.professionInfo.clear();
    }
    if (value.available && value.activeSkill !== void 0) this.prepared = value.activeSkill || null;
    if (value.skillIds) this.abilitySnapshot = { ids: value.skillIds, at };
    if (value.skillPoints !== void 0 && this.learning?.points !== value.skillPoints)
      this.learning = { points: value.skillPoints, at };
    if (value.available && prior?.available && prior.classId === value.classId) {
      value = {
        ...value,
        ...value.skillPoints === void 0 && prior.skillPoints !== void 0 ? { skillPoints: prior.skillPoints } : {},
        ...value.activeSkill === void 0 && prior.activeSkill !== void 0 ? { activeSkill: prior.activeSkill } : {}
      };
    }
    this.profile = { value, at, source };
    const signature = JSON.stringify([value.available, value.classId, value.level, value.skillPoints, value.activeSkill, value.economy, value.preview, value.guidance, value.skillIds]);
    const changed = signature !== this.signature;
    this.signature = signature;
    return changed;
  }
  brief() {
    const observation = this.profile;
    if (!observation) return "";
    const p = observation.value, head = `[\u539F\u751F RPG \u6700\u8FD1\u89C2\u6D4B] ${observation.source} ${observation.at}\uFF1B`;
    if (!p.available) return head + "\u804C\u4E1A\u540E\u7AEF\u672A\u5C31\u7EEA\uFF0C\u804C\u4E1A\u3001\u7ECF\u9A8C\u3001\u4F59\u989D\u548C\u9B54\u529B\u672A\u77E5\uFF1B\u4E0D\u6CBF\u7528\u65E7\u503C\u3002";
    const fields = [`\u804C\u4E1A ${names[p.classId] ?? p.classId}`, `RPG\u6218\u6597\u7B49\u7EA7 ${p.level}\uFF0C\u7ECF\u9A8C ${p.xp}`];
    if (p.nextLevelXp !== void 0) fields.push(`\u8DDD\u4E0B\u7EA7 ${p.nextLevelXp}`);
    const skillPoints = this.learning?.points ?? p.skillPoints;
    if (skillPoints !== void 0) fields.push(`\u5B66\u4E60\u70B9 ${skillPoints}`);
    if (this.prepared || p.activeSkill !== void 0 || this.skills?.activeSpell !== void 0) fields.push(`\u5F53\u524D\u51C6\u5907\u6280\u80FD ${this.prepared || "\u672A\u51C6\u5907"}`);
    fields.push(p.mana ? `\u9B54\u529B ${p.mana.current}/${p.mana.max}` : "\u9B54\u529B\u672A\u77E5");
    fields.push(p.economy?.available && p.economy.balance !== null ? `\u670D\u52A1\u7AEF\u4F59\u989D ${p.economy.balance}` : "\u7ECF\u6D4E\u672A\u5C31\u7EEA\u6216\u4F59\u989D\u672A\u77E5");
    if (p.preview) fields.push("\u670D\u52A1\u7AEF\u6807\u8BB0\u9884\u89C8");
    const skills = this.learning?.skills;
    const options = skills?.nodes?.slice(0, 6).map((n) => ({
      id: n.id,
      ...n.displayName ? { name: n.displayName } : {},
      requiredLevel: n.requiredLevel,
      learningPointCost: n.cost,
      ...n.grantedSpellId ? { grantsActiveSpell: n.grantedSpellId } : { kind: "passive_attribute_node" },
      levelAndPointsMet: p.level === void 0 ? null : p.level >= n.requiredLevel && this.learning.points >= n.cost
    }));
    const current = this.currentAbilities(), available = current?.ids;
    return head + fields.join("\uFF1B") + '\u3002RPG\u7B49\u7EA7\u4E0E\u539F\u7248\u7ECF\u9A8C\u7B49\u7EA7\u5206\u522B\u8BB0\u5F55\uFF1B\u6280\u80FD\u8D44\u683C\u67E5 mc_query {"query":"skills.status"}\uFF0C\u5B8C\u6574\u72B6\u6001\u67E5 mc_query {"query":"status"}\u3002' + (skills ? `
\u804C\u4E1A\u6280\u80FD\u6700\u8FD1\u89C2\u6D4B ${skills.observedAt}\uFF1A\u5B66\u4E60\u5019\u9009 ${JSON.stringify(options ?? skills.learnable.slice(0, 6))}` + (skills.learnable.length > 6 ? `\uFF1B\u53E6\u6709 ${skills.learnable.length - 6} \u9879\u672A\u5C55\u5F00` : "") + "\u3002\u8FD9\u662F\u670D\u52A1\u5668\u6E05\u5355\uFF1B\u7B49\u7EA7\u548C\u5B66\u4E60\u70B9\u6EE1\u8DB3\u4E0D\u4EE3\u8868\u5DF2\u5B66\u4E60\uFF0C\u8BE6\u60C5\u4E0E\u5176\u4ED6\u6761\u4EF6\u6309 skills.info \u56DE\u6267\u6838\u5BF9\u3002" : "") + (available ? "\n[\u804C\u4E1A\u6280\u80FD\u73B0\u8BFB] " + current.source + " " + current.at + "\uFF1B\u804C\u4E1A\u53EF\u7528\uFF1A" + (available.slice(0, 12).join("\u3001") || "\u65E0") + (available.length > 12 ? `\uFF08\u5171${available.length}\u9879\uFF0C\u6458\u8981\u7701\u7565\u5176\u4F59\uFF09` : "") + (this.skills ? "\uFF1B\u5B8C\u6574\u6E05\u5355\u7684\u539F\u89C2\u5BDF\u65F6\u95F4\u8BFB mc_skills" : "\uFF1B\u901A\u7528/\u53EF\u5B66\u4E60\u6E05\u5355\u5C1A\u672A\u8BFB\u53D6") + '\u3002mc_skills \u8BFB\u5B8C\u6574\u5217\u8868\uFF1Bmc_query {"query":"skills.info","arguments":["\u6280\u80FDID"]} \u67E5\u76EE\u6807/\u6548\u679C/\u6D88\u8017\u3002\u5DF2\u5B66\u4E0D\u7B49\u4E8E\u5DF2\u7F16\u6392\uFF0Cmc_combat_tactic \u53EF\u6309\u5F53\u524D\u6761\u4EF6\u7EC4\u5408\uFF1B\u53D1\u9001\u4E0D\u7B49\u4E8E\u751F\u6548\u3002' : "") + ([...this.details.values()].some((d) => d.invocation === "command") ? "\n\u5DF2\u67E5\u4E13\u7528\u5165\u53E3\uFF08\u4E0D\u662F /mycli cast\uFF09\uFF1A" + [...this.details.values()].filter((d) => d.invocation === "command").slice(-4).map((d) => `${d.id} \u2192 ${d.command}\uFF08${d.observedAt}\uFF09`).join("\uFF1B") : "") + "\n[\u804C\u4E1A\u6210\u957F] " + (this.talents ? `\u5929\u8D4B\u70B9 ${this.talents.talentPoints}\uFF08${this.talents.observedAt}\uFF09\uFF1B\u5DF2\u5206\u914D ${Object.values(this.talents.allocated).reduce((n, a) => n + a.length, 0)} \u9879\uFF0C\u76EE\u5F55 ${Object.keys(this.talents.nodes).length} \u9879\u3002` : "\u5929\u8D4B\u70B9\u4E0E\u5929\u8D4B\u6811\u5C1A\u672A\u8BFB\u53D6\u3002") + "\u5B66\u4E60\u70B9\u4E0E\u5929\u8D4B\u70B9\u72EC\u7ACB\uFF1B\u5B66\u4E60\u5019\u9009\u4E3A\u7A7A\u4E0D\u8868\u793A\u5929\u8D4B\u6216\u804C\u4E1A\u8FDB\u9636\u5DF2\u5B8C\u6210\u3002mc_query skills.tree \u8BFB\u5929\u8D4B\uFF1Bprofession.info \u52A0\u672C\u4EBA\u804C\u4E1AID\u8BFB\u6210\u957F/\u8FDB\u9636\u6761\u4EF6\uFF1B\u5355\u9879 skills.info\u3002\u88AB\u52A8\u65E0\u9700\u65BD\u6CD5\uFF0C\u6309\u76EE\u6807\u9009\u62E9\u540E\u624D\u7528\u670D\u52A1\u7AEF\u660E\u786E\u7684 learn/\u8FDB\u9636\u5165\u53E3\uFF0C\u56DE\u67E5\u5B9E\u9645\u70B9\u6570\u548C\u80FD\u529B\u3002" + (p.guidance ? "\n\u670D\u52A1\u7AEF\u5EFA\u8BAE\u6570\u636E\uFF08\u6CBF\u7528\u672C\u6B21\u72B6\u6001\u89C2\u5BDF\u65F6\u95F4\uFF0C\u672A\u6267\u884C\uFF09\uFF1A" + JSON.stringify(p.guidance) : "");
  }
  /** Connection-local, class-bound list; no disk history, command or learned conclusion. */
  hasCurrentSkills() {
    return !!this.profile?.value.available && !!(this.skills || this.abilitySnapshot);
  }
  skillsReadout(skillId) {
    const profession = skillId ? this.professionInfo.readout(skillId, this.currentAbilities()) : null;
    const detail = skillId ? this.skillDetail(skillId) : null;
    if (detail) return "[\u672C\u8FDE\u63A5\u6280\u80FD\u8BE6\u60C5\uFF1B\u6309\u5B9E\u9645 command \u9009\u62E9\u5DE5\u5177\uFF0C\u672A\u6267\u884C]\n" + JSON.stringify(detail) + (detail.invocation === "command" ? "\n\u8FD9\u662F\u4E13\u7528\u547D\u4EE4\u5165\u53E3\uFF0C\u4E0D\u662F mc_cast \u6280\u80FD\u3002\u7528 mc_do \u7684 chat \u6B65\u9AA4\u53D1\u9001\u660E\u786E\u7684 command\uFF1B\u4E0D\u8981\u628A\u6280\u80FD ID \u6216\u539F\u53C2\u6570\u585E\u8FDB /mycli cast\u3002" : "\nmc_cast \u6309\u6B64 ID \u548C\u670D\u52A1\u7AEF\u53C2\u6570\u65BD\u6CD5\uFF1B\u53D1\u9001\u4E0D\u8BC1\u660E\u6548\u679C\u3002") + (profession ? "\n" + profession : "");
    if (profession) return profession;
    const invocations = [...this.details.values()].map((d) => ({ id: d.id, name: d.name, command: d.command, invocation: d.invocation, observedAt: d.observedAt }));
    if (!skillId && invocations.length && !this.hasCurrentSkills()) return "[\u672C\u8FDE\u63A5\u547D\u4EE4\u5165\u53E3\u89C2\u5BDF\uFF1B\u672C\u4EBA\u8D44\u683C\u6E05\u5355\u5C1A\u672A\u540C\u6B65\uFF0C\u672A\u6267\u884C]\n" + JSON.stringify({ invocations });
    if (!this.skills && !this.abilitySnapshot || !this.profile?.value.available)
      return '\u5F53\u524D\u804C\u4E1A\u6280\u80FD\u5217\u8868\u672A\u540C\u6B65\uFF1B\u7528 mc_query {"query":"skills.status"} \u8BFB\u53D6\u672C\u4EBA\u5F53\u524D\u5217\u8868\uFF0C\u672A\u8FD4\u56DE\u5386\u53F2\u80FD\u529B\u3002';
    const s = this.skills;
    const current = this.currentAbilities(), available = current.ids;
    const category = !skillId ? null : available.includes(skillId) ? "profession-available" : s?.common.includes(skillId) ? "common-available" : s?.learnable.includes(skillId) ? "learnable-in-last-list" : "not-listed";
    return "[\u672C\u4EBA\u804C\u4E1A\u6280\u80FD\u89C2\u5BDF\uFF1B\u53EF\u7528\u4E0E\u7F16\u6392\u4E0D\u540C\uFF0C\u672A\u6267\u884C\u4EFB\u4F55\u64CD\u4F5C]\n" + JSON.stringify({
      classId: this.profile.value.classId,
      available,
      availableObservedAt: current.at,
      source: current.source,
      lastSkillsList: s,
      talents: this.talents ? { observedAt: this.talents.observedAt, talentPoints: this.talents.talentPoints, allocated: this.talents.allocated, nodeCount: Object.keys(this.talents.nodes).length, detailsQuery: "skills.tree" } : null,
      ...skillId ? { id: skillId, category } : {},
      ...invocations.length ? { invocations } : {},
      cost: null,
      cooldownRemainingMs: null,
      effectVerified: null
    }) + '\n\u5355\u9879\u6548\u679C/\u76EE\u6807/\u6D88\u8017\u7528 mc_query {"query":"skills.info","arguments":["\u6280\u80FDID"]}\uFF1B\u5F53\u524D\u9B54\u529B/\u51B7\u5374\u548C\u5DF2\u9009\u7EC4\u5408\u8BFB mc_combat_tactic\u3002\u5148\u6309\u5355\u9879 command \u533A\u5206 mc_cast \u65BD\u6CD5\u548C\u4E13\u7528\u547D\u4EE4\uFF1B\u88AB\u52A8\u8282\u70B9\u65E0\u9700\u65BD\u653E\u3002\u89C4\u5219/\u7A0B\u5E8F\u53EF\u7531 Agent \u8BFB\u8BF4\u660E\u540E\u7F16\u6392\uFF1B\u672A\u7F16\u6392\u4E0D\u81EA\u52A8\u65BD\u653E\uFF0C\u5B9E\u9645\u6548\u679C\u67E5\u670D\u52A1\u7AEF\u56DE\u6267\u3002';
  }
};

// integrations/qiandengji/engine/travel-points.ts
var TRIAL_ARENA_TRAVEL = {
  name: "\u8BD5\u70BC\u573A\u5165\u53E3",
  target: { x: -594, y: 91, z: -313 },
  radius: 4,
  landing: [-590, 91, -322],
  command: "/mycli goto arena"
};

// integrations/qiandengji/engine/server-query.ts
var subjectId = /^[a-z][a-z0-9_-]{0,63}$/;
var noArguments = {
  type: "array",
  minItems: 0,
  maxItems: 0,
  items: { type: "string" }
};
var subjectArgument = {
  type: "array",
  minItems: 1,
  maxItems: 1,
  items: {
    type: "string",
    pattern: subjectId.source,
    maxLength: 64,
    description: "Copy one ID actually returned by this server; never invent or reuse an ID from another World."
  }
};
var object3 = (value) => !!value && typeof value === "object" && !Array.isArray(value);
function nativeDefinition(id2, description, command, argument, matches) {
  return {
    id: id2,
    description,
    argumentsSchema: argument ? subjectArgument : noArguments,
    command: (args) => argument ? args.length === 1 && subjectId.test(args[0]) ? `${command} ${args[0]} --json` : null : args.length === 0 ? `${command} --json` : null,
    matchReply: (text2, args, username) => {
      if (!username || (argument ? args.length !== 1 || !subjectId.test(args[0]) : args.length !== 0)) return null;
      const value = nativeRpgMessage(text2);
      return value && matches(value, [...args]) ? { data: value, ok: true } : null;
    }
  };
}
function payload(text2, marker) {
  if (!text2.startsWith(marker + " ")) return null;
  const json2 = text2.slice(marker.length + 1);
  if (/[\r\n]/.test(json2)) return null;
  try {
    const value = JSON.parse(json2);
    return value && typeof value === "object" && !Array.isArray(value) && value.schemaVersion === 1 ? value : null;
  } catch {
    return null;
  }
}
function guildExam(kind) {
  const valid = (args) => kind === "info" ? args.length === 1 && subjectId.test(args[0]) : args.length === 0;
  return {
    id: `guild.exam.${kind}`,
    argumentsSchema: kind === "info" ? subjectArgument : noArguments,
    description: `\u53EA\u8BFB\u516C\u4F1A\u8003\u8BD5${kind === "promotion" ? "\u4E0B\u4E00\u9636\u8D44\u683C\u3001\u58F0\u671B\u7F3A\u9879\u3001\u5C65\u5386\u4E0E\u672C\u573A\u5B9E\u64CD\u8981\u6C42" : kind === "status" ? "\u672C\u4EBA\u5F53\u524D\u8003\u8BD5\u4E0E\u539F\u751F\u5206\u6B65\u6307\u5F15" : "\u4E00\u9879\u670D\u52A1\u7AEF\u5DF2\u5217\u51FA\u7684\u8003\u9898\u3001\u51C6\u5907\u6761\u4EF6\u4E0E\u9A8C\u6536\u8981\u6C42"}\u3002` + (kind === "info" ? 'arguments:["\u5B9E\u9645\u8003\u9898ID"]\u3002' : "arguments:[]\u3002") + "\u516C\u4F1A\u6BB5\u4F4D\u4E0D\u662F\u804C\u4E1A\u7B49\u7EA7\uFF1B\u4FDD\u7559\u539F\u751F subjectUuid\u3001\u5386\u53F2\u7ED3\u679C\u548C\u4E0B\u4E00\u6B65\u547D\u4EE4\uFF0C\u67E5\u8BE2\u4E0D\u6267\u884C nextCommand\u3001\u4E0D\u62A5\u540D\u3001\u4E0D\u4EA4\u4ED8\u3001\u4E0D\u664B\u7EA7\u3002\u65E0\u8BF7\u6C42 nonce\uFF0C\u7531\u6838\u5FC3\u6821\u9A8C\u5F53\u524D\u8FDE\u63A5\u7684\u53EF\u4FE1\u670D\u52A1\u7AEF\u56DE\u5305\u3002",
    command: (args) => valid(args) ? `/mycli guild exam ${kind}${kind === "info" ? " " + args[0] : ""} --json` : null,
    matchReply: (text2, args, username) => {
      if (!username || !valid(args)) return null;
      const value = payload(text2, "MC_GUILD_EXAM");
      if (!value || value.scope !== "self" || typeof value.subjectUuid !== "string" || !/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value.subjectUuid)) return null;
      const matches = kind === "info" ? value.type === "definition" && value.id === args[0] && typeof value.eligibility === "string" : value.type === kind && typeof value.available === "boolean" && Number.isSafeInteger(value.gradeIndex) && Number(value.gradeIndex) >= 0 && (kind !== "promotion" || typeof value.fame === "number" && Number.isFinite(value.fame));
      return matches ? { ok: true, data: value } : null;
    }
  };
}
function dungeonDefinition(kind, marker, description) {
  return {
    id: `dungeon.${kind}`,
    description,
    argumentsSchema: subjectArgument,
    command: (args) => args.length === 1 && subjectId.test(args[0]) ? `/mycli dungeon ${kind} ${args[0]} --json` : null,
    matchReply: (text2, args, username) => {
      if (args.length !== 1 || !subjectId.test(args[0]) || !username) return null;
      const error = payload(text2, "MC_SITE_DUNGEON_RESULT");
      if (error && error.activityType === "site_dungeon" && error.commandRoot === "/mycli dungeon" && error.recipient === username && error.id === args[0] && error.action === kind && error.success === false && typeof error.reason === "string") return { data: error, ok: false };
      const value = payload(text2, marker);
      if (!value || value.activityType !== "site_dungeon" || value.commandRoot !== "/mycli dungeon" || value.recipient !== username || value.id !== args[0]) return null;
      return { data: value, ok: true };
    }
  };
}
var pagePattern = /^[1-9][0-9]{0,3}$/;
function dungeonCatalogPage(args) {
  if (args.length === 0) return 1;
  return args.length === 1 && pagePattern.test(args[0]) ? Number(args[0]) : null;
}
var dungeonList = {
  id: "dungeon.list",
  description: 'Read a site dungeon catalog page. Omit arguments for page 1; arguments:["2"] reads page 2. Copy a matching items[].id for dungeon.info/status or a separate join command. Catalog IDs identify sites; a run ID or event cursor is different. An active entry does not establish that you can join it.',
  argumentsSchema: {
    type: "array",
    minItems: 0,
    maxItems: 1,
    items: { type: "string", pattern: pagePattern.source, maxLength: 4 }
  },
  command: (args) => {
    const page2 = dungeonCatalogPage(args);
    if (page2 === null) return null;
    return args.length === 0 ? "/mycli dungeon list --json" : `/mycli dungeon list --page ${page2} --json`;
  },
  matchReply: (text2, args, username) => {
    const page2 = dungeonCatalogPage(args);
    if (!username || page2 === null) return null;
    const value = payload(text2, "MC_SITE_DUNGEON_LIST");
    if (!value || value.activityType !== "site_dungeon" || value.commandRoot !== "/mycli dungeon" || value.recipient !== username || value.page !== page2 || !Number.isSafeInteger(value.pages) || Number(value.pages) < page2 || !Number.isSafeInteger(value.total) || !Array.isArray(value.items) || value.items.length > 64 || Number(value.total) < value.items.length || !value.items.every((item) => object3(item) && typeof item.id === "string" && subjectId.test(item.id))) return null;
    return { data: value, ok: true };
  }
};
var journalArgument = {
  type: "array",
  minItems: 0,
  maxItems: 2,
  items: {
    type: "string",
    pattern: "^(?:guild|skills|[1-9][0-9]{0,2})$",
    maxLength: 6,
    description: "Optional group (guild|skills) and/or page (1-999). Omit for all groups. Copy a later page from the current journal nextCommand."
  }
};
function journalDefinition(id2) {
  return {
    id: id2,
    argumentsSchema: journalArgument,
    description: 'Read the current private two-axis journal (guild/life and personal skills/foundation), at most seven rows per page. arguments:[] or ["guild"|"skills"] and optional ["page"]. Returns current itemId, sourceSystem/sourceId, runId, state, nextCommand and journalSubmitCommand. Old task-list emptiness is not evidence that no journal item exists. This query never accepts, submits, claims, learns or migrates; execute only an exact current nextCommand in a separate explicit body action, then read the journal again.',
    command: (args) => {
      if (args.length > 2 || args.some((arg) => !/^(?:guild|skills|[1-9][0-9]{0,2})$/.test(arg)) || args.length === 2 && !["guild", "skills"].includes(args[0])) return null;
      const group = args.length === 2 ? ` ${args[0]}` : args.length === 1 && ["guild", "skills"].includes(args[0]) ? ` ${args[0]}` : "";
      const page2 = args.length === 2 ? ` ${args[1]}` : args.length === 1 && /^[1-9]/.test(args[0]) ? ` ${args[0]}` : "";
      return `/mycli journal${group}${page2} --json`;
    },
    matchReply: (text2, args, username) => {
      if (!username || args.length > 2 || args.some((arg) => !/^(?:guild|skills|[1-9][0-9]{0,2})$/.test(arg)) || args.length === 2 && !["guild", "skills"].includes(args[0])) return null;
      const value = payload(text2, "MC_JOURNAL");
      if (!value || value.type !== "journal" || value.scope !== "self" || value.readOnly !== true || typeof value.subjectUuid !== "string" || !/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value.subjectUuid) || !["all", "guild", "skills"].includes(String(value.filter)) || !Number.isSafeInteger(value.page) || Number(value.page) < 1 || !Number.isSafeInteger(value.pages) || Number(value.pages) < Number(value.page) || value.pageSize !== 7 || !Array.isArray(value.items) || value.items.length > 7 || !Array.isArray(value.groups) || value.groups.length !== 2 || !value.groups.includes("guild") || !value.groups.includes("skills")) return null;
      const filter = args[0] && ["guild", "skills"].includes(args[0]) ? args[0] : "all";
      const page2 = args.length === 2 ? Number(args[1]) : args.length === 1 && /^[1-9]/.test(args[0]) ? Number(args[0]) : 1;
      if (value.filter !== filter || value.page !== page2) return null;
      if (!value.items.every((item) => object3(item) && typeof item.itemId === "string" && /^[a-z_]{1,32}:[A-Za-z0-9_:.-]{1,100}$/.test(item.itemId) && ["guild", "skills"].includes(String(item.group)) && typeof item.sourceSystem === "string" && typeof item.sourceId === "string" && typeof item.state === "string" && typeof item.nextCommand === "string" && item.nextCommand.startsWith("/mycli "))) return null;
      return { ok: true, data: value };
    }
  };
}
var sharedQueries = [
  journalDefinition("journal"),
  journalDefinition("tasks.overview"),
  guildExam("promotion"),
  guildExam("status"),
  guildExam("info"),
  {
    id: "trial.status",
    argumentsSchema: noArguments,
    description: "Read the trial tower (\u8BD5\u70BC\u5854 / arena), NOT a site dungeon. arguments:[] only. Returns native MC_TRIAL_STATE, including participant, floor, remainingMobs and canStart. If the server directs travel to the entrance, entryTravel.step supplies the configured landing, which differs from the button coordinates. Recheck this status after travel. canStart is current server eligibility; lastOutcome is historical. Does not start or claim.",
    command: (args) => args.length === 0 ? "/mycli arena status --json" : null,
    matchReply: (text2, args, username) => {
      if (args.length || !username) return null;
      const value = payload(text2, "MC_TRIAL_STATE");
      if (!value || value.activityType !== "trial_tower" || value.recipient !== username || typeof value.active !== "boolean" || typeof value.participant !== "boolean" || !Number.isSafeInteger(value.floor) || Number(value.floor) < 0 || !Number.isSafeInteger(value.maxFloor) || Number(value.maxFloor) < 1 || !Number.isSafeInteger(value.remainingMobs) || Number(value.remainingMobs) < 0) return null;
      if (value.reason === "reach_trial_entrance" && value.nextCommand === TRIAL_ARENA_TRAVEL.command && value.canStart === false && value.participant === false) {
        return { data: { ...value, entryTravel: {
          source: "qiandengji-travel-profile",
          step: {
            skill: "server_travel",
            command: TRIAL_ARENA_TRAVEL.command,
            at: [...TRIAL_ARENA_TRAVEL.landing],
            within: 3,
            dimension: "overworld"
          },
          verifyQuery: "trial.status"
        } }, ok: true };
      }
      return { data: value, ok: true };
    }
  },
  {
    id: "status",
    argumentsSchema: noArguments,
    description: "Read current self status, including Vortex class, RPG level/xp, mana and economy when available. arguments:[] only. Requests --json and matches either the native MC_RPG status shape or legacy MC_STATUS self/name. Native replies have no subject/nonce: the core checks trusted server transport/current connection, not unique request attribution.",
    command: (args) => args.length === 0 ? "/mycli status --json" : null,
    matchReply: (text2, args, username) => {
      if (args.length || !username) return null;
      const native = nativeRpgMessage(text2);
      if (native && readNativeRpgStatus(native)) return { data: native, ok: true };
      const value = payload(text2, "MC_STATUS");
      if (!value || value.kind !== "state" || value.scope !== "self" || value.readOnly !== true || value.name !== username) return null;
      return { data: value, ok: true };
    }
  },
  {
    id: "skills.status",
    argumentsSchema: noArguments,
    description: "Read current self native MC_RPG available/common/learnable skills and skillPoints, preserving complete server fields such as learning cost/requiredLevel. arguments:[] only. Querying never chooses a class, learns/prepares/casts or spends points. No subject/nonce in native replies; current-connection server provenance is checked by the core.",
    command: (args) => args.length === 0 ? "/mycli skills status --json" : null,
    matchReply: (text2, args, username) => {
      if (args.length || !username) return null;
      const value = nativeRpgMessage(text2);
      return value && readNativeSkills(value, (/* @__PURE__ */ new Date()).toISOString()) ? { data: value, ok: true } : null;
    }
  },
  nativeDefinition(
    "profession.list",
    "Read the native class directory. arguments:[] only; no selection or spending. No subject/nonce: trusted current-connection transport is checked, not unique request attribution.",
    "/mycli profession list",
    false,
    (value) => Array.isArray(value.classes) && value.classes.length <= 64 && value.classes.every((id2) => typeof id2 === "string" && subjectId.test(id2))
  ),
  nativeDefinition(
    "skills.tree",
    "Read current self Vortex talent points, allocated passive nodes and prerequisites. Distinct from learning points/active spells; an empty skills.status learnable list does not cover talents or ascensions. arguments:[] only; never spends points. No subject/nonce: trusted current connection required.",
    "/mycli skills tree",
    false,
    (value) => readNativeTalentTree(value, (/* @__PURE__ */ new Date()).toISOString()) !== null
  ),
  nativeDefinition(
    "profession.status",
    "Read the currently selected class; none means unselected, not an unavailable server. arguments:[] only. Preserves current authority metadata when present (for example VortexRPG). Never chooses, changes or resets a class.",
    "/mycli profession status",
    false,
    (value) => typeof value.class === "string" && subjectId.test(value.class) && value.queryOnly === true && (!Object.hasOwn(value, "authority") || value.authority === "VortexRPG")
  ),
  nativeDefinition(
    "profession.info",
    'Read one server-listed class and its starter spell. arguments:["class_id"]. Querying a class does not choose it; only an explicit separate profession choose operation may do so.',
    "/mycli profession info",
    true,
    (value, args) => value.id === args[0] && value.queryOnly === true && typeof value.starterSpell === "string" && subjectId.test(value.starterSpell)
  ),
  nativeDefinition(
    "skills.info",
    'Read a current skill/spell or learning/talent node. arguments:["observed_id"]. Preserves the full native definition, prerequisites, actual learning state and nextCommand without executing it. Learning nodes and castable spells are distinct; no points, preparation or casting are performed.',
    "/mycli skills info",
    true,
    (value, args) => value.id === args[0] && value.common === true && typeof value.available === "boolean" && typeof value.learned === "boolean" || value.id === args[0] && value.common === true && value.queryOnly === true && typeof value.available === "boolean" && typeof value.name === "string" && typeof value.command === "string" && typeof value.effect === "string" || object3(value.definition) && value.definition.id === args[0] && typeof value.available === "boolean" || object3(value.skill) && value.skill.id === args[0] && value.queryOnly === true && typeof value.learned === "boolean" || object3(value.talent) && value.talent.id === args[0] && value.queryOnly === true && typeof value.learned === "boolean"
  ),
  dungeonList,
  dungeonDefinition(
    "status",
    "MC_SITE_DUNGEON_STATE",
    'Read a site dungeon state (\u9057\u8FF9/\u5893\u7A74), NOT the trial tower; use trial.status for \u8BD5\u70BC\u5854/arena. arguments:["server_observed_id"], one lowercase ASCII ID (letters, digits, underscore or hyphen, max64). Matches the connected recipient and exact dungeon ID. Active/current room, attendance, rewards and lastOutcome remain the server response; no start, join, travel, claim or retry.'
  ),
  dungeonDefinition(
    "info",
    "MC_SITE_DUNGEON_INFO",
    'Read a site dungeon description and entry geometry. arguments:["server_observed_id"], one lowercase ASCII ID (letters, digits, underscore or hyphen, max64). Matches the connected recipient and exact dungeon ID. An info response does not establish a current run, cooldown, room clear or successful travel.'
  ),
  ...STORAGE_TRADE_QUERIES
];
function qiandengjiServerQueriesForPlayer(uuid3) {
  return [...sharedQueries, ...inventoryBatchPreviews(uuid3)];
}
var QIANDENGJI_SERVER_QUERIES = qiandengjiServerQueriesForPlayer();

// integrations/qiandengji/engine/trial-search.ts
var TrialSearchState = class {
  current;
  progress;
  epoch = 0;
  reset() {
    this.current = void 0;
    this.progress = void 0;
    this.epoch++;
  }
  read(now = Date.now()) {
    return this.current && this.current.expiresAtMs > now ? { ...this.current } : void 0;
  }
  facts(now = Date.now()) {
    if (!this.progress) return { source: "server", fresh: false, status: "unverified", floorCleared: null, query: "trial.status" };
    const fresh = now >= this.progress.observedAtMs && now - this.progress.observedAtMs < 6e4;
    return {
      ...this.progress,
      fresh,
      status: fresh ? "observed" : "stale",
      guidance: fresh ? this.progress.guidance ?? null : null,
      requiresStatusRead: !!this.progress.terminal || !fresh || this.progress.source !== "MC_TRIAL_STATE",
      floorCleared: fresh ? this.progress.floorCleared : null,
      query: "trial.status",
      meaning: "\u5F53\u524D\u6311\u6218\u89C2\u5BDF\uFF1Bparticipant=false \u53EA\u8868\u793A\u6CA1\u6709\u53C2\u8D5B\u8EAB\u4EFD\uFF0C\u4E0D\u8BC1\u660E\u5DF2\u79BB\u5F00\u8BD5\u70BC\u5EFA\u7B51\u3002\u5386\u53F2 lastOutcome\u3001\u5C40\u90E8\u6218\u6597 clear\u3001\u6CA1\u770B\u89C1\u654C\u4EBA\u5747\u4E0D\u662F\u672C\u5C42\u901A\u5173\u8BC1\u636E\u3002\u8FC7\u671F\u540E\u987B\u91CD\u65B0\u67E5\u8BE2 trial.status \u83B7\u53D6\u5F53\u524D\u6307\u5F15\u3002"
    };
  }
  observe(text2, username, now = Date.now()) {
    text2 = text2.replace(/^【试炼塔·第\d+层】\s*/, "");
    const native = QIANDENGJI_SERVER_QUERIES.find((q) => q.id === "trial.status").matchReply(text2, [], username)?.data;
    if (native) {
      this.record(native, "MC_TRIAL_STATE", now);
      return;
    }
    if (text2.startsWith("MC_TRIAL_RESULT ")) {
      let result;
      try {
        result = JSON.parse(text2.slice("MC_TRIAL_RESULT ".length));
      } catch {
        return;
      }
      if (!result || typeof result !== "object" || Array.isArray(result)) return;
      const previous = this.progress;
      if (!previous || !username || result.schemaVersion !== 1 || result.recipient !== username || result.activityType !== "trial_tower" || typeof result.run !== "string" || result.run !== previous.run || !Number.isSafeInteger(result.revision) || Number(result.revision) < (previous.revision ?? 0) || result.status !== "completed" || !["won", "lost", "aborted"].includes(String(result.outcome))) return;
      this.current = void 0;
      this.progress = {
        ...previous,
        source: "MC_TRIAL_RESULT",
        revision: Number(result.revision),
        active: false,
        participant: false,
        remainingMobs: null,
        floorCleared: false,
        observedAtMs: now,
        guidance: void 0,
        terminal: { status: "completed", outcome: String(result.outcome), reason: typeof result.reason === "string" && result.reason.length <= 1024 ? result.reason : null }
      };
      return;
    }
    if (text2.startsWith("MC_DUNGEON status ")) {
      const fields = Object.fromEntries(text2.slice("MC_DUNGEON status ".length).split(/\s+/).map((s) => {
        const i = s.indexOf("=");
        return [s.slice(0, i), s.slice(i + 1)];
      }));
      if (!username || fields.recipient !== username || fields.activityType !== "trial_tower" || !["true", "false"].includes(fields.participant) || !["true", "false"].includes(fields.globalActive)) return;
      this.record({
        active: fields.globalActive === "true",
        participant: fields.participant === "true",
        floor: Number(fields.selfFloor),
        globalFloor: Number(fields.globalFloor),
        remainingMobs: Number(fields.remainingMobs),
        globalState: fields.globalState,
        run: fields.run,
        revision: fields.revision
      }, "MC_DUNGEON status", now);
      return;
    }
    const match = /^本人试炼：参赛中；全服试炼：第\s*(\d+)\/\d+\s*层[^\n]*本层剩余\s*(\d+)\s*只怪物[。.]?$/.exec(text2);
    if (match) {
      this.record({ active: true, participant: true, floor: Number(match[1]), remainingMobs: Number(match[2]) }, "server-message", now);
      return;
    }
    const entered = /^(?:附近\s+\d+\s+人进入第|进入第|已恢复第)\s*(\d+)\s*\/\s*\d+\s*层/.exec(text2);
    if (entered) {
      const previous = this.progress;
      this.current = void 0;
      this.epoch++;
      this.progress = previous?.participant && previous.active ? {
        ...previous,
        source: "server-room-transition",
        floor: Number(entered[1]),
        remainingMobs: null,
        floorCleared: false,
        observedAtMs: now,
        guidance: void 0
      } : void 0;
      return;
    }
    const cleared = /^第\s*(\d+)\s*\/\s*\d+\s*层已通关/.exec(text2);
    if (cleared && this.progress?.active && this.progress.participant && this.progress.floor === Number(cleared[1])) {
      this.current = void 0;
      this.progress = { ...this.progress, source: "server-floor-clear", remainingMobs: 0, floorCleared: true, observedAtMs: now, guidance: void 0 };
      return;
    }
    if (/^(?:进入第|已恢复第|第\s*\d+\s*\/\s*\d+\s*层已通关|本人试炼：)/.test(text2)) this.reset();
  }
  record(native, source, now) {
    const floor = Number(native.selfFloor ?? native.floor), remaining = Number(native.remainingMobs);
    if (!Number.isSafeInteger(floor) || floor < 0 || !Number.isSafeInteger(remaining) || remaining < 0) return;
    const run = typeof native.run === "string" ? native.run : null;
    const revision = native.revision !== void 0 && Number.isSafeInteger(Number(native.revision)) ? Number(native.revision) : null;
    const previous = this.progress;
    if (source === "MC_DUNGEON status" && run === null && revision === null && previous) {
      if (previous.terminal) {
        this.current = void 0;
        return;
      }
      if (previous.source === "MC_TRIAL_STATE" && previous.floor === floor && previous.remainingMobs === remaining && previous.participant === (native.participant === true) && previous.active === (native.active === true)) return;
    }
    if (run && run === this.progress?.run && revision !== null && this.progress.revision !== null && revision < this.progress.revision) return;
    if (run && run !== this.progress?.run) this.epoch++;
    this.progress = {
      source,
      run,
      revision,
      participant: native.participant === true,
      active: native.active === true,
      floor,
      remainingMobs: remaining,
      floorCleared: native.participant === true && native.active === true && remaining === 0 && (native.globalFloor === void 0 || Number(native.globalFloor) === floor) && (native.globalState === "cleared" || native.state === "cleared"),
      observedAtMs: now,
      guidance: this.guidance(native)
    };
    if (native.active && native.participant && remaining > 0) this.set(floor, remaining, now);
    else this.current = void 0;
  }
  guidance(native) {
    const value = { source: "server", automaticExecution: false };
    for (const key of ["reason", "nextAction", "nextCommand", "verifyCommand"]) {
      if (typeof native[key] === "string" && native[key].length <= 1024) value[key] = native[key];
    }
    if (native.reason === "reach_trial_entrance" && native.participant === false && native.canStart === false && native.nextCommand === "/mycli goto arena" && native.entryTravel) value.entryTravel = native.entryTravel;
    return Object.keys(value).length > 2 ? value : void 0;
  }
  set(floor, remaining, now) {
    if (!Number.isSafeInteger(floor) || floor < 1 || !Number.isSafeInteger(remaining) || remaining <= 0) {
      this.reset();
      return;
    }
    this.current = { key: `trial-room:${this.epoch}:${floor}`, remaining, observedAtMs: now, expiresAtMs: now + 6e4 };
  }
};

// integrations/qiandengji/engine/adventure-gatherings.ts
var AdventureGatherings = class {
  notices = /* @__PURE__ */ new Map();
  current(now = Date.now()) {
    for (const [id2, notice] of this.notices) if (notice.expiresAt <= now) this.notices.delete(id2);
    return Array.from(this.notices.values(), (notice) => ({ ...notice }));
  }
  observe(text2, recipient, now = Date.now()) {
    if (!recipient || !text2.startsWith("MC_COACH ") || text2.length > 4096) return;
    let v;
    try {
      v = JSON.parse(text2.slice(9));
    } catch {
      return;
    }
    if (!v || v.type !== "adventure_gathering" || v.recipient !== recipient || v.requiresDecision !== true || v.participationAutomatic !== false || v.isTaskProgress !== false || v.progressMeaning !== "event_time_remaining" || typeof v.id !== "string" || !/^[a-z0-9_-]{1,80}$/.test(v.id) || !Number.isSafeInteger(v.expiresAt) || v.eventId !== v.id + ":" + v.expiresAt || v.expiresAt <= now || typeof v.name !== "string" || !v.name.length || v.name.length > 120 || typeof v.nextCommand !== "string" || !v.nextCommand.startsWith("/mycli ") || v.nextCommand.length > 160 || /[\u0000-\u001f\u007f]/.test(v.name + v.nextCommand)) return;
    this.current(now);
    const old = this.notices.get(v.id);
    if (old && old.expiresAt >= v.expiresAt) return;
    if (!old && this.notices.size >= 4) return;
    this.notices.set(v.id, { id: v.id, name: v.name, eventId: v.eventId, expiresAt: v.expiresAt, nextCommand: v.nextCommand });
  }
};

// integrations/qiandengji/engine/world.ts
import { ObservedCommandCatalog, serverQueryTool, bindEntityIdentityResolver, readWorldIdentity } from "agent-mc-world/extension";
import { hasExecutionFeedbackContext } from "agent-mc-world/context";

// integrations/qiandengji/engine/command-usage.ts
function observedCommandUsage(text2, observedAt = Date.now()) {
  const match = /^MC_CLI_DETAIL (\{[^\r\n]*\})$/.exec(text2.trim());
  if (!match) return null;
  try {
    const value = JSON.parse(match[1]);
    if (!value || value.schemaVersion !== 1 || typeof value.id !== "string" || typeof value.usage !== "string" || !value.usage.startsWith("/mycli ")) return null;
    return { id: value.id, usage: value.usage, observedAt };
  } catch {
    return null;
  }
}
function observedCommandRoot(text2, recipient, observedAt = Date.now()) {
  if (!recipient) return null;
  const match = /^MC_SITE_DUNGEON_(?:INFO|STATE) (\{[^\r\n]*\})$/.exec(text2.trim());
  if (!match) return null;
  try {
    const value = JSON.parse(match[1]);
    if (!value || value.schemaVersion !== 1 || value.activityType !== "site_dungeon" || value.recipient !== recipient || value.commandRoot !== "/mycli dungeon" || typeof value.id !== "string" || !/^[a-z][a-z0-9_-]{0,63}$/.test(value.id)) return null;
    return { id: "site_dungeon.commandRoot", usage: `${value.commandRoot} <subcommand>`, observedAt };
  } catch {
    return null;
  }
}

// integrations/qiandengji/engine/maid-port.mjs
import { randomUUID } from "node:crypto";
var MAID_CHANNEL = "qiandengji:maids";
var MAID_REQUEST_CHANNEL = "qiandengji:maid_request";
var commandWindows = /* @__PURE__ */ new WeakMap();
var uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
var requestId = /^[A-Za-z0-9_-]{1,48}$/;
var writes = /* @__PURE__ */ new Set(["brain", "chat", "talk", "follow", "recall", "stay", "speak", "ack", "sit", "task", "make", "schedule", "pickup", "transfer", "equip", "skin", "voice", "voice-test", "mute", "resource-pack", "rename"]);
var workshopId = /^[a-z0-9_-]{1,24}$/;
var recipeId = /^[a-z0-9_.-]+:[a-z0-9_./-]+$/;
var sameMaid = (id2, expected) => typeof id2 === "string" && id2.toLowerCase() === expected;
var MAID_TOOL = {
  name: "mc_maids",
  tags: ["read", "act"],
  description: "Qiandengji NPC interface on this authenticated connection. First list exact maid IDs and read context capabilities/hostKind. brain without choice reads configured native/Harness backends and their models; use an exact returned choice and retained requestId to select while idle, preserving the original maid and memory. tasks lists original mode IDs and prerequisites, including native farming when available; inventory reads original slots/equipment. task/schedule/pickup change native settings. workshop reads authorized workstations, recipes and any active order. Read workshop or confirm the workshop handshake before make. After submitting, use receipt with the original operationId and operationAction:make; verify completed, goalCompleted and the delivered item/count/inventory. transfer moves actual items between player and maid inventories; equip swaps a native slot with main/off/head/chest/legs/feet. list finds owned maids; nearby finds visible maids and publicChatEnabled within eight blocks in the same dimension. chat invokes the selected native TLM model: owner history/tools stay private, while enabled nearby visitors receive conversation-only replies without tools. Shared inference remains limited to the configured original maid. pending is NOT a reply; query receipt until replied/unknown. Nearby visitor speech is attributed and heard locally. talk only queues the existing host inbox. context reports lifeState and exact original tombstone location; unloaded is not death. Never automatically recreate a maid or retry uncertain writes. skins/voices list installed original IDs; skin/voice apply a selection. resources reports this connection asset readiness; resource-pack offers Java voice assets. voice-test privately auditions an available event and requires loaded assets; mute controls original automatic speech frequency while manual audition remains available. rename consumes a real named name tag held in the main hand. inbox is attributed, untrusted human dialogue; use the NPC sessionKey and memoryNamespace in your existing host, then speak and acknowledge the event. follow/stay/sit change movement mode. recall brings the owned maid to the authenticated player and reports actual arrival, including across dimensions and inside an activity. Writes require a retained unique requestId. If unknown, query receipt using the SAME operationId without retrying. Mode application is not task completion. No new model loop or owner transfer.",
  parameters: { type: "object", additionalProperties: false, properties: {
    action: { type: "string", enum: ["nearby", "brain", "chat", "talk", "list", "context", "follow", "recall", "stay", "speak", "receipt", "inbox", "ack", "tasks", "inventory", "sit", "task", "workshop", "make", "schedule", "pickup", "transfer", "equip", "skins", "skin", "voices", "voice", "voice-test", "mute", "resources", "resource-pack", "rename"] },
    choice: { type: "string", pattern: "^[a-z0-9][a-z0-9_-]{0,31}$", description: "For brain: omit to read current configured choices; otherwise use an exact returned choice and retain a unique requestId. Selection preserves the original maid and history." },
    maidId: { type: "string", format: "uuid" },
    requestId: { type: "string", pattern: "^[A-Za-z0-9_-]{1,48}$" },
    operationId: { type: "string", pattern: "^[A-Za-z0-9_-]{1,48}$", description: "Original operation ID for receipt queries." },
    operationAction: { type: "string", enum: [...writes], description: "Original write action for a receipt, if known. Use make when reconciling a craft after reconnect." },
    page: { type: "integer", minimum: 0, maximum: 1e4 },
    text: { type: "string", minLength: 1, maxLength: 140 },
    eventId: { type: "string", description: "Exact attributed event ID from inbox, for ack only." },
    taskId: { type: "string", description: "Exact original ID from tasks, for task only." },
    workshopId: { type: "string", pattern: workshopId.source, description: "Authorized workstation ID from workshop, for make." },
    recipeId: { type: "string", pattern: recipeId.source, description: "Exact recipe ID from the chosen workstation, for make." },
    quantity: { type: "integer", minimum: 1, maximum: 2147483647, description: "Finished item count for make. Use a multiple of productsPerCraft within maxBatches. Omit for one batch." },
    inventory: { type: "string", enum: ["chest", "backpack"], description: "Material and output inventory for make. Defaults to the authorized supply chest." },
    schedule: { type: "string", enum: ["DAY", "NIGHT", "ALL"] },
    enabled: { type: "boolean", description: "For pickup or mute." },
    skinId: { type: "string", description: "Exact original model ID observed in skins." },
    voiceId: { type: "string", description: "Installed local voice ID observed in voices; optional for preview." },
    soundEvent: { type: "string", description: "Exact available event observed in voices, for voice-test." },
    direction: { type: "string", enum: ["put", "take"] },
    slot: { type: "integer", minimum: 0, maximum: 255, description: "Zero-based native maid slot from inventory.usableSlotIndexes. freeSlotIndexes lists empty unlocked slots; availableSlots is usable capacity, not free space. Backing slotCount does not unlock slots." },
    count: { type: "integer", minimum: 1, maximum: 64 },
    playerSlot: { type: "integer", minimum: 0, maximum: 35, description: "Exact player inventory slot; required for put." },
    hand: { type: "string", enum: ["main", "off", "head", "chest", "legs", "feet"] }
  }, required: ["action"] }
};
function decodeMaidReply(packet, recipient) {
  if (packet?.channel !== MAID_CHANNEL || !uuid.test(recipient ?? "") || !(packet.data instanceof Uint8Array) || !packet.data.length || packet.data.length > 24e3) return null;
  let value;
  try {
    value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(packet.data));
  } catch {
    return null;
  }
  if (!value || Array.isArray(value) || value.schema !== 1 || value.protocol !== "qiandengji-maids/v1" || typeof value.recipientUuid !== "string" || value.recipientUuid.toLowerCase() !== recipient.toLowerCase() || typeof value.requestId !== "string" || !requestId.test(value.requestId) || !["nearby", "create", "list", "context", ...writes, "receipt", "inbox", "dialogue", "talk", "tasks", "inventory", "workshop", "skins", "voices", "resources", "transport", "lifecycle", "chat-result"].includes(value.action) || typeof value.ok !== "boolean" || typeof value.sampledAt !== "string" || !Number.isFinite(Date.parse(value.sampledAt)) || (value.ok ? !value.data || typeof value.data !== "object" || Array.isArray(value.data) : typeof value.error !== "string")) return null;
  return value;
}
function maidCommand(args) {
  if (!args || typeof args !== "object" || Array.isArray(args)) throw Error("arguments must be an object");
  const { action, maidId: inputMaid, operationId, operationAction, text: text2, eventId } = args;
  if (!["nearby", "list", "context", ...writes, "receipt", "inbox", "tasks", "inventory", "workshop", "skins", "voices", "resources"].includes(action)) throw Error("unsupported action");
  const allowed = /* @__PURE__ */ new Set([
    "action",
    "requestId",
    ...action === "list" ? ["page"] : action === "nearby" ? [] : ["maidId"],
    ...action === "skins" ? ["page"] : [],
    ...action === "receipt" ? ["operationId", "operationAction"] : [],
    ...action === "brain" ? ["choice"] : [],
    ...["speak", "talk", "chat"].includes(action) ? ["text"] : [],
    ...action === "ack" ? ["eventId"] : [],
    ...action === "task" ? ["taskId"] : [],
    ...action === "schedule" ? ["schedule"] : [],
    ...["pickup", "mute"].includes(action) ? ["enabled"] : [],
    ...action === "make" ? ["workshopId", "recipeId", "quantity", "inventory"] : [],
    ...action === "skin" ? ["skinId"] : [],
    ...action === "voice" ? ["voiceId"] : [],
    ...action === "voice-test" ? ["voiceId", "soundEvent"] : [],
    ...action === "transfer" ? ["direction", "slot", "count", "playerSlot"] : [],
    ...action === "equip" ? ["hand", "slot"] : []
  ]);
  if (Object.keys(args).some((key) => !allowed.has(key))) throw Error("unexpected argument");
  const writing = writes.has(action) && !(action === "brain" && args.choice === void 0);
  if (action === "brain" && args.choice !== void 0 && (typeof args.choice !== "string" || !/^[a-z0-9][a-z0-9_-]{0,31}$/.test(args.choice))) throw Error("brain choice must be an exact ID returned by brain");
  const id2 = args.requestId ?? (writing ? null : randomUUID());
  if (typeof id2 !== "string" || !requestId.test(id2)) throw Error("writes require a retained requestId");
  if (!["list", "nearby"].includes(action) && (typeof inputMaid !== "string" || !uuid.test(inputMaid))) throw Error("use the exact maidId returned by list or nearby");
  const maidId = typeof inputMaid === "string" ? inputMaid.toLowerCase() : void 0;
  if (action === "receipt" && (typeof operationId !== "string" || !requestId.test(operationId))) throw Error("receipt requires the original operationId");
  if (operationAction !== void 0 && !writes.has(operationAction)) throw Error("operationAction must be the original write action");
  if (["speak", "talk", "chat"].includes(action) && (typeof text2 !== "string" || !text2.trim() || text2.length > 140 || /[\u0000-\u001f\u007f-\u009f§]/u.test(text2))) throw Error("speak needs 1-140 plain-text characters");
  if (action === "ack" && (typeof eventId !== "string" || !/^[0-9a-f-]{36}:[A-Za-z0-9_-]{1,48}$/.test(eventId))) throw Error("ack requires the exact eventId");
  if (action === "task" && (typeof args.taskId !== "string" || !/^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(args.taskId))) throw Error("task needs an observed original taskId");
  if (action === "schedule" && !["DAY", "NIGHT", "ALL"].includes(args.schedule)) throw Error("invalid native schedule");
  if (["pickup", "mute"].includes(action) && typeof args.enabled !== "boolean") throw Error("setting needs enabled");
  if (action === "skin" && !/^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(args.skinId ?? "")) throw Error("skin needs an observed original model ID");
  if (["voice", "voice-test"].includes(action) && (args.voiceId !== void 0 || action === "voice") && !/^[a-z0-9_.-]+$/.test(args.voiceId ?? "")) throw Error("voice needs an installed pack ID");
  if (action === "voice-test" && !/^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(args.soundEvent ?? "")) throw Error("voice-test needs an available sound event");
  if (["transfer", "equip"].includes(action) && (!Number.isSafeInteger(args.slot) || args.slot < 0 || args.slot > 255)) throw Error("invalid native slot");
  if (action === "transfer" && (!["put", "take"].includes(args.direction) || !Number.isSafeInteger(args.count) || args.count < 1 || args.count > 64 || args.direction === "put" && args.playerSlot === void 0 || args.playerSlot !== void 0 && (!Number.isSafeInteger(args.playerSlot) || args.playerSlot < 0 || args.playerSlot > 35))) throw Error("transfer needs direction, slot, count and exact playerSlot for put");
  if (action === "equip" && !["main", "off", "head", "chest", "legs", "feet"].includes(args.hand)) throw Error("equip needs main/off/head/chest/legs/feet");
  if (args.page !== void 0 && (!Number.isSafeInteger(args.page) || args.page < 0 || args.page > 1e4)) throw Error("invalid page");
  let order;
  let orderArgs = "";
  if (action === "make") {
    const { workshopId: site, recipeId: recipe, quantity, inventory = "chest" } = args;
    if (typeof site !== "string" || !workshopId.test(site) || typeof recipe !== "string" || !recipeId.test(recipe)) {
      throw Error("make needs an exact workshopId and recipeId returned by workshop");
    }
    if (quantity !== void 0 && (!Number.isSafeInteger(quantity) || quantity < 1 || quantity > 2147483647)) {
      throw Error("quantity must be a positive finished item count, or omitted for one batch");
    }
    if (!["chest", "backpack"].includes(inventory)) throw Error("inventory must be chest or backpack");
    order = { workshopId: site, recipeId: recipe, quantity, inventory };
    orderArgs = `${site} ${recipe} ${quantity ?? "once"} ${inventory}`;
  }
  const tail = action === "brain" ? args.choice ?? "" : ["speak", "talk", "chat"].includes(action) ? text2.trim().replace(/ +/g, " ") : action === "ack" ? eventId : action === "task" ? args.taskId : action === "schedule" ? args.schedule : ["pickup", "mute"].includes(action) ? String(args.enabled) : action === "skin" ? args.skinId : action === "voice" ? args.voiceId : action === "voice-test" ? `${args.voiceId ? args.voiceId + " " : ""}${args.soundEvent}` : action === "skins" ? String(args.page ?? 0) : action === "transfer" ? `${args.direction} ${args.slot} ${args.count}${args.playerSlot === void 0 ? "" : ` ${args.playerSlot}`}` : action === "equip" ? `${args.hand} ${args.slot}` : orderArgs;
  const command = action === "nearby" ? `/qdmaid nearby ${id2}` : action === "list" ? `/qdmaid list ${id2} ${args.page ?? 0}` : action === "receipt" ? `/qdmaid receipt ${maidId} ${operationId} ${id2}` : `/qdmaid ${action} ${maidId} ${id2}${tail ? ` ${tail}` : ""}`;
  if (command.length > 256) throw Error("command exceeds the vanilla 256 character limit");
  return { action, requestId: id2, maidId, operationId: writing ? id2 : operationId, operationAction, command, order };
}
function matchesMaidReply(reply, entry, order = entry.order) {
  if (reply.action !== entry.action || reply.requestId !== entry.requestId) return false;
  const data = reply.data;
  if (entry.maidId && (reply.ok || data?.maidId !== void 0) && !sameMaid(data?.maidId, entry.maidId)) return false;
  if (!reply.ok) return data?.operationId === void 0 || data.operationId === entry.operationId;
  if (entry.action === "workshop") return Array.isArray(data.workshops);
  if (!["receipt", "make"].includes(entry.action)) return true;
  const expectedAction = entry.operationAction ?? (entry.action === "make" || order ? "make" : void 0);
  if (data.operationId !== entry.operationId || typeof data.action !== "string" || !data.action || expectedAction !== void 0 && expectedAction !== data.action) return false;
  if (data.action !== "make") return true;
  if (!sameMaid(data.actorId, reply.recipientUuid.toLowerCase()) || !["reserved", "pending", "completed", "rejected", "cancelled", "unknown"].includes(data.status)) return false;
  if (data.status !== "completed") return data.goalCompleted !== true;
  const seen = data.observation;
  return data.goalCompleted === true && seen?.operationId === entry.operationId && seen.verified === true && seen.effectsApplied === true && typeof seen.itemId === "string" && recipeId.test(seen.itemId) && seen.itemId !== "minecraft:air" && Number.isSafeInteger(seen.count) && seen.count > 0 && seen.count === seen.quantity && ["chest", "backpack"].includes(seen.inventory) && (!order || seen.workshopId === order.workshopId && seen.recipeId === order.recipeId && seen.inventory === (order.inventory ?? "chest") && (order.quantity === void 0 ? seen.batches === 1 : seen.count === order.quantity));
}
function createMaidPort(bot, { timeoutMs = 5e3, onDialogue = () => {
}, onLifecycle = () => {
}, onChatResult = () => {
} } = {}) {
  const recipient = bot?._client?.uuid ?? bot?.player?.uuid;
  if (!uuid.test(recipient ?? "")) throw Error("authenticated connection UUID required");
  const pending = /* @__PURE__ */ new Map();
  const crafts = /* @__PURE__ */ new Map();
  let closed = false, pluginTransport = false, workshopTransport = false, workshopObserved = false;
  const commandWindow = commandWindows.get(bot) ?? { next: 0, payloadNext: 0 };
  commandWindows.set(bot, commandWindow);
  const settle = (id2, value) => {
    const slot = pending.get(id2);
    if (!slot) return;
    clearTimeout(slot.timer);
    clearTimeout(slot.queuedTimer);
    pending.delete(id2);
    slot.resolve(value);
  };
  const unknown = (entry, reason) => ({
    ok: false,
    action: entry.action,
    requestId: entry.requestId,
    operationId: entry.operationId,
    status: entry.operationId && writes.has(entry.action) ? "unknown" : "unavailable",
    reason,
    retryAllowed: false
  });
  const workshopSupported = () => !closed && (workshopTransport || workshopObserved);
  const onPacket = (packet) => {
    if (closed) return;
    const value = decodeMaidReply(packet, recipient);
    if (value?.action === "transport" && value.ok && value.data.requestChannel === MAID_REQUEST_CHANNEL) {
      pluginTransport = true;
      workshopTransport ||= value.data.workshop === true;
      for (const slot2 of pending.values()) if (!slot2.sent) {
        clearTimeout(slot2.queuedTimer);
        schedule(slot2);
      }
      return;
    }
    if (value?.action === "dialogue" && value.ok && uuid.test(value.data.maidId ?? "") && typeof value.data.eventId === "string" && typeof value.data.sessionKey === "string") {
      onDialogue(value);
      return;
    }
    if (value?.ok && value.action === "lifecycle") {
      onLifecycle(value);
      return;
    }
    if (value?.ok && value.action === "chat-result") {
      onChatResult(value);
      return;
    }
    const slot = value && pending.get(value.requestId);
    if (!slot || value.action !== slot.entry.action) return;
    if (!matchesMaidReply(value, slot.entry, slot.order)) {
      slot.mismatchedReply = true;
      return;
    }
    if (value.ok && value.action === "workshop") workshopObserved = true;
    settle(value.requestId, value);
  };
  const onSystemText = (text2, position, original, sender) => {
    if (position !== "system" || sender != null || typeof text2 !== "string" || !text2.startsWith("QD_MAID ")) return;
    onPacket({ channel: MAID_CHANNEL, data: Buffer.from(text2.slice(8), "utf8") });
  };
  bot.on("messagestr", onSystemText);
  const close = () => {
    if (closed) return;
    closed = true;
    bot.off("messagestr", onSystemText);
    bot._client.off("custom_payload", onPacket);
    bot._client.off("end", close);
    for (const [id2, slot] of pending) settle(id2, slot.sent ? unknown(slot.entry, "connection_closed") : { ok: false, status: "not_dispatched", reason: "connection_closed" });
  };
  function usePayload(slot) {
    return pluginTransport && (workshopTransport || !["workshop", "make"].includes(slot.entry.action));
  }
  function send(slot) {
    if (closed || slot.sent || !pending.has(slot.entry.requestId)) return;
    slot.sent = true;
    slot.timer = setTimeout(() => settle(slot.entry.requestId, unknown(slot.entry, slot.mismatchedReply ? "reply_mismatch" : "reply_timeout")), timeoutMs);
    try {
      if (usePayload(slot)) bot._client.write("custom_payload", { channel: MAID_REQUEST_CHANNEL, data: Buffer.from(JSON.stringify({ schema: 1, protocol: "qiandengji-maids/v1", command: slot.entry.command })) });
      else bot.chat(slot.entry.command);
    } catch {
      settle(slot.entry.requestId, unknown(slot.entry, "send_uncertain"));
    }
  }
  function schedule(slot) {
    const payload2 = usePayload(slot);
    const key = payload2 ? "payloadNext" : "next", spacing = payload2 ? 80 : 1100;
    const wait = Math.max(0, (commandWindow[key] ?? 0) - Date.now());
    commandWindow[key] = Date.now() + wait + spacing;
    if (wait) slot.queuedTimer = setTimeout(() => send(slot), wait);
    else send(slot);
  }
  bot._client.on("custom_payload", onPacket);
  bot._client.once("end", close);
  bot._client.write("custom_payload", { channel: "minecraft:register", data: Buffer.from(MAID_CHANNEL + "\0" + MAID_REQUEST_CHANNEL) });
  return {
    close,
    get transport() {
      return pluginTransport ? "plugin_message" : "rate_limited_command";
    },
    get workshopSupported() {
      return workshopSupported();
    },
    async request(args) {
      let entry;
      try {
        entry = maidCommand(args);
      } catch (error) {
        return { ok: false, status: "not_dispatched", error: String(error.message) };
      }
      const notDispatched = (reason) => ({ ...unknown(entry, reason), status: "not_dispatched" });
      const make = entry.action === "make";
      if (make && !workshopSupported()) return notDispatched(closed ? "connection_closed" : "workshop_capability_unconfirmed");
      const craft = crafts.get(entry.operationId);
      if (craft && entry.action !== "receipt") return craft.command === entry.command ? craft.result : notDispatched("request_conflict");
      if (closed || pending.size >= 8 || pending.has(entry.requestId)) return { ok: false, status: "not_dispatched", reason: closed ? "connection_closed" : "request_busy" };
      let resolve;
      const result = new Promise((done) => {
        resolve = done;
      });
      const order = entry.order ?? craft?.order;
      if (make) crafts.set(entry.operationId, { command: entry.command, result, order });
      const slot = { entry, order, resolve, sent: false, timer: null, queuedTimer: null, mismatchedReply: false };
      pending.set(entry.requestId, slot);
      schedule(slot);
      return result;
    }
  };
}

// integrations/qiandengji/engine/maids.ts
var uuid2 = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
var object4 = (v) => !!v && typeof v === "object" && !Array.isArray(v);
var text = (v, max = 160) => typeof v === "string" ? v.replace(/[\r\n\u0000-\u001f]/g, " ").slice(0, max) : "";
var reads = /* @__PURE__ */ new Set(["nearby", "list", "context", "inventory", "tasks", "workshop", "receipt", "inbox", "skins", "voices", "resources"]);
var maidReadAction = (action, args = {}) => typeof action === "string" && (reads.has(action) || action === "brain" && args.choice === void 0);
var parameters = structuredClone(MAID_TOOL.parameters);
delete parameters.properties.playerSlot;
parameters.properties.playerWindowSlot = {
  type: "integer",
  minimum: 9,
  maximum: 44,
  description: "Actual self inventory window slot: 9\u201335 main inventory, 36\u201344 hotbar. Read mc_script api:inventory.items, then await bot.inventory.items() for exact slots; mc_bag totals do not identify a slot. Converted to Bukkit 0\u201335 by this adapter; do not pass a Bukkit slot here. Required for transfer put."
};
var QIANDENGJI_MAIDS_TOOL = {
  ...MAID_TOOL,
  parameters,
  readOnlyCall: (args) => maidReadAction(args.action, args),
  description: 'Optional server-owned companion NPC operations, distinct from real players. list finds owned companions; nearby discovers public conversation targets. Read context/inventory/tasks for an observed maidId and choose an available task, including farming at a permitted plot. Read results are native observations. Writes require a saved requestId and enter the existing body queue; queue acceptance is not application. Use receipt with the original operationId after the body command is sent. chat invokes the native maid model; pending/queued/unknown are not replies. workshop lists authorized workstations, recipes, output per craft and currentOrder. make needs confirmed workshop support and queues each requestId once per connection. After dispatch or reconnect, query receipt with the original operationId and operationAction:make. Check status, goalCompleted, and the verified delivered item, count and inventory. transfer uses playerWindowSlot (Mineflayer 9\u201344), not Bukkit slots; read mc_bag {detail:"slots"} for exact self slots. inventoryAccess distinguishes usable capacity from empty slots. equip swaps an observed maid slot with main/off/head/chest/legs/feet. Observe actual equipment afterwards. Death/unloaded are separate; context gives original tombstone evidence. No automatic recreation or retry. When context.conversation is present, ordinary nearby name-addressed chat uses its observed range and channel. brain without choice only reads configured modes; selecting a returned choice is a separate write. Full task, voice, menu and recovery semantics are in mc_guide topic:maids. Mutation commands are not ordinary public chat or mc_cast spells.'
};
function maidArguments(args) {
  if (Object.hasOwn(args, "playerSlot")) throw Error("Use playerWindowSlot from your current inventory (9\u201344); Bukkit playerSlot is internal to this adapter.");
  const { playerWindowSlot, ...native } = args;
  if (playerWindowSlot !== void 0) {
    if (args.action !== "transfer" || !Number.isInteger(playerWindowSlot) || Number(playerWindowSlot) < 9 || Number(playerWindowSlot) > 44)
      throw Error("playerWindowSlot must be an observed self inventory slot 9\u201344, only for transfer.");
    native.playerSlot = Number(playerWindowSlot) >= 36 ? Number(playerWindowSlot) - 36 : Number(playerWindowSlot);
  }
  maidCommand(native);
  return native;
}
function maidSystemReply(line, selfUuid) {
  return line.startsWith("QD_MAID ") && line.length <= 24008 ? decodeMaidReply({ channel: MAID_CHANNEL, data: Buffer.from(line.slice(8), "utf8") }, selfUuid) : null;
}
function maidInventoryAccess(reply) {
  const data = reply.data, n = data?.availableSlots, total = data?.slotCount;
  if (!reply.ok || reply.action !== "inventory" || !Number.isSafeInteger(n) || !Number.isSafeInteger(total) || Number(n) < 0 || Number(n) > Number(total) || Number(total) > 256 || !Array.isArray(data?.slots)) return null;
  const occupied = /* @__PURE__ */ new Set();
  for (const value of data.slots) {
    if (!object4(value) || !Number.isSafeInteger(value.slot) || Number(value.slot) < 0 || Number(value.slot) >= Number(total) || typeof value.count !== "number" || !Number.isFinite(value.count)) return null;
    if (value.count > 0 && value.id !== "minecraft:air" && Number(value.slot) < Number(n)) occupied.add(Number(value.slot));
  }
  const emptySlots = Array.from({ length: Number(n) }, (_, i) => i).filter((i) => !occupied.has(i));
  return {
    observedAt: reply.sampledAt,
    usableSlotCount: n,
    usableSlotRange: Number(n) > 0 ? [0, Number(n) - 1] : null,
    emptySlots,
    freeSlotCount: emptySlots.length,
    lockedSlotCount: Number(total) - Number(n),
    note: "availableSlots \u662F\u5DF2\u89E3\u9501\u53EF\u7528\u5BB9\u91CF\uFF0C\u4E0D\u662F\u7A7A\u69FD\u6570\u3002\u53EA\u5728\u53EF\u7528\u69FD\u8303\u56F4\u64CD\u4F5C\uFF1B\u7A7A\u69FD\u4E3A\u672C\u6B21 inventory \u56DE\u6267\u7684\u63A8\u5BFC\uFF0C\u80CC\u5305\u53D8\u5316\u540E\u91CD\u8BFB\u3002"
  };
}
var finiteDistance = (v, max) => typeof v === "number" && Number.isFinite(v) && v >= 0 && v <= max ? v : null;
function followObservation(row, observedAt) {
  if (!object4(row.follow)) return null;
  const f = row.follow;
  return {
    observedAt,
    policy: text(f.policy, 80),
    active: typeof f.active === "boolean" ? f.active : null,
    state: text(f.state, 80) || null,
    walkBeyond: finiteDistance(f.walkBeyond, 256),
    stopWithin: finiteDistance(f.stopWithin, 256),
    recoveryBeyond: finiteDistance(f.recoveryBeyond, 256),
    ownerDistance: finiteDistance(row.ownerDistance, 6e7),
    distanceUnit: text(f.distanceUnit, 16),
    customized: typeof f.customized === "boolean" ? f.customized : null,
    nextStep: text(f.nextStep, 240)
  };
}
function decisionFollow(f, now) {
  if (!f) return null;
  const age = now - Date.parse(f.observedAt), recent = Number.isFinite(age) && age >= 0 && age <= 1e4;
  return recent ? { ...f, freshness: "recent" } : {
    ...f,
    freshness: "historical",
    active: null,
    state: null,
    ownerDistance: null,
    lastObservation: { active: f.active, state: f.state, ownerDistance: f.ownerDistance }
  };
}
var receiptOf = (reply) => ({
  protocol: reply.protocol,
  recipientUuid: reply.recipientUuid,
  action: reply.action,
  requestId: reply.requestId,
  sampledAt: reply.sampledAt
});
var observedTime = (value, sampledAt) => typeof value === "string" && Number.isFinite(Date.parse(value)) && Date.parse(value) <= Date.parse(sampledAt) ? value : null;
var laterTime = (...values) => values.filter((v) => !!v).sort((a, b) => Date.parse(b) - Date.parse(a))[0] ?? null;
var ownedEvidence = (value, row) => object4(value) && value.maidId === row.maidId && value.ownerId === row.ownerId && typeof value.eventId === "string" && /^[A-Za-z0-9_-]{1,48}$/.test(value.eventId) ? value : null;
function deathEvidence(value, row, sampledAt) {
  const d = ownedEvidence(value, row);
  return d && ["original_tlm_tombstone", "original_tlm_death_event"].includes(String(d.evidence)) && observedTime(d.diedAt, sampledAt) ? d : null;
}
var MaidState = class {
  rows = /* @__PURE__ */ new Map();
  notices = /* @__PURE__ */ new Set();
  scene;
  sceneChangedAt = 0;
  captions = /* @__PURE__ */ new Map();
  reset() {
    this.rows.clear();
    this.notices.clear();
    this.scene = void 0;
    this.sceneChangedAt = 0;
    for (const row of this.captions.values()) clearTimeout(row.timer);
    this.captions.clear();
  }
  /** Source-owned supervisor summary; full inventory and task lists stay on demand. */
  summary() {
    return [...this.rows.values()].slice(0, 4).map((row) => ({
      maidId: row.maidId,
      ownerId: row.ownerId,
      name: row.name,
      ownerRelation: "self-is-owner",
      controlNote: "\u672C\u4EBA\u662F\u6B64\u89D2\u8272\u7684\u670D\u52A1\u7AEF\u767B\u8BB0\u4E3B\u4EBA\uFF0C\u53EF\u7ECF mc_maids chat \u4E0B\u5DE5\u4F5C\u6307\u4EE4\u5E76\u67E5\u8BE2 receipt\uFF1B\u516C\u5F00\u804A\u5929\u4E0D\u81EA\u52A8\u7B49\u4E8E\u5DE5\u4F5C\u6307\u4EE4\u3002",
      entityIdentity: {
        uuid: row.maidId,
        kind: "maid",
        source: "qiandengji-maids/v1",
        originalEntity: row.originalEntity,
        viewerAppearance: row.viewerAppearance
      },
      observedAt: row.sampledAt,
      sourceReceipt: { ...row.sourceReceipt },
      lifeState: row.lifeState,
      loaded: row.loaded,
      health: row.health,
      taskId: row.taskId,
      sitting: row.sitting,
      canMove: row.canMove,
      dimension: row.dimension,
      position: row.position,
      lastAliveAt: row.lastAliveAt,
      recovery: row.recovery ? {
        eventId: row.recovery.eventId,
        observedAt: row.recovery.observedAt,
        resolvedDeathEventId: row.recovery.resolvedDeathEventId,
        actualRevivalTimeKnown: false,
        persisted: row.recovery.persisted
      } : null,
      historicalDeath: row.historicalDeath ? { eventId: row.historicalDeath.eventId, diedAt: row.historicalDeath.diedAt } : null,
      death: row.death ? { eventId: row.death.eventId, diedAt: row.death.diedAt, dimension: row.death.dimension, position: row.death.position } : null,
      equipment: row.equipment ? Object.fromEntries(["main", "off", "head", "chest", "legs", "feet"].map((slot) => {
        const item = row.equipment?.[slot];
        return [slot, object4(item) ? {
          id: text(item.id, 128),
          ...text(item.displayName ?? item.name) ? { displayName: text(item.displayName ?? item.name) } : {},
          count: typeof item.count === "number" ? item.count : null
        } : null];
      })) : null,
      equipmentObservedAt: row.equipmentAt,
      conversation: row.conversation,
      follow: row.follow,
      read: { tool: "mc_maids", action: "context", maidId: row.maidId }
    }));
  }
  /** A context/list reply is a dated sample, not a continuously tracked entity.
   * Keep identity and lifecycle evidence, but never reuse old geometry as current. */
  decisionSummary(now = Date.now(), observations = [], boundary) {
    if (boundary !== void 0) {
      if (this.scene !== void 0 && boundary !== this.scene) this.sceneChangedAt = now;
      this.scene = boundary;
    }
    return this.summary().map((row) => {
      const age = now - Date.parse(row.observedAt), current = Number.isFinite(age) && age >= 0 && age <= 1e4 && Date.parse(row.observedAt) >= this.sceneChangedAt;
      const entityObservation = observations.find((e) => e.uuid.toLowerCase() === row.maidId.toLowerCase() && e.identitySource === "qiandengji-maids/v1" && now - Date.parse(e.sampledAt) >= 0 && now - Date.parse(e.sampledAt) <= 1e4) ?? null;
      const presence = {
        entityObservation,
        presence: entityObservation ? "observed-here" : "unknown",
        presenceNote: entityObservation ? "\u5F53\u524D\u5B9E\u4F53\u5FEB\u7167\u6309\u670D\u52A1\u7AEF UUID \u5339\u914D\uFF1B\u8FD9\u91CC\u7684\u8DDD\u79BB\u4E0E\u53EF\u89C1\u6027\u4F18\u5148\u4E8E\u65E7 context \u4F4D\u7F6E\u3002\u4E0D\u662F\u58F0\u97F3\u6216\u4EA4\u4E92\u8BB8\u53EF\u3002" : "\u672C\u6B21\u672A\u89C2\u5BDF\u5230\uFF0C\u4E0D\u8BC1\u660E\u672A\u4F20\u9001\u3001\u6389\u961F\u6216\u6B7B\u4EA1\u3002\u65E0\u9700\u4E3A\u7B49\u540C\u4F34\u800C\u51BB\u7ED3\u81EA\u8EAB\u4EFB\u52A1\uFF1B\u8DDF\u968F\u7531\u5B9E\u9645\u914D\u7F6E\u548C\u670D\u52A1\u7AEF\u5904\u7406\u3002"
      };
      if (current && !entityObservation) return { ...row, ...presence, follow: decisionFollow(row.follow, now), freshness: "recent", ageMs: age };
      const { position, dimension, health, loaded, lifeState, taskId, sitting, canMove, ...identityAndEvidence } = row;
      return {
        ...identityAndEvidence,
        ...presence,
        follow: decisionFollow(row.follow, now),
        freshness: "historical",
        ageMs: Number.isFinite(age) ? age : null,
        position: null,
        dimension: null,
        health: null,
        loaded: null,
        lifeState: "unknown",
        taskId: null,
        sitting: null,
        canMove: null,
        lastObservation: { observedAt: row.observedAt, position, dimension, health, loaded, lifeState, taskId, sitting, canMove },
        note: "context \u662F\u72EC\u7ACB\u65F6\u523B\u7684\u670D\u52A1\u7AEF\u91C7\u6837\uFF1B\u672C\u6B21\u5B9E\u4F53\u4F4D\u7F6E\u6765\u81EA entityObservation\u3002\u65E7\u4F4D\u7F6E\u4E0D\u8BC1\u660E\u6389\u961F\uFF1B\u65E0\u5B9E\u4F53\u89C2\u5BDF\u4E5F\u4E0D\u80FD\u63A8\u51FA\u672A\u4F20\u9001\u3002\u8EAB\u4F53\u8BE6\u60C5\u6309\u9700 mc_maids context \u6838\u5BF9\u3002"
      };
    });
  }
  /** Join only a server-owned UUID from this connection, never a custom-name guess. */
  identity(entityUuid) {
    if (!entityUuid) return null;
    const row = [...this.rows.values()].find((row2) => row2.maidId.toLowerCase() === entityUuid.toLowerCase());
    if (!row) return null;
    return {
      uuid: row.maidId,
      kind: "maid",
      name: row.name,
      label: row.name,
      ownerUuid: row.ownerId,
      source: "qiandengji-maids/v1",
      observedAt: row.sampledAt
    };
  }
  /** Match the literal server presentation format against a current native entity.
   * This is nearby scene speech, not an ASR transcript or a managed dialogue receipt. */
  nearbySceneSpeech(notice, currentEntityUuids) {
    const match = /^\[MC (?:系统|插件)\] \[附近·女仆\] ([^：:\r\n]{1,160})[：:]([^\r\n]{1,500})$/u.exec(notice);
    if (!match) return;
    const body = match[2].trim();
    if (!body) return;
    const known = [...this.rows.values()].filter((row) => row.name === match[1]);
    if (known.length !== 1 || !currentEntityUuids.has(known[0].maidId.toLowerCase())) return;
    const { maidId, name } = known[0];
    return {
      text: notice,
      senderKey: `maid:${maidId}`,
      meta: {
        from: name,
        body,
        senderUuid: maidId,
        senderKind: "companion",
        channel: "public",
        socialScope: "minecraft-server",
        identityEvidence: "qiandengji-maids/v1",
        chatChannel: "nearby",
        chatScope: "same-world-range",
        chatRoutingSource: "native-maid-scene"
      }
    };
  }
  speechKey(scope, dialogue) {
    return JSON.stringify([scope, dialogue.senderKey, dialogue.meta.body]);
  }
  recentSpeech(key) {
    const now = Date.now();
    for (const [saved, row] of this.captions) if (!row.timer && now - row.at > 2500) this.captions.delete(saved);
    return this.captions.get(key);
  }
  /** The server sends the public caption immediately before its typed dialogue
   * receipt. Give that receipt preference without delaying normal HUD events. */
  queueSceneSpeech(scope, dialogue, deliver) {
    const key = this.speechKey(scope, dialogue), recent = this.recentSpeech(key);
    if (recent) {
      if (recent.kind === "typed") this.captions.delete(key);
      return true;
    }
    if (this.captions.size >= 64) return false;
    const row = { kind: "caption", at: Date.now() };
    row.timer = setTimeout(() => {
      if (this.captions.get(key) !== row) return;
      delete row.timer;
      row.at = Date.now();
      deliver();
    }, 400);
    row.timer.unref();
    this.captions.set(key, row);
    return true;
  }
  acceptTypedSpeech(scope, dialogue) {
    const key = this.speechKey(scope, dialogue), recent = this.recentSpeech(key);
    if (recent?.kind === "caption") {
      this.captions.delete(key);
      if (!recent.timer) return false;
      clearTimeout(recent.timer);
      return true;
    }
    if (!recent && this.captions.size < 64) this.captions.set(key, { kind: "typed", at: Date.now() });
    return true;
  }
  /** Legacy additive note; new consumers should carry identity() as the primary label. */
  identityNote(entityUuid) {
    const identity = this.identity(entityUuid);
    if (!identity) return null;
    const row = [...this.rows.values()].find((row2) => row2.maidId === identity.uuid);
    return `\u670D\u52A1\u7AEF\u786E\u8BA4\u8EAB\u4EFD\uFF1A${identity.name}\uFF08\u5F52\u5C5E\u672C\u4EBA\uFF0C\u4E0D\u662F\u72EC\u7ACB\u73A9\u5BB6\uFF09` + (row.originalEntity && row.viewerAppearance === "vanilla_compat_projection" ? "\uFF1B\u5F53\u524D\u5B9E\u4F53\u79CD\u7C7B\u4EC5\u4E3A\u539F\u7248\u517C\u5BB9\u5916\u89C2\uFF0C\u4E0D\u662F\u5979\u7684\u771F\u5B9E\u79CD\u7C7B" : "");
  }
  observe(reply) {
    const d = reply.data;
    if (!reply.ok || !object4(d)) return null;
    const candidates = reply.action === "list" && Array.isArray(d.maids) ? d.maids.slice(0, 8) : ["context", "lifecycle"].includes(reply.action) ? [d] : [];
    const changes = [];
    for (const row2 of candidates) {
      if (!object4(row2) || typeof row2.maidId !== "string" || !uuid2.test(row2.maidId) || typeof row2.ownerId !== "string" || row2.ownerId.toLowerCase() !== reply.recipientUuid.toLowerCase()) continue;
      const previous = this.rows.get(row2.maidId);
      if (previous && Date.parse(previous.sampledAt) > Date.parse(reply.sampledAt)) continue;
      const reportedDeath = row2.lifeState === "dead" ? deathEvidence(row2.death, row2, reply.sampledAt) : null;
      const candidateRecovery = ownedEvidence(row2.recovery, row2);
      const recovery = candidateRecovery && candidateRecovery.evidence === "original_tlm_alive_entity" && candidateRecovery.actualRevivalTimeKnown === false && typeof candidateRecovery.persisted === "boolean" && observedTime(candidateRecovery.observedAt, reply.sampledAt) ? candidateRecovery : previous?.recovery ?? null;
      const lastAliveAt = laterTime(
        previous?.lastAliveAt,
        row2.lifeState === "alive" ? reply.sampledAt : null,
        object4(row2.lastSeenAlive) ? observedTime(row2.lastSeenAlive.observedAt, reply.sampledAt) : null,
        recovery?.persisted === true ? observedTime(recovery.observedAt, reply.sampledAt) : null
      );
      const superseded = !!(reportedDeath && lastAliveAt && (Date.parse(String(reportedDeath.diedAt)) < Date.parse(lastAliveAt) || recovery?.persisted === true && recovery.resolvedDeathEventId === reportedDeath.eventId && Date.parse(String(reportedDeath.diedAt)) <= Date.parse(String(recovery.observedAt))));
      const death = superseded ? null : reportedDeath;
      const lifeState = row2.lifeState === "dead" && death ? "dead" : row2.lifeState === "alive" ? "alive" : "unknown";
      const historicalDeath = [
        deathEvidence(row2.historicalDeath, row2, reply.sampledAt),
        previous?.historicalDeath,
        superseded ? reportedDeath : null,
        lifeState === "alive" ? previous?.death : null
      ].filter((d2) => !!d2).sort((a, b) => Date.parse(String(b.diedAt)) - Date.parse(String(a.diedAt)))[0] ?? null;
      const equipmentInvalidated = lifeState === "dead" || previous?.lifeState === "dead" && lifeState === "alive";
      const next = {
        maidId: row2.maidId,
        ownerId: row2.ownerId,
        name: text(row2.name) || previous?.name || row2.maidId,
        originalEntity: typeof row2.fullOriginalEntityMaid === "boolean" ? row2.fullOriginalEntityMaid : previous?.originalEntity ?? false,
        viewerAppearance: typeof row2.viewerAppearance === "string" ? text(row2.viewerAppearance, 80) : previous?.viewerAppearance ?? null,
        sampledAt: reply.sampledAt,
        sourceReceipt: receiptOf(reply),
        lifeState,
        loaded: typeof row2.loaded === "boolean" ? row2.loaded : null,
        health: typeof row2.health === "number" && Number.isFinite(row2.health) ? row2.health : null,
        maxHealth: typeof row2.maxHealth === "number" && Number.isFinite(row2.maxHealth) ? row2.maxHealth : null,
        taskId: typeof row2.taskId === "string" ? row2.taskId : null,
        dialogueMode: typeof row2.dialogueMode === "string" ? row2.dialogueMode : null,
        sitting: typeof row2.sitting === "boolean" ? row2.sitting : null,
        canMove: typeof row2.canMove === "boolean" ? row2.canMove : null,
        dimension: typeof row2.dimension === "string" ? text(row2.dimension, 128) : null,
        position: Array.isArray(row2.position) && row2.position.length === 3 && row2.position.every(Number.isFinite) ? [...row2.position] : null,
        death,
        lastAliveAt,
        historicalDeath,
        recovery,
        follow: reply.action === "context" ? followObservation(row2, reply.sampledAt) : previous?.follow ?? null,
        conversation: reply.action === "context" ? object4(row2.conversation) ? {
          observedAt: reply.sampledAt,
          nearbyRange: typeof row2.conversation.nearbyRange === "number" && Number.isFinite(row2.conversation.nearbyRange) && row2.conversation.nearbyRange >= 0 && row2.conversation.nearbyRange <= 128 ? row2.conversation.nearbyRange : null,
          addressExample: text(row2.conversation.addressExample, 140),
          ownerWorkCommand: text(row2.conversation.ownerWorkCommand, 256)
        } : null : previous?.conversation ?? null,
        equipment: equipmentInvalidated ? null : previous?.equipment ?? null,
        equipmentAt: equipmentInvalidated ? null : previous?.equipmentAt ?? null
      };
      this.rows.set(row2.maidId, next);
      const changed = previous?.lifeState !== lifeState || previous?.death?.eventId !== death?.eventId || previous?.recovery?.eventId !== recovery?.eventId;
      if (changed) {
        const notice = this.lifeNotice(next, previous, reply);
        if (notice) changes.push(notice);
      }
    }
    if (reply.action === "inventory" && typeof d.maidId === "string" && object4(d.equipment)) {
      const row2 = this.rows.get(d.maidId);
      if (row2 && row2.ownerId.toLowerCase() === reply.recipientUuid.toLowerCase() && (d.ownerId === void 0 || d.ownerId === row2.ownerId) && (!row2.equipmentAt || Date.parse(reply.sampledAt) >= Date.parse(row2.equipmentAt))) {
        row2.equipment = d.equipment;
        row2.equipmentAt = reply.sampledAt;
      }
    }
    while (this.rows.size > 32) this.rows.delete(this.rows.keys().next().value);
    if (changes.length) return changes.length === 1 ? changes[0] : {
      text: changes.map((n) => n.text).join("\n"),
      urgent: changes.some((n) => n.urgent),
      meta: { maidObservations: changes.map((n) => n.meta.maidObservation) }
    };
    if (reply.action !== "chat-result" || typeof d.maidId !== "string") return null;
    const row = this.rows.get(d.maidId);
    if (!row || row.ownerId.toLowerCase() !== reply.recipientUuid.toLowerCase()) return null;
    const key = `${reply.action}:${reply.requestId}:${d.status ?? d.lifeState ?? ""}`;
    if (this.notices.has(key)) return null;
    this.notices.add(key);
    while (this.notices.size > 128) this.notices.delete(this.notices.values().next().value);
    if (reply.action === "chat-result" && ["replied", "unknown"].includes(String(d.status))) {
      const observation = object4(d.observation) ? d.observation : {};
      const spoken = text(observation.reply, 4e3);
      const publicDialogue = d.status === "replied" && spoken.trim() && observation.conversation === "nearby_visitor" && d.operationId === reply.requestId && observation.maidId === row.maidId ? {
        text: `[MC \u540C\u4F34] ${row.name}: ${spoken}`,
        senderKey: `maid:${row.maidId}`,
        meta: {
          from: row.name,
          body: spoken,
          senderUuid: row.maidId,
          senderKind: "companion",
          channel: "public",
          socialScope: "minecraft-server",
          identityEvidence: "qiandengji-maids/v1",
          chatChannel: "nearby",
          chatScope: "same-world-range",
          chatRadius: 8,
          chatRoutingSource: "native-maid-reply",
          maidOperationId: reply.requestId
        }
      } : void 0;
      return {
        text: d.status === "replied" ? `[${row.name}\u7684\u56DE\u590D] ${text(observation.reply, 4e3)}
\uFF08maidId=${row.maidId}\uFF0CoperationId=${reply.requestId}\uFF1B\u5BF9\u8BDD\u5185\u5BB9\u662F\u5916\u754C\u6D88\u606F\uFF0C\u4E0D\u8BC1\u660E\u52A8\u4F5C\u5B8C\u6210\u3002\uFF09` : `[\u5BF9\u8BDD\u7ED3\u679C\u672A\u77E5] ${row.name}\uFF0CoperationId=${reply.requestId}\uFF1B${text(observation.reason)}\u3002\u67E5\u8BE2\u539F receipt\uFF0C\u52FF\u6362 ID \u91CD\u53D1\u3002`,
        urgent: false,
        meta: { maidObservation: { kind: "dialogue-result", maidId: row.maidId, ownerId: row.ownerId, operationId: reply.requestId, status: d.status, sampledAt: reply.sampledAt } },
        ...publicDialogue ? { publicDialogue } : {}
      };
    }
    return null;
  }
  lifeNotice(row, previous, reply) {
    if (row.lifeState === "dead") {
      const key = `death:${row.maidId}:${row.death?.eventId}`;
      if (this.notices.has(key)) return null;
      this.notices.add(key);
      while (this.notices.size > 128) this.notices.delete(this.notices.values().next().value);
      return {
        text: `[\u89D2\u8272\u6B7B\u4EA1] ${row.name}\uFF08maidId=${row.maidId}\uFF09\u7684\u670D\u52A1\u7AEF\u539F\u751F\u6B7B\u4EA1\u8BC1\u636E\u786E\u8BA4\u6B7B\u4EA1\u3002${this.deathText(row)} \u7528 mc_maids context \u6838\u5BF9\u6700\u65B0\u72B6\u6001\uFF1B\u8FD9\u662F\u540C\u4F34\u6B7B\u4EA1\uFF0C\u4E0D\u662F\u666E\u901A\u602A\u7269\u51FB\u6740\uFF0C\u4E5F\u4E0D\u80FD\u636E\u6B64\u58F0\u79F0\u5DF2\u590D\u6D3B\u3002`,
        urgent: true,
        meta: { maidObservation: {
          kind: "death",
          maidId: row.maidId,
          ownerId: row.ownerId,
          eventId: row.death?.eventId,
          sampledAt: reply.sampledAt,
          death: row.death,
          sourceReceipt: receiptOf(reply)
        } }
      };
    }
    const recoveryChanged = !!row.recovery && previous?.recovery?.eventId !== row.recovery.eventId;
    const recoveryKey = recoveryChanged ? `recovery:${row.maidId}:${row.recovery.eventId}` : null;
    const reportRecovery = !!recoveryKey && !this.notices.has(recoveryKey);
    if (reportRecovery) {
      this.notices.add(recoveryKey);
      while (this.notices.size > 128) this.notices.delete(this.notices.values().next().value);
    }
    if (row.lifeState === "unknown" && !previous && !reportRecovery) return null;
    if (previous?.lifeState === row.lifeState && !reportRecovery) return null;
    const state = row.lifeState === "alive" ? `\u539F UUID \u5F53\u65F6\u5B58\u6D3B\uFF0C\u751F\u547D ${row.health ?? "\u672A\u77E5"}/${row.maxHealth ?? "\u672A\u77E5"}` : "\u5F53\u524D\u672A\u786E\u8BA4\u5B58\u6D3B\u72B6\u6001\uFF1B\u672A\u52A0\u8F7D\u4E0D\u7B49\u4E8E\u6B7B\u4EA1";
    return {
      text: `[\u89D2\u8272\u72B6\u6001\u66F4\u65B0] ${row.name}\uFF08maidId=${row.maidId}\uFF09\uFF0C${reply.sampledAt}\uFF1A${state}\u3002` + (reportRecovery ? ` \u670D\u52A1\u7AEF\u6062\u590D\u89C1\u8BC1 eventId=${row.recovery.eventId}\uFF0C\u89C2\u5BDF ${row.recovery.observedAt}\uFF1B\u4E0D\u662F\u5B9E\u9645\u590D\u6D3B\u65F6\u95F4\uFF0C\u4E5F\u4E0D\u8BC1\u660E\u5F53\u524D\u5B9E\u4F53\u5DF2\u52A0\u8F7D\u3002` : "") + (row.lifeState === "alive" ? "\u65E7\u6B7B\u4EA1\u8BB0\u5F55\u4E0D\u80FD\u5F53\u4F5C\u5F53\u524D\u6B7B\u4EA1\uFF1B\u9057\u7269\u53D6\u56DE\u3001\u88C5\u5907\u548C\u5DE5\u4F5C\u5B8C\u6210\u4ECD\u987B\u5206\u522B\u6838\u9A8C\u3002" : "\u7528 mc_maids context \u6309\u9700\u6838\u5BF9\u3002"),
      urgent: previous?.lifeState === "dead" && row.lifeState === "alive",
      meta: { maidObservation: {
        kind: "life-state",
        maidId: row.maidId,
        ownerId: row.ownerId,
        previousLifeState: previous?.lifeState ?? null,
        lifeState: row.lifeState,
        sampledAt: reply.sampledAt,
        requestId: reply.requestId,
        sourceReceipt: receiptOf(reply),
        ...reportRecovery ? {
          eventId: row.recovery.eventId,
          lifecycleEventKind: "recovery-observation",
          recovery: { ...row.recovery }
        } : {}
      } }
    };
  }
  deathText(row) {
    const d = row.death;
    if (!d) return "";
    const pos = Array.isArray(d.position) && d.position.length === 3 && d.position.every(Number.isFinite) ? JSON.stringify(d.position) : "\u672A\u77E5";
    return `\u6B7B\u4EA1\u8BB0\u5F55 ${text(d.diedAt)}\uFF1B\u9057\u7269 ${text(d.dimension)} ${pos}\uFF1B${text(d.nextStep, 360)}`;
  }
  brief(now = Date.now()) {
    if (!this.rows.size) return "";
    return "[\u968F\u884C\u89D2\u8272\u7684\u6700\u8FD1\u670D\u52A1\u7AEF\u8BB0\u5F55\uFF1B\u8EAB\u4EFD\u4E0E\u5F52\u5C5E\u5DF2\u786E\u8BA4\uFF0C\u540E\u7EED\u53D8\u5316\u987B\u67E5\u8BE2]\n" + [...this.rows.values()].slice(0, 4).map((row) => {
      const age = now - Date.parse(row.sampledAt), historical = !Number.isFinite(age) || age < 0 || age > 1e4;
      const state = row.lifeState === "dead" ? "\u5DF2\u786E\u8BA4\u6B7B\u4EA1\uFF0C\u590D\u6D3B\u672A\u9A8C\u8BC1" : row.lifeState === "alive" ? `\u5F53\u65F6\u5B58\u6D3B\uFF0C\u751F\u547D${row.health ?? "\u672A\u77E5"}/${row.maxHealth ?? "\u672A\u77E5"}` : "\u5B58\u6D3B\u72B6\u6001\u672A\u77E5\uFF0C\u672A\u52A0\u8F7D\u4E0D\u7B49\u4E8E\u6B7B\u4EA1";
      return `${row.name} maidId=${row.maidId}\uFF0C${row.sampledAt}${historical ? "\uFF08\u5386\u53F2\u91C7\u6837\uFF0C\u5F53\u524D\u8EAB\u4F53/\u4F4D\u7F6E\u5F85\u91CD\u8BFB\uFF09" : ""}\uFF1A${state}\uFF0C\u5F53\u65F6\u5DE5\u4F5C=${row.taskId ?? "\u672A\u77E5"}\uFF0C\u5BF9\u8BDD=${row.dialogueMode ?? "\u672A\u77E5"}\u3002 \u5F53\u65F6\u5750\u4E0B=${row.sitting ?? "\u672A\u77E5"}\uFF0C\u53EF\u79FB\u52A8=${row.canMove ?? "\u672A\u77E5"}\uFF0C${historical ? "\u5386\u53F2\u91C7\u6837\u4F4D\u7F6E\uFF08\u975E\u5F53\u524D\u4F4D\u7F6E\uFF09" : "\u91C7\u6837\u4F4D\u7F6E"}=${row.dimension ?? "\u672A\u77E5"} ${row.position ? JSON.stringify(row.position) : "\u672A\u77E5"}\u3002` + (row.conversation ? ` \u4EA4\u8C08\u5951\u7EA6\uFF08${row.conversation.observedAt}\uFF09\uFF1A\u540C\u4E16\u754C\u9644\u8FD1\u70B9\u540D\u201C${row.conversation.addressExample}\u201D\uFF0C\u8303\u56F4=${row.conversation.nearbyRange ?? "\u672A\u77E5"}\u683C\uFF1B\u8FD9\u662F\u516C\u5F00\u804A\u5929\u3002\u4E3B\u4EBA\u5DE5\u4F5C\u4ECD\u7528 mc_maids chat \u2192 receipt\uFF0C\u53D1\u9001\u4E0D\u7B49\u4E8E\u56DE\u590D\u6216\u5B8C\u6210\u3002` : "") + (row.follow ? ` \u8DDF\u968F\u91C7\u6837\uFF08${row.follow.observedAt}\uFF09\uFF1A${JSON.stringify(decisionFollow(row.follow, now))}\uFF1B\u9608\u503C\u6765\u81EA\u670D\u52A1\u7AEF\uFF0C\u4E0D\u662F\u9700\u8981\u7B49\u5979\u8D34\u8EAB\u7684\u4EFB\u52A1\u6761\u4EF6\uFF1B\u5B8C\u6574\u968F\u884C/\u4F20\u9001\u6761\u4EF6\u89C1 mc_guide maids\u3002` : "") + (row.historicalDeath ? ` \u5386\u53F2\u6B7B\u4EA1 ${text(row.historicalDeath.diedAt)}${row.lastAliveAt ? `\uFF1B\u6700\u8FD1\u786E\u8BA4\u5B58\u6D3B ${row.lastAliveAt}` : ""}\uFF0C\u4E0D\u80FD\u5F53\u6210\u518D\u6B21\u6B7B\u4EA1\uFF1B\u9057\u7269\u53E6\u67E5\u3002` : "") + (row.recovery ? ` \u6062\u590D\u89C1\u8BC1 ${text(row.recovery.observedAt)}\uFF08\u4E0D\u662F\u5B9E\u9645\u590D\u6D3B\u65F6\u95F4\uFF1B\u6301\u4E45\u4FDD\u5B58=${row.recovery.persisted}\uFF09\u3002` : "") + (row.death ? this.deathText(row) : "") + (row.equipment ? ` \u88C5\u5907\u8BB0\u5F55 ${row.equipmentAt}\uFF1A${JSON.stringify(row.equipment).slice(0, 850)}` : " \u88C5\u5907\u672A\u67E5\u8BE2\uFF0C\u4E0D\u80FD\u5F53\u4F5C\u5DF2\u7ED9\u5979\u6B66\u5668/\u62A4\u7532\u3002");
    }).join("\n") + `
\u5171\u5DF2\u89C2\u5BDF${this.rows.size}\u4F4D\uFF1Bmc_maids \u7684 list/context/inventory/tasks/workshop/receipt \u6309\u9700\u8BFB\uFF0Cmc_guide maids \u67E5\u64CD\u4F5C\u3002`;
  }
};

// integrations/qiandengji/engine/world.ts
import { join } from "node:path";

// integrations/qiandengji/engine/viewer-ysm-assets.mjs
import { createHash, randomBytes } from "node:crypto";
import { gunzipSync } from "node:zlib";
var YSM_ASSET_CHANNEL = "mcagent:ysm_asset";
var MAX_BYTES = 2 * 1024 * 1024;
var MAX_RAW = 8 * 1024 * 1024;
var sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
function decodeYsmBundle(compressed, hash) {
  if (compressed.length > MAX_BYTES || sha(compressed) !== hash) throw Error("YSM_ASSET_HASH_MISMATCH");
  const raw = gunzipSync(compressed, { maxOutputLength: MAX_RAW });
  const bundle = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(raw));
  if (bundle.schemaVersion !== 1 || bundle.ysmVersion !== "2.4.1" || bundle.format !== "ysm-bedrock-original" || typeof bundle.modelId !== "string" || bundle.modelId.length > 96 || !bundle.files || Object.keys(bundle.files).length > 32) throw Error("YSM_ASSET_FORMAT_UNSUPPORTED");
  let total = 0;
  for (const [path, file] of Object.entries(bundle.files)) {
    if (path.startsWith("/") || path.includes("\\") || path.includes(":") || path.split("/").includes("..") || typeof file.base64 !== "string") throw Error("YSM_ASSET_PATH_INVALID");
    const bytes = Buffer.from(file.base64, "base64");
    total += bytes.length;
    if (total > MAX_RAW || bytes.length !== file.bytes || sha(bytes) !== file.sha256) throw Error("YSM_SOURCE_HASH_MISMATCH");
  }
  if (!bundle.files[bundle.model] || !bundle.files[bundle.animation] || !bundle.files["ysm.json"] || Object.values(bundle.textures ?? {}).some((path) => !bundle.files[path]) || Object.values(bundle.animations ?? {}).some((path) => typeof path !== "string" || !bundle.files[path]) || !Array.isArray(bundle.controllers ?? []) || (bundle.controllers?.length ?? 0) > 8 || (bundle.controllers ?? []).some((path) => typeof path !== "string" || !bundle.files[path])) throw Error("YSM_SOURCE_MISSING");
  return { ...bundle, assetSha256: hash };
}
function createYsmAssetReceiver(bot, { onAsset = () => {
}, onError = () => {
} } = {}) {
  const cache = /* @__PURE__ */ new Map(), queue = /* @__PURE__ */ new Map(), attempts = /* @__PURE__ */ new Map();
  let active = null, disposed = false, bytes = 0, lastStarted = 0;
  const start = () => {
    if (disposed || active || !queue.size || bot._client.state !== "play" || Date.now() - lastStarted < 600) return;
    const [hash, row] = queue.entries().next().value;
    queue.delete(hash);
    const requestId2 = randomBytes(16).toString("hex");
    active = { row, hash, requestId: requestId2, parts: [], size: 0, count: null, started: Date.now() };
    lastStarted = Date.now();
    attempts.set(hash, (attempts.get(hash) ?? 0) + 1);
    bot._client.write("custom_payload", { channel: YSM_ASSET_CHANNEL, data: Buffer.from(JSON.stringify({ type: "get", modelId: row.modelId, sha256: hash, requestId: requestId2 })) });
  };
  const fail = (reason) => {
    const prior = active;
    active = null;
    if (prior) onError(prior.row, reason);
    start();
  };
  const payload2 = (packet) => {
    if (packet.channel !== YSM_ASSET_CHANNEL || !active || packet.data.length > 18e3) return;
    try {
      const p = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(packet.data));
      if (p.schemaVersion !== 1 || p.type !== "chunk" || p.requestId !== active.requestId || p.sha256 !== active.hash) return;
      if (!Number.isInteger(p.count) || p.count < 1 || p.count > 171 || !Number.isInteger(p.index) || p.index < 0 || p.index >= p.count || !Number.isInteger(p.bytes) || p.bytes < 1 || p.bytes > MAX_BYTES || typeof p.data !== "string" || p.data.length > 16384 || active.count !== null && (active.count !== p.count || active.bytes !== p.bytes)) throw Error("YSM_TRANSFER_INVALID");
      active.count = p.count;
      active.bytes = p.bytes;
      if (active.parts[p.index]) return;
      const part = Buffer.from(p.data, "base64");
      if (part.length !== Math.min(12288, p.bytes - p.index * 12288)) throw Error("YSM_TRANSFER_SIZE_INVALID");
      active.parts[p.index] = part;
      active.size += part.length;
      if (active.parts.filter(Boolean).length === p.count) {
        if (active.size !== p.bytes) throw Error("YSM_TRANSFER_SIZE_INVALID");
        const bundle = decodeYsmBundle(Buffer.concat(active.parts), active.hash);
        if (bundle.modelId !== active.row.modelId) throw Error("YSM_MODEL_BINDING_MISMATCH");
        const size = Buffer.byteLength(JSON.stringify(bundle));
        while (cache.size >= 32 || bytes + size > 32 * 1024 * 1024) {
          const key = cache.keys().next().value;
          bytes -= cache.get(key).size;
          cache.delete(key);
        }
        const hash = active.hash;
        cache.set(hash, { bundle, size });
        bytes += size;
        active = null;
        onAsset(bundle);
        setTimeout(start, 600).unref?.();
      }
    } catch (error) {
      fail(error.message?.startsWith("YSM_") ? error.message : "YSM_TRANSFER_INVALID");
    }
  };
  const timer = setInterval(() => {
    if (active && Date.now() - active.started > 2e4) fail("YSM_TRANSFER_TIMEOUT");
    else start();
  }, 1e3);
  timer.unref?.();
  bot._client.on("custom_payload", payload2);
  return { get: (hash) => cache.get(hash)?.bundle, request(row) {
    if (disposed || row.webAvailable !== true || cache.has(row.assetSha256) || active?.hash === row.assetSha256 || (attempts.get(row.assetSha256) ?? 0) >= 3 || queue.size >= 40) return;
    queue.set(row.assetSha256, row);
    start();
  }, reset() {
    active = null;
    queue.clear();
    attempts.clear();
  }, dispose() {
    disposed = true;
    clearInterval(timer);
    bot._client.off("custom_payload", payload2);
    cache.clear();
    queue.clear();
    active = null;
  } };
}

// integrations/qiandengji/engine/viewer-ysm-motion.mjs
var angle = (value) => Math.atan2(Math.sin(value), Math.cos(value));
var compactItem = (item) => {
  if (item === null) return null;
  if (!item || !/^(?:[a-z0-9_.-]+:)?[a-z0-9_./-]{1,128}$/.test(item.name ?? "")) return null;
  const result = { name: item.name, count: Math.min(99, Math.max(1, item.count ?? 1)) };
  for (const key of ["type", "metadata", "enchants", "components", "nbt"]) {
    if (item[key] === void 0) continue;
    try {
      const value = JSON.stringify(item[key], (_k, v) => typeof v === "bigint" ? v.toString() : v);
      if (value.length <= 8192) result[key] = JSON.parse(value);
      else result.visualDataUnavailable = true;
    } catch {
      result.visualDataUnavailable = true;
    }
  }
  return result;
};
function createViewerYsmMotion(bot, { binding, emit, now = Date.now } = {}) {
  const states = /* @__PURE__ */ new Map(), ground = /* @__PURE__ */ new Map(), sleep = /* @__PURE__ */ new WeakMap();
  let sequence = 0;
  const listeners = [];
  const on = (target, name, fn) => {
    target.on(name, fn);
    listeners.push(() => target.off(name, fn));
  };
  function actual(row) {
    const own = (bot._client.uuid ?? bot.player?.uuid)?.toLowerCase() === row.playerUuid;
    const entity = own ? bot.entity : bot.entities?.[row.entityId];
    return entity && entity.id === row.entityId && (own || entity.uuid?.toLowerCase() === row.playerUuid) ? entity : null;
  }
  function sample(row) {
    if (!row?.available) return null;
    const entity = actual(row);
    if (!entity) return null;
    const position = entity.position;
    if (!position || ![position.x, position.y, position.z].every(Number.isFinite)) return null;
    let prior = states.get(row.playerUuid);
    const time = now();
    if (!prior || prior.entityId !== entity.id || prior.epoch !== row.epoch) {
      prior = { entityId: entity.id, epoch: row.epoch, position: { ...position }, at: time, movedAt: time, speed: 0, sentAt: 0 };
      states.set(row.playerUuid, prior);
    }
    const distance = Math.hypot(position.x - prior.position.x, position.z - prior.position.z), elapsed = (time - prior.at) / 1e3;
    if (distance > 0 && elapsed > 0) {
      prior.speed = distance < 4 && elapsed < 2 ? Math.min(30, distance / elapsed) : 0;
      prior.movedAt = time;
    } else if (time - prior.movedAt > 250) prior.speed = 0;
    prior.position = { x: position.x, y: position.y, z: position.z };
    prior.at = time;
    const metadata = entity.metadata ?? [], flags = Number(metadata[0]) || 0, living = Number(metadata[8]) || 0;
    const yaw = entity.yaw ?? 0, headYaw = entity.headYaw ?? yaw, pitch = entity.pitch ?? 0;
    const mainArm = metadata[18] === 0 ? "left" : "right";
    const equipment = entity === bot.entity ? [bot.heldItem ?? entity.equipment?.[0] ?? null, bot.inventory?.slots?.[45] ?? entity.equipment?.[1] ?? null] : entity.equipment?.slice(0, 2);
    const result = {
      schemaVersion: 1,
      source: "same_connection_java_protocol",
      epoch: row.epoch,
      playerUuid: row.playerUuid,
      entityId: entity.id,
      sequence: ++sequence,
      horizontalSpeed: prior.speed,
      bodyYaw: yaw,
      headYawDegrees: angle(headYaw - yaw) * 180 / Math.PI,
      headPitchDegrees: -pitch * 180 / Math.PI,
      crouching: !!(flags & 2),
      sprinting: !!(flags & 8),
      usingItem: !!(living & 1),
      activeHand: living & 2 ? "offhand" : "mainhand",
      mainArm,
      pose: typeof metadata[6] === "number" ? ["standing", "fall_flying", "sleeping", "swimming", "spin_attack", "crouching", "long_jumping", "dying"][metadata[6]] : metadata[6],
      equipment: Array.isArray(equipment) ? equipment.map(compactItem) : null
    };
    const knownGround = entity === bot.entity ? entity.onGround : ground.get(entity.id);
    const sleeping = entity === bot.entity && typeof bot.isSleeping === "boolean" ? bot.isSleeping : sleep.get(entity);
    if (typeof sleeping === "boolean") result.pose = sleeping ? "sleeping" : result.pose === "sleeping" ? "standing" : result.pose;
    if (typeof knownGround === "boolean") result.onGround = knownGround;
    const flying = entity === bot.entity ? bot.game?.gameMode === "creative" && bot.entity?.isFlying : void 0;
    if (typeof flying === "boolean") result.flying = flying;
    if (prior.swing && time - prior.swing.at < 2500) result.swing = { hand: prior.swing.hand, sequence: prior.swing.sequence, ageSeconds: (time - prior.swing.at) / 1e3 };
    if (prior.hurt && time - prior.hurt.at < 700) result.hurt = { sequence: prior.hurt.sequence, ageSeconds: (time - prior.hurt.at) / 1e3 };
    return result;
  }
  function send(row, force = false) {
    const prior = states.get(row?.playerUuid);
    if (!force && prior && now() - prior.sentAt < 100) return;
    const value = sample(row);
    if (!value) return;
    const current = states.get(row.playerUuid), signature = JSON.stringify({ ...value, sequence: 0, swing: value.swing ? { ...value.swing, ageSeconds: 0 } : null, hurt: value.hurt ? { ...value.hurt, ageSeconds: 0 } : null });
    if (!force && current.signature === signature && now() - current.sentAt < 1e3) return;
    current.signature = signature;
    current.sentAt = now();
    emit("appearanceMotion", value);
  }
  const update = (entity) => {
    const row = binding(entity?.id);
    if (row) send(row);
  };
  for (const event of ["entityMoved", "entityEquip", "entityUpdate", "entitySpawn"]) on(bot, event, update);
  on(bot, "move", () => update(bot.entity));
  on(bot, "heldItemChanged", () => update(bot.entity));
  for (const [event, value] of [["entitySleep", true], ["entityWake", false]]) on(bot, event, (entity) => {
    sleep.set(entity, value);
    const row = binding(entity?.id);
    if (row) send(row, true);
  });
  for (const event of ["sleep", "wake"]) on(bot, event, () => {
    const row = binding(bot.entity?.id);
    if (row) send(row, true);
  });
  on(bot._client, "packet", (packet, meta) => {
    if (["rel_entity_move", "entity_move_look", "entity_teleport", "entity_position_sync"].includes(meta?.name) && typeof packet.onGround === "boolean") {
      if (ground.size < 128 || ground.has(packet.entityId)) ground.set(packet.entityId, packet.onGround);
    }
  });
  on(bot._client, "animation", (packet) => {
    if (![0, 3].includes(packet.animation)) return;
    const row = binding(packet.entityId);
    if (!row || !sample(row)) return;
    states.get(row.playerUuid).swing = { at: now(), hand: packet.animation === 3 ? "offhand" : "mainhand", sequence: ++sequence };
    send(row, true);
  });
  let serializer = null, outgoing = null;
  const attachOutgoing = () => {
    if (serializer && outgoing) serializer.off("data", outgoing);
    serializer = bot._client.serializer;
    outgoing = null;
    if (!serializer?.createPacketBuffer || !serializer.proto?.parsePacketBuffer) return;
    try {
      const armBytes = serializer.createPacketBuffer({ name: "arm_animation", params: { hand: 0 } });
      if (!Buffer.isBuffer(armBytes) || armBytes.length < 2 || armBytes.length > 8) return;
      const probe = serializer.proto.parsePacketBuffer(serializer.mainType, armBytes).data;
      if (probe.name !== "arm_animation" || probe.params?.hand !== 0) return;
      const prefix = armBytes.subarray(0, armBytes.length - 1);
      outgoing = (bytes) => {
        if (bot._client.state !== "play" || bytes.length !== armBytes.length || !bytes.subarray(0, prefix.length).equals(prefix)) return;
        try {
          const decoded = serializer.proto.parsePacketBuffer(serializer.mainType, bytes).data;
          if (decoded.name !== "arm_animation" || ![0, 1].includes(decoded.params.hand)) return;
          const row = binding(bot.entity?.id);
          if (!row || !sample(row)) return;
          states.get(row.playerUuid).swing = { at: now(), hand: decoded.params.hand ? "offhand" : "mainhand", sequence: ++sequence };
          send(row, true);
        } catch {
        }
      };
      serializer.on("data", outgoing);
    } catch {
    }
  };
  on(bot._client, "state", attachOutgoing);
  attachOutgoing();
  on(bot, "entityHurt", (entity) => {
    const row = binding(entity?.id);
    if (!row || !sample(row)) return;
    states.get(row.playerUuid).hurt = { at: now(), sequence: ++sequence };
    send(row, true);
  });
  on(bot, "entityGone", (entity) => {
    ground.delete(entity?.id);
    for (const [uuid3, row] of states) if (row.entityId === entity?.id) states.delete(uuid3);
  });
  const timer = setInterval(() => {
    for (const [uuid3, prior] of states) {
      const row = binding(prior.entityId);
      if (!row || row.playerUuid !== uuid3 || row.epoch !== prior.epoch) states.delete(uuid3);
      else send(row);
    }
  }, 100);
  timer.unref?.();
  return {
    send: (row) => send(row, true),
    snapshot: (rows) => rows.map(sample).filter(Boolean),
    reset() {
      states.clear();
      ground.clear();
    },
    dispose() {
      clearInterval(timer);
      if (serializer && outgoing) serializer.off("data", outgoing);
      for (const off of listeners) off();
      states.clear();
      ground.clear();
    }
  };
}

// integrations/qiandengji/engine/viewer-appearance.mjs
var UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
var APPEARANCE_CHANNEL = "mcagent:appearance";
var PAPER_YSM_JAR_SHA256 = "ec51cfae84d219a45fac5098a31bfe980bcb7c2d8b413e8fffbd05a411a85680";
function parseAppearancePacket(packet) {
  if (packet?.channel !== APPEARANCE_CHANNEL || !(packet.data instanceof Uint8Array) || packet.data.length > 2048) return null;
  let value;
  try {
    value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(packet.data));
  } catch {
    return null;
  }
  if (!value || value.schemaVersion !== 1 || value.source !== "freesia_worker" || !UUID.test(value.epoch ?? "") || !UUID.test(value.playerUuid ?? "")) return null;
  const base = { schemaVersion: 1, source: value.source, epoch: value.epoch, playerUuid: value.playerUuid.toLowerCase(), type: value.type };
  if (value.type === "remove") return base;
  if (value.type !== "state" || typeof value.available !== "boolean" || value.ysmVersion !== "2.4.1" || value.protocolVersion !== "2.4.0" || value.jarSha256 !== PAPER_YSM_JAR_SHA256) return null;
  Object.assign(base, { available: value.available, ysmVersion: value.ysmVersion, protocolVersion: value.protocolVersion, jarSha256: value.jarSha256 });
  if (typeof value.workerConnected === "boolean") base.workerConnected = value.workerConnected;
  if (["confirmed", "unsupported", "awaiting_model_state", "worker_offline", "awaiting_initial_poll"].includes(value.stateStatus)) base.stateStatus = value.stateStatus;
  if (typeof value.message === "string" && value.message.length <= 160 && !/[\u0000-\u001f\u007f]/.test(value.message)) base.message = value.message;
  if (!value.available) return { ...base, reason: value.reason === "YSM_WORKER_STATE_UNSUPPORTED" ? "YSM_WORKER_STATE_UNSUPPORTED" : "YSM_WORKER_STATE_UNAVAILABLE" };
  if (!Number.isSafeInteger(value.entityId) || value.entityId < 0 || value.entityId > 2147483647 || typeof value.mandatory !== "boolean" || !/^[\p{L}\p{N}_./-]{1,96}$/u.test(value.modelId ?? "") || value.modelId.includes("..") || value.modelId.startsWith("/") || !/^[\p{L}\p{N}_.-]{1,96}$/u.test(value.texture ?? "") || typeof value.animation !== "string" || value.animation.length > 96) return null;
  const web = value.webAvailable === true && /^[a-f0-9]{64}$/.test(value.assetSha256 ?? "") && Number.isInteger(value.assetBytes) && value.assetBytes > 0 && value.assetBytes <= 2 * 1024 * 1024;
  return {
    ...base,
    entityId: value.entityId,
    modelId: value.modelId,
    texture: value.texture,
    mandatory: value.mandatory,
    animation: value.animation,
    webAvailable: web,
    ...web ? { assetSha256: value.assetSha256, assetBytes: value.assetBytes } : { webReason: typeof value.webReason === "string" ? value.webReason.slice(0, 96) : "YSM_SOURCE_NOT_REGISTERED" }
  };
}
function createViewerAppearanceBridge(bot, { now = Date.now } = {}) {
  const records = /* @__PURE__ */ new Map(), listeners = /* @__PURE__ */ new Set();
  let epoch = null, disposed = false;
  const errors = /* @__PURE__ */ new Map();
  const assets = createYsmAssetReceiver(bot, { onAsset: (bundle) => {
    emit("appearanceAsset", bundle);
    for (const row of records.values()) if (row.assetSha256 === bundle.assetSha256) {
      const bound = binding(row);
      if (bound) emit("appearanceState", bound);
    }
  }, onError: (row, reason) => {
    errors.set(row.assetSha256, reason);
    const bound = binding(row);
    if (bound) emit("appearanceState", bound);
  } });
  const emit = (name, row) => {
    for (const fn of listeners) try {
      fn(name, row);
    } catch {
      listeners.delete(fn);
    }
  };
  const motion = createViewerYsmMotion(bot, { now, emit, binding: (id2) => {
    for (const row of records.values()) if (row.entityId === id2 && now() - row.receivedAt <= 15e3) return binding(row);
    return null;
  } });
  const reset = () => {
    records.clear();
    errors.clear();
    assets.reset();
    motion.reset();
    epoch = null;
    emit("appearanceReset", { schemaVersion: 1 });
  };
  function binding(row) {
    const ownUuid = bot._client.uuid ?? bot.player?.uuid;
    const own = ownUuid?.toLowerCase() === row.playerUuid;
    const entity = own ? bot.entity : bot.entities?.[row.entityId];
    const actualUuid = own ? ownUuid : entity?.uuid;
    if (!entity || typeof actualUuid !== "string" || actualUuid.toLowerCase() !== row.playerUuid || row.available && entity.id !== row.entityId) return null;
    const { receivedAt, ...publicRow } = row;
    const asset = assets.get(row.assetSha256), renderAvailable = row.available === true && asset?.modelId === row.modelId && Object.hasOwn(asset.textures, row.texture);
    return { ...publicRow, entityId: entity.id, renderAvailable, renderReason: renderAvailable ? null : errors.get(row.assetSha256) ?? row.webReason ?? row.reason ?? "YSM_ASSET_PENDING", completeEntityParityVerified: false };
  }
  function payload2(packet) {
    const row = parseAppearancePacket(packet);
    if (!row) return;
    if (epoch !== row.epoch) {
      reset();
      epoch = row.epoch;
    }
    if (row.type === "remove") {
      records.delete(row.playerUuid);
      emit("appearanceRemove", { schemaVersion: 1, playerUuid: row.playerUuid });
      return;
    }
    if (records.size >= 40 && !records.has(row.playerUuid)) return;
    if (!row.available) row.entityId = records.get(row.playerUuid)?.entityId;
    records.set(row.playerUuid, { ...row, receivedAt: now() });
    const bound = binding(row);
    if (bound) {
      const bundle = assets.get(row.assetSha256);
      if (bundle) emit("appearanceAsset", bundle);
      emit("appearanceState", bound);
      motion.send(bound);
      if (listeners.size) assets.request(row);
    }
  }
  const tracked = (entity) => {
    const uuid3 = entity?.uuid?.toLowerCase();
    const row = uuid3 && records.get(uuid3);
    const bound = row && binding(row);
    if (bound) emit("appearanceState", bound);
  };
  const gone = (entity) => {
    if (entity?.uuid) emit("appearanceRemove", { schemaVersion: 1, playerUuid: entity.uuid.toLowerCase() });
  };
  bot._client.on("custom_payload", payload2);
  bot.on("entitySpawn", tracked);
  bot.on("entityGone", gone);
  bot.on("login", reset);
  bot.on("respawn", reset);
  bot.on("end", reset);
  const expire = () => {
    for (const [uuid3, row] of records) if (now() - row.receivedAt > 15e3) {
      records.delete(uuid3);
      emit("appearanceRemove", { schemaVersion: 1, playerUuid: uuid3 });
    }
  };
  const timer = setInterval(expire, 1e3);
  timer.unref?.();
  const snapshot = () => {
    expire();
    return Array.from(records.values()).map(binding).filter(Boolean);
  };
  return { snapshot, subscribeSocket(socket) {
    if (disposed) throw Error("viewer_appearance_disposed");
    const fn = (name, row) => socket.emit(name, row);
    listeners.add(fn);
    socket.emit("appearanceReset", { schemaVersion: 1 });
    for (const row of snapshot()) {
      const bundle = assets.get(row.assetSha256);
      if (bundle) socket.emit("appearanceAsset", bundle);
      socket.emit("appearanceState", row);
      motion.send(row);
      assets.request(row);
    }
    return () => listeners.delete(fn);
  }, dispose() {
    if (disposed) return;
    disposed = true;
    assets.dispose();
    motion.dispose();
    clearInterval(timer);
    bot._client.off("custom_payload", payload2);
    bot.off("entitySpawn", tracked);
    bot.off("entityGone", gone);
    bot.off("login", reset);
    bot.off("respawn", reset);
    bot.off("end", reset);
    records.clear();
    listeners.clear();
  } };
}

// integrations/qiandengji/engine/viewer-observer.mjs
var CHANNELS = /* @__PURE__ */ new Set(["mcviewer:state", "corti:viewer_state"]);
var UUID2 = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function createViewerObserverBridge(bot, { now = Date.now, staleMs = 12e3, serializeWindow } = {}) {
  const subscribers = /* @__PURE__ */ new Set();
  let nativeWindow = null;
  const windowChanged = () => {
    if (nativeWindow && current?.viewerSession?.attached && current.viewerSession.windowOpen && serializeWindow)
      emit("containerState", serializeWindow(nativeWindow));
  };
  function openWindow(window) {
    nativeWindow?.off?.("updateSlot", windowChanged);
    nativeWindow = window;
    nativeWindow?.on?.("updateSlot", windowChanged);
    windowChanged();
  }
  let current = null, pending = null, cameraId = null, at = 0, closed = false;
  const key = (state) => state?.viewerSession?.attached ? [
    state.viewerSession.playerUuid,
    state.viewerSession.entityId,
    state.viewerSession.worldUuid
  ].join(":") : "";
  const emit = (event, value) => {
    for (const socket of subscribers) socket.emit(event, value);
  };
  function reset(reason) {
    openWindow(null);
    current = null;
    pending = null;
    at = 0;
    emit("viewerSession", { mode: "observer", attached: false, reason });
    emit("containerState", null);
    emit("skillsState", { schemaVersion: 1, mana: null, skills: [], abilities: [] });
    emit("observerState", { attached: false, reason });
  }
  function accept(state) {
    const session = state.viewerSession;
    if (session.mode === "observer" && session.attached && session.entityId !== cameraId) {
      pending = state;
      return;
    }
    if (key(current) !== key(state)) emit("containerState", null);
    current = state;
    pending = null;
    at = now();
    emit("viewerSession", session);
    if (!session.attached || !session.windowOpen) emit("containerState", null);
    emit("skillsState", state);
    emit("observerState", { ...session, vitals: state.vitals ?? null });
    windowChanged();
  }
  function payload2(packet) {
    if (!CHANNELS.has(packet.channel) || !Buffer.isBuffer(packet.data) || packet.data.length > 16384) return;
    let state;
    try {
      state = JSON.parse(packet.data.toString("utf8"));
    } catch {
      return;
    }
    const session = state?.viewerSession;
    if (state?.schemaVersion !== 1 || !session || !UUID2.test(session.recipientUuid ?? "") || session.recipientUuid.toLowerCase() !== String(bot._client?.uuid ?? bot.player?.uuid ?? bot.entity?.uuid ?? bot.uuid).toLowerCase() || !["self", "observer"].includes(session.mode) || typeof session.attached !== "boolean") return;
    if (session.attached && (!UUID2.test(session.playerUuid ?? "") || !UUID2.test(session.worldUuid ?? "") || !Number.isSafeInteger(session.entityId) || !/^[A-Za-z0-9_.]{1,32}$/.test(session.playerName ?? "") || typeof session.windowOpen !== "boolean")) return;
    accept(state);
  }
  function camera(packet) {
    const previous = cameraId, candidate = pending;
    cameraId = packet.cameraId;
    if (current?.viewerSession?.mode === "observer" && current.viewerSession.entityId !== cameraId) reset("camera_changed");
    if (previous !== cameraId && candidate?.viewerSession?.entityId === cameraId) accept(candidate);
  }
  const respawn = () => {
    cameraId = null;
    reset("respawn");
  };
  const closeWindow = () => {
    openWindow(null);
    emit("containerState", null);
  };
  const outgoing = (name) => {
    if (name === "close_window") closeWindow();
  };
  const register = () => {
    if (bot._client?.state === "play") bot._client.write("custom_payload", {
      channel: "minecraft:register",
      data: Buffer.from("mcviewer:state")
    });
  };
  bot._client.on("custom_payload", payload2);
  bot._client.on("camera", camera);
  bot._client.on("respawn", respawn);
  bot._client.on("close_window", closeWindow);
  bot._client.on("writePacket", outgoing);
  bot.on("windowClose", closeWindow);
  bot.on("spawn", register);
  if (serializeWindow) bot.on("windowOpen", openWindow);
  const onEnd = () => reset("disconnected");
  bot.on("end", onEnd);
  register();
  const timer = setInterval(() => {
    if (current && now() - at > staleMs) reset("state_stale");
  }, 1e3);
  timer.unref?.();
  return {
    subscribeSocket(socket) {
      if (closed) throw Error("observer_bridge_closed");
      subscribers.add(socket);
      if (current) {
        socket.emit("viewerSession", current.viewerSession);
        socket.emit("skillsState", current);
        socket.emit("observerState", { ...current.viewerSession, vitals: current.vitals ?? null });
        if (nativeWindow && current.viewerSession.attached && current.viewerSession.windowOpen && serializeWindow)
          socket.emit("containerState", serializeWindow(nativeWindow));
      }
      const off = () => {
        subscribers.delete(socket);
        socket.off?.("disconnect", off);
      };
      socket.on("disconnect", off);
      return off;
    },
    snapshot: () => current,
    dispose() {
      if (closed) return;
      closed = true;
      clearInterval(timer);
      reset("disposed");
      subscribers.clear();
      bot._client.off("custom_payload", payload2);
      bot._client.off("camera", camera);
      bot._client.off("respawn", respawn);
      bot._client.off("close_window", closeWindow);
      bot._client.off("writePacket", outgoing);
      bot.off("windowClose", closeWindow);
      bot.off("spawn", register);
      bot.off("end", onEnd);
      bot.off("windowOpen", openWindow);
    }
  };
}

// integrations/qiandengji/engine/viewer-cast.ts
import { publishViewerCastCommand, observeViewerCastCommands } from "agent-mc-world/extension";
var SPELL_NAMES = {
  home: "\u5F52\u4E61",
  blink: "\u95EA\u73B0",
  selfheal: "\u5723\u6108\u672F",
  heal: "\u6CBB\u7597\u961F\u53CB",
  food: "\u9971\u98DF",
  give: "\u9020\u7269\u672F",
  fireworks: "\u70DF\u82B1\u672F",
  starlight: "\u661F\u5C18\u672F",
  starbolt: "\u661F\u8292\u7BAD",
  frostnova: "\u971C\u73AF",
  flamewave: "\u7130\u6D6A",
  golem: "\u5B88\u62A4\u5080\u5121",
  prospect: "\u63A2\u77FF\u672F",
  sense: "\u63A2\u654C",
  leap: "\u8DC3\u7A7A",
  flight: "\u98DE\u884C",
  blood_mana: "\u71C3\u8840\u672F",
  feather: "\u7FBD\u843D\u4E4B\u9774",
  night: "\u591C\u89C6"
};
function starboltTargetRefusal(text2) {
  const match = /^(?:\[RPG\]\s*)?(\d+(?:\.\d+)?)\s*格准星和\s*(\d+(?:\.\d+)?)\s*格自动锁定都没找到怪物[；;]\s*未消耗魔力[。.!！]?$/u.exec(text2.trim());
  if (!match) return null;
  const aimed = Number(match[1]), automatic = Number(match[2]);
  return aimed > 0 && automatic > 0 && Number.isFinite(aimed) && Number.isFinite(automatic) ? { aimed, automatic } : null;
}
function viewerCastCommand(text2) {
  if (typeof text2 !== "string") return null;
  const match = /^\s*\/mycli\s+cast\s+([a-z0-9_:-]{1,64})(?=\s|$)/i.exec(text2);
  if (!match) return null;
  const id2 = match[1].toLowerCase();
  return { id: id2, name: SPELL_NAMES[id2] ?? id2.replaceAll("_", " ") };
}
function viewerCastResult(text2, spellId) {
  if (typeof text2 !== "string" || text2.length > 1024) return null;
  if (spellId === "starbolt" && starboltTargetRefusal(text2)) return { phase: "failed", detail: "\u672A\u9501\u5B9A\u76EE\u6807\uFF0C\u672A\u6D88\u8017\u9B54\u529B" };
  const locked = /\bSpell\s+([a-z0-9_:-]+)\s+is not unlocked\b/i.exec(text2);
  if (locked) return locked[1].toLowerCase() === spellId.toLowerCase() ? { phase: "failed", detail: "\u6280\u80FD\u672A\u89E3\u9501" } : null;
  if (/\[RPG\].*(?:参数过多|缺少参数|参数无效|用法错误)/u.test(text2)) {
    return { phase: "failed", detail: "\u65BD\u6CD5\u53C2\u6570\u88AB\u62D2\u7EDD" };
  }
  if (/(?:not|don't have) enough (?:mana|magic)|insufficient (?:mana|magic)|(?:on |in )?cooldown|you cannot (?:blink|cast|use)|cannot cast|failed to cast|\bno permission\b|魔力不足|灵力不足|冷却中|无法施放|施法失败|未学会|不能在此施法|不可在此施法|没有看得见的怪物|没有可用目标/i.test(text2)) {
    return { phase: "failed", detail: "\u65BD\u6CD5\u53D7\u963B" };
  }
  if (spellId === "home" && /传送到|teleported to|you have been teleported/i.test(text2)) {
    return { phase: "succeeded", detail: "\u4F20\u9001\u5B8C\u6210" };
  }
  if ((spellId === "selfheal" || spellId === "heal") && /sacred healing restores|治疗成功|恢复了生命/i.test(text2)) {
    return { phase: "succeeded", detail: "\u6CBB\u7597\u751F\u6548" };
  }
  if (spellId === "food" && /feel less hungry|饥饿值已恢复|饱食生效/i.test(text2)) {
    return { phase: "succeeded", detail: "\u9971\u98DF\u751F\u6548" };
  }
  const successBySpell = {
    golem: /守护傀儡.*(?:帮你|召唤|出现)/u,
    frostnova: /霜环.*(?:命中|冻结|冻住)/u,
    flamewave: /焰浪.*(?:命中|灼烧)/u,
    starbolt: /星芒箭.*命中/u,
    prospect: /探矿术.*(?:发现|找到|探查完成)/u,
    sense: /探敌.*(?:发现|探查|感知)/u,
    leap: /跃空.*(?:生效|腾空|跳跃)/u,
    flight: /飞行.*(?:生效|起飞|持续)/u
  };
  if (successBySpell[spellId]?.test(text2)) return { phase: "succeeded", detail: "\u65BD\u6CD5\u751F\u6548" };
  if (/咏唱成功|施法成功|成功施放|successfully cast/i.test(text2)) {
    return { phase: "succeeded", detail: "\u65BD\u6CD5\u751F\u6548" };
  }
  return null;
}

// integrations/qiandengji/engine/viewer-state.ts
var finite = (value) => typeof value === "number" && Number.isFinite(value);
var bounded = (value, min, max) => finite(value) ? Math.max(min, Math.min(max, value)) : null;
var VIEWER_STATE_CHANNEL = "mcagent:state";
function manaSnapshotFromText(text2) {
  if (typeof text2 !== "string" || text2.length > 512) return null;
  const label = /(?:魔力|法力|\b(?:mana|mp)\b)/iu.exec(text2);
  if (!label) return null;
  const part = text2.slice(label.index + label[0].length, label.index + label[0].length + 60);
  const pair = /(?:当前|current)?[^\d\n]{0,24}(\d{1,6})\s*\/\s*(\d{1,6})/iu.exec(part);
  if (!pair) return null;
  const current = Number(pair[1]);
  const max = Number(pair[2]);
  return max > 0 && current <= max ? { current, max } : null;
}
function spellCatalogueFromText(text2) {
  if (typeof text2 !== "string" || text2.length > 16384 || !/(?:战斗咏唱|探索咏唱)[：:]/u.test(text2)) return null;
  const abilities = [];
  for (const match of text2.matchAll(/([^、，；：:()（）\s]{1,32})[（(]([a-z][a-z0-9_:-]{0,63})[，,]([^）)]{0,160})[）)]/giu)) {
    const id2 = match[2].toLowerCase();
    const cost = /(\d{1,4})\s*魔力/u.exec(match[3]);
    const cooldown = /(?:\/|冷却\s*)(\d{1,5})\s*秒/u.exec(match[3]);
    abilities.push({
      id: id2,
      name: match[1],
      level: null,
      cooldownMs: cooldown ? Number(cooldown[1]) * 1e3 : null,
      manaCost: cost ? Number(cost[1]) : null
    });
  }
  return abilities.length ? abilities : null;
}
function parseSkillsPayload(channel, data) {
  if (channel !== VIEWER_STATE_CHANNEL && channel !== "mcviewer:state" && channel !== "corti:viewer_state" || !Buffer.isBuffer(data) || data.length > 65536) return null;
  let raw;
  try {
    raw = JSON.parse(data.toString("utf8"));
  } catch {
    return null;
  }
  if (!raw || typeof raw !== "object") return null;
  const input = raw;
  if (channel === VIEWER_STATE_CHANNEL) {
    if (input.schemaVersion !== 1 || !Object.hasOwn(input, "mana")) return null;
    if (input.mana !== null) {
      if (!input.mana || typeof input.mana !== "object" || Array.isArray(input.mana)) return null;
      const mana3 = input.mana;
      const current2 = bounded(mana3.current, 0, 1e6);
      const max2 = bounded(mana3.max, 0, 1e6);
      if (current2 === null || max2 === null || max2 <= 0 || current2 > max2) return null;
    }
  }
  if (input.schemaVersion !== 1 || !("mana" in input || "skills" in input || "abilities" in input) || input.skills !== void 0 && !Array.isArray(input.skills) || input.abilities !== void 0 && !Array.isArray(input.abilities)) return null;
  const mana2 = input.mana;
  const current = bounded(mana2?.current, 0, 1e6);
  const max = bounded(mana2?.max, 0, 1e6);
  const readName = (value, maxLength) => typeof value === "string" && value.length <= maxLength ? value : null;
  const skillsInput = Array.isArray(input.skills) ? input.skills : [];
  const skills = skillsInput.map((value) => {
    if (!value || typeof value !== "object") return null;
    const row = value;
    const id2 = readName(row.id, 64);
    const name = readName(row.name, 80);
    const level = bounded(row.level, 0, 1e5);
    if (!id2 || !/^[a-z0-9_:.-]+$/.test(id2) || !name || level === null) return null;
    return {
      id: id2,
      name,
      level,
      xp: bounded(row.xp, 0, 1e9),
      requiredXp: bounded(row.requiredXp, 0, 1e9)
    };
  });
  if (skills.some((entry) => !entry)) return null;
  const topAbilities = Array.isArray(input.abilities) ? input.abilities : [];
  const profession = input.profession;
  const native = channel === VIEWER_STATE_CHANNEL ? readNativeRpgPacket(channel, data) : null;
  const professionAbilities = native?.available && Array.isArray(profession?.abilities) && profession.abilities.length <= 48 ? profession.abilities : [];
  const abilitiesInput = [...topAbilities, ...professionAbilities];
  const abilities = abilitiesInput.map((value) => {
    if (!value || typeof value !== "object") return null;
    const row = value;
    const id2 = readName(row.id, 64);
    const name = readName(row.name, 80);
    if (!id2 || !/^[a-z0-9_:.-]+$/.test(id2) || !name) return null;
    const icon = readName(row.icon, 64);
    const cooldownMs = bounded(row.cooldownMs, 0, 864e5);
    return {
      id: id2,
      name,
      level: bounded(row.level, 0, 1e5),
      cooldownMs: channel === "mcviewer:state" ? null : cooldownMs,
      ...channel === "mcviewer:state" ? { cooldownRemainingMs: cooldownMs } : row.cooldownRemainingMs !== void 0 ? { cooldownRemainingMs: bounded(row.cooldownRemainingMs, 0, 864e5) } : {},
      manaCost: bounded(row.manaCost, 0, 1e6),
      ...icon && /^(?:minecraft:)?[a-z0-9_]+$/.test(icon) ? { icon: icon.replace(/^minecraft:/, "") } : {}
    };
  });
  if (abilities.some((entry) => !entry)) return null;
  return {
    schemaVersion: 1,
    mana: current !== null && max !== null && max > 0 && current <= max ? { current, max } : null,
    skills,
    abilities: [...new Map(abilities.map((a) => [a.id, a])).values()]
  };
}
function matchingAbility(abilities, id2) {
  const exact = abilities.find((entry) => entry.id === id2);
  if (exact) return exact;
  const suffix = id2.split(":").at(-1);
  const matches = abilities.filter((entry) => entry.id.split(":").at(-1) === suffix);
  return matches.length === 1 ? matches[0] : void 0;
}
function mergeViewerSkillState(previous, next, channel, agentStateSeen) {
  const authoritative = channel === VIEWER_STATE_CHANNEL;
  const oldAbilities = previous?.abilities ?? [];
  const abilities = authoritative ? next.abilities.map((ability) => ({
    ...ability,
    manaCost: ability.manaCost ?? matchingAbility(oldAbilities, ability.id)?.manaCost ?? null
  })) : agentStateSeen ? oldAbilities : next.abilities.length ? next.abilities : oldAbilities;
  return {
    ...next,
    mana: authoritative || !agentStateSeen ? next.mana : previous?.mana ?? null,
    skills: next.skills.length ? next.skills : previous?.skills ?? [],
    abilities,
    source: "plugin",
    observedAt: Date.now()
  };
}
function mergeViewerSpellCatalogue(previous, catalogue, agentStateSeen) {
  const oldAbilities = previous?.abilities ?? [];
  const abilities = agentStateSeen ? oldAbilities.map((ability) => ({
    ...ability,
    manaCost: ability.manaCost ?? matchingAbility(catalogue, ability.id)?.manaCost ?? null
  })) : (() => {
    const merged = new Map(oldAbilities.map((ability) => [ability.id, ability]));
    for (const entry of catalogue) {
      const old = matchingAbility(oldAbilities, entry.id);
      merged.set(old?.id ?? entry.id, old ? {
        ...entry,
        ...old,
        cooldownMs: old.cooldownMs ?? entry.cooldownMs,
        manaCost: old.manaCost ?? entry.manaCost
      } : entry);
    }
    return [...merged.values()];
  })();
  return {
    ...previous ?? { schemaVersion: 1, mana: null, skills: [] },
    abilities,
    observedAt: Date.now()
  };
}
var VIEWER_EVENT_CHANNEL = "mcagent:event";
function parseViewerCustomEvent(channel, data) {
  if (channel !== VIEWER_EVENT_CHANNEL && channel !== "mcviewer:event" || !Buffer.isBuffer(data) || data.length > 16384) return null;
  let raw;
  try {
    raw = JSON.parse(data.toString("utf8"));
  } catch {
    return null;
  }
  if (!raw || typeof raw !== "object") return null;
  const row = raw;
  const kinds = /* @__PURE__ */ new Set(["skill", "quest", "notice", "combat", "environment", "achievement"]);
  const tones = /* @__PURE__ */ new Set(["positive", "neutral", "warning", "danger", "arcane", "healing", "frost", "fire", "movement"]);
  if (row.schemaVersion !== 1 || !kinds.has(String(row.kind)) || typeof row.id !== "string" || !/^[a-z0-9_:.-]{1,80}$/.test(row.id) || typeof row.title !== "string" || row.title.length < 1 || row.title.length > 80 || typeof row.body !== "string" || row.body.length > 240) return null;
  const sourcePosition = row.position;
  const position = sourcePosition && point(sourcePosition.x, sourcePosition.y, sourcePosition.z);
  if (sourcePosition && !position) return null;
  return {
    kind: row.kind,
    id: row.id,
    title: row.title,
    body: row.body,
    tone: tones.has(String(row.tone)) ? row.tone : "arcane",
    ...position ? { position } : {}
  };
}
var serverViewerProtocol = { createAppearance: createViewerAppearanceBridge, createObserver: createViewerObserverBridge, castCommand: viewerCastCommand, castResult: viewerCastResult, stateChannel: VIEWER_STATE_CHANNEL, parseSkillsPayload, manaSnapshotFromText, spellCatalogueFromText, mergeViewerSkillState, mergeViewerSpellCatalogue, parseViewerCustomEvent };
var point = (x, y, z) => finite(x) && finite(y) && finite(z) ? { x, y, z } : null;

// integrations/qiandengji/engine/bridge.ts
import { Bridge } from "agent-mc-world/extension";

// integrations/qiandengji/engine/agentfriend-protection.ts
import { Vec3 as Vec32 } from "vec3";
var CHANNEL = "mcagent:protection";
var PREFIX = "MC_PROTECT";
var TIMEOUT_MS = 4e3;
var QUERY_GAP_MS = 1500;
var RATE_LIMIT_BACKOFF_MS = 5e3;
var DENY_TTL_MS = 3e5;
var UNKNOWN_TTL_MS = 4e3;
var ALLOW_TTL_MS = 15e3;
var normDimension = (s) => s.replace(/^minecraft:/, "");
var keyOf = (action, dimension, cell) => `${action}|${normDimension(dimension)}|${cell.x},${cell.y},${cell.z}`;
function parseProtectReply(raw, channel) {
  let text2;
  if (typeof raw === "string") text2 = raw;
  else if (raw instanceof Uint8Array) text2 = Buffer.from(raw).toString("utf8");
  else if (raw && typeof raw === "object" && "toString" in raw) text2 = String(raw);
  else return null;
  const start = channel === CHANNEL ? text2.indexOf("{") : text2.indexOf(PREFIX);
  if (start < 0) return null;
  const jsonStart = text2.indexOf("{", start);
  if (jsonStart < 0) return null;
  let obj;
  try {
    obj = JSON.parse(text2.slice(jsonStart));
  } catch {
    return null;
  }
  const action = obj.action;
  const status = obj.status;
  const dimension = obj.dimension ?? obj.world;
  if (typeof obj.dimension === "string" && typeof obj.world === "string" && normDimension(obj.dimension) !== normDimension(obj.world)) return null;
  const c = obj.coordinates && typeof obj.coordinates === "object" ? obj.coordinates : obj;
  const x = Number(c.x), y = Number(c.y), z = Number(c.z);
  if (action !== "break" && action !== "place" || status !== "deny" && status !== "unknown" && status !== "allow_likely" || typeof dimension !== "string" || ![x, y, z].every(Number.isInteger)) return null;
  return {
    action,
    dimension: normDimension(dimension),
    x,
    y,
    z,
    status,
    reason: typeof obj.reason === "string" ? obj.reason : ""
  };
}
var AgentFriendProtection = class {
  constructor(bot, onReply) {
    this.bot = bot;
    this.onReply = onReply;
    bot.on("message", (message, position) => {
      if (position !== "system") return;
      this.accept(parseProtectReply(message));
    });
    bot._client?.on("custom_payload", (packet) => {
      if (packet?.channel === CHANNEL) this.accept(parseProtectReply(packet.data, CHANNEL));
    });
  }
  bot;
  onReply;
  cache = /* @__PURE__ */ new Map();
  inflight = /* @__PURE__ */ new Map();
  chain = Promise.resolve();
  waiting = null;
  nextCommandAt = 0;
  accept(reply) {
    if (!reply) return;
    const key = keyOf(reply.action, reply.dimension, reply);
    const ttl = reply.status === "deny" ? DENY_TTL_MS : reply.status === "unknown" ? UNKNOWN_TTL_MS : ALLOW_TTL_MS;
    this.cache.set(key, { reply, until: Date.now() + ttl });
    if (reply.status === "unknown" && reply.reason.includes("rate_limited")) {
      this.nextCommandAt = Math.max(this.nextCommandAt, Date.now() + RATE_LIMIT_BACKOFF_MS);
    }
    if (this.cache.size > 1024) this.cache.delete(this.cache.keys().next().value);
    this.onReply?.(reply);
    if (this.waiting?.key === key) this.waiting.resolve(reply);
  }
  verdict(action, dimension, cell) {
    const entry = this.cache.get(keyOf(action, dimension, cell));
    return entry && entry.until > Date.now() ? entry.reply.status : null;
  }
  /** 路径试算只预取少量挖/放目标；真实操作仍走 fresh 检查。 */
  prefetch(action, dimension, cell) {
    if (this.inflight.size >= 1 || this.verdict(action, dimension, cell) !== null) return;
    void this.check(action, dimension, cell).catch(() => void 0);
  }
  /** 执行前 fresh=true 再查一次；已明确拒绝的格子直接停，不刷同一命令。 */
  check(action, dimension, cell, fresh = false) {
    const point2 = { x: Math.floor(cell.x), y: Math.floor(cell.y), z: Math.floor(cell.z) };
    const key = keyOf(action, dimension, point2);
    const cached = this.cache.get(key);
    if (cached && cached.until > Date.now() && (cached.reply.status === "deny" || !fresh)) {
      return Promise.resolve(cached.reply);
    }
    const existing = this.inflight.get(key);
    if (existing) return existing;
    const task = this.chain.then(() => this.ask(action, dimension, point2));
    this.chain = task.catch(() => void 0);
    this.inflight.set(key, task);
    void task.then(
      () => {
        if (this.inflight.get(key) === task) this.inflight.delete(key);
      },
      () => {
        if (this.inflight.get(key) === task) this.inflight.delete(key);
      }
    );
    return task;
  }
  async ask(action, dimension, cell) {
    const delay = this.nextCommandAt - Date.now();
    if (delay > 0) await new Promise((resolve) => setTimeout(resolve, delay));
    const pos = this.bot.entity?.position;
    const dist = pos ? Math.hypot(pos.x - cell.x, pos.y - cell.y, pos.z - cell.z) : Infinity;
    if (dist > 16 || this.bot.blockAt?.(new Vec32(cell.x, cell.y, cell.z)) == null) {
      const reply = {
        action,
        dimension: normDimension(dimension),
        ...cell,
        status: "unknown",
        reason: dist > 16 ? "\u76EE\u6807\u8D85\u8FC7\u670D\u52A1\u7AEF\u9884\u68C0\u7684 16 \u683C\u8303\u56F4" : "\u76EE\u6807\u533A\u5757\u5C1A\u672A\u52A0\u8F7D"
      };
      this.accept(reply);
      return reply;
    }
    const key = keyOf(action, dimension, cell);
    this.nextCommandAt = Date.now() + QUERY_GAP_MS;
    return new Promise((resolve) => {
      let finished = false;
      const finish = (reply) => {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        if (this.waiting?.key === key) this.waiting = null;
        resolve(reply);
      };
      const timer = setTimeout(() => {
        const reply = {
          action,
          dimension: normDimension(dimension),
          ...cell,
          status: "unknown",
          reason: "\u4FDD\u62A4\u9884\u68C0\u56DE\u6267\u8D85\u65F6"
        };
        this.accept(reply);
        finish(reply);
      }, TIMEOUT_MS);
      this.waiting = { key, resolve: finish };
      try {
        this.bot.chat(`/mycli protect ${action} ${cell.x} ${cell.y} ${cell.z}`);
      } catch (error) {
        finish({
          action,
          dimension: normDimension(dimension),
          ...cell,
          status: "unknown",
          reason: `\u4FDD\u62A4\u9884\u68C0\u547D\u4EE4\u53D1\u9001\u5931\u8D25: ${String(error)}`
        });
      }
    });
  }
};

// integrations/qiandengji/engine/bridge.ts
import { BREAK_ACL_CHANNEL } from "agent-mc-world/extension";

// integrations/qiandengji/engine/server-identity.ts
var AGENT_IDENTITY_CHANNEL = "qiandengji:agent";
function advertiseAgentIdentity(client, reconnect) {
  try {
    client.write("custom_payload", { channel: "minecraft:register", data: Buffer.from(AGENT_IDENTITY_CHANNEL, "utf8") });
    client.write("custom_payload", {
      channel: AGENT_IDENTITY_CHANNEL,
      data: Buffer.from(JSON.stringify({ op: "identity", protocol: 1, control: "agent", reconnect }), "utf8")
    });
    return true;
  } catch {
    return false;
  }
}

// integrations/qiandengji/engine/bridge.ts
var QiandengjiBridge = class extends Bridge {
  constructor(options) {
    super({ ...options, protectionChannel: BREAK_ACL_CHANNEL, onServerReady(bot, reconnect) {
      if (!advertiseAgentIdentity(bot._client, reconnect)) options.log.warn("Qiandengji identity announcement failed");
      options.onServerReady?.(bot, reconnect);
    } });
  }
  createProtectionPort(bot, reply) {
    return new AgentFriendProtection(bot, reply);
  }
  attachServerProtocols(bot, gen) {
    this.agentMana = void 0;
    const onAgentState = (packet) => {
      if (packet.channel !== VIEWER_STATE_CHANNEL || this._bot !== bot || this.generation !== gen) return;
      const state = parseSkillsPayload(packet.channel, packet.data);
      if (state) this.agentMana = state.mana;
    };
    bot._client.on("custom_payload", onAgentState);
    this.bagFor(gen).register("agent-state", () => {
      bot._client.off("custom_payload", onAgentState);
    });
    bot.on("death", () => {
      if (this._bot === bot && this.generation === gen) this.agentMana = null;
    });
  }
  viewerServerProtocol() {
    return serverViewerProtocol;
  }
};

// integrations/qiandengji/engine/chat-policy.ts
var ChatPolicyState = class {
  value = null;
  unknownAt = null;
  reset() {
    this.value = null;
    this.unknownAt = null;
  }
  observe(text2, uuid3) {
    const match = /^MC_(?:STATUS|GUIDE|COMMUNICATION) (\{[^\r\n]*\})$/.exec(text2);
    if (!match || !uuid3 || text2.length > 65536) return false;
    try {
      const envelope = JSON.parse(match[1]), p = envelope.communication;
      if (envelope.schemaVersion !== 1 || envelope.playerUuid !== uuid3 || !Number.isFinite(envelope.observedAt) || !p || p.schema !== "agent-mc/chat-policy/v1") return false;
      if (p.provider === "unknown") {
        this.reset();
        this.unknownAt = new Date(envelope.observedAt).toISOString();
        return true;
      }
      if (p.provider !== "EssentialsXChat" || !["nearby", "server", "unknown"].includes(p.defaultChannel) || p.nearby?.scope !== "same-world-range" || !Number.isFinite(p.nearby.radius) || p.nearby.radius < 0 || p.nearby.radius > 1e4 || p.defaultChannel === "nearby" && p.nearby.radius === 0 || p.shout?.scope !== "server" || typeof p.shout.prefix !== "string" || !/^[^\s\p{Cc}<>/\\]$/u.test(p.shout.prefix)) return false;
      const permission = (node) => p.permissionObservationSource === "bukkit.hasPermission" && typeof p.permissionNodes?.[node] === "boolean" ? p.permissionNodes[node] : null;
      const privateCommand = p.private?.scope === "single-recipient" && typeof p.private.command === "string" && /^\/[a-z][a-z0-9_-]{0,31} <player> <text>$/i.test(p.private.command) ? p.private.command : null;
      this.unknownAt = null;
      this.value = {
        schema: p.schema,
        provider: p.provider,
        defaultChannel: p.defaultChannel,
        nearby: { scope: "same-world-range", radius: p.nearby.radius },
        shout: { prefix: p.shout.prefix, scope: "server" },
        permissions: { shout: permission("essentials.chat.shout"), private: permission("essentials.msg") },
        privateCommand,
        observedAt: new Date(envelope.observedAt).toISOString()
      };
      return true;
    } catch {
      return false;
    }
  }
  audience(text2, rendered, direction) {
    if (direction === "incoming") {
      const label = rendered && /^\[(附近|大喇叭|喊话)\]\s*\[[^\]\r\n]{1,80}\]/u.exec(rendered)?.[1];
      if (!label) return void 0;
      return {
        channel: label === "\u9644\u8FD1" ? "nearby" : "shout",
        scope: label === "\u9644\u8FD1" ? "same-world-range" : "server",
        source: "server-decoration",
        ...label === "\u9644\u8FD1" && this.value && this.value.nearby.radius > 0 ? { radius: this.value.nearby.radius } : {},
        ...this.value ? { observedAt: this.value.observedAt } : {}
      };
    }
    const p = this.value;
    if (!p) return void 0;
    if (text2.startsWith(p.shout.prefix)) return { channel: "shout", scope: "server", source: "server-policy", observedAt: p.observedAt };
    return p.defaultChannel === "nearby" ? { channel: "nearby", scope: "same-world-range", radius: p.nearby.radius, source: "server-policy", observedAt: p.observedAt } : { channel: "server-default", scope: p.defaultChannel === "server" ? "server" : "unknown", source: "server-policy", observedAt: p.observedAt };
  }
  /** This server's rendered relay carries a display name, not a packet sender. */
  nearbyRelay(text2) {
    const policy = this.value;
    if (!policy || policy.defaultChannel !== "nearby" || text2.length > 2048 || /[\r\n]/u.test(text2)) return null;
    const line = text2.replace(/§[0-9a-fk-orx]/gi, "");
    const match = /^\[附近\]\s+(?:\[[^\]\r\n]{1,80}\]\s+)?([\p{L}\p{N}_. -]{1,32})\s*[:：]\s*(\S.*)$/u.exec(line);
    if (!match) return null;
    const displayName = match[1].trim();
    if (!/[\p{L}\p{N}_]/u.test(displayName)) return null;
    return { displayName, body: match[2], shoutPrefix: policy.shout.prefix, radius: policy.nearby.radius };
  }
  nearbyRelayResponse(worldKey) {
    return worldKey && this.value?.defaultChannel === "nearby" ? { worldKey, shoutPrefix: this.value.shout.prefix, channel: "nearby" } : null;
  }
  brief() {
    const p = this.value;
    if (!p) return this.unknownAt ? "[\u804A\u5929\u9891\u9053\u670D\u52A1\u7AEF\u89C2\u6D4B] " + this.unknownAt + "\uFF1B\u5F53\u524D\u9891\u9053\u63D0\u4F9B\u65B9\u6216\u8303\u56F4\u672A\u77E5\uFF0C\u4E0D\u6CBF\u7528\u65E7\u8303\u56F4\uFF1B\u672A\u81EA\u52A8\u6539\u7528\u558A\u8BDD\u6216\u79C1\u804A\u3002" : "";
    const permission = (value) => value === true ? "\u672C\u4EBA\u5DF2\u83B7\u6743\u9650" : value === false ? "\u672C\u4EBA\u65E0\u6743\u9650" : "\u672C\u4EBA\u6743\u9650\u672A\u77E5";
    return "[\u804A\u5929\u9891\u9053\u670D\u52A1\u7AEF\u89C2\u6D4B] " + p.observedAt + "\uFF1B\u666E\u901A\u6587\u5B57\uFF1A" + (p.defaultChannel === "nearby" ? `\u540C\u4E00\u5B9E\u9645\u4E16\u754C\u9644\u8FD1 ${p.nearby.radius} \u683C` : p.defaultChannel === "server" ? "\u670D\u52A1\u5668\u8303\u56F4" : "\u9ED8\u8BA4\u8303\u56F4\u672A\u77E5") + `\uFF1B${p.shout.prefix}\u5185\u5BB9\u4E3A\u5355\u6B21\u5168\u670D\u558A\u8BDD\uFF08${permission(p.permissions.shout)}\uFF09\uFF1B\u79C1\u804A\uFF1A${permission(p.permissions.private)}` + (p.privateCommand ? `\uFF0C\u670D\u52A1\u7AEF\u547D\u4EE4 ${p.privateCommand}` : "\uFF0C\u5F53\u524D\u547D\u4EE4\u672A\u77E5") + (p.permissions.private === false ? "\uFF0C\u4E0D\u8981\u91CD\u590D\u5C1D\u8BD5\u65E0\u6743\u9650\u79C1\u804A" : "") + "\u3002@\u540D\u5B57\u4E0D\u6269\u5927\u8303\u56F4\uFF1B\u4F20\u8F93\u6210\u529F\u4E0D\u8BC1\u660E\u6536\u5230\u3001\u542C\u89C1\u6216\u5DF2\u8BFB\u3002";
  }
};

// integrations/qiandengji/engine/combat-spells.ts
import { HOSTILE } from "agent-mc-world/extension";
import { CombatAbilities } from "agent-mc-world/tactics";
var SPELLS = ["golem", "frostnova", "flamewave", "starbolt"];
var SPELL_COOLDOWN_MS = {
  golem: 75e3,
  frostnova: 15e3,
  flamewave: 15e3,
  starbolt: 6e3
};
var DEFAULT_COST = {
  golem: 12,
  frostnova: 7,
  flamewave: 8,
  starbolt: 4
};
var GLOBAL_GAP_MS = 1500;
var RANGED = /* @__PURE__ */ new Set(["skeleton", "stray", "bogged", "pillager", "witch", "blaze", "ghast", "illusioner", "breeze"]);
var CombatSpells = class extends CombatAbilities {
  unlockDenials = /* @__PURE__ */ new Map();
  starboltRange = null;
  reset() {
    super.reset();
    this.unlockDenials.clear();
    this.starboltRange = null;
  }
  get defaultSpells() {
    return SPELLS;
  }
  get defaultCosts() {
    return DEFAULT_COST;
  }
  get defaultCooldowns() {
    return SPELL_COOLDOWN_MS;
  }
  get supportSpell() {
    return "selfheal";
  }
  cooldownOf(spell) {
    return this.cooldowns.get(spell) ?? SPELL_COOLDOWN_MS[spell] ?? 15e3;
  }
  noteAbilities(abilities, now = Date.now()) {
    const current = abilities.map((a) => ({ ...a, id: a.id.split(":").at(-1) }));
    for (const ability of current) {
      const deniedAt = this.unlockDenials.get(ability.id);
      if (deniedAt !== void 0 && now >= deniedAt) this.unlockDenials.delete(ability.id);
    }
    super.noteAbilities(current, now);
  }
  capabilityIndex(now = Date.now()) {
    const denials = [...this.unlockDenials].slice(-16).map(([id2, at]) => ({ id: id2, reason: "not-unlocked", observedAt: new Date(at).toISOString() }));
    return super.capabilityIndex(now) + (denials.length ? "\n[\u670D\u52A1\u7AEF\u6280\u80FD\u62D2\u7EDD\u89C2\u5BDF] " + JSON.stringify(denials) + "\uFF1B\u6309\u5F53\u524D /mycli skills status \u4E0E\u5355\u9879\u8BE6\u60C5\u6838\u5BF9\uFF0C\u89C2\u5BDF\u8BB0\u5F55\u4E0D\u589E\u52A0\u624B\u52A8\u65BD\u6CD5\u7981\u4EE4\u3002" : "");
  }
  noteServerMessage(text2, now = Date.now()) {
    if (starboltTargetRefusal(text2)) return;
    const attempt = this.casts.at(-1);
    const result = attempt && viewerCastResult(text2, attempt.spell);
    if (attempt && now - Date.parse(attempt.sentAt) >= 0 && now - Date.parse(attempt.sentAt) <= 3e3 && !attempt.reply && result) {
      attempt.reply = text2.slice(0, 240);
      attempt.replyAt = new Date(now).toISOString();
      if (result.detail === "\u6280\u80FD\u672A\u89E3\u9501") {
        this.unlockDenials.set(attempt.spell, now);
        if (this.unlockDenials.size > 128) this.unlockDenials.delete(this.unlockDenials.keys().next().value);
        this.available.delete(attempt.spell);
        this.serverReadyAt.delete(attempt.spell);
      }
    }
    const reportedMana = manaSnapshotFromText(text2);
    if (reportedMana) this.noteMana(reportedMana.current, now);
    if (/^(?:战斗咏唱|探索咏唱)[：:]/.test(text2)) {
      for (const match of text2.matchAll(/[（(]([a-z][a-z0-9_:-]*)[，,]([^）)]*)[）)]/gi)) {
        const spell = match[1].toLowerCase();
        if (!this.available.has(spell)) {
          this.available.add(spell);
          this.lastCheck = Number.NEGATIVE_INFINITY;
        }
        const cost = /(\d+)\s*魔力/.exec(match[2]);
        if (cost) this.costs.set(spell, Number(cost[1]));
        const cooldown = /(\d+)\s*秒/.exec(match[2]);
        if (cooldown) this.cooldowns.set(spell, Number(cooldown[1]) * 1e3);
      }
    }
    if (/魔力不足|灵力不足|not enough (?:mana|magic)|insufficient (?:mana|magic)/i.test(text2)) {
      if (this.pending && now - this.pending.at <= 3e3) {
        const required = /需要\s*(\d+)/.exec(text2);
        if (required) this.costs.set(this.pending.spell, Number(required[1]));
        if (reportedMana) {
          this.manaRetryAt.set(
            this.pending.spell,
            Math.max(reportedMana.current + 1, Number(required?.[1] ?? 0))
          );
        }
      }
      this.manaBlockedUntil = now + (reportedMana ? GLOBAL_GAP_MS : 15e3);
      this.pending = null;
    } else if (this.pending && now - this.pending.at <= 3e3 && /冷却中|cooldown|无法施放|施法失败|cannot cast|failed to cast/i.test(text2)) {
      this.pending = null;
    }
    if (attempt?.replyAt === new Date(now).toISOString() && result?.phase === "failed") this.pending = null;
  }
  noteTargetFeedback(text2, now = Date.now()) {
    const range = starboltTargetRefusal(text2);
    if (!range || this.pending?.spell !== "starbolt") return;
    const attempt = this.casts.at(-1);
    const age = now - this.pending.at;
    if (!attempt || attempt.reply || age < 0 || age > 3e3) return;
    attempt.reply = text2.slice(0, 240);
    attempt.replyAt = new Date(now).toISOString();
    this.starboltRange = range;
    this.noteUnspentMana(attempt);
  }
  automaticTargetBlock(bot, spell) {
    const range = this.starboltRange;
    if (spell !== "starbolt" || !range || !bot.entity || !bot.entities) return null;
    const origin = bot.entity.position;
    let possibleAimedTarget = false;
    for (const entity of Object.values(bot.entities)) {
      if (!entity?.position || entity === bot.entity || entity.isValid === false) continue;
      if (entity.type !== "mob" && entity.type !== "hostile" && !HOSTILE.has(entity.name ?? "")) continue;
      const half = (entity.width ?? 1) / 2;
      const dx = Math.max(0, Math.abs(entity.position.x - origin.x) - half);
      const dz = Math.max(0, Math.abs(entity.position.z - origin.z) - half);
      const dy = Math.max(0, entity.position.y - origin.y - (bot.entity.height ?? 2), origin.y - entity.position.y - (entity.height ?? 2));
      const distance = Math.hypot(dx, dy, dz);
      if (distance <= range.automatic) return null;
      if (distance <= range.aimed) possibleAimedTarget = true;
    }
    if (possibleAimedTarget) return null;
    return `\u661F\u8292\u7BAD\u670D\u52A1\u7AEF\u62A5\u544A\u51C6\u661F ${range.aimed} \u683C\u3001\u81EA\u52A8\u9501\u5B9A ${range.automatic} \u683C\uFF1B\u5F53\u524D\u8303\u56F4\u5185\u672A\u89C2\u5BDF\u5230\u53EF\u80FD\u76EE\u6807`;
  }
  selectFallback(_bot, foes, ready, near) {
    const planned = this.tactic?.spells ?? null;
    for (const spell of planned ?? SPELLS) {
      if (!ready(spell)) continue;
      if (spell === "golem" && foes.length >= (planned ? 1 : 3)) return spell;
      if (spell === "frostnova" && near(7) >= (planned ? 1 : 2)) return spell;
      if (spell === "flamewave" && near(8) >= (planned ? 1 : 2)) return spell;
      if (spell === "starbolt" && (planned ? near(12) >= 1 : foes.some((e) => RANGED.has(e.name ?? "")))) return spell;
      if (planned && !SPELLS.includes(spell) && near(12) >= 1) return spell;
    }
    return null;
  }
};

// integrations/qiandengji/engine/combat-tactics.ts
var combat_tactics_exports = {};
__reExport(combat_tactics_exports, tactics_star);
import * as tactics_star from "agent-mc-world/tactics";

// integrations/qiandengji/engine/agentfriend-flight.ts
import { setFlightExpiry } from "agent-mc-world/extension";
function watchAgentFriendFlight(bot) {
  let sentAt = null;
  const reset = () => {
    sentAt = null;
  };
  const detachCommands = observeViewerCastCommands(bot, (text2) => {
    sentAt = viewerCastCommand(text2)?.id === "flight" ? Date.now() : null;
  });
  const message = (value, position) => {
    if (position !== "system" || sentAt === null) return;
    const elapsed = Date.now() - sentAt;
    if (elapsed < 0 || elapsed > 3e3) {
      reset();
      return;
    }
    const text2 = value.toString().trim();
    const result = viewerCastResult(text2, "flight");
    if (result?.phase === "failed") {
      reset();
      return;
    }
    const duration = /^[✦\s]*飞行术持续\s*(\d+(?:\.\d+)?)\s*秒[；;]/u.exec(text2);
    if (!duration || result?.phase !== "succeeded") return;
    const expiresAt = sentAt + Number(duration[1]) * 1e3;
    reset();
    if (Number.isSafeInteger(expiresAt)) setFlightExpiry(bot, expiresAt);
  };
  const dispose = () => {
    reset();
    detachCommands();
    bot.off("message", message);
    bot.off("respawn", reset);
    bot.off("death", reset);
    bot.off("end", dispose);
  };
  bot.on("message", message);
  bot.on("respawn", reset);
  bot.on("death", reset);
  bot.on("end", dispose);
  return dispose;
}

// integrations/qiandengji/engine/trial-body-state.ts
function trialBodyState(text2, selfUuid, currentlyDowned) {
  if (text2.length > 1024 || !/^MC_TRIAL_RESCUE(?: [a-zA-Z]+=[^\s]+)+$/.test(text2)) return null;
  const fields = {};
  for (const field of text2.split(" ").slice(1)) {
    const at = field.indexOf("="), key = field.slice(0, at);
    if (Object.hasOwn(fields, key)) return null;
    fields[key] = field.slice(at + 1);
  }
  const player = fields.player?.toLowerCase(), self = selfUuid?.toLowerCase();
  if (player && (!self || player !== self)) return null;
  if (fields.status === "downed" && player && self) return "downed";
  if (currentlyDowned && (fields.status === "revived" || fields.status === "recovered")) return "revived";
  if (currentlyDowned && fields.status === "denied" && fields.reason === "downed") return "downed";
  return null;
}
var TRIAL_DOWNED_REASON = "\u670D\u52A1\u7AEF\u786E\u8BA4\u5012\u5730\u5F85\u6551\uFF0C\u5F53\u524D\u4E0D\u80FD\u79FB\u52A8\u6216\u6218\u6597\uFF1B\u7B49\u5F85\u961F\u53CB\u6551\u63F4\u6216\u670D\u52A1\u7AEF\u590D\u6D3B";

// integrations/qiandengji/engine/world.ts
import { TacticalMinecraftWorld, COMBAT_TACTIC_TOOL, BATTLEFIELD_CHANNEL } from "agent-mc-world/tactics";
var SERVER_QUERY_DECLARATION = serverQueryTool(QIANDENGJI_SERVER_QUERIES);
var SERVER_TOOLS = [QIANDENGJI_CAST_TOOL, COMBAT_TACTIC_TOOL, {
  name: "mc_skills",
  tags: ["read"],
  description: "Read this connection and class's native available profession spells, common spells and learnable nodes. Optional id selects its membership; a learnable/passive node is not a castable spell. No queries, point spending, preparation or casting are performed. Unknown cost/cooldown/effect remain null. Read mc_query skills.info for the current full definition, mc_combat_tactic for observed combat constraints and Agent-authored combinations, and actual server receipts for effects.",
  parameters: { type: "object", properties: { id: { type: "string", pattern: "^[a-z][a-z0-9_:-]{0,63}$" } } }
}, SERVER_QUERY_DECLARATION, QIANDENGJI_MAIDS_TOOL];
var QiandengjiEngine = class extends TacticalMinecraftWorld {
  selfHealAvailable = false;
  combatSpells;
  arenaFloor = null;
  trialSearch = new TrialSearchState();
  adventureGatherings;
  observedCommands = new ObservedCommandCatalog();
  nativeRpg = new NativeRpgState();
  chatPolicy = new ChatPolicyState();
  maids = new MaidState();
  maidPort = null;
  /** Submission records for this connection; read the server for the actual effect. */
  maidWrites = /* @__PURE__ */ new Map();
  releaseMaidIdentity = null;
  lastNearbyRelay;
  constructor(options) {
    const tactics = new CombatSpells(new combat_tactics_exports.CombatTacticBook(options.dataDir ? join(options.dataDir, "minecraft-combat-tactics.json") : null));
    super(options, tactics);
    this.combatSpells = tactics;
  }
  battlefieldChannel() {
    return BATTLEFIELD_CHANNEL;
  }
  extensionInventoryArrival(command) {
    return stashTakeArrival(command);
  }
  emit(...args) {
    const [type, text2, urgent, options] = args;
    const bot = this.bridge?.bot;
    const feedback = options?.meta?.executionFeedback;
    if (type === "minecraft.chat" && options?.deliver !== false && bot?._client?.state === "play" && this.bridge?.connected && /^\[MC (?:系统|插件)\] \[附近·女仆\] /u.test(text2) && feedback?.kind === "server-message" && hasExecutionFeedbackContext(text2, feedback)) {
      const world = readWorldIdentity(bot);
      if (world.key) {
        const current = new Set(Object.values(bot.entities).flatMap((entity) => entity.isValid !== false && typeof entity.uuid === "string" ? [entity.uuid.toLowerCase()] : []));
        const dialogue = this.maids.nearbySceneSpeech(text2, current);
        if (dialogue && this.maids.queueSceneSpeech(JSON.stringify([world.key, world.revision]), dialogue, () => {
          const live = readWorldIdentity(bot);
          if (!this.bridge?.connected || this.bridge.bot !== bot || bot._client?.state !== "play" || live.revision !== world.revision) return;
          const { executionFeedback: _feedback, ...meta } = options?.meta ?? {};
          super.emit(type, dialogue.text, urgent, {
            ...options,
            meta: {
              ...meta,
              ...dialogue.meta,
              deliveryWorld: world,
              deliveryWorldKey: world.key,
              companionSpeech: { kind: "nearby-caption", originalSha256: feedback.originalSha256 }
            }
          }, dialogue.senderKey);
        })) return;
      }
    }
    super.emit(...args);
  }
  playerQueries;
  serverQueryDefinitions() {
    const bot = this.bridge?.bot;
    const uuid3 = bot?.player?.uuid ?? bot?._client?.uuid;
    if (!uuid3) return QIANDENGJI_SERVER_QUERIES;
    if (this.playerQueries?.uuid !== uuid3) this.playerQueries = { uuid: uuid3, definitions: qiandengjiServerQueriesForPlayer(uuid3) };
    return this.playerQueries.definitions;
  }
  combatHealingUrgent(bot) {
    return this.selfHealAvailable && this.combatSpells.wantsHeal(bot.health ?? 0);
  }
  extensionTools() {
    return [
      ...super.extensionTools(),
      { ...SERVER_TOOLS[0], handler: async (args) => this.castSpell(args) },
      { ...SERVER_TOOLS[2], handler: async (args) => ({
        text: this.nativeRpg.skillsReadout(typeof args.id === "string" ? args.id : void 0),
        meta: {
          nativeSkillsCurrent: this.nativeRpg.hasCurrentSkills(),
          nativeProfessionSkillObserved: typeof args.id === "string" && this.nativeRpg.hasProfessionSkillInfo(args.id),
          nativeSkillRouteObserved: this.nativeRpg.hasInvocationInfo(typeof args.id === "string" ? args.id : void 0)
        }
      }) },
      { ...QIANDENGJI_MAIDS_TOOL, handler: (args, ctx) => this.invokeMaidTool(args, ctx) }
    ];
  }
  async invokeMaidTool(args, ctx) {
    let native, entry;
    try {
      native = maidArguments(args);
      entry = maidCommand(native);
    } catch (error) {
      return { text: String(error), failed: true };
    }
    const port = this.maidPort, bot = this.bridge?.bot;
    if (!port || !bot) return { text: "\u5973\u4EC6\u63A5\u53E3\u672A\u8FDE\u63A5\uFF0C\u8BF7\u8FDE\u63A5\u540E\u6309\u539F\u7F16\u53F7\u67E5\u8BE2\u3002", failed: true };
    if (maidReadAction(entry.action, native)) {
      return this.readMaid(port, bot, entry, native);
    }
    const previous = this.maidWrites.get(entry.requestId);
    if (previous && previous.entry.command !== entry.command) {
      return { text: "requestId \u5DF2\u7528\u4E8E\u4E0D\u540C\u64CD\u4F5C\uFF0C\u8BF7\u67E5\u539F operationId \u7684\u56DE\u6267\u3002", failed: true };
    }
    if (entry.order && previous) return this.maidSubmission(previous, void 0, true);
    const write = previous ?? { entry };
    if (!previous) this.maidWrites.set(entry.requestId, write);
    if (entry.order) {
      if (!port.workshopSupported) {
        write.submission = "checking_capability";
        const probe = maidCommand({ action: "workshop", maidId: entry.maidId });
        const outcome2 = await this.readMaid(port, bot, probe, { action: "workshop", maidId: entry.maidId });
        if (outcome2.failed) {
          write.submission = "not_dispatched";
          write.reason = String(outcome2.data?.error ?? outcome2.data?.reason ?? "workshop_capability_unconfirmed");
          if (this.maidWrites.get(entry.requestId) === write) this.maidWrites.delete(entry.requestId);
          return this.maidSubmission(write, outcome2);
        }
      }
      if (this.maidPort !== port || this.bridge?.bot !== bot || ctx.signal?.aborted) {
        write.submission = "not_dispatched";
        write.reason = ctx.signal?.aborted ? "call_cancelled" : "connection_closed";
        return this.maidSubmission(write);
      }
    }
    const steps = [{ skill: "chat", text: entry.command }];
    write.submission = "unknown";
    let result;
    try {
      result = this.enqueueTool("mc_do", { steps, queue: "append" }, () => ({ steps }), void 0, ctx.role, ctx.attribution?.controller, ctx);
    } catch (error) {
      write.reason = "queue_result_unknown";
      this.diag.write({ lane: "task", event: "maid-queue-result-unknown", msg: String(error) });
      return this.maidSubmission(write, { text: "\u672A\u53D6\u5F97\u961F\u5217\u56DE\u6267\uFF0C\u4FDD\u7559\u539F\u5DE5\u5355\u7F16\u53F7\u3002", failed: true });
    }
    const outcome = typeof result === "string" ? { text: result } : result;
    write.submission = outcome.failed ? "not_dispatched" : "queued";
    return this.maidSubmission(write, outcome);
  }
  async readMaid(port, bot, entry, native) {
    const stored = entry.action === "receipt" && entry.operationId ? this.maidWrites.get(entry.operationId) : void 0;
    const original = stored && stored.entry.maidId === entry.maidId ? stored : void 0;
    if (original) {
      if (entry.operationAction && entry.operationAction !== original.entry.action) {
        return {
          text: "operationAction \u4E0E\u672C\u6B21\u8FDE\u63A5\u4FDD\u7559\u7684\u539F\u52A8\u4F5C\u4E0D\u540C\uFF0C\u8BF7\u7528\u539F\u52A8\u4F5C\u67E5\u8BE2\u3002",
          failed: true,
          data: { status: "not_dispatched", reason: "request_conflict", goalCompleted: false }
        };
      }
      entry.operationAction = original.entry.action;
    }
    const result = await port.request({
      ...native,
      requestId: entry.requestId,
      ...entry.operationAction ? { operationAction: entry.operationAction } : {}
    });
    if (this.maidPort !== port || this.bridge?.bot !== bot) {
      return this.unavailableMaidRead(entry, "connection_closed");
    }
    const reply = maidSystemReply("QD_MAID " + JSON.stringify(result), bot.player?.uuid ?? bot._client?.uuid);
    if (!reply) {
      const reason = result && typeof result === "object" && "reason" in result && typeof result.reason === "string" ? result.reason : "reply_unavailable";
      return this.unavailableMaidRead(entry, reason);
    }
    if (!matchesMaidReply(reply, entry, original?.entry.order)) return this.unavailableMaidRead(entry, "reply_mismatch");
    if (!reply.ok && reply.error === "receipt_missing" && original?.reply) {
      const data2 = {
        receiptSource: "current_connection_original_reply",
        operationId: entry.operationId,
        reply: original.reply,
        serverQuery: reply,
        retryAllowed: false,
        goalCompleted: false
      };
      return { text: JSON.stringify(data2), data: data2, failed: true };
    }
    this.observeMaidReply(reply);
    const inventoryAccess = maidInventoryAccess(reply);
    const data = inventoryAccess ? { ...reply, inventoryAccess } : { ...reply };
    return { text: JSON.stringify(data), data, ...!reply.ok ? { failed: true } : {} };
  }
  unavailableMaidRead(entry, reason) {
    const data = {
      ok: false,
      action: entry.action,
      requestId: entry.requestId,
      operationId: entry.operationId,
      status: "unavailable",
      reason,
      retryAllowed: false,
      goalCompleted: false,
      nextStep: entry.action === "receipt" ? "\u91CD\u65B0\u67E5\u8BE2\u539F operationId\uFF1B\u4FDD\u7559\u672A\u77E5\u7ED3\u679C\u3002" : "\u6062\u590D\u8FDE\u63A5\u540E\u91CD\u67E5\u5973\u4EC6\u63A5\u53E3\u3002"
    };
    return { text: JSON.stringify(data), data, failed: true };
  }
  maidSubmission(write, outcome, duplicate = false) {
    const { entry, submission: status, reason } = write;
    const operation = { maidId: entry.maidId, operationId: entry.operationId, action: entry.action, status, reason, duplicate, goalCompleted: false };
    const next = status === "not_dispatched" ? "\u672A\u8FDB\u5165\u8EAB\u4F53\u961F\u5217\u3002\u8BF7\u6839\u636E\u539F\u56E0\u5904\u7406\uFF1B\u80FD\u529B\u672A\u77E5\u65F6\u5148\u67E5 workshop\u3002" : `\u961F\u5217\u53D7\u7406\u3001\u53D1\u9001\u548C\u5236\u4F5C\u5B8C\u6210\u5206\u522B\u6838\u5BF9\u3002\u7528 mc_maids {action:"receipt",maidId:"${entry.maidId}",operationId:"${entry.operationId}",operationAction:"${entry.action}"} \u67E5\u8BE2\u539F\u7ED3\u679C\uFF0C\u4FDD\u7559\u539F ID\u3002`;
    return {
      ...outcome,
      text: [outcome?.text, `\u5973\u4EC6 operationId=${entry.operationId} \xB7 ${status}\u3002`, next].filter(Boolean).join("\n"),
      data: { ...outcome?.data, maidOperation: operation },
      ...["not_dispatched", "unknown"].includes(status ?? "") ? { failed: true } : {}
    };
  }
  observeMaidReply(reply) {
    const original = this.maidWrites.get(reply.requestId);
    if (!reply.ok && original && matchesMaidReply(reply, original.entry))
      original.reply = reply;
    const notice = this.maids.observe(reply);
    if (notice?.publicDialogue) {
      const dialogue = notice.publicDialogue;
      const world = readWorldIdentity(this.bridge?.bot), scope = JSON.stringify([world.key, world.revision]);
      if (this.maids.acceptTypedSpeech(scope, dialogue))
        this.emit("minecraft.chat", dialogue.text, false, { meta: { ...dialogue.meta, ...notice.meta } }, dialogue.senderKey);
    } else if (notice) this.emit("minecraft.event", notice.text, notice.urgent, { meta: notice.meta });
  }
  castSpell(args) {
    return invokeQiandengjiCast({
      blockedReason: () => this.bodyInhibitReason,
      abilities: this.combatSpells,
      commands: this.observedCommands,
      skillDetail: (id2) => this.nativeRpg?.skillDetail(id2) ?? null,
      connection: () => {
        const bot = this.bridge?.bot;
        return bot ? { send: (command) => bot.chat(command), published: (command) => publishViewerCastCommand(bot, command) } : null;
      },
      log: (name, input, result) => this.toolLog(name, input, result)
    }, args);
  }
  tryAutoSelfHeal(bot) {
    if (this.bodyInhibitReason || !this.selfHealAvailable || (bot.health ?? 0) <= 0) return false;
    const now = Date.now();
    if (this.combatSpells.manualCastBlock("selfheal", now)) return false;
    const command = "/mycli cast selfheal";
    try {
      bot.chat(command);
    } catch (error) {
      this.diag.write({ lane: "combat", event: "auto-selfheal-send-failed", msg: String(error) });
      return false;
    }
    this.combatSpells.noteSupportSent(now);
    publishViewerCastCommand(bot, command);
    this.diag.write({
      lane: "combat",
      event: "auto-selfheal",
      msg: `\u4F4E\u8840\u5C1D\u8BD5\u5723\u6108\u672F,\u751F\u547D ${Math.ceil(bot.health ?? 0)}/20\uFF1B\u6548\u679C\u5F85\u670D\u52A1\u7AEF\u786E\u8BA4`,
      data: { health: bot.health, connectionGeneration: this.connectionGeneration }
    });
    this.emit("minecraft.event", "[Minecraft] \u8840\u4F4E\u65F6\u8BD5\u7740\u65BD\u4E86\u5723\u6108\u672F\uFF0C\u662F\u5426\u751F\u6548\u7B49\u670D\u52A1\u7AEF\u56DE\u6267\u548C\u751F\u547D\u8BFB\u6570\u786E\u8BA4\u3002", false, { trigger: "piggyback" });
    return true;
  }
  tryAutoCombatSpell(bot) {
    if (this.bodyInhibitReason || this.bridge?.bot !== bot) return;
    const fighting = (this.combat?.fighting ?? false) || (this.executor?.attacking ?? false);
    const underThreat = (this.combat?.active ?? false) || fighting;
    if (underThreat && this.selfHealAvailable && (this.combatSpells.wantsHeal(bot.health ?? 0) || (bot.health ?? 0) <= 6)) {
      if (this.tryAutoSelfHeal(bot)) return;
    }
    const spell = this.combatSpells.next(bot, fighting);
    if (!spell) return;
    this.sendAutoCombatSpell(bot, spell);
  }
  sendAutoCombatSpell(bot, spell, ruleId) {
    const command = `/mycli cast ${spell}`;
    try {
      bot.chat(command);
    } catch (error) {
      this.diag.write({ lane: "combat", event: "auto-spell-send-failed", msg: `${spell}: ${String(error)}` });
      return false;
    }
    this.combatSpells.noteSent(spell, Date.now(), "automatic", ruleId);
    publishViewerCastCommand(bot, command);
    this.diag.write({
      lane: "combat",
      event: "auto-spell",
      msg: `\u4EA4\u6218\u4E2D\u5C1D\u8BD5 ${spell}\uFF1B\u6548\u679C\u5F85\u670D\u52A1\u7AEF\u786E\u8BA4`,
      data: { spell, health: bot.health, connectionGeneration: this.connectionGeneration }
    });
    this.emit(
      "minecraft.event",
      `[Minecraft] \u8BD5\u7740\u65BD\u653E ${spell}\uFF0C\u662F\u5426\u751F\u6548\u7B49\u670D\u52A1\u7AEF\u56DE\u6267\u786E\u8BA4\u3002`,
      false,
      { trigger: "piggyback" }
    );
    return true;
  }
  extensionCombatTuning() {
    return { arena: this.arenaFloor !== null };
  }
  extensionCombatSearchObjective() {
    return this.trialSearch.read();
  }
  extensionLowHealth(bot) {
    this.tryAutoSelfHeal(bot);
  }
  extensionServerRelayedChat(text2) {
    const bot = this.bridge?.bot;
    if (!bot) return false;
    const relay = this.chatPolicy.nearbyRelay(text2);
    if (!relay) return false;
    const world = readWorldIdentity(bot);
    if (!world.key) return false;
    const username = this.chatName();
    const ownDisplay = bot.players?.[username]?.displayName?.toString().replace(/§[0-9a-fk-orx]/gi, "").trim();
    const label = relay.displayName.toLowerCase();
    if ([username, bot.username, ownDisplay].some((name) => name?.toLowerCase() === label)) return true;
    const at = performance.now();
    const previous = this.lastNearbyRelay;
    if (previous?.text === text2 && previous.worldRevision === world.revision && previous.connectionGeneration === this.connectionGeneration && at - previous.at < 500) return true;
    this.lastNearbyRelay = { text: text2, worldRevision: world.revision, connectionGeneration: this.connectionGeneration, at };
    this.emit("minecraft.chat", `[MC \u9644\u8FD1\u8F6C\u8FF0\uFF0C\u8EAB\u4EFD\u672A\u786E\u8BA4] ${relay.displayName}\uFF1A${relay.body}`, true, {
      meta: {
        channel: "nearby",
        chatChannel: "nearby",
        chatScope: "same-world-range",
        chatRadius: relay.radius,
        chatRoutingSource: "server-nearby-relay",
        socialScope: "minecraft-server",
        relaySpeakerDisplayName: relay.displayName,
        body: relay.body,
        relayShoutPrefix: relay.shoutPrefix,
        deliveryWorld: world,
        deliveryWorldKey: world.key
      }
    });
    return true;
  }
  extensionMessage(text2) {
    if (parseProtectReply(text2)) return true;
    const bot = this.bridge?.bot;
    this.trialSearch.observe(text2, bot?.username ?? "");
    const body = trialBodyState(
      text2,
      bot?.player?.uuid ?? bot?._client?.uuid,
      this.bodyInhibitReason === TRIAL_DOWNED_REASON
    );
    if (body) {
      this.setBodyInhibited(body === "downed" ? TRIAL_DOWNED_REASON : null, body === "downed" ? "downed" : null);
      return true;
    }
    this.combatSpells.noteServerMessage(text2);
    if (/^(?:可用咏唱|守护\/恢复)[：:]/.test(text2)) this.selfHealAvailable = /\bselfheal\b/i.test(text2);
    const match = /(?:进入第|已恢复第|^第)\s*(\d+)\s*\/\s*(\d+)\s*层(?=[：:试炼]|$)/.exec(text2);
    if (match) this.arenaFloor = { floor: Number(match[1]), total: Number(match[2]) };
    if (/第\s*(\d+)\s*\/\s*\1\s*层已通关/.test(text2)) this.arenaFloor = null;
    return false;
  }
  extensionServerFeedback(text2) {
    this.combatSpells.noteTargetFeedback(text2);
    this.trialSearch.observe(text2, this.bridge?.bot?.username ?? "");
    if (text2.startsWith("MC_COACH ")) {
      (this.adventureGatherings ??= new AdventureGatherings()).observe(text2, this.bridge?.bot?.player?.uuid ?? this.bridge?.bot?._client?.uuid);
    }
    const maid = maidSystemReply(text2, this.bridge?.bot?.player?.uuid ?? this.bridge?.bot?._client?.uuid);
    if (maid) this.observeMaidReply(maid);
    this.chatPolicy?.observe(text2, this.bridge?.bot?.player?.uuid ?? this.bridge?.bot?._client?.uuid);
    if (text2.startsWith("MC_RPG ") && this.nativeRpg.chat(text2)) this.publishNativeRpg();
    const usage = observedCommandUsage(text2) ?? observedCommandRoot(text2, this.bridge?.bot?.username);
    if (usage) this.observedCommands.note(usage);
  }
  tacticReview;
  preparedRuleGap() {
    const spell = this.nativeRpg.preparedAbility();
    if (!spell) {
      this.tacticReview = void 0;
      return null;
    }
    const revision = this.combatSpells.tacticRevision();
    if (this.tacticReview?.spell !== spell || this.tacticReview.revision !== revision) {
      const rules = this.combatSpells.getTactic()?.rules ?? [];
      this.tacticReview = { spell, revision, missing: !rules.some((rule) => rule.spell === spell && rule.intent) };
    }
    return this.tacticReview.missing ? {
      spell,
      tacticRevision: revision,
      detailQuery: { query: "skills.info", arguments: [spell] },
      reviewTool: "mc_combat_tactic"
    } : null;
  }
  requestFacts() {
    const facts = super.requestFacts();
    if (!facts) return facts;
    const observations = facts.decision?.state?.identityObservations;
    const nearbyRelayResponse = this.bridge?.connectionState?.ready ? this.chatPolicy.nearbyRelayResponse(readWorldIdentity(this.bridge.bot).key) : null;
    const currentTrial = this.trialSearch.facts();
    const preparedSkillWithoutRule = this.preparedRuleGap();
    const gatherings = currentTrial.fresh && "participant" in currentTrial && currentTrial.participant ? [] : this.adventureGatherings?.current() ?? [];
    const companions = this.maids.decisionSummary(Date.now(), Array.isArray(observations) ? observations : [], facts.decisionBoundary);
    const present = companions.map((c) => `${c.name}: ${c.presenceNote}` + (c.entityObservation ? ` \u5F53\u524D ${JSON.stringify(c.entityObservation)}` : ""));
    const companionParts = [{ key: "companions", text: present.length ? "[\u540C\u4F34\u5F53\u524D\u89C2\u5BDF\uFF1B\u65E7\u670D\u52A1\u7AEF\u91C7\u6837\u4E0D\u8986\u76D6\u6B64\u9879]\n" + present.join("\n") + "\n" + this.maids.brief() : "" }].filter((p) => p.text), parts = [
      { key: "currentTrial", text: "[\u5F53\u524D\u8BD5\u70BC\uFF1B\u5386\u53F2\u6210\u7EE9\u4E0D\u80FD\u5F53\u4F5C\u672C\u6B21\u901A\u5173]\n" + JSON.stringify(currentTrial) },
      { key: "nativeRpg", text: this.nativeRpg.brief() + (preparedSkillWithoutRule ? "\n[\u6218\u672F\u5F85\u8BC4\u4F30] \u5DF2\u51C6\u5907 " + preparedSkillWithoutRule.spell + "\uFF0C\u5F53\u524D\u6218\u672F v" + preparedSkillWithoutRule.tacticRevision + " \u6CA1\u6709\u5B83\u7684\u5FEB\u51B3\u7B56\u65BD\u6CD5\u89C4\u5219\u3002\u53EF\u8BFB skills.info \u6838\u5BF9\u6761\u4EF6\uFF0C\u518D\u51B3\u5B9A\u662F\u5426\u7528 mc_combat_tactic \u7F16\u6392\u3002" : "") },
      { key: "adventureGatherings", text: gatherings.length ? "[\u670D\u52A1\u5668\u96C6\u7ED3\u516C\u544A\uFF1B\u62A5\u540D\u72B6\u6001\u53E6\u67E5] " + JSON.stringify(gatherings) : "" },
      { key: "communication", text: this.chatPolicy.brief() }
    ].filter((p) => p.text);
    return {
      ...facts,
      partKeys: [.../* @__PURE__ */ new Set([...facts.partKeys ?? facts.parts?.map((p) => p.key) ?? [], "companions", "nativeRpg", "communication", "currentTrial", "adventureGatherings"])],
      ...facts.executionPartKeys ? { executionPartKeys: [.../* @__PURE__ */ new Set([...facts.executionPartKeys, "currentTrial"])] } : {},
      text: [...companionParts.map((p) => p.text), facts.text, ...parts.map((p) => p.text)].join("\n"),
      ...facts.parts ? { parts: [...companionParts, ...facts.parts, ...parts] } : {},
      // Delegated execution uses the compact decision state on the supervisor.
      // Preserve ownership and lifecycle there, without expanding the NPC's inventory/history.
      ...facts.decision ? { decision: { ...facts.decision, state: {
        ...facts.decision.state,
        currentTrial,
        ...nearbyRelayResponse ? { nearbyRelayResponse } : {},
        ...preparedSkillWithoutRule ? { preparedSkillWithoutRule } : {},
        ...gatherings.length ? { adventureGatherings: gatherings } : {},
        ...companions.length ? { companionObservations: companions } : {}
      } } } : {}
    };
  }
  extensionChatAudience(text2, rendered, direction = "outgoing") {
    return this.chatPolicy.audience(text2, rendered, direction);
  }
  publishNativeRpg() {
    const text2 = this.nativeRpg.brief();
    if (text2) this.emit("minecraft.event", text2, false, {
      trigger: "piggyback",
      meta: { nativeRpgObservation: true, nativeRpgProfile: this.nativeRpg.identity() }
    });
  }
  extensionImportantMessage(text2) {
    return /可用咏唱|可学习|魔力|命格|探矿|selfheal|healing restores|full health/i.test(text2);
  }
  extensionSpawn(bot) {
    super.extensionSpawn(bot);
    this.selfHealAvailable = false;
    this.arenaFloor = null;
    this.trialSearch.reset();
    this.extensionRespawn();
    const generation = this.connectionGeneration;
    setTimeout(() => {
      if (this.shuttingDown || this.bridge?.bot !== bot || generation !== this.connectionGeneration) return;
      const currentClass = this.nativeRpg.identity()?.classId;
      for (const command of [
        "/mycli status --json",
        "/mycli skills status --json",
        ...currentClass && currentClass !== "none" ? ["/mycli skills tree --json"] : []
      ]) {
        try {
          bot.chat(command);
        } catch (error) {
          this.diag.write({ lane: "link", event: "native-rpg-sync-send-failed", msg: String(error) });
          break;
        }
      }
      const port = this.maidPort;
      if (port) void port.request({ action: "list" }).then((result) => {
        if (this.shuttingDown || this.bridge?.bot !== bot || generation !== this.connectionGeneration) return;
        const reply = maidSystemReply("QD_MAID " + JSON.stringify(result), bot.player?.uuid ?? bot._client?.uuid);
        if (reply) this.observeMaidReply(reply);
      }).catch((error) => this.diag.write({ lane: "link", event: "maid-discovery-failed", msg: String(error) }));
    }, 1500).unref();
  }
  extensionRespawn() {
    this.trialSearch.reset();
    this.nativeRpg.reset();
    this.chatPolicy.reset();
    const mana2 = this.bridge?.agentManaState;
    if (mana2 !== void 0) this.combatSpells.noteMana(mana2?.current ?? null);
  }
  attachExtension(bot) {
    this.adventureGatherings = void 0;
    this.maidPort?.close();
    this.maidPort = null;
    this.maids.reset();
    this.maidWrites.clear();
    this.releaseMaidIdentity?.();
    const releaseIdentity = bindEntityIdentityResolver(bot, (entity) => this.maids.identity(entity.uuid));
    this.releaseMaidIdentity = releaseIdentity;
    try {
      this.maidPort = createMaidPort(bot);
    } catch (error) {
      this.diag.write({ lane: "link", event: "maid-port-unavailable", msg: String(error) });
    }
    const port = this.maidPort;
    const onMaid = (packet) => {
      if (this.shuttingDown || this.bridge?.bot !== bot) return;
      const reply = decodeMaidReply(packet, bot.player?.uuid ?? bot._client?.uuid);
      if (reply) this.observeMaidReply(reply);
    };
    bot._client.on("custom_payload", onMaid);
    bot._client.once("end", () => {
      bot._client.off("custom_payload", onMaid);
      port?.close();
      releaseIdentity();
      if (this.releaseMaidIdentity === releaseIdentity) {
        this.releaseMaidIdentity = null;
        this.maidPort = null;
        this.maids.reset();
        this.maidWrites.clear();
        this.adventureGatherings = void 0;
      }
    });
    this.nativeRpg.reset();
    this.chatPolicy.reset();
    this.observedCommands.clear();
    watchAgentFriendFlight(bot);
    bot.on("physicsTick", () => {
      if (!this.shuttingDown) this.tryAutoCombatSpell(bot);
    });
    bot.on("death", () => {
      this.arenaFloor = null;
      this.trialSearch.reset();
      this.combatSpells.noteMana(null);
    });
    bot.on("forcedMove", () => this.trialSearch.reset());
    bot._client.on("custom_payload", (packet) => {
      if (this.shuttingDown || this.bridge?.bot !== bot) return;
      if (this.nativeRpg.packet(packet.channel, packet.data)) this.publishNativeRpg();
      const state = parseSkillsPayload(packet.channel, packet.data);
      if (!state) return;
      if (packet.channel === VIEWER_STATE_CHANNEL) {
        this.combatSpells.noteMana(state.mana?.current ?? null);
        this.combatSpells.noteAbilities(state.abilities);
        this.selfHealAvailable = this.combatSpells.hasAbility("selfheal");
      } else if (state.mana) this.combatSpells.noteMana(state.mana.current);
    });
  }
  extensionAdmission(steps) {
    return stashTakeAdmission(steps) ?? portableStorageMisuseNote(this.bridge?.bot ?? null, steps);
  }
  createBridge(options) {
    return new QiandengjiBridge(options);
  }
};
function createEngine(options) {
  return new QiandengjiEngine(options);
}
export {
  ChatPolicyState,
  CombatSpells,
  QiandengjiBridge as EngineBridge,
  QiandengjiEngine as EngineWorld,
  MaidState,
  NativeRpgState,
  QIANDENGJI_CAST_TOOL,
  QIANDENGJI_MAIDS_TOOL,
  SERVER_TOOLS,
  TRIAL_DOWNED_REASON,
  VIEWER_STATE_CHANNEL,
  createEngine,
  createQiandengjiCastTool,
  invokeQiandengjiCast,
  maidArguments,
  maidSystemReply,
  nativeRpgMessage,
  observedCommandRoot,
  observedCommandUsage,
  parseSkillsPayload,
  readNativeProfessionSkillInfo,
  readNativeRpgPacket,
  readNativeRpgStatus,
  readNativeSkillDetail,
  readNativeSkillInvocations,
  readNativeSkills,
  readNativeTalentTree,
  trialBodyState
};
