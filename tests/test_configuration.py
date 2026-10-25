def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "8b89927db49c9547a50029f039cbfe534d38e78b"
    assert SOURCE["version"] == "0.5.7-rc.90"
    assert SOURCE["source_revision"] == "073448ab341740cb540234c88af3e68ba44ec4f5"
    assert SOURCE["sha256"] == "0aca100e7752357fbf48b331549260a98e86557a31a95ed95f76a2c95652eccc"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.100"
