def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "97e76665b501c2fc50ffa3f46c96b3d3d353266b"
    assert SOURCE["version"] == "0.5.7-rc.160-preview.11"
    assert SOURCE["source_revision"] == "f97ba444b8cda50f7bdbbc5f71d62add167e6034"
    assert SOURCE["sha256"] == "937ea55dc722cc475344fb7fe12451b8c001ae36c4aaad850ed2541e7ef3cb0f"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.152"
