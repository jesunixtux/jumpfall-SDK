import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "content-mod"
sys.path.insert(0, str(ROOT))

from jumpfall_menu_editor import run_self_test
from jumpfall_sdk import Validator, pack_command


class JumpfallSdkTests(unittest.TestCase):
    def test_template_is_valid(self) -> None:
        validator = Validator(TEMPLATE)
        self.assertTrue(validator.validate(), [str(problem) for problem in validator.problems])

    def test_template_packages_with_root_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "template.jfmod"
            self.assertEqual(pack_command(TEMPLATE, output), 0)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
            self.assertIn("jumpfall.mod.json", names)
            self.assertIn("content/level-editor/pieces.json", names)
            self.assertTrue(all("\\" not in name for name in names))
            self.assertTrue(all(not Path(name).is_absolute() for name in names))

    def test_visual_menu_editor_self_test_is_headless(self) -> None:
        self.assertEqual(run_self_test(), 0)

    def test_rejects_unknown_level_editor_archetype(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "content" / "level-editor").mkdir(parents=True)
            manifest = {
                "schemaVersion": "1.0.0",
                "id": "com.test.invalid",
                "name": "Invalid",
                "version": "1.0.0",
                "author": "Test",
                "type": "content",
                "gameVersion": {"min": "0.50.05", "max": ""},
                "capabilities": ["level_editor"],
                "content": {
                    "maps": [],
                    "levelEditor": ["content/level-editor/pieces.json"],
                    "scenePatches": [],
                    "menus": [],
                    "localization": [],
                    "scripts": [],
                    "playerTuning": {},
                },
            }
            pieces = {
                "pieces": [
                    {"id": "bad", "name": "Bad", "baseId": "freeform_3d"}
                ]
            }
            (root / "jumpfall.mod.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "content" / "level-editor" / "pieces.json").write_text(
                json.dumps(pieces), encoding="utf-8"
            )

            validator = Validator(root)
            self.assertFalse(validator.validate())
            self.assertIn("level_editor.base", {problem.code for problem in validator.problems})

    def test_rejects_package_output_inside_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "mod"
            source.mkdir()
            (source / "jumpfall.mod.json").write_text("{}", encoding="utf-8")
            output = source / "dist" / "bad.jfmod"
            self.assertEqual(pack_command(source, output), 1)
            self.assertFalse(output.exists())

    def test_selectors_match_runtime_security_rules(self) -> None:
        self.assertTrue(Validator._safe_selector("/Canvas/MainPanel/Title"))
        self.assertFalse(Validator._safe_selector("/Player"))
        self.assertFalse(Validator._safe_selector("/Canvas/Main Camera"))
        self.assertFalse(Validator._safe_selector("/Canvas//Title"))
        self.assertFalse(Validator._safe_selector("/Canvas/../Title"))

    def test_rejects_lua_files_even_without_manifest_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "main.lua").write_text("return true", encoding="utf-8")
            (root / "jumpfall.mod.json").write_text("{}", encoding="utf-8")
            validator = Validator(root)
            self.assertFalse(validator.validate())
            self.assertIn("package.extension", {problem.code for problem in validator.problems})

    def test_rejects_oversized_manifest_content_arrays_early(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            validator = Validator(Path(temporary))
            validator._validate_content(
                {
                    "maps": [{} for _ in range(129)],
                    "levelEditor": [],
                    "scenePatches": [],
                    "menus": [],
                    "localization": [],
                    "scripts": [],
                    "playerTuning": {},
                },
                set(),
                "com.test.limit",
            )
            self.assertIn("content.count", {problem.code for problem in validator.problems})
            self.assertEqual(len(validator.problems), 1)

    def test_lighting_example_and_legacy_maps_validate(self) -> None:
        validator = Validator(TEMPLATE)
        path = TEMPLATE / "examples" / "lighting.jfue"
        validator._validate_map_piece_ids(path.resolve(), set())
        self.assertFalse(validator.problems, validator.problems)
        validator._validate_map_lights(path, None, [])
        self.assertFalse(validator.problems, validator.problems)

    def test_lighting_rejects_invalid_values_and_duplicate_ids(self) -> None:
        validator = Validator(TEMPLATE)
        path = TEMPLATE / "examples" / "lighting.jfue"
        validator._validate_map_lights(path, [
            {"objectId": "lamp", "range": float("nan")},
            {"objectId": "lamp", "intensity": -1, "vertices": []},
            {"objectId": [], "shape": {}, "color": []},
        ], [{"id": "light", "eventAction": "set_light", "eventValue": "toggle", "eventTargetObjectId": "missing"}])
        codes = {problem.code for problem in validator.problems}
        self.assertTrue({"map.light_value", "map.light_id", "map.light_vertices", "map.light_target"} <= codes)
        validator._validate_map_lights(path, [], [{"id": "light", "eventAction": "set_light", "eventValue": {}, "eventTargetObjectId": []}])
        self.assertIn("map.light_action", {problem.code for problem in validator.problems})

    def test_validates_ghost_player_limits_and_safe_events(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            map_path = root / "ghosts.jfue"
            ghost = {
                "displayName": "tutorial_jump",
                "startDelay": 0.0,
                "playbackSpeed": 1.0,
                "opacity": 0.45,
                "sampleInterval": 1.0 / 30.0,
                "frames": [
                    {"time": 0.0, "px": 0.0, "py": 0.0, "rotZ": 0.0, "sx": 1.0, "sy": 1.0, "animatorStateHash": 123, "animatorNormalizedTime": 0.0},
                    {"time": 0.1, "px": 1.0, "py": 1.0, "rotZ": 0.0, "sx": 1.0, "sy": 1.0, "animatorStateHash": 123, "animatorNormalizedTime": 0.25},
                ],
            }
            map_path.write_text(
                json.dumps(
                    {
                        "pieces": [],
                        "triggers": [
                            {
                                "id": "event",
                                "eventAction": "level_event",
                                "eventId": "ghost.restart",
                                "eventDelaySeconds": 0.0,
                            }
                        ],
                        "ghosts": [ghost],
                    }
                ),
                encoding="utf-8",
            )

            validator = Validator(root)
            validator._validate_map_piece_ids(map_path.resolve(), set())
            self.assertEqual([], [str(problem) for problem in validator.problems])

            invalid = json.loads(map_path.read_text(encoding="utf-8"))
            invalid["triggers"][0]["eventAction"] = "send_message"
            invalid["ghosts"] = [ghost for _ in range(33)]
            map_path.write_text(json.dumps(invalid), encoding="utf-8")

            validator = Validator(root)
            validator._validate_map_piece_ids(map_path.resolve(), set())
            codes = {problem.code for problem in validator.problems}
            self.assertIn("map.event_action", codes)
            self.assertIn("map.ghost_count", codes)
            self.assertIn("map.ghost_duplicate", codes)


if __name__ == "__main__":
    unittest.main()
