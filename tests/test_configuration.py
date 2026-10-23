def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "dd7c4011abe4e5e7498fe60740b0c23abe7fbb3f"
    assert SOURCE["version"] == "0.5.7-rc.76"
    assert SOURCE["source_revision"] == "d1798e51137ef0f0c3b7b3b3405829d01b905085"
    assert SOURCE["sha256"] == "f36e98505a5c2cdc194f008da834119d90eed9e762860516fb9352c840cf6e41"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.92"
