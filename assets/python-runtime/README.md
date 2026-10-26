# Platform Python resources

The official Neko workflow keeps its normal Linux `vendor/`. This resource adds
the CPython 3.11 Windows x64 wheels needed by this plugin to that **same** Market
artifact. `platform_dependencies.py` verifies the archive and every member,
prepares a short current-user cache, and selects it before importing the
framework. It never installs into Neko's interpreter, runs `.pth` scripts,
removes SDK modules, or changes the host.

`win32-cp311-x64.json` records exact distributions, upstream wheel SHA256 values,
archive SHA256, member sizes and hashes. The archive was built from fresh public
PyPI wheels with `--only-binary=:all:`; original package metadata and licenses are
included. It contains no framework copy, account, model or runtime data.

Linux continues to use the standard official vendor. Existing host imports keep
their original package paths and ABI pairs; cold Windows imports use a coherent
Windows dependency layer. The same final artifact must pass real native imports
on both supported platforms before publication. Other Windows Python ABIs and
CPU architectures are explicitly unsupported rather than loading Linux code.
