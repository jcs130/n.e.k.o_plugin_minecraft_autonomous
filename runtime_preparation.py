"""User-initiated Market resource preparation, using the canonical installer."""

import asyncio
import copy
import os
import platform
import re
import sys
import threading
from pathlib import Path

from agent_mc_autonomy.configuration import Settings
from agent_mc_autonomy.ownership import session_is_owned
from agent_mc_autonomy.runtime_bundle.download import ReleaseBundle, prepare_release
from agent_mc_autonomy.runtime_bundle.manifest import read_json
from plugin.sdk.plugin import Err, Ok, plugin_entry, ui

from .prepared_runtime import resolve_host_runtime

RESOURCE = Path(__file__).with_name("runtime-download.json")
SELECTION = {
    "backend": ("node", "directory"),
    "viewer": ("renderer_directory", "catalog_file", "bundled_appearance_catalog_file", "url"),
    "runtime": ("mode", "bundle_root", "bundle_manifest_sha256"),
}
ERRORS = {
    "download_network_failed": "下载连接中断。可点击重试；也可使用同版本完整离线包。",
    "download_http_failed": "组件下载暂不可用。请稍后重试，或使用同版本完整离线包。",
    "download_disk_space": "本机可用空间不足，需为下载、解压和完整安装预留空间。清理空间后重试。",
    "download_hash_or_size_mismatch": "下载未通过完整性校验，未安装。请重试。",
    "download_size_mismatch": "下载大小不符合当前版本，未安装。请重试。",
    "download_cancelled": "已取消准备；原账号、模型和运行环境保持。",
}


def selection(raw):
    return {section: {key: raw.get(section, {}).get(key) for key in keys} for section, keys in SELECTION.items()}


def managed(raw):
    """Only defaults or a known short-cache installation may be selected by this action."""
    if any(not isinstance(raw.get(key, {}), dict) for key in SELECTION):
        return False
    if (
        raw.get("runtime", {}).get("mode") == "external"
        or raw.get("viewer", {}).get("url")
        or raw.get("backend", {}).get("provider") == "java-client"
    ):
        return False
    root = raw.get("runtime", {}).get("bundle_root")
    if not root:
        return not any(
            raw.get(section, {}).get(key) for section, keys in SELECTION.items() for key in keys if section != "runtime"
        )
    sha = raw.get("runtime", {}).get("bundle_manifest_sha256", "")
    local = os.environ.get("LOCALAPPDATA", "")
    if not local or not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{64}", sha):
        return False
    expected = Path(local) / "AgentMCWorld/installations" / ("r-" + sha[:32]) / "runtime"
    if Path(root).resolve() != expected.resolve():
        return False
    allowed = {
        "node": Path(root) / "node/node.exe",
        "directory": Path(root) / "backend",
        "renderer_directory": Path(root) / "viewer/modern-viewer/renderer-src",
        "catalog_file": Path(root).parent / "viewer-catalog.json",
        "bundled_appearance_catalog_file": Path(root) / "resources/appearances/catalog.json",
    }
    return all(
        not raw.get(section, {}).get(key) or Path(raw[section][key]).resolve() == allowed[key].resolve()
        for section in ["backend", "viewer"]
        for key in SELECTION[section]
        if key != "url"
    )


def supported():
    return sys.platform == "win32" and platform.machine().lower() in {"amd64", "x86_64"}


