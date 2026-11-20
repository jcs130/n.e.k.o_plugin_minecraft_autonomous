def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "5ea674456ba18798db27bf8b64b330b4fdb77a36"
    assert SOURCE["version"] == "0.5.7-rc.160-preview.115"
    assert SOURCE["source_revision"] == "22a1798ea59198682e048e874a74e534e323e9c1"
    assert SOURCE["sha256"] == "ec20b265b92e917a45874428d3223c94e79400149336a26addea20e11e6af48f"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.157"
