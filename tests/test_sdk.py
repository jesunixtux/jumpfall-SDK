import hashlib
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "content-mod"
sys.path.insert(0, str(ROOT))

import jumpfall_menu_editor
import jumpfall_sdk
from jumpfall_menu_editor import run_self_test
from jumpfall_sdk import Validator, pack_command


def write_minimal_mod(root: Path, **overrides) -> None:
    manifest = {
        "schemaVersion": "1.0.0",
        "id": "com.test.mod",
        "name": "Test",
        "version": "1.0.0",
        "author": "Test",
        "type": "content",
        "gameVersion": {"min": "0.50.05", "max": ""},
        "capabilities": [],
        "content": {
            "maps": [],
            "levelEditor": [],
            "scenePatches": [],
            "menus": [],
            "localization": [],
            "scripts": [],
            "playerTuning": {},
        },
    }
    manifest.update(overrides)
    (root / "jumpfall.mod.json").write_text(json.dumps(manifest), encoding="utf-8")


def make_png(width: int, height: int, valid_signature: bool = True) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n" if valid_signature else b"NOTAPNG!"
    ihdr = struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height)
    return signature + ihdr + b"\x08\x02\x00\x00\x00" + b"\x00" * 16


def make_jpeg(width: int, height: int) -> bytes:
    body = (
        b"\xff\xd8"
        + b"\xff\xc0"
        + struct.pack(">H", 8)
        + b"\x08"
        + struct.pack(">HH", height, width)
        + b"\x01\x01\x11\x00"
        + b"\xff\xd9"
    )
    return body


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
                        "version": 29,
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


    def test_validates_image_dimensions_and_magic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_minimal_mod(root, capabilities=["visuals"])
            (root / "ok.png").write_bytes(make_png(64, 64))
            (root / "ok.jpg").write_bytes(make_jpeg(64, 64))
            validator = Validator(root)
            self.assertTrue(validator.validate(), [str(p) for p in validator.problems])

            (root / "fake.png").write_bytes(make_png(64, 64, valid_signature=False))
            validator = Validator(root)
            self.assertFalse(validator.validate())
            self.assertIn("package.image_magic", {p.code for p in validator.problems})
            (root / "fake.png").unlink()

            (root / "huge.png").write_bytes(make_png(5000, 10))
            validator = Validator(root)
            self.assertFalse(validator.validate())
            self.assertIn("package.image_dimensions", {p.code for p in validator.problems})

    def test_validates_audio_magic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_minimal_mod(root)
            (root / "ok.wav").write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
            (root / "ok.ogg").write_bytes(b"OggS" + b"\x00" * 8)
            validator = Validator(root)
            self.assertTrue(validator.validate(), [str(p) for p in validator.problems])

            (root / "bad.wav").write_bytes(b"XXXX\x00\x00\x00\x00YYYY")
            validator = Validator(root)
            self.assertFalse(validator.validate())
            self.assertIn("package.audio_magic", {p.code for p in validator.problems})

    def test_rejects_windows_reserved_and_trailing_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_minimal_mod(root)
            (root / "COM1.txt").write_text("reserved", encoding="utf-8")
            validator = Validator(root)
            self.assertFalse(validator.validate())
            self.assertIn("package.reserved_name", {p.code for p in validator.problems})

    def test_detects_case_insensitive_collisions(self) -> None:
        seen: set[str] = set()
        self.assertIsNone(Validator._tree_name_problem(Path("assets/Logo.png"), seen))
        self.assertEqual(
            "package.case_collision",
            Validator._tree_name_problem(Path("assets/logo.PNG"), seen),
        )
        seen2: set[str] = set()
        self.assertEqual(
            "package.reserved_name",
            Validator._tree_name_problem(Path("docs/AUX.md"), seen2),
        )

    def test_validates_dependency_version_ranges(self) -> None:
        valid_ranges = ["*", "1.2.3", ">=1.2.0 <2.0.0", "^1.2.0", "~1.2.0", "1.2.x", "^1.0.0 || ^2.0.0"]
        for range_value in valid_ranges:
            self.assertTrue(Validator._is_valid_version_range(range_value), range_value)
        invalid_ranges = ["foo", ">>1.0.0", "^", "1.0.0 ||", ">=1.0", "~", "1.2.3.4"]
        for range_value in invalid_ranges:
            self.assertFalse(Validator._is_valid_version_range(range_value), range_value)

    def test_rejects_invalid_dependency_range_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_minimal_mod(
                root, dependencies=[{"id": "com.test.lib", "version": "sometime-later"}]
            )
            validator = Validator(root)
            self.assertFalse(validator.validate())
            self.assertIn("dependency.version", {p.code for p in validator.problems})

    def test_warns_on_game_version_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_minimal_mod(root, gameVersion={"min": "9.99.99", "max": ""})
            validator = Validator(root)
            self.assertTrue(validator.validate(), [str(p) for p in validator.problems])
            self.assertIn("game_version.newer_required", {p.code for p in validator.problems})

            write_minimal_mod(root, gameVersion={"min": "0.1.0", "max": "0.1.0"})
            validator = Validator(root)
            self.assertTrue(validator.validate(), [str(p) for p in validator.problems])
            self.assertIn("game_version.older_supported", {p.code for p in validator.problems})

    def test_rejects_bad_patch_color_scene_and_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "content" / "patches").mkdir(parents=True)
            (root / "content" / "patches" / "bad.json").write_text(
                json.dumps(
                    {
                        "patches": [
                            {"scene": "Menugame", "target": "/Canvas/Title", "operation": "set_color", "value": "red"},
                            {"scene": "", "target": "/Canvas/Title", "operation": "set_text", "value": "hi"},
                            {"scene": "Menugame", "target": "/Canvas/Title", "operation": "set_text", "value": "x" * 5000},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            write_minimal_mod(
                root,
                capabilities=["visuals"],
                content={
                    "maps": [], "levelEditor": [],
                    "scenePatches": ["content/patches/bad.json"],
                    "menus": [], "localization": [], "scripts": [], "playerTuning": {},
                },
            )
            validator = Validator(root)
            self.assertFalse(validator.validate())
            codes = {p.code for p in validator.problems}
            self.assertIn("scene_patch.color", codes)
            self.assertIn("scene_patch.scene", codes)
            self.assertIn("scene_patch.value", codes)

    def test_rejects_future_map_and_invalid_bosses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "content" / "maps").mkdir(parents=True)
            map_path = root / "content" / "maps" / "arena.jfue"
            map_path.write_text(
                json.dumps(
                    {
                        "version": 99,
                        "pieces": [],
                        "triggers": [],
                        "bosses": [{"objectId": "b0", "nodes": [{} for _ in range(129)]},
                                   {"objectId": "b0", "nodes": []}],
                    }
                ),
                encoding="utf-8",
            )
            write_minimal_mod(
                root,
                capabilities=["maps"],
                content={
                    "maps": [{"id": "arena", "name": "Arena", "file": "content/maps/arena.jfue"}],
                    "levelEditor": [], "scenePatches": [], "menus": [],
                    "localization": [], "scripts": [], "playerTuning": {},
                },
            )
            validator = Validator(root)
            self.assertFalse(validator.validate())
            codes = {p.code for p in validator.problems}
            self.assertIn("map.version_future", codes)
            self.assertIn("map.boss_nodes", codes)
            self.assertIn("map.boss_duplicate", codes)

            too_many = [{"objectId": f"b{i}", "nodes": []} for i in range(9)]
            invalid = json.loads(map_path.read_text(encoding="utf-8"))
            invalid["version"] = 29
            invalid["bosses"] = too_many
            map_path.write_text(json.dumps(invalid), encoding="utf-8")
            validator = Validator(root)
            self.assertFalse(validator.validate())
            self.assertIn("map.boss_count", {p.code for p in validator.problems})

    def test_localization_aliases_collide_and_unknown_warns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "content" / "localization").mkdir(parents=True)
            for name in ("a.json", "b.json", "c.json"):
                (root / "content" / "localization" / name).write_text(
                    json.dumps({"items": [{"key": "k", "value": "v"}]}), encoding="utf-8"
                )
            write_minimal_mod(
                root,
                capabilities=["localization"],
                content={
                    "maps": [], "levelEditor": [], "scenePatches": [], "menus": [],
                    "localization": [
                        {"language": "es", "file": "content/localization/a.json"},
                        {"language": "Spanish", "file": "content/localization/b.json"},
                        {"language": "Klingon", "file": "content/localization/c.json"},
                    ],
                    "scripts": [], "playerTuning": {},
                },
            )
            validator = Validator(root)
            self.assertFalse(validator.validate())
            codes = {p.code for p in validator.problems}
            self.assertIn("localization.duplicate", codes)
            self.assertIn("localization.unknown_language", codes)

    def test_map_background_and_track_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "content" / "maps").mkdir(parents=True)
            map_path = root / "content" / "maps" / "m.jfue"
            map_path.write_text(
                json.dumps(
                    {
                        "version": 29,
                        "pieces": [],
                        "triggers": [],
                        "backgrounds": [{"objectId": "bg", "fileName": "assets/missing.png"}],
                        "soundtrack": {"tracks": [{"fileName": "assets/missing.ogg", "volume": 2.0}]},
                    }
                ),
                encoding="utf-8",
            )
            write_minimal_mod(
                root,
                capabilities=["maps"],
                content={
                    "maps": [{"id": "m", "name": "M", "file": "content/maps/m.jfue"}],
                    "levelEditor": [], "scenePatches": [], "menus": [],
                    "localization": [], "scripts": [], "playerTuning": {},
                },
            )
            validator = Validator(root)
            self.assertFalse(validator.validate())
            codes = {p.code for p in validator.problems}
            self.assertIn("map.soundtrack_volume", codes)
            self.assertIn("map.background_asset", codes)
            self.assertIn("map.soundtrack_asset", codes)

    def test_menu_editor_constants_match_sdk(self) -> None:
        self.assertEqual(set(jumpfall_menu_editor.MENU_TYPES), set(jumpfall_sdk.MENU_TYPES))
        self.assertEqual(set(jumpfall_menu_editor.MENU_ACTIONS), set(jumpfall_sdk.MENU_ACTIONS))
        for pattern in (jumpfall_menu_editor.ID_PATTERN, jumpfall_sdk.CONTENT_ID_PATTERN):
            self.assertTrue(pattern.fullmatch("panel-1"))
            self.assertFalse(pattern.fullmatch("UPPERCASE invalid"))

    def test_pack_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            out_a = Path(temporary) / "a.jfmod"
            out_b = Path(temporary) / "b.jfmod"
            self.assertEqual(pack_command(TEMPLATE, out_a), 0)
            self.assertEqual(pack_command(TEMPLATE, out_b), 0)
            digest_a = hashlib.sha256(out_a.read_bytes()).hexdigest()
            digest_b = hashlib.sha256(out_b.read_bytes()).hexdigest()
            self.assertEqual(digest_a, digest_b)


if __name__ == "__main__":
    unittest.main()
