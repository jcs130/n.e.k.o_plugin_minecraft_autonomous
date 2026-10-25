def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "dd7c4011abe4e5e7498fe60740b0c23abe7fbb3f"
    assert SOURCE["version"] == "0.5.7-rc.86"
    assert SOURCE["source_revision"] == "01fe3bd11421549eac8e3be02db82b6bd0abf82a"
    assert SOURCE["sha256"] == "35c83a1474e43867d819effeeb7b288bd696cdf935d4db0de6b8d56f3e82433e"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.97"
