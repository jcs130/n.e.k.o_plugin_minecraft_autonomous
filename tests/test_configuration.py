def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "1cbd5574660c99a6c72a55224e84f4460778fd6a"
    assert SOURCE["version"] == "0.5.7-rc.39"
    assert SOURCE["source_revision"] == "3c5477754ac7a52be74ce7525bb10d99fb023e82"
    assert SOURCE["sha256"] == "0c439eb109b85305ee0fa39f922e60cc590e09ab089f525168fe1a36206ef743"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.36"
