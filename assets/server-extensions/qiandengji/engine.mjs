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
  const parameters = args.arguments === void 0 ? [] : args.arguments;
  if (!Array.isArray(parameters) || !parameters.every((value) => typeof value === "string" && value.length > 0 && !/[\s\u0000-\u001f\u007f-\u009f<>]/u.test(value))) {
    return { text: log(
      "mc_cast",
      args,
      "[mc_cast \u5931\u8D25] arguments \u5FC5\u987B\u662F\u72EC\u7ACB\u53C2\u6570\u8BCD\u7EC4\u6210\u7684\u6570\u7EC4\uFF0C\u4E0D\u80FD\u5305\u542B\u7A7A\u767D\u3001\u63A7\u5236\u7B26\u6216 <\u5360\u4F4D\u7B26>\uFF1B\u6309\u670D\u52A1\u7AEF\u8BF4\u660E\u586B\u5199\u5B9E\u9645\u503C"
    ), failed: true };
  }
  const command = `/mycli cast ${spell}${parameters.length ? ` ${parameters.join(" ")}` : ""}`;
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

// integrations/qiandengji/engine/world.ts
import { ObservedCommandCatalog, serverQueryTool } from "agent-mc-world/extension";

// integrations/qiandengji/engine/command-usage.ts
function observedCommandUsage(text, observedAt = Date.now()) {
  const match = /^MC_CLI_DETAIL (\{[^\r\n]*\})$/.exec(text.trim());
  if (!match) return null;
  try {
    const value = JSON.parse(match[1]);
    if (!value || value.schemaVersion !== 1 || typeof value.id !== "string" || typeof value.usage !== "string" || !value.usage.startsWith("/mycli ")) return null;
    return { id: value.id, usage: value.usage, observedAt };
  } catch {
    return null;
  }
}
function observedCommandRoot(text, recipient, observedAt = Date.now()) {
  if (!recipient) return null;
  const match = /^MC_SITE_DUNGEON_(?:INFO|STATE) (\{[^\r\n]*\})$/.exec(text.trim());
  if (!match) return null;
  try {
    const value = JSON.parse(match[1]);
    if (!value || value.schemaVersion !== 1 || value.activityType !== "site_dungeon" || value.recipient !== recipient || value.commandRoot !== "/mycli dungeon" || typeof value.id !== "string" || !/^[a-z][a-z0-9_-]{0,63}$/.test(value.id)) return null;
    return { id: "site_dungeon.commandRoot", usage: `${value.commandRoot} <subcommand>`, observedAt };
  } catch {
    return null;
  }
}

