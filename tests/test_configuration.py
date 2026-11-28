def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "41e3e52f24fc5776ce59b322a547e0e7a38cdd5e"
    assert SOURCE["version"] == "0.5.7-rc.160-preview.160"
    assert SOURCE["source_revision"] == "673b3bb6e98e44eb7b3aaea99432a8c9352d308b"
    assert SOURCE["sha256"] == "d7d039de50821e960b3f86f11807ebbca10a4afeb343ab454cddd10783fd6d42"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.162"
