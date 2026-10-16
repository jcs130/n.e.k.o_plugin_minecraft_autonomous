def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["version"] == "0.5.7-dev.20261016.39"
    assert SOURCE["source_revision"] == "3ee62ca25b60693132f7b7b8ae6bac3df7ad452f"
    assert SOURCE["sha256"] == "44c161edb81aad330aef57933716b31d329eb11506d6ba8e0b6c322f57285b56"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.1.77"
