import { Accordion, Stack, Grid, Field, Input, Select, Text, Button } from "@neko/plugin-ui"

const booleans = [
  ["combat","enabled","主动近身战斗"], ["reflex","fightBack","受击反击"],
  ["reflex","antiDrown","防溺水反射"], ["reflex","antiLava","避开熔岩反射"],
  ["journey","enabled","旅途中的停留与发现"], ["idle","enabled","空闲小动作"],
  ["idle","allowMovement","空闲时允许移动"], ["idle","afterArrival","到达后的空闲动作"],
  ["visual","background","后台获取图像"],
]
const numbers = [
  ["perception","entityRange","实体感知距离（格，1–64）",64],
  ["perception","nearbyOccludedRange","附近遮挡实体提示距离（格，0–16）",8],
  ["reflex","fleeHealth","脱战生命阈值",10], ["reflex","reactCooldownSec","受击反应间隔（秒）",8],
  ["combat","engageRadius","交战半径（格）",3], ["combat","chaseMax","追击距离（格）",6],
  ["combat","maxSec","单次战斗时长（秒）",30], ["combat","space","近战间距（格）",2.6],
  ["combat","busyRatio","战斗占比上限（%）",60], ["combat","cooldownSec","过度战斗后休息（秒）",60],
  ["journey","choiceMinBlocks","旅途最短分段（格）",10], ["journey","choiceMaxBlocks","旅途最长分段（格）",20],
  ["journey","dangerChoiceMaxBlocks","危险时最长分段（格）",5],
  ["idle","minIdleMs","空闲动作等待（毫秒）",6000], ["idle","minIntervalMs","空闲动作最短间隔（毫秒）",12000],
  ["idle","maxIntervalMs","空闲动作最长间隔（毫秒）",28000],
  ["show","clickMs","容器点击间隔（毫秒）",400], ["show","dwellOpenMs","开窗停留（毫秒）",800],
  ["show","dwellResultMs","结果停留（毫秒）",1200], ["show","dwellCloseMs","关窗停留（毫秒）",600],
  ["show","reopenGapMs","再次开窗间隔（毫秒）",900], ["show","budgetMs","容器演出总预算（毫秒）",12000],
]

export default function NativeControls({value = {}, onChange}: {value:any,onChange:(v:any)=>void}) {
  const set = (group:string,key:string,next:any) => {
    const updated = {...value,[group]:{...value[group]}}
    if (next === undefined) delete updated[group][key]
    else updated[group][key] = next
    if (!Object.keys(updated[group]).length) delete updated[group]
    onChange(updated)
  }
  return <Accordion open={false} title="MC 核心行为（通常无需修改）"><Stack gap={10}>
    <Text>留空或“跟随核心”沿用当前核心默认值。只在下次显式启动生效；不改变服务器权限、碰撞、未知回执或库存保护。</Text>
    <Grid cols={2}>
      <Field label="实体感知视角"><Select value={value.perception?.entityView??"default"}
        options={[{value:"default",label:"跟随核心（推荐）"},{value:"surroundings",label:"周边感知"},{value:"camera",label:"镜头范围"}]}
        onChange={v=>set("perception","entityView",v==="default"?undefined:v)} /></Field>
      {booleans.map(([group,key,label])=><Field key={`${group}.${key}`} label={label}>
        <Select value={value[group]?.[key] === undefined?"default":String(value[group][key])}
          options={[{value:"default",label:"跟随核心（推荐）"},{value:"true",label:"开启"},{value:"false",label:"关闭"}]}
          onChange={v=>set(group,key,v==="default"?undefined:v==="true")} />
      </Field>)}
      {numbers.map(([group,key,label,standard])=><Field key={`${group}.${key}`} label={String(label)}>
        <Input type="number" value={value[group]?.[key]??""} placeholder={`跟随核心（当前 ${standard}）`}
          onChange={v=>set(String(group),String(key),String(v)===""?undefined:Number(v))} />
      </Field>)}
      <Field label="寻路垫脚方块（英文 ID，逗号分隔）"><Input value={value.scaffold_blocks?.join(", ")??""}
        placeholder="跟随核心：dirt, cobblestone" onChange={v=>{
          const updated={...value}; if(!v.trim())delete updated.scaffold_blocks
          else updated.scaffold_blocks=v.split(",").map(s=>s.trim())
          onChange(updated)
        }} /></Field>
    </Grid>
    <Button onClick={()=>onChange({})}>全部跟随核心默认值</Button>
  </Stack></Accordion>
}
