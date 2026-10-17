def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "1e2a9cb9e925e8a65b33e16412ab20ee331eda67"
    assert SOURCE["version"] == "0.5.7-rc.9"
    assert SOURCE["source_revision"] == "44f37d032abf44f425c2232766449abf0aa707b3"
    assert SOURCE["sha256"] == "9d717dac04ce00fd0f732e1527030599ddaef8af9a0f2ef9cd9f2975240f7f8e"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.6"
