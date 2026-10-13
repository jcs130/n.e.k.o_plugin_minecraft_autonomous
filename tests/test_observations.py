import importlib
import json


def test_voxel_receipt_keeps_real_material_coordinates_and_original(plugin_module):
    context = importlib.import_module(plugin_module.__name__ + ".autonomy.context")
    observation = {"source": "client-loaded-world", "observedAt": "now", "kind": "voxels", "dimension": "overworld",
                   "frame": {"feet": [-2, 64, 7]}, "bounds": [-2, 64, 7, 5, 71, 14], "order": "y,z,x; x fastest",
                   "palette": [{"name": "air", "air": True}, {"name": "oak_log"}], "cells": [1] + [0] * 511,
                   "unknownCells": 0, "entities": []}
    original = "Task completed: " + json.dumps(observation)
    facts = {"parts": [{"key": "lastTask", "text": original, "original": "log:complete"}]}
    messages, budget = context.assemble("stable", [], "survive", facts, [], [], context_tokens=6000, reserved_output=1024)
    tail = json.loads(messages[-1]["content"])
    assert not tail["omitted_facts"]
    brief = tail["current_facts"][0]
    assert brief["original"] == "log:complete"
    assert '"name":"oak_log"' in brief["text"] and '[-2,64,7]' in brief["text"]
    assert '"count":1' in brief["text"] and '"unknownCells":0' in brief["text"]
    assert '"cells"' not in brief["text"]
    assert facts["parts"][0]["text"] == original
    assert budget["total"] <= 6000


def test_spatial_summary_never_turns_unread_cells_into_air(plugin_module):
    module = importlib.import_module(plugin_module.__name__ + ".autonomy.observations")
    observation = {"source": "client-loaded-world", "kind": "voxels", "frame": {"feet": [0, 0, 0]},
                   "bounds": [0, 0, 0, 1, 0, 0], "order": "y,z,x; x fastest", "palette": [{"name": "air", "air": True}],
                   "cells": [0, None], "unknownCells": 1}
    brief = json.loads(module.spatial_text(json.dumps(observation)))
    assert brief["materials"] == [{"name": "air", "count": 1}]
    assert brief["unknownCells"] == 1
    assert "passable" not in brief and "safe" not in brief


def test_malformed_or_differently_ordered_observation_is_preserved(plugin_module):
    module = importlib.import_module(plugin_module.__name__ + ".autonomy.observations")
    for text in ('{"source":"client-loaded-world","kind":"voxels"',
                 '{"source":"client-loaded-world","kind":"voxels","order":"unknown"}'):
        assert module.spatial_text(text) == text
