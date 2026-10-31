def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "b99464bb7efce76dedb00471605019932b1e8d7e"
    assert SOURCE["version"] == "0.5.7-rc.150-preview.3"
    assert SOURCE["source_revision"] == "3c0c2d24c8e9a7f796c86f9dbb7a8ec590d48012"
    assert SOURCE["sha256"] == "c12c168dc98f8a5c4ae852433948936f886e9b2d51f1183bc1eab637d4d13470"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.141"
