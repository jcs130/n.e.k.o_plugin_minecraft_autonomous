def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "8b89927db49c9547a50029f039cbfe534d38e78b"
    assert SOURCE["version"] == "0.5.7-rc.95"
    assert SOURCE["source_revision"] == "c798963bcd2aa8437fd918b78892b2dbd2aed91d"
    assert SOURCE["sha256"] == "e1108da2ecd41c30ebd0e04b4096081186036b83fdec907bc0cb3c0d66f97bb9"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.101"
