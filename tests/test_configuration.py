def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "b99464bb7efce76dedb00471605019932b1e8d7e"
    assert SOURCE["version"] == "0.5.7-rc.108"
    assert SOURCE["source_revision"] == "8170ebd0384ffa00c7cd43031e23779a54224bf0"
    assert SOURCE["sha256"] == "905509e1202f5ed54167885dbe325d7a2e9bbe8184ca765a56e5209e5a772fb4"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.110"
