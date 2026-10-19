def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "1cbd5574660c99a6c72a55224e84f4460778fd6a"
    assert SOURCE["version"] == "0.5.7-rc.42"
    assert SOURCE["source_revision"] == "25cf75bac93a8ca8afc20b7f0db2e769869ba364"
    assert SOURCE["sha256"] == "286a3e89fdb626fa6c2373cdd9697023686024fa5fea628638c9a88636580752"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.40"
