def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "5ea674456ba18798db27bf8b64b330b4fdb77a36"
    assert SOURCE["version"] == "0.5.7-rc.160-preview.117"
    assert SOURCE["source_revision"] == "db92c22527a74976439fd5ec0e2569c6cae3b407"
    assert SOURCE["sha256"] == "1d42513ca112c62fab99b554c185ad10b7d3f506f635fcf82effb9378a1ad2be"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.158"
