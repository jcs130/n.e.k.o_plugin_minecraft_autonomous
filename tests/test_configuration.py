def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "8e72a5549ac738f2b183306619004d6f319d94d7"
    assert SOURCE["version"] == "0.5.7-rc.13"
    assert SOURCE["source_revision"] == "6812a982a7f3fa6ff1cde6b0e9740143a53d3ec0"
    assert SOURCE["sha256"] == "f781bbe3f7dd637f252cc3cc9d7a4c3ba77e9209607abf18b81478b82134f5e8"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.8"
