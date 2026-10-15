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
export function installationGuidance(installation, external, viewerUrl) {
  return {
    backend: known(backend, installation?.backend),
    localResources: known(viewer, installation?.viewer),
    externalView: external || !!viewerUrl
      ? '实际渲染器与资源由外部执行器管理；请在实际观战页面核验画面、资源和角色绑定。'
      : '未配置观战时可使用文字模式；请按安装说明准备匹配资源。',
  };
}
