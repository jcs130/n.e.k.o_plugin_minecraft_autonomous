def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "b99464bb7efce76dedb00471605019932b1e8d7e"
    assert SOURCE["version"] == "0.5.7-rc.118"
    assert SOURCE["source_revision"] == "d4d294ac17e4233e98a6789eb422d8b72c2a1807"
    assert SOURCE["sha256"] == "c874ae8cf9b2093c926ae4f5a4d4e05df991348c54f2ad70e5d0a9bfc7323467"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.118"
