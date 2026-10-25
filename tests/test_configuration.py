def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "8b89927db49c9547a50029f039cbfe534d38e78b"
    assert SOURCE["version"] == "0.5.7-rc.89"
    assert SOURCE["source_revision"] == "3b612556a4844a220ae830e2169eca3828944835"
    assert SOURCE["sha256"] == "08f88d402bf7c1d1a79fc036dbf808ecf52575420df704759155ae92930b7148"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.99"
