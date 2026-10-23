def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "dd7c4011abe4e5e7498fe60740b0c23abe7fbb3f"
    assert SOURCE["version"] == "0.5.7-rc.73"
    assert SOURCE["source_revision"] == "2e128092926b8f8c1bcf2483fea1c18a7c28200c"
    assert SOURCE["sha256"] == "f1ece4c7016f8f6702ac56f30c26e505d5f613f7819adf692dbefc760bb53994"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.91"
