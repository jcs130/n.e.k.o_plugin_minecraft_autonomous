def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "5e9405067bd1eda4a23abc06f6b70383154c9408"
    assert SOURCE["version"] == "0.5.7-rc.154"
    assert SOURCE["source_revision"] == "a74b8bde7834c694bf85d7a61c3fb69460fb81a2"
    assert SOURCE["sha256"] == "3d6c08f6f54e4ef9e84898c91cbcd3ece7f05bf93055cc5769ea7f676764d564"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.144"
