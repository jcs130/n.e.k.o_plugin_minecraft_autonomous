# Body distribution compatibility

The canonical build entry, hash verification and dependency manifest live in
minecraft-ai-friend/packages/agent-mc-autonomy/src/agent_mc_autonomy/core_distribution.
This directory only forwards the existing build.py, install.py and check_disconnected.py commands.
The plugin dependency pins the actual implementation. The checked 0.4.5 body uses
canonical source 784f32a47072823c5aac1b8f8b1b7be680fa3e82 and its archive/build/type hashes.
Changing the pin does not replace a running body; install explicitly into a new directory.

Canonical build/type receipt hashes and the archive hash are verified during installation.
No Neko runtime is needed for this check. LICENSE-Agent-MC-World.txt preserves the body source license.
