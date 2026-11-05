def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "97e76665b501c2fc50ffa3f46c96b3d3d353266b"
    assert SOURCE["version"] == "0.5.7-rc.160-preview.18"
    assert SOURCE["source_revision"] == "9d8be3bb4ca2b12ed6b7806ae15aae1eb7718316"
    assert SOURCE["sha256"] == "cad61ba23056919f079229a3d64d1f97512af157260c0599ee034df9e326262d"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.153"