// integrations/qiandengji/engine/native-rpg.ts
var object = (value) => !!value && typeof value === "object" && !Array.isArray(value);
var number = (value) => typeof value === "number" && Number.isFinite(value);
var nonnegative = (value) => number(value) && value >= 0;
var points = (value) => Number.isSafeInteger(value) && Number(value) >= 0;
var id = (value) => typeof value === "string" && /^[a-z][a-z0-9_:-]{0,63}$/i.test(value);
function readNativeSkills(value, at, saved = false) {
  if (!object(value) || !Number.isFinite(Date.parse(at))) return null;
  const ids = (values) => Array.isArray(values) && values.length <= 256 && values.every(id) ? [...new Set(values)] : null;
  const available = ids(value.available), common = ids(value.common);
  const learnable = ids(saved ? value.learnable : Array.isArray(value.learnable) ? value.learnable.map((v) => object(v) ? v.id : null) : null);
  if (!available || !common || !learnable || !points(value.skillPoints)) return null;
  const node = (v) => {
    if (!object(v) || !id(v.id) || !points(v.requiredLevel) || !points(v.cost)) return null;
    const bonuses = object(v.permanentBonuses) && Object.keys(v.permanentBonuses).length <= 16 && Object.entries(v.permanentBonuses).every(([key, value2]) => id(key) && number(value2) && Math.abs(value2) <= 1e6) ? { ...v.permanentBonuses } : void 0;
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
function nativeRpgMessage(text) {
  if (text.length > 65536 || !text.startsWith("MC_RPG ") || /[\r\n]/.test(text)) return null;
  try {
    const value = JSON.parse(text.slice(7));
    return object(value) ? value : null;
  } catch {
    return null;
  }
}
function readNativeSkillDetail(value, at) {
  const text = (v, max) => typeof v === "string" && !!v.trim() && v.length <= max && !/[\u0000-\u001f\u007f-\u009f\u00a7]/.test(v);
  if (!object(value) || value.schemaVersion !== 1 || !id(value.id) || !text(value.name, 80) || !text(value.command, 256) || !value.command.startsWith("/mycli ") || !Number.isFinite(Date.parse(at))) return null;
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
    effect: text(value.effect, 1024) ? value.effect : null,
    requires: text(value.requires, 1024) ? value.requires : null,
    available: typeof value.available === "boolean" ? value.available : null
  };
}
function readNativeSkillInvocations(value, at) {
  if (!object(value) || value.schemaVersion !== 1 || value.kind !== "skill_invocations" || value.queryOnly !== true || !Array.isArray(value.entries) || value.entries.length > 64) return null;
  const entries = value.entries.map((entry) => {
    if (object(entry) && object(entry.invocation)) {
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
  if (!object(value)) return void 0;
  const text = (v, max) => typeof v === "string" && v.trim().length > 0 && v.length <= max && !/[\u0000-\u001f\u007f]/.test(v);
  if (!id(value.step) || !id(value.reason) || !text(value.nextAction, 512)) return void 0;
  const command = (v) => text(v, 180) && v.startsWith("/mycli ") ? v : void 0;
  const missing = Array.isArray(value.missing) && value.missing.length <= 12 && value.missing.every((v) => text(v, 120)) ? [...value.missing] : null;
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
function economy(value) {
  if (!object(value) || typeof value.available !== "boolean") return void 0;
  return { available: value.available, balance: value.available && number(value.balance) ? value.balance : null };
}
function mana(current, max) {
  return nonnegative(current) && nonnegative(max) && current <= max ? { current, max } : void 0;
}
function readNativeRpgStatus(value) {
  if (!object(value) || value.authority !== "VortexRPG" || !id(value.class) || !points(value.level) || !nonnegative(value.xp) || !nonnegative(value.nextLevelXp) || !mana(value.mana, value.maxMana) || typeof value.preview !== "boolean" || !economy(value.economy)) return null;
  const next = guidance(value.guide);
  return {
    available: true,
    classId: value.class,
    level: value.level,
    xp: value.xp,
    nextLevelXp: value.nextLevelXp,
    mana: mana(value.mana, value.maxMana),
    economy: economy(value.economy),
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
  if (!object(payload2) || payload2.schemaVersion !== 1 || !object(payload2.profession)) return null;
  const value = payload2.profession;
  if (value.backend !== "vortex" || typeof value.available !== "boolean") return null;
  if (!value.available) return { available: false };
  if (!(value.combat === "" || id(value.combat)) || !points(value.level) || !nonnegative(value.xp) || !points(value.skillPoints) || !(value.activeSkill === "" || id(value.activeSkill))) return null;
  const m = object(value.mana) ? mana(value.mana.current, value.mana.max) : void 0;
  const skillIds = Array.isArray(value.abilities) && value.abilities.length <= 48 && value.abilities.every((a) => object(a) && id(a.id)) ? [...new Set(value.abilities.map((a) => String(a.id).replace(/^mycli:/, "")))] : void 0;
  return {
    available: true,
    classId: value.combat || "none",
    level: value.level,
    xp: value.xp,
    skillPoints: value.skillPoints,
    activeSkill: value.activeSkill,
    ...m ? { mana: m } : {},
    economy: economy(value.economy),
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
  abilitySnapshot = null;
  details = /* @__PURE__ */ new Map();
  signature = "";
  reset() {
    this.profile = null;
    this.learning = null;
    this.skills = null;
    this.abilitySnapshot = null;
    this.details.clear();
    this.signature = "";
  }
  skillDetail(id2) {
    return this.details.get(id2) ?? null;
  }
  hasInvocationInfo(id2) {
    return id2 ? this.details.has(id2) : this.details.size > 0;
  }
  identity() {
    return this.profile ? { available: this.profile.value.available, classId: this.profile.value.classId } : null;
  }
  currentAbilities() {
    if (this.abilitySnapshot && (!this.skills || Date.parse(this.abilitySnapshot.at) >= Date.parse(this.skills.observedAt)))
      return { ...this.abilitySnapshot, source: "mcagent:state.profession" };
    return this.skills ? { ids: this.skills.available, at: this.skills.observedAt, source: "MC_RPG" } : null;
  }
  chat(text, at = (/* @__PURE__ */ new Date()).toISOString()) {
    const value = nativeRpgMessage(text);
    if (!value) return false;
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
      this.abilitySnapshot = null;
      this.details.clear();
    }
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
    if (p.activeSkill !== void 0) fields.push(`\u5F53\u524D\u51C6\u5907\u6280\u80FD ${p.activeSkill || "\u672A\u51C6\u5907"}`);
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
\u804C\u4E1A\u6280\u80FD\u6700\u8FD1\u89C2\u6D4B ${skills.observedAt}\uFF1A\u5B66\u4E60\u5019\u9009 ${JSON.stringify(options ?? skills.learnable.slice(0, 6))}` + (skills.learnable.length > 6 ? `\uFF1B\u53E6\u6709 ${skills.learnable.length - 6} \u9879\u672A\u5C55\u5F00` : "") + "\u3002\u8FD9\u662F\u670D\u52A1\u5668\u6E05\u5355\uFF1B\u7B49\u7EA7\u548C\u5B66\u4E60\u70B9\u6EE1\u8DB3\u4E0D\u4EE3\u8868\u5DF2\u5B66\u4E60\uFF0C\u8BE6\u60C5\u4E0E\u5176\u4ED6\u6761\u4EF6\u6309 skills.info \u56DE\u6267\u6838\u5BF9\u3002" : "") + (available ? "\n[\u804C\u4E1A\u6280\u80FD\u73B0\u8BFB] " + current.source + " " + current.at + "\uFF1B\u804C\u4E1A\u53EF\u7528\uFF1A" + (available.slice(0, 12).join("\u3001") || "\u65E0") + (available.length > 12 ? `\uFF08\u5171${available.length}\u9879\uFF0C\u6458\u8981\u7701\u7565\u5176\u4F59\uFF09` : "") + (this.skills ? "\uFF1B\u5B8C\u6574\u6E05\u5355\u7684\u539F\u89C2\u5BDF\u65F6\u95F4\u8BFB mc_skills" : "\uFF1B\u901A\u7528/\u53EF\u5B66\u4E60\u6E05\u5355\u5C1A\u672A\u8BFB\u53D6") + '\u3002mc_skills \u8BFB\u5B8C\u6574\u5217\u8868\uFF1Bmc_query {"query":"skills.info","arguments":["\u6280\u80FDID"]} \u67E5\u76EE\u6807/\u6548\u679C/\u6D88\u8017\u3002\u5DF2\u5B66\u4E0D\u7B49\u4E8E\u5DF2\u7F16\u6392\uFF0Cmc_combat_tactic \u53EF\u6309\u5F53\u524D\u6761\u4EF6\u7EC4\u5408\uFF1B\u53D1\u9001\u4E0D\u7B49\u4E8E\u751F\u6548\u3002' : "") + ([...this.details.values()].some((d) => d.invocation === "command") ? "\n\u5DF2\u67E5\u4E13\u7528\u5165\u53E3\uFF08\u4E0D\u662F /mycli cast\uFF09\uFF1A" + [...this.details.values()].filter((d) => d.invocation === "command").slice(-4).map((d) => `${d.id} \u2192 ${d.command}\uFF08${d.observedAt}\uFF09`).join("\uFF1B") : "") + (p.guidance ? "\n\u670D\u52A1\u7AEF\u5EFA\u8BAE\u6570\u636E\uFF08\u6CBF\u7528\u672C\u6B21\u72B6\u6001\u89C2\u5BDF\u65F6\u95F4\uFF0C\u672A\u6267\u884C\uFF09\uFF1A" + JSON.stringify(p.guidance) : "");
  }
  /** Connection-local, class-bound list; no disk history, command or learned conclusion. */
  hasCurrentSkills() {
    return !!this.profile?.value.available && !!(this.skills || this.abilitySnapshot);
  }
  skillsReadout(skillId) {
    const detail = skillId ? this.skillDetail(skillId) : null;
    if (detail) return "[\u672C\u8FDE\u63A5\u6280\u80FD\u8BE6\u60C5\uFF1B\u6309\u5B9E\u9645 command \u9009\u62E9\u5DE5\u5177\uFF0C\u672A\u6267\u884C]\n" + JSON.stringify(detail) + (detail.invocation === "command" ? "\n\u8FD9\u662F\u4E13\u7528\u547D\u4EE4\u5165\u53E3\uFF0C\u4E0D\u662F mc_cast \u6280\u80FD\u3002\u7528 mc_do \u7684 chat \u6B65\u9AA4\u53D1\u9001\u660E\u786E\u7684 command\uFF1B\u4E0D\u8981\u628A\u6280\u80FD ID \u6216\u539F\u53C2\u6570\u585E\u8FDB /mycli cast\u3002" : "\nmc_cast \u6309\u6B64 ID \u548C\u670D\u52A1\u7AEF\u53C2\u6570\u65BD\u6CD5\uFF1B\u53D1\u9001\u4E0D\u8BC1\u660E\u6548\u679C\u3002");
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
      ...skillId ? { id: skillId, category } : {},
      ...invocations.length ? { invocations } : {},
      cost: null,
      cooldownRemainingMs: null,
      effectVerified: null
    }) + '\n\u5355\u9879\u6548\u679C/\u76EE\u6807/\u6D88\u8017\u7528 mc_query {"query":"skills.info","arguments":["\u6280\u80FDID"]}\uFF1B\u5F53\u524D\u9B54\u529B/\u51B7\u5374\u548C\u5DF2\u9009\u7EC4\u5408\u8BFB mc_combat_tactic\u3002\u5148\u6309\u5355\u9879 command \u533A\u5206 mc_cast \u65BD\u6CD5\u548C\u4E13\u7528\u547D\u4EE4\uFF1B\u88AB\u52A8\u8282\u70B9\u65E0\u9700\u65BD\u653E\u3002\u89C4\u5219/\u7A0B\u5E8F\u53EF\u7531 Agent \u8BFB\u8BF4\u660E\u540E\u7F16\u6392\uFF1B\u672A\u7F16\u6392\u4E0D\u81EA\u52A8\u65BD\u653E\uFF0C\u5B9E\u9645\u6548\u679C\u67E5\u670D\u52A1\u7AEF\u56DE\u6267\u3002';
  }
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
var object2 = (value) => !!value && typeof value === "object" && !Array.isArray(value);
function nativeDefinition(id2, description, command, argument, matches) {
  return {
    id: id2,
    description,
    argumentsSchema: argument ? subjectArgument : noArguments,
    command: (args) => argument ? args.length === 1 && subjectId.test(args[0]) ? `${command} ${args[0]} --json` : null : args.length === 0 ? `${command} --json` : null,
    matchReply: (text, args, username) => {
      if (!username || (argument ? args.length !== 1 || !subjectId.test(args[0]) : args.length !== 0)) return null;
      const value = nativeRpgMessage(text);
      return value && matches(value, [...args]) ? { data: value, ok: true } : null;
    }
  };
}
function payload(text, marker) {
  if (!text.startsWith(marker + " ")) return null;
  const json = text.slice(marker.length + 1);
  if (/[\r\n]/.test(json)) return null;
  try {
    const value = JSON.parse(json);
    return value && typeof value === "object" && !Array.isArray(value) && value.schemaVersion === 1 ? value : null;
  } catch {
    return null;
  }
}
function dungeonDefinition(kind, marker, description) {
  return {
    id: `dungeon.${kind}`,
    description,
    argumentsSchema: subjectArgument,
    command: (args) => args.length === 1 && subjectId.test(args[0]) ? `/mycli dungeon ${kind} ${args[0]} --json` : null,
    matchReply: (text, args, username) => {
      if (args.length !== 1 || !subjectId.test(args[0]) || !username) return null;
      const value = payload(text, marker);
      if (!value || value.activityType !== "site_dungeon" || value.commandRoot !== "/mycli dungeon" || value.recipient !== username || value.id !== args[0]) return null;
      return { data: value, ok: true };
    }
  };
}
var QIANDENGJI_SERVER_QUERIES = [
  {
    id: "status",
    argumentsSchema: noArguments,
    description: "Read current self status, including Vortex class, RPG level/xp, mana and economy when available. arguments:[] only. Requests --json and matches either the native MC_RPG status shape or legacy MC_STATUS self/name. Native replies have no subject/nonce: the core checks trusted server transport/current connection, not unique request attribution.",
    command: (args) => args.length === 0 ? "/mycli status --json" : null,
    matchReply: (text, args, username) => {
      if (args.length || !username) return null;
      const native = nativeRpgMessage(text);
      if (native && readNativeRpgStatus(native)) return { data: native, ok: true };
      const value = payload(text, "MC_STATUS");
      if (!value || value.kind !== "state" || value.scope !== "self" || value.readOnly !== true || value.name !== username) return null;
      return { data: value, ok: true };
    }
  },
  {
    id: "skills.status",
    argumentsSchema: noArguments,
    description: "Read current self native MC_RPG available/common/learnable skills and skillPoints, preserving complete server fields such as learning cost/requiredLevel. arguments:[] only. Querying never chooses a class, learns/prepares/casts or spends points. No subject/nonce in native replies; current-connection server provenance is checked by the core.",
    command: (args) => args.length === 0 ? "/mycli skills status --json" : null,
    matchReply: (text, args, username) => {
      if (args.length || !username) return null;
      const value = nativeRpgMessage(text);
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
    "profession.status",
    "Read the currently selected class; none means unselected, not an unavailable server. arguments:[] only. Never chooses, changes or resets a class.",
    "/mycli profession status",
    false,
    (value) => typeof value.class === "string" && subjectId.test(value.class) && value.queryOnly === true && !Object.hasOwn(value, "authority")
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
    (value, args) => value.id === args[0] && value.common === true && typeof value.available === "boolean" && typeof value.learned === "boolean" || value.id === args[0] && value.common === true && value.queryOnly === true && typeof value.available === "boolean" && typeof value.name === "string" && typeof value.command === "string" && typeof value.effect === "string" || object2(value.definition) && value.definition.id === args[0] && typeof value.available === "boolean" || object2(value.skill) && value.skill.id === args[0] && value.queryOnly === true && typeof value.learned === "boolean" || object2(value.talent) && value.talent.id === args[0] && value.queryOnly === true && typeof value.learned === "boolean"
  ),
  dungeonDefinition(
    "status",
    "MC_SITE_DUNGEON_STATE",
    'Read a site dungeon state. arguments:["server_observed_id"], one lowercase ASCII ID (letters, digits, underscore or hyphen, max64). Matches the connected recipient and exact dungeon ID. Active/current room, attendance, rewards and lastOutcome remain the server response; no start, join, travel, claim or retry.'
  ),
  dungeonDefinition(
    "info",
    "MC_SITE_DUNGEON_INFO",
    'Read a site dungeon description and entry geometry. arguments:["server_observed_id"], one lowercase ASCII ID (letters, digits, underscore or hyphen, max64). Matches the connected recipient and exact dungeon ID. An info response does not establish a current run, cooldown, room clear or successful travel.'
  )
];

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
    const requestId = randomBytes(16).toString("hex");
    active = { row, hash, requestId, parts: [], size: 0, count: null, started: Date.now() };
    lastStarted = Date.now();
    attempts.set(hash, (attempts.get(hash) ?? 0) + 1);
    bot._client.write("custom_payload", { channel: YSM_ASSET_CHANNEL, data: Buffer.from(JSON.stringify({ type: "get", modelId: row.modelId, sha256: hash, requestId })) });
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
    for (const [uuid, row] of states) if (row.entityId === entity?.id) states.delete(uuid);
  });
  const timer = setInterval(() => {
    for (const [uuid, prior] of states) {
      const row = binding(prior.entityId);
      if (!row || row.playerUuid !== uuid || row.epoch !== prior.epoch) states.delete(uuid);
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
    const uuid = entity?.uuid?.toLowerCase();
    const row = uuid && records.get(uuid);
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
    for (const [uuid, row] of records) if (now() - row.receivedAt > 15e3) {
      records.delete(uuid);
      emit("appearanceRemove", { schemaVersion: 1, playerUuid: uuid });
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
function viewerCastCommand(text) {
  if (typeof text !== "string") return null;
  const match = /^\s*\/mycli\s+cast\s+([a-z0-9_:-]{1,64})(?=\s|$)/i.exec(text);
  if (!match) return null;
  const id2 = match[1].toLowerCase();
  return { id: id2, name: SPELL_NAMES[id2] ?? id2.replaceAll("_", " ") };
}
function viewerCastResult(text, spellId) {
  if (typeof text !== "string" || text.length > 1024) return null;
  const locked = /\bSpell\s+([a-z0-9_:-]+)\s+is not unlocked\b/i.exec(text);
  if (locked) return locked[1].toLowerCase() === spellId.toLowerCase() ? { phase: "failed", detail: "\u6280\u80FD\u672A\u89E3\u9501" } : null;
  if (/\[RPG\].*(?:参数过多|缺少参数|参数无效|用法错误)/u.test(text)) {
    return { phase: "failed", detail: "\u65BD\u6CD5\u53C2\u6570\u88AB\u62D2\u7EDD" };
  }
  if (/(?:not|don't have) enough (?:mana|magic)|insufficient (?:mana|magic)|(?:on |in )?cooldown|you cannot (?:blink|cast|use)|cannot cast|failed to cast|\bno permission\b|魔力不足|灵力不足|冷却中|无法施放|施法失败|未学会|不能在此施法|不可在此施法|没有看得见的怪物|没有可用目标/i.test(text)) {
    return { phase: "failed", detail: "\u65BD\u6CD5\u53D7\u963B" };
  }
  if (spellId === "home" && /传送到|teleported to|you have been teleported/i.test(text)) {
    return { phase: "succeeded", detail: "\u4F20\u9001\u5B8C\u6210" };
  }
  if ((spellId === "selfheal" || spellId === "heal") && /sacred healing restores|治疗成功|恢复了生命/i.test(text)) {
    return { phase: "succeeded", detail: "\u6CBB\u7597\u751F\u6548" };
  }
  if (spellId === "food" && /feel less hungry|饥饿值已恢复|饱食生效/i.test(text)) {
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
  if (successBySpell[spellId]?.test(text)) return { phase: "succeeded", detail: "\u65BD\u6CD5\u751F\u6548" };
  if (/咏唱成功|施法成功|成功施放|successfully cast/i.test(text)) {
    return { phase: "succeeded", detail: "\u65BD\u6CD5\u751F\u6548" };
  }
  return null;
}

// integrations/qiandengji/engine/viewer-state.ts
var finite = (value) => typeof value === "number" && Number.isFinite(value);
var bounded = (value, min, max) => finite(value) ? Math.max(min, Math.min(max, value)) : null;
var VIEWER_STATE_CHANNEL = "mcagent:state";
function manaSnapshotFromText(text) {
  if (typeof text !== "string" || text.length > 512) return null;
  const label = /(?:魔力|法力|\b(?:mana|mp)\b)/iu.exec(text);
  if (!label) return null;
  const part = text.slice(label.index + label[0].length, label.index + label[0].length + 60);
  const pair = /(?:当前|current)?[^\d\n]{0,24}(\d{1,6})\s*\/\s*(\d{1,6})/iu.exec(part);
  if (!pair) return null;
  const current = Number(pair[1]);
  const max = Number(pair[2]);
  return max > 0 && current <= max ? { current, max } : null;
}
function spellCatalogueFromText(text) {
  if (typeof text !== "string" || text.length > 16384 || !/(?:战斗咏唱|探索咏唱)[：:]/u.test(text)) return null;
  const abilities = [];
  for (const match of text.matchAll(/([^、，；：:()（）\s]{1,32})[（(]([a-z][a-z0-9_:-]{0,63})[，,]([^）)]{0,160})[）)]/giu)) {
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
  let text;
  if (typeof raw === "string") text = raw;
  else if (raw instanceof Uint8Array) text = Buffer.from(raw).toString("utf8");
  else if (raw && typeof raw === "object" && "toString" in raw) text = String(raw);
  else return null;
  const start = channel === CHANNEL ? text.indexOf("{") : text.indexOf(PREFIX);
  if (start < 0) return null;
  const jsonStart = text.indexOf("{", start);
  if (jsonStart < 0) return null;
  let obj;
  try {
    obj = JSON.parse(text.slice(jsonStart));
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
var QiandengjiBridge = class extends Bridge {
  constructor(options) {
    super({ ...options, protectionChannel: BREAK_ACL_CHANNEL });
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
  observe(text, uuid) {
    const match = /^MC_(?:STATUS|GUIDE|COMMUNICATION) (\{[^\r\n]*\})$/.exec(text);
    if (!match || !uuid || text.length > 65536) return false;
    try {
      const envelope = JSON.parse(match[1]), p = envelope.communication;
      if (envelope.schemaVersion !== 1 || envelope.playerUuid !== uuid || !Number.isFinite(envelope.observedAt) || !p || p.schema !== "agent-mc/chat-policy/v1") return false;
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
  audience(text, rendered, direction) {
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
    if (text.startsWith(p.shout.prefix)) return { channel: "shout", scope: "server", source: "server-policy", observedAt: p.observedAt };
    return p.defaultChannel === "nearby" ? { channel: "nearby", scope: "same-world-range", radius: p.nearby.radius, source: "server-policy", observedAt: p.observedAt } : { channel: "server-default", scope: p.defaultChannel === "server" ? "server" : "unknown", source: "server-policy", observedAt: p.observedAt };
  }
  brief() {
    const p = this.value;
    if (!p) return this.unknownAt ? "[\u804A\u5929\u9891\u9053\u670D\u52A1\u7AEF\u89C2\u6D4B] " + this.unknownAt + "\uFF1B\u5F53\u524D\u9891\u9053\u63D0\u4F9B\u65B9\u6216\u8303\u56F4\u672A\u77E5\uFF0C\u4E0D\u6CBF\u7528\u65E7\u8303\u56F4\uFF1B\u672A\u81EA\u52A8\u6539\u7528\u558A\u8BDD\u6216\u79C1\u804A\u3002" : "";
    const permission = (value) => value === true ? "\u672C\u4EBA\u5DF2\u83B7\u6743\u9650" : value === false ? "\u672C\u4EBA\u65E0\u6743\u9650" : "\u672C\u4EBA\u6743\u9650\u672A\u77E5";
    return "[\u804A\u5929\u9891\u9053\u670D\u52A1\u7AEF\u89C2\u6D4B] " + p.observedAt + "\uFF1B\u666E\u901A\u6587\u5B57\uFF1A" + (p.defaultChannel === "nearby" ? `\u540C\u4E00\u5B9E\u9645\u4E16\u754C\u9644\u8FD1 ${p.nearby.radius} \u683C` : p.defaultChannel === "server" ? "\u670D\u52A1\u5668\u8303\u56F4" : "\u9ED8\u8BA4\u8303\u56F4\u672A\u77E5") + `\uFF1B${p.shout.prefix}\u5185\u5BB9\u4E3A\u5355\u6B21\u5168\u670D\u558A\u8BDD\uFF08${permission(p.permissions.shout)}\uFF09\uFF1B\u79C1\u804A\uFF1A${permission(p.permissions.private)}` + (p.privateCommand ? `\uFF0C\u670D\u52A1\u7AEF\u547D\u4EE4 ${p.privateCommand}` : "\uFF0C\u5F53\u524D\u547D\u4EE4\u672A\u77E5") + (p.permissions.private === false ? "\uFF0C\u4E0D\u8981\u91CD\u590D\u5C1D\u8BD5\u65E0\u6743\u9650\u79C1\u804A" : "") + "\u3002@\u540D\u5B57\u4E0D\u6269\u5927\u8303\u56F4\uFF1B\u4F20\u8F93\u6210\u529F\u4E0D\u8BC1\u660E\u6536\u5230\u3001\u542C\u89C1\u6216\u5DF2\u8BFB\u3002";
  }
};

// integrations/qiandengji/engine/combat-spells.ts
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
  reset() {
    super.reset();
    this.unlockDenials.clear();
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
  noteServerMessage(text, now = Date.now()) {
    const attempt = this.casts.at(-1);
    const result = attempt && viewerCastResult(text, attempt.spell);
    if (attempt && now - Date.parse(attempt.sentAt) >= 0 && now - Date.parse(attempt.sentAt) <= 3e3 && !attempt.reply && result) {
      attempt.reply = text.slice(0, 240);
      attempt.replyAt = new Date(now).toISOString();
      if (result.detail === "\u6280\u80FD\u672A\u89E3\u9501") {
        this.unlockDenials.set(attempt.spell, now);
        if (this.unlockDenials.size > 128) this.unlockDenials.delete(this.unlockDenials.keys().next().value);
        this.available.delete(attempt.spell);
        this.serverReadyAt.delete(attempt.spell);
      }
    }
    const reportedMana = manaSnapshotFromText(text);
    if (reportedMana) this.noteMana(reportedMana.current, now);
    if (/^(?:战斗咏唱|探索咏唱)[：:]/.test(text)) {
      for (const match of text.matchAll(/[（(]([a-z][a-z0-9_:-]*)[，,]([^）)]*)[）)]/gi)) {
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
    if (/魔力不足|灵力不足|not enough (?:mana|magic)|insufficient (?:mana|magic)/i.test(text)) {
      if (this.pending && now - this.pending.at <= 3e3) {
        const required = /需要\s*(\d+)/.exec(text);
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
    } else if (this.pending && now - this.pending.at <= 3e3 && /冷却中|cooldown|无法施放|施法失败|cannot cast|failed to cast/i.test(text)) {
      this.pending = null;
    }
    if (attempt?.replyAt === new Date(now).toISOString() && result?.phase === "failed") this.pending = null;
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
  const detachCommands = observeViewerCastCommands(bot, (text) => {
    sentAt = viewerCastCommand(text)?.id === "flight" ? Date.now() : null;
  });
  const message = (value, position) => {
    if (position !== "system" || sentAt === null) return;
    const elapsed = Date.now() - sentAt;
    if (elapsed < 0 || elapsed > 3e3) {
      reset();
      return;
    }
    const text = value.toString().trim();
    const result = viewerCastResult(text, "flight");
    if (result?.phase === "failed") {
      reset();
      return;
    }
    const duration = /^[✦\s]*飞行术持续\s*(\d+(?:\.\d+)?)\s*秒[；;]/u.exec(text);
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
function trialBodyState(text, selfUuid, currentlyDowned) {
  if (text.length > 1024 || !/^MC_TRIAL_RESCUE(?: [a-zA-Z]+=[^\s]+)+$/.test(text)) return null;
  const fields = {};
  for (const field of text.split(" ").slice(1)) {
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
}, SERVER_QUERY_DECLARATION];
var QiandengjiEngine = class extends TacticalMinecraftWorld {
  selfHealAvailable = false;
  combatSpells;
  arenaFloor = null;
  observedCommands = new ObservedCommandCatalog();
  nativeRpg = new NativeRpgState();
  chatPolicy = new ChatPolicyState();
  constructor(options) {
    const tactics = new CombatSpells(new combat_tactics_exports.CombatTacticBook(options.dataDir ? join(options.dataDir, "minecraft-combat-tactics.json") : null));
    super(options, tactics);
    this.combatSpells = tactics;
  }
  battlefieldChannel() {
    return BATTLEFIELD_CHANNEL;
  }
  serverQueryDefinitions() {
    return QIANDENGJI_SERVER_QUERIES;
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
          nativeSkillRouteObserved: this.nativeRpg.hasInvocationInfo(typeof args.id === "string" ? args.id : void 0)
        }
      }) }
    ];
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
      this.tryAutoSelfHeal(bot);
      return;
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
  extensionLowHealth(bot) {
    this.tryAutoSelfHeal(bot);
  }
  extensionMessage(text) {
    if (parseProtectReply(text)) return true;
    const bot = this.bridge?.bot;
    const body = trialBodyState(
      text,
      bot?.player?.uuid ?? bot?._client?.uuid,
      this.bodyInhibitReason === TRIAL_DOWNED_REASON
    );
    if (body) {
      this.setBodyInhibited(body === "downed" ? TRIAL_DOWNED_REASON : null, body === "downed" ? "downed" : null);
      return true;
    }
    this.combatSpells.noteServerMessage(text);
    if (/^(?:可用咏唱|守护\/恢复)[：:]/.test(text)) this.selfHealAvailable = /\bselfheal\b/i.test(text);
    const match = /(?:进入第|已恢复第|^第)\s*(\d+)\s*\/\s*(\d+)\s*层(?=[：:试炼]|$)/.exec(text);
    if (match) this.arenaFloor = { floor: Number(match[1]), total: Number(match[2]) };
    if (/第\s*(\d+)\s*\/\s*\1\s*层已通关/.test(text)) this.arenaFloor = null;
    return false;
  }
  extensionServerFeedback(text) {
    this.chatPolicy?.observe(text, this.bridge?.bot?.player?.uuid ?? this.bridge?.bot?._client?.uuid);
    if (text.startsWith("MC_RPG ") && this.nativeRpg.chat(text)) this.publishNativeRpg();
    const usage = observedCommandUsage(text) ?? observedCommandRoot(text, this.bridge?.bot?.username);
    if (usage) this.observedCommands.note(usage);
  }
  requestFacts() {
    const facts = super.requestFacts(), parts = [
      { key: "nativeRpg", text: this.nativeRpg.brief() },
      { key: "communication", text: this.chatPolicy.brief() }
    ].filter((p) => p.text);
    if (!facts || !parts.length) return facts;
    return {
      ...facts,
      text: facts.text + "\n" + parts.map((p) => p.text).join("\n"),
      ...facts.parts ? { parts: [...facts.parts, ...parts] } : {}
    };
  }
  extensionChatAudience(text, rendered, direction = "outgoing") {
    return this.chatPolicy.audience(text, rendered, direction);
  }
  publishNativeRpg() {
    const text = this.nativeRpg.brief();
    if (text) this.emit("minecraft.event", text, false, {
      trigger: "piggyback",
      meta: { nativeRpgObservation: true, nativeRpgProfile: this.nativeRpg.identity() }
    });
  }
  extensionImportantMessage(text) {
    return /可用咏唱|可学习|魔力|命格|探矿|selfheal|healing restores|full health/i.test(text);
  }
  extensionSpawn(bot) {
    super.extensionSpawn(bot);
    this.selfHealAvailable = false;
    this.arenaFloor = null;
    this.extensionRespawn();
    const generation = this.connectionGeneration;
    setTimeout(() => {
      if (this.shuttingDown || this.bridge?.bot !== bot || generation !== this.connectionGeneration) return;
      for (const command of ["/mycli status --json", "/mycli skills status --json"]) {
        try {
          bot.chat(command);
        } catch (error) {
          this.diag.write({ lane: "link", event: "native-rpg-sync-send-failed", msg: String(error) });
          break;
        }
      }
    }, 1500).unref();
  }
  extensionRespawn() {
    this.nativeRpg.reset();
    this.chatPolicy.reset();
    const mana2 = this.bridge?.agentManaState;
    if (mana2 !== void 0) this.combatSpells.noteMana(mana2?.current ?? null);
  }
  attachExtension(bot) {
    this.nativeRpg.reset();
    this.chatPolicy.reset();
    this.observedCommands.clear();
    watchAgentFriendFlight(bot);
    bot.on("physicsTick", () => {
      if (!this.shuttingDown) this.tryAutoCombatSpell(bot);
    });
    bot.on("death", () => {
      this.arenaFloor = null;
      this.combatSpells.noteMana(null);
    });
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
    return portableStorageMisuseNote(this.bridge?.bot ?? null, steps);
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
  NativeRpgState,
  QIANDENGJI_CAST_TOOL,
  SERVER_TOOLS,
  TRIAL_DOWNED_REASON,
  VIEWER_STATE_CHANNEL,
  createEngine,
  createQiandengjiCastTool,
  invokeQiandengjiCast,
  nativeRpgMessage,
  observedCommandRoot,
  observedCommandUsage,
  parseSkillsPayload,
  readNativeRpgPacket,
  readNativeRpgStatus,
  readNativeSkillDetail,
  readNativeSkillInvocations,
  readNativeSkills,
  trialBodyState
};
