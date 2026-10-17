def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "b5a41c37d8f503df5344762bd5df5e61c1734f4b"
    assert SOURCE["version"] == "0.5.7-rc.7"
    assert SOURCE["source_revision"] == "20d731efe8e165887f8af97ff1ed13c7241c75df"
    assert SOURCE["sha256"] == "aca644510c07634869ee08ffba621a3be1d52b365df376f914ca2d78f196e76a"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.4"
