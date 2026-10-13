# Body distribution compatibility

The canonical build, hash verification, dependency manifest and reviewed patch set now live in
minecraft-ai-friend/packages/agent-mc-autonomy/src/agent_mc_autonomy/core_distribution.
This directory only forwards the existing build.py, install.py and check_disconnected.py commands.
The plugin dependency pins the actual implementation. The body remains pinned to 7889ce2 until
its separately tested upgrade; moving source ownership does not replace a running body.

The old nekoBuild/neko-headless receipt names are preserved as a file format compatibility detail,
not a dependency on a Neko runtime. LICENSE-Agent-MC-World.txt preserves the body source license.
