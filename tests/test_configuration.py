def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "ef251a6cf3ff2c57930cca2f577e9b6dcfa56119"
    assert SOURCE["version"] == "0.5.7-rc.31"
    assert SOURCE["source_revision"] == "c1a16034ca5533bc095cc3062da9cd12f9ad1c32"
    assert SOURCE["sha256"] == "a2f3f08e0ee694d79cb05dbdca9d93d4cebfc75ed0799d7df4d4b9af504aa053"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.26"
