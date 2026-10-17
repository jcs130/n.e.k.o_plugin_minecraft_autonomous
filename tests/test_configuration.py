def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "8e72a5549ac738f2b183306619004d6f319d94d7"
    assert SOURCE["version"] == "0.5.7-rc.14"
    assert SOURCE["source_revision"] == "768d8906a9a09b8c21f5c1c4f37818147bf9ca93"
    assert SOURCE["sha256"] == "3c390af436ba0ced69319a24b0d67441afdf21a64f7f7fe814df0b68b36686e1"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.9"
