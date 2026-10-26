def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "8b89927db49c9547a50029f039cbfe534d38e78b"
    assert SOURCE["version"] == "0.5.7-rc.107"
    assert SOURCE["source_revision"] == "5f8f5166ff9ac2ee65f96088af204f551e50b286"
    assert SOURCE["sha256"] == "1949e498fa3ef5fa121bbf45a50b93ed9dea2a00c95dae9fc14fe7cedc96eb54"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.109"
