def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "b99464bb7efce76dedb00471605019932b1e8d7e"
    assert SOURCE["version"] == "0.5.7-rc.121"
    assert SOURCE["source_revision"] == "4556b9ec06d6e63d9a44ec51a054b0970111d3de"
    assert SOURCE["sha256"] == "e7d7868fb9296607ceb8e94638804fddc6fc3d0f3101035f53f1710995e5860f"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.120"
