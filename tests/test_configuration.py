def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "1cbd5574660c99a6c72a55224e84f4460778fd6a"
    assert SOURCE["version"] == "0.5.7-rc.51"
    assert SOURCE["source_revision"] == "360eb64b3cee147148b1e626e48e6e0ef08e7cb1"
    assert SOURCE["sha256"] == "e0915f73f9988c4d1f852788cce0332b9267b5125bbea9c7edcd5de93f805190"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.52"
