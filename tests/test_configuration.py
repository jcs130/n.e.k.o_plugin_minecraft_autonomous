def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "b99464bb7efce76dedb00471605019932b1e8d7e"
    assert SOURCE["version"] == "0.5.7-rc.128"
    assert SOURCE["source_revision"] == "f581760e5d46bcdc3511e671c42aab62abfea165"
    assert SOURCE["sha256"] == "afc37924d3f20b9d0a5437e8dabac36f8f2b9825f37e825cb2b6b6a9bd2628e4"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.126"
