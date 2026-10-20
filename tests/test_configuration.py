def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "1cbd5574660c99a6c72a55224e84f4460778fd6a"
    assert SOURCE["version"] == "0.5.7-rc.52"
    assert SOURCE["source_revision"] == "bba59bb92a0b83d0321671a19f272eef38400cd1"
    assert SOURCE["sha256"] == "8b5fcc50c80914f6375f3ef7d1c5855e60aeb3598ccba7c7886f831f36b75f1f"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.57"
