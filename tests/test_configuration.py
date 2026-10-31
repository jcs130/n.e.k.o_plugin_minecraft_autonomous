def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "b99464bb7efce76dedb00471605019932b1e8d7e"
    assert SOURCE["version"] == "0.5.7-rc.149-preview.1"
    assert SOURCE["source_revision"] == "b6ac47b27cd68a5abf0f6a3294d9c576eac89d98"
    assert SOURCE["sha256"] == "aa3d92f28b94370171d5d957933bf7e18610b6eb572c3c0458aa3b5947e853f4"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.139"
