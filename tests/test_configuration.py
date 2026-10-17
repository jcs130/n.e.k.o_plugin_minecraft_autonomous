def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["version"] == "0.5.7-rc.3"
    assert SOURCE["source_revision"] == "bfa3882fc8f6e93d7bedd453127c91488852fd9b"
    assert SOURCE["sha256"] == "1a91d462a5b88c91d43c09a14c3b87370a2c9f56d099184948f4ff977705a3f4"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.1.81"
