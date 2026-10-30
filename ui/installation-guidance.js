const backend = {
  version_matches_not_integrity_verified: '版本匹配；仍须完整性校验',
  version_mismatch: '版本不匹配，请安装要求的核心版本',
  metadata_unavailable: '元数据暂不可用，请检查后端目录',
};
const viewer = {
  text_only: '未配置本地渲染器与资源；可查看文字观测',
  renderer_catalog_pair_required: '渲染器与资源 catalog 须一起配置',
  renderer_missing: '本地渲染器缺失，请检查目录',
  catalog_invalid_or_missing: '本地资源 catalog 缺失或无效',
  catalog_version_missing_or_ambiguous: 'catalog 中缺少唯一匹配的版本资源',
  version_resources_invalid_or_missing: '本地版本资源缺失或无效',
  metadata_matches_ready_to_attempt_rendering: '本地元数据匹配；实际画面仍待核验',
};
const known = (table, code) => Object.hasOwn(table, code) ? table[code] : '状态暂不可用，请检查配置与安装说明';
const prepared = {
  prepared: '完整离线运行环境已准备；显式启动时校验完整性。',
  missing: '首次使用请点击“准备游戏组件”。插件会下载并校验当前版本的运行环境、画面和声音；无需填写路径或执行命令。',
  incompatible: '当前版本需要匹配的游戏组件。请停止游玩后点击“准备游戏组件”；保留账号、模型和游戏数据。',
  custom: '正在使用明确配置的自定义运行环境；不会混入离线包默认路径。',
  external: '外部观察模式：运行环境由独立执行器管理。',
};
export function preparationView(installation) {
  const setup=installation?.setup||{};
  const labels={idle:'准备游戏组件',preparing:'正在准备组件',downloading:'正在下载游戏组件',
    downloaded:'下载完成，正在校验',extracting:'正在解压游戏组件',verifying:'正在完整校验',
    installing:'正在安装游戏组件',ready:'游戏组件已就绪',failed:'组件准备未完成',cancelled:'已取消组件准备'};
  const value=setup.phase==='extracting'?setup.files:setup.downloaded_bytes;
  const total=setup.phase==='extracting'?setup.total_files:setup.total_bytes;
  const measured=['downloading','extracting'].includes(setup.phase)&&Number.isFinite(value)&&value>=0&&Number.isFinite(total)&&total>0;
  return {available:setup.available===true,active:setup.active===true,phase:setup.phase||'idle',
    label:Object.hasOwn(labels,setup.phase)?labels[setup.phase]:labels.idle,
    button:['failed','cancelled'].includes(setup.phase)?'重试准备游戏组件':'准备游戏组件',
    progress:measured?Math.min(100,Math.floor(value/total*100)):null,
    size:Number.isFinite(setup.total_bytes)&&setup.total_bytes>0?`${(setup.total_bytes/1024**3).toFixed(2)} GB`:'',
    message:typeof setup.message==='string'?setup.message:''};
}
export function preparedRuntimeSelection(settings, installation) {
  const oldBundle=installation?.prepared_runtime==='incompatible'&&!!settings?.runtime?.bundle_root;
  const missingCustom=installation?.prepared_runtime==='custom'&&['metadata_unavailable','version_mismatch'].includes(installation?.backend);
  if ((!oldBundle&&!missingCustom)||settings?.runtime?.mode==='external'||settings?.viewer?.url
      ||settings?.backend?.provider==='java-client') return null;
  return {
    backend:{node:'',directory:''},
    viewer:{renderer_directory:'',catalog_file:'',bundled_appearance_catalog_file:''},
    runtime:{bundle_root:'',bundle_manifest_sha256:''},
  };
}
export function startPreparationRequired(installation) {
  if (installation?.prepared_runtime==='external') return false;
  return ['missing','incompatible'].includes(installation?.prepared_runtime)
    ||installation?.backend!=='version_matches_not_integrity_verified';
}
export function installationGuidance(installation, external, viewerUrl) {
  return {
    preparedRuntime: known(prepared, installation?.prepared_runtime),
    backend: known(backend, installation?.backend),
    localResources: known(viewer, installation?.viewer),
    externalView: external || !!viewerUrl
      ? '实际渲染器与资源由外部执行器管理；请在实际观战页面核验画面、资源和角色绑定。'
      : '未配置观战时可使用文字模式；请按安装说明准备匹配资源。',
  };
}
