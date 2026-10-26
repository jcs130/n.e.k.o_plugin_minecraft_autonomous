def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "8b89927db49c9547a50029f039cbfe534d38e78b"
    assert SOURCE["version"] == "0.5.7-rc.100"
    assert SOURCE["source_revision"] == "a26f199313fa7923506a0940c2edd30b49569f21"
    assert SOURCE["sha256"] == "47eb8c110078ceb1ad52b1f592bc708f6a8cb18d01d222b5812b73f1bddbf0a1"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.104"
