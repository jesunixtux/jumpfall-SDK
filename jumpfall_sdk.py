#!/usr/bin/env python3
"""JumpFall SDK 1.0 validator and .jfmod packer.

Uses only Python's standard library so mod authors do not need Unity.
"""

from __future__ import annotations

import argparse
import json
import math
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
MAP_CURRENT_VERSION = 29
MAX_IMAGE_DIMENSION = 4096
MAX_BOSSES_PER_MAP = 8
MAX_BOSS_NODES = 128

MAX_PACKAGE_BYTES = 256 * 1024 * 1024
MAX_EXPANDED_BYTES = 512 * 1024 * 1024
MAX_SINGLE_FILE_BYTES = 128 * 1024 * 1024
MAX_MANIFEST_BYTES = 256 * 1024
MAX_IMAGE_BYTES = 32 * 1024 * 1024
MAX_AUDIO_BYTES = 64 * 1024 * 1024
MAX_MAP_BYTES = 16 * 1024 * 1024
MAX_FILES = 2000
MAX_GHOSTS_PER_MAP = 32
MAX_GHOST_FRAMES = 18000
MAX_GHOST_SECONDS = 600.0

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
RESTRICTED_SELECTOR_FRAGMENTS = {
    "player",
    "rigidbody",
    "collider",
    "camera",
    "spawn",
    "loading",
    "modruntime",
    "modmanager",
    "eventsystem",
    "inputsystem",
}
LEVEL_EDITOR_PIECE_BASE_IDS = {
    "box_ground",
    "checkpoint",
    "apple",
    "orb_jump",
    "plane_jump",
    "elevator",
}
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
CANONICAL_LANGUAGES = ("english", "spanishlatam", "spanishspain", "portuguese")
# Mirrors ModContentRuntime.NormalizeLanguage: punctuation/spacing removed,
# then matched case-insensitively. Unknown input returns None.
_LANGUAGE_ALIASES = {
    "en": "english",
    "english": "english",
    "es": "spanishlatam",
    "es419": "spanishlatam",
    "spanish": "spanishlatam",
    "spanishlatam": "spanishlatam",
    "latam": "spanishlatam",
    "espanol": "spanishlatam",
    "eses": "spanishspain",
    "spanishspain": "spanishspain",
    "espanolespana": "spanishspain",
    "pt": "portuguese",
    "ptbr": "portuguese",
    "portuguese": "portuguese",
    "portugues": "portuguese",
    "brazilian": "portuguese",
}
LEVEL_TRIGGER_IDS = {
    "limit_map",
    "deathzone",
    "changelevel",
    "finish_level",
    "lua_event",
    "static_camera",
    "visibility",
    "event",
    "timer",
    "wall_jump",
    "light",
}
LEVEL_EVENT_ACTIONS = {
    "set_light",
    "set_active",
    "set_renderer",
    "set_collider",
    "animator_trigger",
    "animator_bool",
    "animator_play",
    "finish_level",
    "level_event",
}
CONTENT_ARRAY_LIMITS = {
    "maps": 128,
    "levelEditor": 16,
    "scenePatches": 32,
    "menus": 16,
    "localization": 16,
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
        seen_case_insensitive: set[str] = set()
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

            problem = self._tree_name_problem(relative, seen_case_insensitive)
            if problem == "package.case_collision":
                self.error(problem, f"Path collides case-insensitively (breaks on Windows/macOS): {relative}")
            elif problem is not None:
                self.error(problem, f"Unsafe file name for Windows extraction: {relative}")

            size = path.stat().st_size
            total += size
            if size > self._maximum_for_file(path):
                self.error("package.file_size", f"File exceeds its limit: {relative}")
            if total > MAX_EXPANDED_BYTES:
                self.error("package.total_size", "Expanded package exceeds 512 MiB.")
                break
            self._validate_media_content(path, relative, extension)

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
        known = self._version_tuple(KNOWN_GAME_VERSION)
        if isinstance(minimum, str) and GAME_VERSION_PATTERN.fullmatch(minimum):
            if self._version_tuple(minimum) > known:
                self.warning(
                    "game_version.newer_required",
                    f"gameVersion.min {minimum} is newer than SDK-known {KNOWN_GAME_VERSION}; "
                    "current players cannot activate this mod.",
                )
        if isinstance(maximum, str) and maximum and GAME_VERSION_PATTERN.fullmatch(maximum):
            if self._version_tuple(maximum) < known:
                self.warning(
                    "game_version.older_supported",
                    f"gameVersion.max {maximum} is older than SDK-known {KNOWN_GAME_VERSION}; "
                    "players on newer builds will be rejected as too_new.",
                )

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
            if (
                not isinstance(version, str)
                or not version.strip()
                or not self._is_valid_version_range(version)
            ):
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

        arrays = {
            "maps": maps,
            "levelEditor": level_editor,
            "scenePatches": patches,
            "menus": menus,
            "localization": localization,
        }
        counts_valid = True
        for name, maximum in CONTENT_ARRAY_LIMITS.items():
            if len(arrays[name]) > maximum:
                self.error("content.count", f"{name} contains more than {maximum} entries.")
                counts_valid = False
        if not counts_valid:
            return

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
        if len(editor_piece_ids) > 512:
            self.error("level_editor.total_count", "A mod can register at most 512 level-editor pieces.")

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
                continue
            canonical = self._normalize_language(language)
            if canonical is None:
                self.warning(
                    "localization.unknown_language",
                    f"Unknown language '{language}' at index {index}; the game only "
                    f"applies {', '.join(CANONICAL_LANGUAGES)} (aliases included) and will ignore this file.",
                )
                if language.lower() in languages:
                    self.error("localization.duplicate", f"Duplicate language: {language}")
                else:
                    languages.add(language.lower())
            elif canonical in languages:
                self.error(
                    "localization.duplicate",
                    f"Duplicate language: '{language}' normalizes to '{canonical}', already declared.",
                )
            else:
                languages.add(canonical)
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
        version = data.get("version")
        if version is None:
            self.warning("map.version_missing", f"{path.relative_to(self.root)} has no version; assuming legacy map.")
        elif not isinstance(version, int) or isinstance(version, bool):
            self.error("map.version", f"{path.relative_to(self.root)} version must be an integer.")
        elif version > MAP_CURRENT_VERSION:
            self.error(
                "map.version_future",
                f"{path.relative_to(self.root)} is version {version}; this SDK supports up to {MAP_CURRENT_VERSION}. "
                "Newer maps must be rejected, never normalized.",
            )
        elif version < MAP_CURRENT_VERSION:
            self.warning(
                "map.version_legacy",
                f"{path.relative_to(self.root)} is version {version}; current is {MAP_CURRENT_VERSION}.",
            )
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
        triggers = data.get("triggers", [])
        backgrounds = data.get("backgrounds", [])
        ghosts = data.get("ghosts", [])
        soundtrack = data.get("soundtrack", {})
        tracks = soundtrack.get("tracks", []) if isinstance(soundtrack, dict) else []
        if len(pieces) > 10000:
            self.error("map.piece_count", f"{path.relative_to(self.root)} contains more than 10000 pieces.")
        if not isinstance(triggers, list) or len(triggers) > 2000:
            self.error("map.trigger_count", f"{path.relative_to(self.root)} triggers must be an array with at most 2000 entries.")
        elif isinstance(triggers, list):
            self._validate_map_triggers(path, triggers)
        if not isinstance(backgrounds, list) or len(backgrounds) > 256:
            self.error("map.background_count", f"{path.relative_to(self.root)} backgrounds must be an array with at most 256 entries.")
        elif isinstance(backgrounds, list):
            self._validate_map_asset_refs(path, backgrounds, "fileName", "map.background_asset")
        if not isinstance(tracks, list) or len(tracks) > 256:
            self.error("map.soundtrack_count", f"{path.relative_to(self.root)} soundtrack tracks must be an array with at most 256 entries.")
        elif isinstance(tracks, list):
            for track_index, track in enumerate(tracks):
                if isinstance(track, dict) and "volume" in track:
                    volume = track["volume"]
                    if not self._number_in_range(volume, 0.0, 1.0):
                        self.error("map.soundtrack_volume", f"{path.relative_to(self.root)} track {track_index} volume must be 0-1.")
            self._validate_map_asset_refs(path, tracks, "fileName", "map.soundtrack_asset")
        self._validate_map_ghosts(path, ghosts)
        self._validate_map_bosses(path, data.get("bosses", []))
        self._validate_map_lights(path, data.get("lights"), triggers)
        lua = data.get("lua")
        if isinstance(lua, dict) and lua.get("enabled"):
            self.warning("map.lua_disabled", f"Lua is enabled in {path.relative_to(self.root)} but will be disabled in .jfmod runtime.")

    def _validate_map_asset_refs(self, path: Path, entries: list[Any], field: str, code: str) -> None:
        """Background/track fileName should resolve inside the package (warning-level)."""
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            raw = entry.get(field)
            if not raw:
                continue
            if not isinstance(raw, str):
                self.warning(code, f"{path.relative_to(self.root)} entry {index} has a non-string {field}.")
                continue
            candidate = (self.root / Path(raw.replace("\\", "/"))).resolve()
            try:
                candidate.relative_to(self.root)
                exists = candidate.is_file()
            except ValueError:
                exists = False
            if not exists:
                sibling = (path.parent / Path(raw.replace("\\", "/"))).resolve()
                try:
                    sibling.relative_to(self.root)
                    exists = sibling.is_file()
                except ValueError:
                    exists = False
            if not exists:
                self.warning(code, f"{path.relative_to(self.root)} entry {index} references missing asset: {raw}")

    def _validate_map_bosses(self, path: Path, bosses: Any) -> None:
        relative = path.relative_to(self.root)
        if not isinstance(bosses, list):
            self.error("map.boss_count", f"{relative} bosses must be an array with at most {MAX_BOSSES_PER_MAP} entries.")
            return
        if len(bosses) > MAX_BOSSES_PER_MAP:
            self.error("map.boss_count", f"{relative} contains more than {MAX_BOSSES_PER_MAP} bosses.")
        seen: set[str] = set()
        for index, boss in enumerate(bosses):
            if not isinstance(boss, dict):
                self.error("map.boss", f"{relative} boss {index} must be an object.")
                continue
            object_id = boss.get("objectId")
            if not isinstance(object_id, str) or not object_id.strip():
                self.warning("map.boss_id", f"{relative} boss {index} has no objectId; triggers cannot target it.")
            elif object_id in seen:
                self.error("map.boss_duplicate", f"{relative} duplicate boss objectId: {object_id}")
            else:
                seen.add(object_id)
            nodes = boss.get("nodes", [])
            if not isinstance(nodes, list) or len(nodes) > MAX_BOSS_NODES:
                self.error("map.boss_nodes", f"{relative} boss {index} nodes must be an array with at most {MAX_BOSS_NODES} entries.")

    def _validate_map_triggers(self, path: Path, triggers: list[Any]) -> None:
        relative = path.relative_to(self.root)
        for index, trigger in enumerate(triggers):
            if not isinstance(trigger, dict):
                self.error("map.trigger", f"{relative} trigger {index} must be an object.")
                continue

            trigger_id = trigger.get("id")
            if trigger_id not in LEVEL_TRIGGER_IDS:
                self.error("map.trigger_id", f"Unknown trigger id in {relative} at index {index}: {trigger_id}")
                continue
            if trigger_id not in {"event", "timer", "light"}:
                continue

            action = trigger.get("eventAction", "set_active")
            if action not in LEVEL_EVENT_ACTIONS:
                self.error("map.event_action", f"Unsafe or unknown event action in {relative} at trigger {index}: {action}")
            delay = trigger.get("eventDelaySeconds", 0.0)
            if not self._number_in_range(delay, 0.0, 3600.0):
                self.error("map.event_delay", f"Event delay in {relative} at trigger {index} must be 0-3600 seconds.")
            if action == "level_event":
                event_id = trigger.get("eventId")
                if not isinstance(event_id, str) or not CONTENT_ID_PATTERN.fullmatch(event_id):
                    self.error("map.event_id", f"Invalid safe eventId in {relative} at trigger {index}: {event_id}")

    def _validate_map_lights(self, path: Path, lights: Any, triggers: Any) -> None:
        # Optional v29 addition. Legacy maps and null lists remain valid.
        if lights is None:
            lights = []
        relative = path.relative_to(self.root)
        if not isinstance(lights, list) or len(lights) > 256:
            self.error("map.light_count", f"{relative} lights must be an array of at most 256 lights in mods.")
            return
        ids: set[str] = set()
        for index, light in enumerate(lights):
            if not isinstance(light, dict):
                self.error("map.light", f"{relative} light {index} must be an object.")
                continue
            object_id = light.get("objectId")
            if not isinstance(object_id, str) or not object_id or object_id in ids:
                self.error("map.light_id", f"{relative} light {index} needs a unique objectId.")
            else:
                ids.add(object_id)
            shape = light.get("shape", "radial")
            if not isinstance(shape, str) or shape not in {"radial", "spot", "rectangle", "freeform"}:
                self.error("map.light_shape", f"{relative} light {index} has unknown shape: {shape}")
            limits = {"px": (-100000, 100000), "py": (-100000, 100000), "rotZ": (0, 360),
                      "width": (0.05, 200), "height": (0.05, 200),
                      "range": (0.05 if shape in ("radial", "spot") else 0, 200),
                      "intensity": (0, 8), "falloff": (0, 1), "innerRadius": (0, 200),
                      "innerAngle": (0, 360), "outerAngle": (1, 360),
                      "lightOrder": (-32767, 32767), "blendStyle": (0, 3)}
            for key, (minimum, maximum) in limits.items():
                if key in light and not self._number_in_range(light[key], minimum, maximum):
                    self.error("map.light_value", f"{relative} light {index} {key} must be finite in [{minimum}, {maximum}].")
            for key in ("lightOrder", "blendStyle"):
                if key in light and (not isinstance(light[key], int) or isinstance(light[key], bool)):
                    self.error("map.light_value", f"{relative} light {index} {key} must be an integer.")
            if "color" in light:
                color = light["color"]
                if not isinstance(color, dict) or any(not self._number_in_range(color.get(channel), 0, 1) for channel in "rgba"):
                    self.error("map.light_color", f"{relative} light {index} requires RGBA channels in [0, 1].")
            if "vertices" in light:
                vertices = light["vertices"]
                if not isinstance(vertices, list) or not 3 <= len(vertices) <= 32 or any(
                    not isinstance(v, dict) or not self._number_in_range(v.get("x"), -0.5, 0.5) or
                    not self._number_in_range(v.get("y"), -0.5, 0.5) for v in vertices
                ):
                    self.error("map.light_vertices", f"{relative} light {index} requires 3-32 normalized vertices.")
        for index, trigger in enumerate(triggers if isinstance(triggers, list) else []):
            if not isinstance(trigger, dict) or not (trigger.get("id") == "light" or trigger.get("eventAction") == "set_light"):
                continue
            if trigger.get("eventAction") != "set_light" or trigger.get("eventValue", "on") not in ("on", "off", "toggle"):
                self.error("map.light_action", f"{relative} trigger {index} requires set_light with on/off/toggle.")
            target = trigger.get("eventTargetObjectId")
            if not isinstance(target, str) or target not in ids:
                self.warning("map.light_target", f"{relative} trigger {index} has no valid light target; it will safely do nothing.")

    def _validate_map_ghosts(self, path: Path, ghosts: Any) -> None:
        relative = path.relative_to(self.root)
        if not isinstance(ghosts, list):
            self.error("map.ghost_count", f"{relative} ghosts must be an array with at most {MAX_GHOSTS_PER_MAP} entries.")
            return
        if len(ghosts) > MAX_GHOSTS_PER_MAP:
            self.error("map.ghost_count", f"{relative} contains more than {MAX_GHOSTS_PER_MAP} ghost players.")

        names: set[str] = set()
        for index, ghost in enumerate(ghosts):
            if not isinstance(ghost, dict):
                self.error("map.ghost", f"{relative} ghost {index} must be an object.")
                continue

            name = ghost.get("displayName")
            if not isinstance(name, str) or not CONTENT_ID_PATTERN.fullmatch(name):
                self.error("map.ghost_name", f"Invalid ghost displayName in {relative} at index {index}: {name}")
            elif name in names:
                self.error("map.ghost_duplicate", f"Duplicate ghost displayName in {relative}: {name}")
            else:
                names.add(name)

            ranges = {
                "startDelay": (0.0, 3600.0),
                "playbackSpeed": (0.05, 8.0),
                "opacity": (0.05, 1.0),
                "sampleInterval": (1.0 / 60.0, 0.25),
            }
            for field, (minimum, maximum) in ranges.items():
                value = ghost.get(field, minimum)
                if not self._number_in_range(value, minimum, maximum):
                    self.error("map.ghost_range", f"{field} is outside {minimum}-{maximum} in {relative} ghost {index}.")
            for field in ("autoPlay", "loop", "visible"):
                if field in ghost and not isinstance(ghost[field], bool):
                    self.error("map.ghost_type", f"{field} must be boolean in {relative} ghost {index}.")
            sorting_order = ghost.get("sortingOrder", 120)
            if not isinstance(sorting_order, int) or isinstance(sorting_order, bool) or not -1000 <= sorting_order <= 30000:
                self.error("map.ghost_range", f"sortingOrder must be an integer from -1000 to 30000 in {relative} ghost {index}.")

            frames = ghost.get("frames")
            if not isinstance(frames, list):
                self.error("map.ghost_frames", f"{relative} ghost {index} frames must be an array.")
                continue
            if len(frames) < 2:
                self.error("map.ghost_frames", f"{relative} ghost {index} must contain at least two frames.")
            if len(frames) > MAX_GHOST_FRAMES:
                self.error("map.ghost_frames", f"{relative} ghost {index} contains more than {MAX_GHOST_FRAMES} frames.")

            previous_time = 0.0
            for frame_index, frame in enumerate(frames):
                if not isinstance(frame, dict):
                    self.error("map.ghost_frame", f"{relative} ghost {index} frame {frame_index} must be an object.")
                    continue
                time_value = frame.get("time")
                if not self._number_in_range(time_value, previous_time, MAX_GHOST_SECONDS):
                    self.error("map.ghost_time", f"Invalid or non-monotonic time in {relative} ghost {index} frame {frame_index}.")
                else:
                    previous_time = float(time_value)
                for field in ("px", "py", "rotZ", "sx", "sy"):
                    if not self._is_number(frame.get(field)):
                        self.error("map.ghost_frame", f"Invalid {field} in {relative} ghost {index} frame {frame_index}.")
                for field in ("sx", "sy"):
                    if self._is_number(frame.get(field)) and not 0.01 <= float(frame[field]) <= 100.0:
                        self.error("map.ghost_scale", f"Invalid {field} scale in {relative} ghost {index} frame {frame_index}.")
                animator_hash = frame.get("animatorStateHash", 0)
                if not isinstance(animator_hash, int) or isinstance(animator_hash, bool):
                    self.error("map.ghost_animation", f"Invalid animatorStateHash in {relative} ghost {index} frame {frame_index}.")
                animator_time = frame.get("animatorNormalizedTime", 0.0)
                if not self._number_in_range(animator_time, 0.0, 100000.0):
                    self.error("map.ghost_animation", f"Invalid animatorNormalizedTime in {relative} ghost {index} frame {frame_index}.")

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
                self.error("scene_patch.target", f"Patch target must be an exact, non-restricted path beginning with '/': {selector}")
            scene = patch.get("scene", "*")
            if not isinstance(scene, str) or not scene.strip() or len(scene) > 128:
                self.error("scene_patch.scene", f"Patch scene must be '*' or a name up to 128 characters at index {index}.")
            value = patch.get("value", "")
            if not isinstance(value, str) or len(value) > 4096:
                self.error("scene_patch.value", f"Patch value must be a string up to 4096 characters at index {index}.")
            localization_key = patch.get("localizationKey", "")
            if not isinstance(localization_key, str) or len(localization_key) > 256:
                self.error("scene_patch.localization_key", f"Patch localizationKey must be a string up to 256 characters at index {index}.")
            self._require_capability(True, "audio" if str(operation).startswith("set_audio") else "visuals", capabilities)
            if operation == "set_sprite":
                self._validate_reference(patch.get("asset"), {".png", ".jpg", ".jpeg"}, "scene_patch.asset")
            elif operation == "set_audio_clip":
                self._validate_reference(patch.get("asset"), {".wav", ".ogg"}, "scene_patch.asset")
            elif operation == "set_audio_volume":
                volume = patch.get("numberValue", 1.0)
                if not isinstance(volume, (int, float)) or not 0 <= float(volume) <= 1:
                    self.error("scene_patch.volume", "Audio volume must be between 0 and 1.")
            elif operation == "set_color":
                if not isinstance(value, str) or not COLOR_PATTERN.fullmatch(value):
                    self.error("scene_patch.color", f"set_color value must be #RRGGBB or #RRGGBBAA at index {index} (runtime ignores invalid colors).")

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
                    self.error("menu.hide_target", f"hideTargets must use an exact, non-restricted path: {selector}")
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
                    self.error("menu.target", "set/toggle_active target must be an exact, non-restricted path beginning with '/'.")
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
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )

    @classmethod
    def _number_in_range(cls, value: Any, minimum: float, maximum: float) -> bool:
        return cls._is_number(value) and minimum <= float(value) <= maximum

    @classmethod
    def _valid_optional_scale(cls, value: Any) -> bool:
        return cls._is_number(value) and (float(value) == 0 or 0.05 <= float(value) <= 100)

    @staticmethod
    def _safe_selector(value: Any) -> bool:
        if not isinstance(value, str) or not value.startswith("/") or len(value) > 512:
            return False
        pieces = value.split("/")[1:]
        if not pieces:
            return False
        for piece in pieces:
            if not piece.strip() or piece in {".", ".."}:
                return False
            normalized = "".join(character for character in piece.lower() if character.isalnum())
            if any(fragment in normalized for fragment in RESTRICTED_SELECTOR_FRAGMENTS):
                return False
        return True

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, int, int]:
        pieces = value.split(".")
        return int(pieces[0]), int(pieces[1]), int(pieces[2])

    @staticmethod
    def _tree_name_problem(relative: Path, seen_case_insensitive: set[str]) -> str | None:
        lowered = relative.as_posix().lower()
        if lowered in seen_case_insensitive:
            return "package.case_collision"
        seen_case_insensitive.add(lowered)
        for part in relative.parts:
            stem = part.rsplit(".", 1)[0] if "." in part else part
            if stem.upper() in WINDOWS_RESERVED_NAMES:
                return "package.reserved_name"
            if part != part.strip() or part.endswith("."):
                return "package.trailing_name"
        return None

    def _validate_media_content(self, path: Path, relative: Path, extension: str) -> None:
        if extension in {".png", ".jpg", ".jpeg"}:
            try:
                dimensions = self._image_dimensions(path, extension)
            except OSError as exc:
                self.warning("package.image_unreadable", f"{relative}: cannot read image header ({exc})")
                return
            if dimensions is None:
                self.error("package.image_magic", f"{relative} is not a valid PNG/JPEG file.")
            else:
                width, height = dimensions
                if width < 1 or height < 1 or width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                    self.error(
                        "package.image_dimensions",
                        f"{relative} is {width}x{height}; images must be 1-4096 px per side.",
                    )
        elif extension in {".wav", ".ogg"}:
            try:
                with open(path, "rb") as handle:
                    magic = handle.read(12)
            except OSError as exc:
                self.warning("package.audio_unreadable", f"{relative}: cannot read audio header ({exc})")
                return
            valid = magic[:4] == b"OggS" if extension == ".ogg" else (
                len(magic) >= 12 and magic[:4] == b"RIFF" and magic[8:12] == b"WAVE"
            )
            if not valid:
                self.error("package.audio_magic", f"{relative} is not a valid {'Ogg' if extension == '.ogg' else 'WAV'} file.")

    @staticmethod
    def _image_dimensions(path: Path, extension: str) -> tuple[int, int] | None:
        """Read PNG/JPEG dimensions from headers only (stdlib, no image deps)."""
        with open(path, "rb") as handle:
            if extension == ".png":
                header = handle.read(33)
                if len(header) < 33 or header[:8] != b"\x89PNG\r\n\x1a\n":
                    return None
                if header[12:16] != b"IHDR":
                    return None
                return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")
            if handle.read(2) != b"\xff\xd8":
                return None
            budget = 1024 * 1024
            while budget > 0:
                marker_start = handle.read(1)
                budget -= 1
                if not marker_start:
                    return None
                if marker_start != b"\xff":
                    continue
                marker = handle.read(1)
                budget -= 1
                if not marker or marker == b"\x00":
                    continue
                code = marker[0]
                if code == 0xD8 or code == 0xD9 or 0xD0 <= code <= 0xD7 or code == 0x01:
                    continue
                length_bytes = handle.read(2)
                budget -= 2
                if len(length_bytes) < 2:
                    return None
                length = int.from_bytes(length_bytes, "big")
                if length < 2:
                    return None
                if code in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                            0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    body = handle.read(5)
                    if len(body) < 5:
                        return None
                    return (
                        int.from_bytes(body[3:5], "big"),
                        int.from_bytes(body[1:3], "big"),
                    )
                handle.seek(length - 2, 1)
                budget -= length - 2
            return None
        return None

    @staticmethod
    def _normalize_language(value: str) -> str | None:
        """Mirror ModContentRuntime.NormalizeLanguage; None = unknown to the game."""
        normalized = re.sub(r"[-_ ]", "", value.strip().lower())
        return _LANGUAGE_ALIASES.get(normalized)

    @classmethod
    def _is_valid_version_range(cls, value: str) -> bool:
        """Mirror ModVersionRange.TryValidate: *, ||, space/comma tokens, ^ ~ ops, wildcards."""
        text = value.strip()
        if not text or text == "*":
            return True
        for alternative in text.split("||"):
            normalized = alternative.replace(",", " ").strip()
            if not normalized:
                return False
            if not all(cls._is_valid_range_token(token) for token in normalized.split()):
                return False
        return True

    @classmethod
    def _is_valid_range_token(cls, token: str) -> bool:
        if token == "*" or token.lower() == "x":
            return True
        if token.startswith("^") or token.startswith("~"):
            return (
                len(token) > 1
                and token[1] not in "^~"
                and cls._parse_semver(token[1:]) is not None
            )
        value = token
        for operator in (">=", "<=", ">", "<", "="):
            if token.startswith(operator):
                value = token[len(operator):]
                break
        if not value or value[0] in "><=^~":
            return False
        if "*" in value or "x" in value or "X" in value:
            return cls._is_valid_wildcard(value)
        return cls._parse_semver(value) is not None

    @staticmethod
    def _parse_semver(value: str) -> tuple[int, int, int, tuple, tuple] | None:
        """Mirror ModSemVersion.TryParse (strict: no leading zeros, prerelease rules)."""
        text = value.strip()
        if text[:1].lower() == "v":
            text = text[1:]
        build_index = text.find("+")
        if build_index >= 0:
            if build_index == len(text) - 1 or "+" in text[build_index + 1:]:
                return None
            for identifier in text[build_index + 1:].split("."):
                if not identifier or not all(c.isalnum() or c == "-" for c in identifier):
                    return None
            text = text[:build_index]
        prerelease: tuple = ()
        dash_index = text.find("-")
        if dash_index >= 0:
            for identifier in text[dash_index + 1:].split("."):
                if not identifier or not all(c.isalnum() or c == "-" for c in identifier):
                    return None
            prerelease = tuple(text[dash_index + 1:].split("."))
            text = text[:dash_index]
        pieces = text.split(".")
        if len(pieces) != 3:
            return None
        numbers = []
        for piece in pieces:
            if not piece or (len(piece) > 1 and piece[0] == "0") or not piece.isdigit():
                return None
            numbers.append(int(piece))
        return (numbers[0], numbers[1], numbers[2], prerelease, ())

    @staticmethod
    def _is_valid_wildcard(value: str) -> bool:
        pieces = value.split(".")
        if not 1 <= len(pieces) <= 3:
            return False
        saw_wildcard = False
        for piece in pieces:
            if piece == "*" or piece.lower() == "x":
                saw_wildcard = True
                continue
            if saw_wildcard or not piece or (len(piece) > 1 and piece[0] == "0") or not piece.isdigit():
                return False
        return saw_wildcard

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
        if extension == ".jfue":
            return MAX_MAP_BYTES
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
    source_root = folder.resolve()
    explicit_destination: Path | None = None
    if output is not None:
        explicit_destination = output
        if explicit_destination.suffix.lower() != PACKAGE_EXTENSION:
            explicit_destination = explicit_destination.with_suffix(PACKAGE_EXTENSION)
        explicit_destination = explicit_destination.resolve()
        try:
            explicit_destination.relative_to(source_root)
        except ValueError:
            pass
        else:
            print("[FAILED] Package output must be outside the mod source folder.")
            return 1

    validator = Validator(folder)
    valid = validator.validate()
    for problem in validator.problems:
        print(problem)
    if not valid:
        print("[FAILED] Package was not created.")
        return 1

    assert validator.manifest is not None
    mod_id = str(validator.manifest["id"])
    version = str(validator.manifest["version"])
    destination = explicit_destination or folder.parent / f"{mod_id}-{version}{PACKAGE_EXTENSION}"
    if destination.suffix.lower() != PACKAGE_EXTENSION:
        destination = destination.with_suffix(PACKAGE_EXTENSION)
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        destination.unlink()

    import datetime

    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    try:
        fixed_date = datetime.datetime.fromtimestamp(int(source_date_epoch), tz=datetime.timezone.utc)
    except (ValueError, OverflowError, OSError):
        fixed_date = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    fixed_stamp = (fixed_date.year, fixed_date.month, fixed_date.day,
                   fixed_date.hour, fixed_date.minute, fixed_date.second)

    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in iter_package_files(folder.resolve()):
            arcname = path.relative_to(folder.resolve()).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=fixed_stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())

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
