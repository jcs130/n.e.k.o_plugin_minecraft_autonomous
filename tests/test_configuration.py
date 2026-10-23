def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "dd7c4011abe4e5e7498fe60740b0c23abe7fbb3f"
    assert SOURCE["version"] == "0.5.7-rc.70"
    assert SOURCE["source_revision"] == "ddff4c293ae920995cf17957710ee45eaaff0748"
    assert SOURCE["sha256"] == "f125d94e95b90bae11b8220f42c36f2cccd47795039e1f7a431cf8e860ce1e52"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.90"
