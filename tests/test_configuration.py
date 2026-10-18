def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "1cbd5574660c99a6c72a55224e84f4460778fd6a"
    assert SOURCE["version"] == "0.5.7-rc.34"
    assert SOURCE["source_revision"] == "ba4867dd26dc94d09acde0c486dfe557113d288e"
    assert SOURCE["sha256"] == "170d03c658d95ae515dad55fcd407516b26f1357d308f79a040361cc2474336a"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.31"
