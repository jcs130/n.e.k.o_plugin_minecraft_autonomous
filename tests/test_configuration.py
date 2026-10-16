def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["version"] == "0.5.7-dev.20261017.3"
    assert SOURCE["source_revision"] == "41bed34ac5a3c1a73bb0be2f2457b260d7f2c47e"
    assert SOURCE["sha256"] == "dad654b22683f7a0ffa265948ac7ca8bfbd62d8f071827196abf8f368c59fce4"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.1.78"
