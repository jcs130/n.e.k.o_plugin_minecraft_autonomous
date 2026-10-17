def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["version"] == "0.5.7-rc.6"
    assert SOURCE["source_revision"] == "eac11a06f73c66dfe8366dfc05ec98bc7d04ffdb"
    assert SOURCE["sha256"] == "21aafbbc34b6d54774350dc8db19586874ed440aab8692382ab8c2f132b2d664"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.2"
