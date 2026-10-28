# RPG state in compact requests

0.6.122 pins agent-mc-autonomy 0.2.119, source
`dc6446a5c94dc1c6eba1e763f8ea16250765bb5d`. The canonical framework keeps
current native RPG state and observed combat capabilities before optional bulk
world details. The adapter contains no second priority policy or server rules.

The backend remains agent-mc-world rc.118 with its existing archive and
integrity checks. Character, model, standing goal and personal memory are not
changed by this dependency update. Retaining a fact is not evidence that a
profession was chosen, a trade settled or a skill had an effect; those require
fresh native receipts after the server is available.

The source revision is published on the core repository's main branch. The
initial local validation build consumed its independently built wheel through
the official synchronizer's uv override, with artifact hash and vendored source
checks recorded in the private deployment receipt. The pinned Git revision is
now available for ordinary dependency synchronization. This remains a source
update, not an npm, release-tag or Market publication.
