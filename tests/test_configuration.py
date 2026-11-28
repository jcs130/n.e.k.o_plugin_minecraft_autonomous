def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "41e3e52f24fc5776ce59b322a547e0e7a38cdd5e"
    assert SOURCE["version"] == "0.5.7-rc.160-preview.159"
    assert SOURCE["source_revision"] == "c614dd64e58891b905c347e81cacb406ecdecc7b"
    assert SOURCE["sha256"] == "25aa4ca94497246df6237b77be07fa70bd6794201556de7378a1cb5f9c07c342"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.161"
