def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "16263531586d8ce6ceca561757f4b75806d50855"
    assert SOURCE["version"] == "0.5.7-rc.11"
    assert SOURCE["source_revision"] == "28f771957e0d0f2c3d72f7245c6d388d0120613f"
    assert SOURCE["sha256"] == "b30c8bc2a260fa0b9a834876580ce33e0107d9cb812562374e8141a95d9db414"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.7"
