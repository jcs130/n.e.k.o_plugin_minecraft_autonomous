def test_backend_compatibility_wrapper_uses_canonical_installer(plugin_module):
    import importlib

    from agent_mc_autonomy.core_distribution.install import SOURCE, verify_runtime
    adapter = importlib.import_module(plugin_module.__name__ + ".backend.install")
    assert adapter.verify_runtime is verify_runtime
    assert adapter.SOURCE == SOURCE
    assert SOURCE["external_viewer"]["source_revision"] == "dd7c4011abe4e5e7498fe60740b0c23abe7fbb3f"
    assert SOURCE["version"] == "0.5.7-rc.56"
    assert SOURCE["source_revision"] == "7207ad9d2ddcae4bd14d04158a4832c79904e84e"
    assert SOURCE["sha256"] == "f3fd7d92f2b1ede19eea9d3d31c76b41cbc0de5106ff0a9cd887b729f8cdf190"


def test_canonical_distribution_version():
    from importlib.metadata import version

    assert version("agent-mc-autonomy") == "0.2.70"
