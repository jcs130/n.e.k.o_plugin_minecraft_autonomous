def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "5ea674456ba18798db27bf8b64b330b4fdb77a36"
    assert SOURCE["version"] == "0.5.7-rc.160-preview.119"
    assert SOURCE["source_revision"] == "e0b91b1d5fa800b4bea99958876336b398882dc4"
    assert SOURCE["sha256"] == "c0eeba7bd5f988a91eb9ae89f5af4233272a45a2b5eba1b9c4d97cbbb2a810c7"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.159"
