def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "97e76665b501c2fc50ffa3f46c96b3d3d353266b"
    assert SOURCE["version"] == "0.5.7-rc.160-preview.9"
    assert SOURCE["source_revision"] == "68207f02eb4f0119e7efaf530be51d23c38f7f5e"
    assert SOURCE["sha256"] == "2424d0eaef3b42838a1762169ee7d01f210055acc97cc114ee0aa0b7aeaf5eb4"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.147"
