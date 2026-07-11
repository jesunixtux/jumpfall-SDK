#!/usr/bin/env python3
"""JumpFall SDK 1.0 validator and .jfmod packer.

Uses only Python's standard library so mod authors do not need Unity.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SDK_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
MANIFEST_NAME = "jumpfall.mod.json"
PACKAGE_EXTENSION = ".jfmod"
KNOWN_GAME_VERSION = "0.50.05"

MAX_PACKAGE_BYTES = 256 * 1024 * 1024
MAX_EXPANDED_BYTES = 512 * 1024 * 1024
MAX_SINGLE_FILE_BYTES = 128 * 1024 * 1024
MAX_MANIFEST_BYTES = 256 * 1024
MAX_IMAGE_BYTES = 32 * 1024 * 1024
MAX_AUDIO_BYTES = 64 * 1024 * 1024
MAX_FILES = 2000

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
CONTENT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?$")
SEMVER_PATTERN = re.compile(
    r"^(?:v)?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
GAME_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

ALLOWED_CAPABILITIES = {
    "maps",
    "level_editor",
    "visuals",
    "audio",
    "localization",
    "menus",
    "mechanics",
}

FORBIDDEN_CAPABILITIES = {
    "lua",
    "3d",
    "gameplay.3d",
    "player.controller.replace",
    "player.replace",
    "native_code",
    "managed_code",
    "csharp",
    "assetbundles",
    "base_assets.write",
    "filesystem",
    "network",
    "process",
    "reflection",
}

ALLOWED_EXTENSIONS = {
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".wav",
    ".ogg",
    ".jfue",
    ".txt",
    ".md",
    ".csv",
}

FORBIDDEN_EXTENSIONS = {
    ".dll",
    ".exe",
    ".so",
    ".dylib",
    ".bundle",
    ".assetbundle",
    ".cs",
    ".js",
    ".bat",
    ".cmd",
    ".ps1",
    ".sh",
    ".app",
    ".apk",
    ".jar",
    ".class",
    ".py",
    ".rb",
    ".com",
    ".scr",
}

IGNORED_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
SCENE_OPERATIONS = {
    "set_active",
    "set_text",
    "set_sprite",
    "set_color",
    "set_audio_clip",
    "set_audio_volume",
}
MENU_TYPES = {"panel", "image", "text", "button"}
MENU_ACTIONS = {"", "resume", "quit", "load_map", "set_active", "toggle_active"}
LEVEL_EDITOR_PIECE_BASE_IDS = {
    "box_ground",
    "checkpoint",
    "apple",
    "orb_jump",
    "plane_jump",
    "elevator",
}


@dataclass(frozen=True)
class Problem:
    severity: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.code}: {self.message}"


class Validator:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.problems: list[Problem] = []
        self.manifest: dict[str, Any] | None = None

    def error(self, code: str, message: str) -> None:
        self.problems.append(Problem("ERROR", code, message))

    def warning(self, code: str, message: str) -> None:
        self.problems.append(Problem("WARNING", code, message))

    def validate(self) -> bool:
        if not self.root.is_dir():
            self.error("root.missing", f"Mod folder does not exist: {self.root}")
            return False

        self._validate_package_tree()
        manifest_path = self.root / MANIFEST_NAME
        if not manifest_path.is_file():
            self.error("manifest.missing", f"{MANIFEST_NAME} must exist at the package root.")
            return False

        try:
            if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
                self.error("manifest.size", "Manifest exceeds 256 KiB.")
                return False
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            self.error("manifest.json", str(exc))
            return False

        if not isinstance(data, dict):
            self.error("manifest.root", "Manifest JSON root must be an object.")
            return False

        self.manifest = data
        self._validate_manifest(data)
        return not any(problem.severity == "ERROR" for problem in self.problems)

    def _validate_package_tree(self) -> None:
        count = 0
        total = 0
        for path in self.root.rglob("*"):
            if self._is_ignored(path):
                continue
            if path.is_symlink():
                self.error("package.symlink", f"Symbolic links are not allowed: {path.relative_to(self.root)}")
                continue
            if not path.is_file():
                continue

            count += 1
            if count > MAX_FILES:
                self.error("package.files", f"Package contains more than {MAX_FILES} files.")
                break

            relative = path.relative_to(self.root)
            extension = path.suffix.lower()
            if extension in FORBIDDEN_EXTENSIONS or extension not in ALLOWED_EXTENSIONS:
                self.error("package.extension", f"Unsupported file type: {relative}")

            size = path.stat().st_size
            total += size
            if size > self._maximum_for_file(path):
                self.error("package.file_size", f"File exceeds its limit: {relative}")
            if total > MAX_EXPANDED_BYTES:
                self.error("package.total_size", "Expanded package exceeds 512 MiB.")
                break

    def _validate_manifest(self, manifest: dict[str, Any]) -> None:
        if manifest.get("schemaVersion") != SCHEMA_VERSION:
            self.error("manifest.schema", f"schemaVersion must be exactly {SCHEMA_VERSION}.")

        mod_id = self._require_string(manifest, "id", 64)
        if mod_id and (not ID_PATTERN.fullmatch(mod_id) or mod_id == "jumpfall"):
            self.error("manifest.id", "id must be 3-64 lowercase letters/numbers/dot/dash/underscore and cannot be 'jumpfall'.")

        self._require_string(manifest, "name", 128)
        self._require_string(manifest, "author", 128)
        self._optional_string(manifest, "description", 4096)

        version = self._require_string(manifest, "version", 128)
        if version and not SEMVER_PATTERN.fullmatch(version):
            self.error("manifest.version", "version must use semantic version syntax, for example 1.0.0.")

        package_type = manifest.get("type")
        if package_type not in {"content", "total_conversion"}:
            self.error("manifest.type", "type must be 'content' or 'total_conversion'.")

        priority = manifest.get("priority", 0)
        if not isinstance(priority, int) or isinstance(priority, bool) or not -1000 <= priority <= 1000:
            self.error("manifest.priority", "priority must be an integer between -1000 and 1000.")

        self._validate_game_version(manifest.get("gameVersion"))
        capabilities = self._validate_capabilities(manifest.get("capabilities"))
        self._validate_relations(manifest.get("dependencies", []), mod_id, "dependency")
        self._validate_relations(manifest.get("conflicts", []), mod_id, "conflict")

        content = manifest.get("content")
        if not isinstance(content, dict):
            self.error("content.missing", "content must be an object.")
            return
        self._validate_content(content, capabilities, mod_id)

    def _validate_game_version(self, value: Any) -> None:
        if not isinstance(value, dict):
            self.error("game_version.missing", "gameVersion with a min field is required.")
            return
        minimum = value.get("min")
        maximum = value.get("max", "")
        if not isinstance(minimum, str) or not GAME_VERSION_PATTERN.fullmatch(minimum):
            self.error("game_version.min", "gameVersion.min must use x.y.z syntax.")
        if maximum and (not isinstance(maximum, str) or not GAME_VERSION_PATTERN.fullmatch(maximum)):
            self.error("game_version.max", "gameVersion.max must be empty or use x.y.z syntax.")
        if isinstance(minimum, str) and isinstance(maximum, str) and maximum:
            if self._version_tuple(maximum) < self._version_tuple(minimum):
                self.error("game_version.range", "gameVersion.max cannot be lower than min.")

    def _validate_capabilities(self, value: Any) -> set[str]:
        if not isinstance(value, list):
            self.error("capability.type", "capabilities must be an array.")
            return set()
        result: set[str] = set()
        for raw in value:
            if not isinstance(raw, str):
                self.error("capability.value", "Every capability must be a string.")
                continue
            capability = raw.strip().lower()
            if capability in FORBIDDEN_CAPABILITIES:
                self.error("capability.forbidden", f"Capability is not available: {capability}")
            elif capability not in ALLOWED_CAPABILITIES:
                self.error("capability.unknown", f"Unknown capability: {capability}")
            elif capability in result:
                self.warning("capability.duplicate", f"Duplicate capability: {capability}")
            else:
                result.add(capability)
        return result

    def _validate_relations(self, value: Any, mod_id: str | None, relation: str) -> None:
        if not isinstance(value, list):
            self.error(f"{relation}.type", f"{relation}s must be an array.")
            return
        seen: set[str] = set()
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                self.error(f"{relation}.object", f"{relation}[{index}] must be an object.")
                continue
            relation_id = item.get("id")
            if not isinstance(relation_id, str) or not ID_PATTERN.fullmatch(relation_id) or relation_id == mod_id:
                self.error(f"{relation}.id", f"Invalid or self-referencing {relation} id at index {index}.")
                continue
            if relation_id in seen:
                self.error(f"{relation}.duplicate", f"Duplicate {relation}: {relation_id}")
            seen.add(relation_id)
            version = item.get("version", "*")
            if not isinstance(version, str) or not version.strip():
                self.error(f"{relation}.version", f"Invalid version range for {relation_id}.")

    def _validate_content(
        self,
        content: dict[str, Any],
        capabilities: set[str],
        mod_id: str | None,
    ) -> None:
        maps = self._array(content, "maps")
        level_editor = self._array(content, "levelEditor")
        patches = self._array(content, "scenePatches")
        menus = self._array(content, "menus")
        localization = self._array(content, "localization")
        scripts = self._array(content, "scripts")
        tuning = content.get("playerTuning", {})

        self._require_capability(bool(maps), "maps", capabilities)
        self._require_capability(bool(level_editor), "level_editor", capabilities)
        self._require_capability(bool(menus), "menus", capabilities)
        self._require_capability(bool(localization), "localization", capabilities)
        if scripts:
            self.error("lua.unavailable", "Lua scripts are not supported by the current runtime.")

        map_ids: set[str] = set()
        map_paths: list[Path] = []
        for index, item in enumerate(maps):
            if not isinstance(item, dict):
                self.error("map.object", f"maps[{index}] must be an object.")
                continue
            map_id = item.get("id")
            if not isinstance(map_id, str) or not CONTENT_ID_PATTERN.fullmatch(map_id):
                self.error("map.id", f"Invalid map id at index {index}.")
            elif map_id in map_ids:
                self.error("map.duplicate", f"Duplicate map id: {map_id}")
            else:
                map_ids.add(map_id)
            map_path = self._validate_reference(item.get("file"), {".jfue"}, "map.file")
            if map_path:
                map_paths.append(map_path)
            if item.get("templateScene", "MapJfue") != "MapJfue":
                self.error("map.template", "templateScene must be MapJfue.")

        editor_piece_ids: set[str] = set()
        for raw in level_editor:
            path = self._validate_reference(raw, {".json"}, "level_editor.file")
            if path:
                self._validate_level_editor_file(path, mod_id, editor_piece_ids)

        allowed_map_piece_ids = set(LEVEL_EDITOR_PIECE_BASE_IDS)
        allowed_map_piece_ids.update(editor_piece_ids)
        for path in map_paths:
            self._validate_map_piece_ids(path, allowed_map_piece_ids)

        for raw in patches:
            path = self._validate_reference(raw, {".json"}, "scene_patch.file")
            if path:
                self._validate_patch_file(path, capabilities)

        for raw in menus:
            path = self._validate_reference(raw, {".json"}, "menu.file")
            if path:
                self._validate_menu_file(path, map_ids, capabilities)

        languages: set[str] = set()
        for index, item in enumerate(localization):
            if not isinstance(item, dict):
                self.error("localization.object", f"localization[{index}] must be an object.")
                continue
            language = item.get("language")
            if not isinstance(language, str) or not language.strip() or len(language) > 32:
                self.error("localization.language", f"Invalid language at index {index}.")
            elif language.lower() in languages:
                self.error("localization.duplicate", f"Duplicate language: {language}")
            else:
                languages.add(language.lower())
            path = self._validate_reference(item.get("file"), {".json"}, "localization.file")
            if path:
                self._validate_localization_file(path)

        if not isinstance(tuning, dict):
            self.error("mechanics.type", "playerTuning must be an object.")
            return
        is_default = True
        for key in ("moveSpeedMultiplier", "jumpForceMultiplier", "gravityMultiplier", "dashSpeedMultiplier"):
            value = tuning.get(key, 1.0)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.75 <= float(value) <= 1.25:
                self.error("mechanics.range", f"{key} must be between 0.75 and 1.25.")
            if value != 1 and value != 1.0:
                is_default = False
        jumps = tuning.get("maxJumpsDelta", 0)
        if not isinstance(jumps, int) or isinstance(jumps, bool) or jumps not in {-1, 0, 1}:
            self.error("mechanics.jumps", "maxJumpsDelta must be -1, 0, or 1.")
        if jumps != 0:
            is_default = False
        self._require_capability(not is_default, "mechanics", capabilities)

    def _validate_level_editor_file(
        self,
        path: Path,
        mod_id: str | None,
        qualified_ids: set[str],
    ) -> None:
        data = self._load_json(path, "level_editor.json")
        if not isinstance(data, dict):
            return
        pieces = data.get("pieces")
        if not isinstance(pieces, list):
            self.error("level_editor.root", f"{path.relative_to(self.root)} must contain a pieces array.")
            return
        if len(pieces) > 128:
            self.error("level_editor.count", "A level-editor file can contain at most 128 pieces.")

        local_ids: set[str] = set()
        for index, piece in enumerate(pieces):
            if not isinstance(piece, dict):
                self.error("level_editor.piece", f"Piece {index} must be an object.")
                continue
            piece_id = piece.get("id")
            if (
                not isinstance(piece_id, str)
                or not CONTENT_ID_PATTERN.fullmatch(piece_id)
                or piece_id in local_ids
            ):
                self.error("level_editor.id", f"Invalid or duplicate piece id at index {index}: {piece_id}")
                continue
            local_ids.add(piece_id)
            qualified_id = f"{mod_id}:{piece_id}" if mod_id else piece_id
            if qualified_id in qualified_ids:
                self.error("level_editor.duplicate", f"Duplicate piece across files: {piece_id}")
            qualified_ids.add(qualified_id)

            name = piece.get("name")
            if not isinstance(name, str) or not name.strip() or len(name) > 128:
                self.error("level_editor.name", f"Piece {piece_id} needs a name of 1-128 characters.")
            base_id = piece.get("baseId")
            if base_id not in LEVEL_EDITOR_PIECE_BASE_IDS:
                self.error("level_editor.base", f"Unsupported 2D baseId for {piece_id}: {base_id}")
            asset = piece.get("asset", "")
            if asset:
                self._validate_reference(asset, {".png", ".jpg", ".jpeg"}, "level_editor.asset")
            color = piece.get("color", "")
            if color and (not isinstance(color, str) or not COLOR_PATTERN.fullmatch(color)):
                self.error("level_editor.color", f"Invalid color for {piece_id}: {color}")
            ppu = piece.get("pixelsPerUnit", 100.0)
            if not self._is_number(ppu) or not 1 <= float(ppu) <= 1000:
                self.error("level_editor.ppu", f"pixelsPerUnit for {piece_id} must be 1-1000.")
            scale_x = piece.get("scaleX", 0.0)
            scale_y = piece.get("scaleY", 0.0)
            if not self._valid_optional_scale(scale_x) or not self._valid_optional_scale(scale_y):
                self.error("level_editor.scale", f"Scale for {piece_id} must inherit (0/0) or be 0.05-100.")
            elif (float(scale_x) == 0) != (float(scale_y) == 0):
                self.error("level_editor.scale_pair", f"scaleX and scaleY for {piece_id} must both inherit or both be set.")

    def _validate_map_piece_ids(self, path: Path, allowed_ids: set[str]) -> None:
        data = self._load_json(path, "map.json")
        if not isinstance(data, dict):
            return
        pieces = data.get("pieces", [])
        if not isinstance(pieces, list):
            self.error("map.pieces", f"{path.relative_to(self.root)} pieces must be an array.")
            return
        for index, piece in enumerate(pieces):
            if not isinstance(piece, dict):
                self.error("map.piece", f"{path.relative_to(self.root)} piece {index} must be an object.")
                continue
            piece_id = piece.get("id")
            if not isinstance(piece_id, str) or piece_id not in allowed_ids:
                self.error("map.piece_id", f"Unknown piece id in {path.relative_to(self.root)} at index {index}: {piece_id}")

    def _validate_patch_file(self, path: Path, capabilities: set[str]) -> None:
        data = self._load_json(path, "scene_patch.json")
        if not isinstance(data, dict):
            return
        patches = data.get("patches")
        if not isinstance(patches, list):
            self.error("scene_patch.root", f"{path.relative_to(self.root)} must contain a patches array.")
            return
        if len(patches) > 256:
            self.error("scene_patch.count", "A scene patch file can contain at most 256 patches.")
        for index, patch in enumerate(patches):
            if not isinstance(patch, dict):
                self.error("scene_patch.object", f"Patch {index} must be an object.")
                continue
            operation = patch.get("operation")
            if operation not in SCENE_OPERATIONS:
                self.error("scene_patch.operation", f"Unknown patch operation at index {index}: {operation}")
                continue
            selector = patch.get("target")
            if not self._safe_selector(selector):
                self.error("scene_patch.target", f"Patch target must begin with '/': {selector}")
            self._require_capability(True, "audio" if str(operation).startswith("set_audio") else "visuals", capabilities)
            if operation == "set_sprite":
                self._validate_reference(patch.get("asset"), {".png", ".jpg", ".jpeg"}, "scene_patch.asset")
            elif operation == "set_audio_clip":
                self._validate_reference(patch.get("asset"), {".wav", ".ogg"}, "scene_patch.asset")
            elif operation == "set_audio_volume":
                volume = patch.get("numberValue", 1.0)
                if not isinstance(volume, (int, float)) or not 0 <= float(volume) <= 1:
                    self.error("scene_patch.volume", "Audio volume must be between 0 and 1.")

    def _validate_menu_file(self, path: Path, map_ids: set[str], capabilities: set[str]) -> None:
        data = self._load_json(path, "menu.json")
        if not isinstance(data, dict):
            return
        menus = data.get("menus")
        if not isinstance(menus, list):
            self.error("menu.root", f"{path.relative_to(self.root)} must contain a menus array.")
            return
        if len(menus) > 8:
            self.error("menu.count", "A menu file can contain at most 8 layouts.")
        for menu_index, menu in enumerate(menus):
            if not isinstance(menu, dict):
                self.error("menu.object", f"Menu {menu_index} must be an object.")
                continue
            if menu.get("surface") not in {"main", "pause"}:
                self.error("menu.surface", "Menu surface must be main or pause.")
            menu_id = menu.get("id")
            if not isinstance(menu_id, str) or not CONTENT_ID_PATTERN.fullmatch(menu_id):
                self.error("menu.id", f"Invalid menu id: {menu_id}")
            for selector in menu.get("hideTargets", []):
                if not self._safe_selector(selector):
                    self.error("menu.hide_target", f"hideTargets selector must begin with '/': {selector}")
            elements = menu.get("elements", [])
            if not isinstance(elements, list) or len(elements) > 128:
                self.error("menu.elements", "Menu elements must be an array with at most 128 entries.")
                continue
            seen: set[str] = set()
            for element_index, element in enumerate(elements):
                if not isinstance(element, dict):
                    self.error("menu.element", f"Element {element_index} must be an object.")
                    continue
                element_id = element.get("id")
                if not isinstance(element_id, str) or not CONTENT_ID_PATTERN.fullmatch(element_id) or element_id in seen:
                    self.error("menu.element_id", f"Invalid or duplicate menu element id: {element_id}")
                else:
                    seen.add(element_id)
                parent = element.get("parent", "")
                if parent and parent not in seen:
                    self.error("menu.parent", f"Parent must reference an earlier element: {parent}")
                if element.get("type") not in MENU_TYPES:
                    self.error("menu.element_type", f"Unknown menu element type: {element.get('type')}")
                action = element.get("action", "")
                if action not in MENU_ACTIONS:
                    self.error("menu.action", f"Unknown menu action: {action}")
                if action == "load_map" and element.get("target") not in map_ids:
                    self.error("menu.map", "load_map target must reference a map in the same mod.")
                if action in {"set_active", "toggle_active"} and not self._safe_selector(element.get("target")):
                    self.error("menu.target", "set/toggle_active target must begin with '/'.")
                asset = element.get("asset", "")
                if asset:
                    self._require_capability(True, "visuals", capabilities)
                    self._validate_reference(asset, {".png", ".jpg", ".jpeg"}, "menu.asset")

    def _validate_localization_file(self, path: Path) -> None:
        data = self._load_json(path, "localization.json")
        if not isinstance(data, dict):
            return
        items = data.get("items")
        if not isinstance(items, list):
            self.error("localization.root", f"{path.relative_to(self.root)} must contain an items array.")
            return
        if len(items) > 5000:
            self.error("localization.count", "A localization file can contain at most 5000 items.")
        seen: set[str] = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                self.error("localization.item", f"Localization item {index} must be an object.")
                continue
            key = item.get("key")
            value = item.get("value")
            if not isinstance(key, str) or not key.strip() or len(key) > 256 or key in seen:
                self.error("localization.key", f"Invalid or duplicate localization key at index {index}.")
            else:
                seen.add(key)
            if not isinstance(value, str) or len(value) > 4096:
                self.error("localization.value", f"Localization value {index} must be a string up to 4096 characters.")

    def _load_json(self, path: Path, code: str) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            self.error(code, f"{path.relative_to(self.root)}: {exc}")
            return None

    def _validate_reference(self, raw: Any, extensions: set[str], code: str) -> Path | None:
        if not isinstance(raw, str) or not raw.strip():
            self.error(code, "Referenced path is empty.")
            return None
        relative = Path(raw.replace("\\", "/"))
        if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
            self.error(code, f"Path must remain inside the package: {raw}")
            return None
        candidate = (self.root / relative).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            self.error(code, f"Path escapes the package: {raw}")
            return None
        if candidate.suffix.lower() not in extensions:
            self.error(code, f"Expected {sorted(extensions)}: {raw}")
            return None
        if not candidate.is_file() or candidate.is_symlink():
            self.error(code, f"Referenced file is missing or linked: {raw}")
            return None
        return candidate

    def _require_capability(self, used: bool, capability: str, declared: set[str]) -> None:
        if used and capability not in declared:
            self.error("capability.required", f"Content uses undeclared capability: {capability}")

    def _require_string(self, obj: dict[str, Any], key: str, maximum: int) -> str | None:
        value = obj.get(key)
        if not isinstance(value, str) or not value.strip():
            self.error(f"manifest.{key}", f"{key} is required and must be a string.")
            return None
        if len(value) > maximum:
            self.error(f"manifest.{key}", f"{key} exceeds {maximum} characters.")
        return value.strip()

    def _optional_string(self, obj: dict[str, Any], key: str, maximum: int) -> None:
        value = obj.get(key, "")
        if not isinstance(value, str):
            self.error(f"manifest.{key}", f"{key} must be a string.")
        elif len(value) > maximum:
            self.error(f"manifest.{key}", f"{key} exceeds {maximum} characters.")

    def _array(self, obj: dict[str, Any], key: str) -> list[Any]:
        value = obj.get(key, [])
        if not isinstance(value, list):
            self.error(f"content.{key}", f"{key} must be an array.")
            return []
        return value

    @staticmethod
    def _is_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @classmethod
    def _valid_optional_scale(cls, value: Any) -> bool:
        return cls._is_number(value) and (float(value) == 0 or 0.05 <= float(value) <= 100)

    @staticmethod
    def _safe_selector(value: Any) -> bool:
        return isinstance(value, str) and value.startswith("/") and "//" not in value and "/../" not in value

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, int, int]:
        pieces = value.split(".")
        return int(pieces[0]), int(pieces[1]), int(pieces[2])

    @staticmethod
    def _is_ignored(path: Path) -> bool:
        return path.name in IGNORED_NAMES or "__MACOSX" in path.parts or "__pycache__" in path.parts

    @staticmethod
    def _maximum_for_file(path: Path) -> int:
        if path.name.lower() == MANIFEST_NAME:
            return MAX_MANIFEST_BYTES
        extension = path.suffix.lower()
        if extension in {".png", ".jpg", ".jpeg"}:
            return MAX_IMAGE_BYTES
        if extension in {".wav", ".ogg"}:
            return MAX_AUDIO_BYTES
        return MAX_SINGLE_FILE_BYTES


def iter_package_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if Validator._is_ignored(path) or not path.is_file():
            continue
        yield path


def validate_command(folder: Path) -> int:
    validator = Validator(folder)
    valid = validator.validate()
    for problem in validator.problems:
        print(problem)
    if valid:
        print(f"[OK] Valid JumpFall mod for SDK {SDK_VERSION}.")
        return 0
    print("[FAILED] Mod validation failed.")
    return 1


def pack_command(folder: Path, output: Path | None) -> int:
    validator = Validator(folder)
    if not validator.validate():
        for problem in validator.problems:
            print(problem)
        print("[FAILED] Package was not created.")
        return 1

    assert validator.manifest is not None
    mod_id = str(validator.manifest["id"])
    version = str(validator.manifest["version"])
    destination = output or folder.parent / f"{mod_id}-{version}{PACKAGE_EXTENSION}"
    if destination.suffix.lower() != PACKAGE_EXTENSION:
        destination = destination.with_suffix(PACKAGE_EXTENSION)
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        destination.unlink()

    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in iter_package_files(folder.resolve()):
            archive.write(path, path.relative_to(folder.resolve()).as_posix())

    if destination.stat().st_size > MAX_PACKAGE_BYTES:
        destination.unlink(missing_ok=True)
        print("[FAILED] Compressed package exceeds 256 MiB.")
        return 1

    print(f"[OK] Created {destination}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jumpfall-sdk", description="Validate and package JumpFall .jfmod mods.")
    parser.add_argument("--version", action="version", version=f"JumpFall SDK {SDK_VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a mod folder.")
    validate_parser.add_argument("folder", type=Path)

    pack_parser = subparsers.add_parser("pack", help="Validate and create a .jfmod archive.")
    pack_parser.add_argument("folder", type=Path)
    pack_parser.add_argument("-o", "--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        return validate_command(args.folder)
    if args.command == "pack":
        return pack_command(args.folder, args.output)
    return 2


if __name__ == "__main__":
    sys.exit(main())
