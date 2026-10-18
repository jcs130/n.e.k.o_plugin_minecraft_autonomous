def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "ef251a6cf3ff2c57930cca2f577e9b6dcfa56119"
    assert SOURCE["version"] == "0.5.7-rc.20.env.1"
    assert SOURCE["source_revision"] == "aac8e47d2687c5597a381c999d4e7fbd182ca0ff"
    assert SOURCE["sha256"] == "d9d89f9e7167dfaf13e6998d174fe2eba8e0816e6510e40a5d4b0ecfa246158a"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.23"