class RuntimePreparation:
    def _setup_active(self):
        task = getattr(self, "_runtime_setup_task", None)
        return task is not None and not task.done()

    def _resource_spec(self):
        return ReleaseBundle.parse(read_json(RESOURCE, 65536))

    def runtime_setup_state(self):
        try:
            spec = self._resource_spec()
            metadata = {"available": supported(), "total_bytes": spec.bytes}
        except (OSError, ValueError):
            metadata = {"available": False}
        with self._control_lock:
            return {
                **metadata,
                "phase": "idle",
                **copy.deepcopy(getattr(self, "_runtime_setup_state", {})),
                "active": self._setup_active(),
            }

    def _setup_progress(self, row):
        with self._control_lock:
            self._runtime_setup_state = row

    def _setup_idle(self, raw):
        if not managed(raw):
            raise ValueError("custom_runtime")
        if self._worker and self._worker.snapshot().get("worker_alive"):
            raise ValueError("runtime_active")
        settings = Settings.parse(raw)
        host = settings.data_root(self.data_path()) / "sessions" / settings.identity / "host"
        if session_is_owned(host):
            raise ValueError("runtime_active")
        state = host / "host-state.json"
        if state.exists():
            snapshot = read_json(state, 256 * 1024)
            if snapshot.get("uncertain") or snapshot.get("pending") or snapshot.get("inflight_request"):
                raise ValueError("runtime_unsettled")

    @ui.action(label="准备游戏组件", tone="primary")
    @plugin_entry(
        id="prepare_runtime",
        name="准备或更新游戏组件",
        kind="service",
        description="用户显式准备当前版本的完整游戏组件。下载并校验固定公开资源；保留账号和模型，不启动游戏或调用模型。",
    )
    async def prepare_runtime(self, **_):
        try:
            if self._setup_active():
                return Ok(self.runtime_setup_state())
            if not supported():
                return Err(
                    {
                        "code": "runtime_setup_platform",
                        "message": "此一键组件适用于 Windows x64；其它平台请配置自己的运行环境。",
                    }
                )
            raw = await self.config.dump()
            with self._control_lock:
                if self._setup_active():
                    return Ok(self.runtime_setup_state())
                self._setup_idle(raw)
                spec = self._resource_spec()
                effective, state = resolve_host_runtime(raw)
                if (
                    state == "prepared"
                    and effective.get("runtime", {}).get("bundle_manifest_sha256") == spec.manifest_sha256
                ):
                    self._setup_progress({"phase": "ready"})
                    return Ok(self.runtime_setup_state())
                self._runtime_setup_cancel = threading.Event()
                self._setup_progress({"phase": "preparing", "downloaded_bytes": 0, "total_bytes": spec.bytes})
                self._runtime_setup_task = asyncio.create_task(self._run_runtime_setup(raw, spec))
            return Ok(self.runtime_setup_state())
        except (OSError, ValueError, KeyError) as error:
            code = str(error).split(":", 1)[0]
            return Err(
                {
                    "code": "runtime_setup_not_started",
                    "message": {
                        "custom_runtime": "当前使用自定义或外部运行环境，不会自动接管。请保留原配置，或在高级设置中明确选择完整组件。",
                        "runtime_active": "请先停止游玩并等待动作收尾，再准备组件。",
                        "runtime_unsettled": "原动作尚未结算或存在未知回执，未更换运行环境。请先核对运行状态。",
                    }.get(code, "当前版本的组件目录不可用，未开始下载；请使用同版本完整离线包。"),
                }
            )

    async def _run_runtime_setup(self, original, spec):
        write_started = False
        try:
            cache = Path(os.environ["LOCALAPPDATA"]) / "AgentMCWorld/downloads"
            bundle = await asyncio.to_thread(
                prepare_release, spec, cache, progress=self._setup_progress, cancelled=self._runtime_setup_cancel
            )
            latest = await self.config.dump()
            with self._control_lock:
                self._setup_idle(latest)
                if selection(latest) != selection(original):
                    raise ValueError("selection_changed")
                if self._runtime_setup_cancel.is_set():
                    raise ValueError("runtime_bundle_download_cancelled")
                self._configuration_writes += 1
            try:
                write_started = True
                await self.config.update(
                    {
                        "runtime": {"bundle_root": str(bundle.root), "bundle_manifest_sha256": bundle.manifest_sha256},
                        "backend": {"node": str(bundle.node), "directory": str(bundle.backend)},
                        "viewer": {
                            "renderer_directory": str(bundle.renderer),
                            "catalog_file": str(bundle.catalog),
                            "bundled_appearance_catalog_file": str(bundle.appearances),
                        },
                    }
                )
            finally:
                with self._control_lock:
                    self._configuration_writes -= 1
            self._setup_progress({"phase": "ready"})
        except Exception as error:
            code = str(error).split(":", 1)[0].removeprefix("runtime_bundle_")
            message = (
                "组件已校验，但配置保存结果需要核对。请先刷新页面确认状态；未自动开始游戏。"
                if write_started
                else ERRORS.get(
                    code, "组件准备未完成，未替换原运行环境。可重试或使用完整离线包；若仍失败请检查安装与资源详情。"
                )
            )
            self._setup_progress(
                {"phase": "cancelled" if code == "download_cancelled" else "failed", "message": message}
            )

    @plugin_entry(
        id="cancel_runtime_preparation",
        name="取消组件准备",
        kind="service",
        description="只取消本插件的组件准备任务；不会发送游戏命令、清空原生队列或删除旧资源。",
    )
    async def cancel_runtime_preparation(self, **_):
        if self._setup_active():
            self._runtime_setup_cancel.set()
        return Ok(self.runtime_setup_state())

    async def _close_runtime_setup(self):
        if self._setup_active():
            self._runtime_setup_cancel.set()
            await self._runtime_setup_task
