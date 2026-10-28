# VortexRPG source candidate

This update consumes the shared agent-mc-autonomy server engine port. The instance must explicitly provide an installed server engine module and its SHA-256 in `server_extension.engine_module` and `server_extension.engine_sha256`. No server, account, model or automatic gameplay is selected by this feature.

The hosted settings API preserves these fields when selecting the optional presentation pack. Setting `extension_pack.mode = "none"` clears both engine and presentation ports. Existing viewer composition, planner and speech routing remain host capabilities; game and VortexRPG behavior remain in the canonical core and explicit server package.

Source checks, prepared packages, installation and real game receipts are recorded independently. This candidate is not a published Market release, and does not claim that the previous downloadable runtime contains the new core.
