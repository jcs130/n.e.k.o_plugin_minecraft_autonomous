def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["version"] == "0.5.7-rc.5"
    assert SOURCE["source_revision"] == "78b67164f6fe64bb1e271e43901fc45ed7a760c8"
    assert SOURCE["sha256"] == "f5653b38a0d86314a22eaceaa5445acfa5b441ae2c206a76ce742d04e4920745"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.1.82"
