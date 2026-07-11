import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "content-mod"
sys.path.insert(0, str(ROOT))

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


if __name__ == "__main__":
    unittest.main()
