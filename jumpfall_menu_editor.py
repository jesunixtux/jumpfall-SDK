#!/usr/bin/env python3
"""Visual menu editor for JumpFall SDK 1.0.

The editor writes the same declarative menu JSON consumed by JumpFall's
Modding 1.0 runtime. It intentionally exposes only actions supported by the
runtime and delegates validation/packing to ``jumpfall_sdk.py``.

Python 3.10+ and Tk 8.6 are required. No third-party packages are used.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk

REFERENCE_WIDTH = 1920.0
REFERENCE_HEIGHT = 1080.0
DEFAULT_GRID = 10
MANIFEST_NAME = "jumpfall.mod.json"
MENU_TYPES = ("panel", "image", "text", "button")
MENU_ACTIONS = ("", "resume", "quit", "load_map", "set_active", "toggle_active")
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")


def default_element(element_type: str, element_id: str) -> dict[str, Any]:
    """Return a runtime-compatible menu element with safe defaults."""
    defaults: dict[str, tuple[float, float, str]] = {
        "panel": (520.0, 300.0, ""),
        "image": (520.0, 300.0, ""),
        "text": (520.0, 90.0, "Texto"),
        "button": (360.0, 72.0, "Botón"),
    }
    width, height, text = defaults.get(element_type, defaults["panel"])
    return {
        "id": element_id,
        "parent": "",
        "type": element_type,
        "text": text,
        "localizationKey": "",
        "asset": "",
        "color": "#FFFFFFFF" if element_type != "panel" else "#101820DD",
        "x": 0.0,
        "y": 0.0,
        "width": width,
        "height": height,
        "fontSize": 28,
        "action": "",
        "target": "",
        "value": "",
    }


def default_layout() -> dict[str, Any]:
    return {
        "id": "main-menu",
        "surface": "main",
        "scene": "Menugame",
        "hideTargets": [],
        "sortingOrder": 500,
        "elements": [
            {
                **default_element("panel", "panel"),
                "width": 760.0,
                "height": 460.0,
            },
            {
                **default_element("text", "title"),
                "parent": "panel",
                "text": "Mi menú de JumpFall",
                "y": 120.0,
                "width": 650.0,
                "fontSize": 36,
            },
            {
                **default_element("button", "play-button"),
                "parent": "panel",
                "text": "Jugar",
                "y": -40.0,
            },
        ],
    }


def default_manifest(mod_id: str, name: str, author: str) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0.0",
        "id": mod_id,
        "name": name,
        "version": "1.0.0",
        "author": author,
        "description": "Mod creado con JumpFall Visual Menu Editor.",
        "type": "content",
        "gameVersion": {"min": "0.50.05", "max": ""},
        "priority": 0,
        "dependencies": [],
        "conflicts": [],
        "capabilities": ["visuals", "menus"],
        "content": {
            "maps": [],
            "scenePatches": [],
            "menus": ["content/menus/main-menu.json"],
            "localization": [],
            "scripts": [],
            "playerTuning": {
                "moveSpeedMultiplier": 1.0,
                "jumpForceMultiplier": 1.0,
                "gravityMultiplier": 1.0,
                "dashSpeedMultiplier": 1.0,
                "maxJumpsDelta": 0,
            },
        },
    }


def safe_relative_path(root: Path, path: Path) -> str:
    root = root.resolve()
    path = path.resolve()
    return path.relative_to(root).as_posix()


def normalize_color(value: str, fallback: str = "#FFFFFFFF") -> str:
    value = (value or "").strip().upper()
    if re.fullmatch(r"#[0-9A-F]{6}", value):
        return value + "FF"
    if re.fullmatch(r"#[0-9A-F]{8}", value):
        return value
    return fallback


def color_for_tk(value: str) -> str:
    normalized = normalize_color(value)
    return normalized[:7]


def ensure_manifest_registration(mod_root: Path, menu_path: Path, uses_assets: bool) -> None:
    """Register a menu file and required capabilities in the mod manifest."""
    manifest_path = mod_root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise FileNotFoundError(f"No existe {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    content = manifest.setdefault("content", {})
    menus = content.setdefault("menus", [])
    relative = safe_relative_path(mod_root, menu_path)
    if relative not in menus:
        menus.append(relative)

    capabilities = manifest.setdefault("capabilities", [])
    if "menus" not in capabilities:
        capabilities.append("menus")
    if uses_assets and "visuals" not in capabilities:
        capabilities.append("visuals")

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def create_mod_project(folder: Path, mod_id: str, name: str, author: str) -> Path:
    """Create a minimal valid menu mod project and return its menu file."""
    if not ID_PATTERN.fullmatch(mod_id) or mod_id == "jumpfall":
        raise ValueError("El ID debe usar minúsculas, números, punto, guion o guion bajo (3–64 caracteres).")
    if not name.strip() or not author.strip():
        raise ValueError("Nombre y autor son obligatorios.")

    folder.mkdir(parents=True, exist_ok=True)
    menu_path = folder / "content" / "menus" / "main-menu.json"
    menu_path.parent.mkdir(parents=True, exist_ok=True)
    (folder / "assets" / "images").mkdir(parents=True, exist_ok=True)

    manifest_path = folder / MANIFEST_NAME
    if manifest_path.exists() or menu_path.exists():
        raise FileExistsError("La carpeta ya contiene un proyecto JumpFall o un menú con ese nombre.")

    manifest_path.write_text(
        json.dumps(default_manifest(mod_id, name.strip(), author.strip()), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    menu_path.write_text(
        json.dumps({"menus": [default_layout()]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (folder / "README.md").write_text(
        f"# {name.strip()}\n\nCreado con JumpFall Visual Menu Editor.\n",
        encoding="utf-8",
    )
    return menu_path


def discover_menu_from_manifest(mod_root: Path) -> Path | None:
    manifest_path = mod_root / MANIFEST_NAME
    if not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        menus = manifest.get("content", {}).get("menus", [])
        for raw in menus:
            if isinstance(raw, str):
                candidate = (mod_root / raw).resolve()
                if candidate.is_file():
                    return candidate
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return None


def load_layout_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    menus = data.get("menus") if isinstance(data, dict) else None
    if not isinstance(menus, list) or not menus or not isinstance(menus[0], dict):
        raise ValueError("El archivo debe contener un array 'menus' con al menos un layout.")
    layout = menus[0]
    layout.setdefault("id", "main-menu")
    layout.setdefault("surface", "main")
    layout.setdefault("scene", "Menugame")
    layout.setdefault("hideTargets", [])
    layout.setdefault("sortingOrder", 500)
    layout.setdefault("elements", [])
    if not isinstance(layout["elements"], list):
        raise ValueError("'elements' debe ser un array.")
    return layout


def save_layout_file(path: Path, layout: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"menus": [layout]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


@dataclass
class DragState:
    element_id: str = ""
    mode: str = ""
    start_canvas_x: float = 0.0
    start_canvas_y: float = 0.0
    start_x: float = 0.0
    start_y: float = 0.0
    start_width: float = 0.0
    start_height: float = 0.0


class ProjectDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Crear proyecto de mod")
        self.resizable(False, False)
        self.result: tuple[str, str, str] | None = None
        self.transient(parent)
        self.grab_set()

        self.vars = {
            "id": tk.StringVar(value="com.autor.mi-menu"),
            "name": tk.StringVar(value="Mi menú de JumpFall"),
            "author": tk.StringVar(value="Tu nombre"),
        }
        labels = (("ID del mod", "id"), ("Nombre", "name"), ("Autor", "author"))
        frame = ttk.Frame(self, padding=14)
        frame.grid(sticky="nsew")
        for row, (label, key) in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            ttk.Entry(frame, textvariable=self.vars[key], width=42).grid(row=row, column=1, sticky="ew", pady=5)

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(labels), column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Crear", command=self._accept).pack(side="right")
        self.bind("<Return>", lambda _event: self._accept())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.wait_visibility()
        self.focus_force()

    def _accept(self) -> None:
        mod_id = self.vars["id"].get().strip()
        name = self.vars["name"].get().strip()
        author = self.vars["author"].get().strip()
        if not ID_PATTERN.fullmatch(mod_id) or mod_id == "jumpfall":
            messagebox.showerror("ID inválido", "Usa 3–64 caracteres en minúscula: letras, números, punto, guion o guion bajo.", parent=self)
            return
        if not name or not author:
            messagebox.showerror("Datos incompletos", "Nombre y autor son obligatorios.", parent=self)
            return
        self.result = (mod_id, name, author)
        self.destroy()


class JumpFallMenuEditor:
    def __init__(self, root: tk.Tk, initial_path: Path | None = None) -> None:
        self.root = root
        self.root.title("JumpFall Visual Menu Editor — SDK 1.0")
        self.root.geometry("1500x900")
        self.root.minsize(1120, 700)

        self.mod_root: Path | None = None
        self.menu_path: Path | None = None
        self.layout: dict[str, Any] = default_layout()
        self.selected_id = ""
        self.dirty = False
        self.drag = DragState()
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.canvas_items: dict[int, str] = {}
        self.element_items: dict[str, list[int]] = {}
        self.image_cache: dict[str, tk.PhotoImage] = {}
        self._property_update_lock = False

        self.snap_enabled = tk.BooleanVar(value=True)
        self.grid_size = tk.IntVar(value=DEFAULT_GRID)
        self.status_var = tk.StringVar(value="Crea o abre un proyecto de mod.")
        self.project_var = tk.StringVar(value="Sin proyecto")

        self.layout_vars = {
            "id": tk.StringVar(),
            "surface": tk.StringVar(),
            "scene": tk.StringVar(),
            "sortingOrder": tk.StringVar(),
            "hideTargets": tk.StringVar(),
        }
        self.property_vars: dict[str, tk.StringVar] = {
            key: tk.StringVar()
            for key in (
                "id", "parent", "type", "text", "localizationKey", "asset", "color",
                "x", "y", "width", "height", "fontSize", "action", "target", "value"
            )
        }

        self._build_ui()
        self._bind_shortcuts()
        self._set_layout(default_layout(), mark_dirty=False)

        if initial_path:
            self.root.after(50, lambda: self.open_initial(initial_path))

    # ------------------------- UI construction -------------------------
    def _build_ui(self) -> None:
        self._build_menu_bar()

        top = ttk.Frame(self.root, padding=(8, 6))
        top.pack(fill="x")
        ttk.Label(top, textvariable=self.project_var).pack(side="left", fill="x", expand=True)
        ttk.Checkbutton(top, text="Ajustar a cuadrícula", variable=self.snap_enabled).pack(side="left", padx=8)
        ttk.Label(top, text="Grid").pack(side="left")
        ttk.Spinbox(top, from_=1, to=100, width=5, textvariable=self.grid_size).pack(side="left", padx=(4, 8))
        ttk.Button(top, text="Validar", command=self.validate_mod).pack(side="left", padx=3)
        ttk.Button(top, text="Compilar .jfmod", command=self.build_mod).pack(side="left", padx=3)

        metadata = ttk.LabelFrame(self.root, text="Layout", padding=6)
        metadata.pack(fill="x", padx=8, pady=(0, 6))
        fields = [
            ("ID", "id", 18),
            ("Superficie", "surface", 10),
            ("Escena", "scene", 18),
            ("Orden", "sortingOrder", 8),
            ("Objetos a ocultar (separados por coma)", "hideTargets", 50),
        ]
        for index, (label, key, width) in enumerate(fields):
            ttk.Label(metadata, text=label).grid(row=0, column=index * 2, sticky="w", padx=(0, 4))
            if key == "surface":
                widget: tk.Widget = ttk.Combobox(metadata, textvariable=self.layout_vars[key], values=("main", "pause"), state="readonly", width=width)
                widget.bind("<<ComboboxSelected>>", self._layout_changed)
            else:
                widget = ttk.Entry(metadata, textvariable=self.layout_vars[key], width=width)
                widget.bind("<FocusOut>", self._layout_changed)
                widget.bind("<Return>", self._layout_changed)
            widget.grid(row=0, column=index * 2 + 1, sticky="ew", padx=(0, 10))
        metadata.columnconfigure(9, weight=1)

        main = ttk.Panedwindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        self.left_frame = ttk.Frame(main, padding=6)
        self.center_frame = ttk.Frame(main, padding=0)
        self.right_frame = ttk.Frame(main, padding=6)
        main.add(self.left_frame, weight=1)
        main.add(self.center_frame, weight=5)
        main.add(self.right_frame, weight=2)

        self._build_left_panel()
        self._build_canvas()
        self._build_property_panel()

        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w", relief="sunken", padding=(6, 3))
        status.pack(fill="x", side="bottom")

    def _build_menu_bar(self) -> None:
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Crear proyecto…", command=self.create_project, accelerator="Ctrl/Cmd+N")
        file_menu.add_command(label="Abrir proyecto…", command=self.open_project)
        file_menu.add_command(label="Abrir menú JSON…", command=self.open_menu_file)
        file_menu.add_separator()
        file_menu.add_command(label="Guardar", command=self.save, accelerator="Ctrl/Cmd+S")
        file_menu.add_command(label="Guardar como…", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Validar mod", command=self.validate_mod)
        file_menu.add_command(label="Compilar .jfmod…", command=self.build_mod)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._close)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)

        edit_menu = tk.Menu(menu_bar, tearoff=False)
        edit_menu.add_command(label="Duplicar", command=self.duplicate_selected, accelerator="Ctrl/Cmd+D")
        edit_menu.add_command(label="Eliminar", command=self.delete_selected, accelerator="Delete")
        edit_menu.add_separator()
        edit_menu.add_command(label="Subir capa", command=lambda: self.move_layer(1))
        edit_menu.add_command(label="Bajar capa", command=lambda: self.move_layer(-1))
        menu_bar.add_cascade(label="Editar", menu=edit_menu)
        self.root.config(menu=menu_bar)

    def _build_left_panel(self) -> None:
        ttk.Label(self.left_frame, text="Agregar elemento", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        toolbar = ttk.Frame(self.left_frame)
        toolbar.pack(fill="x", pady=(5, 10))
        for row, element_type in enumerate(MENU_TYPES):
            ttk.Button(toolbar, text=f"+ {element_type.capitalize()}", command=lambda value=element_type: self.add_element(value)).grid(row=row // 2, column=row % 2, sticky="ew", padx=2, pady=2)
        toolbar.columnconfigure(0, weight=1)
        toolbar.columnconfigure(1, weight=1)

        ttk.Label(self.left_frame, text="Capas", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        layers_frame = ttk.Frame(self.left_frame)
        layers_frame.pack(fill="both", expand=True, pady=(5, 5))
        self.layers_list = tk.Listbox(layers_frame, exportselection=False)
        scroll = ttk.Scrollbar(layers_frame, orient="vertical", command=self.layers_list.yview)
        self.layers_list.config(yscrollcommand=scroll.set)
        self.layers_list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.layers_list.bind("<<ListboxSelect>>", self._layer_selected)

        controls = ttk.Frame(self.left_frame)
        controls.pack(fill="x")
        ttk.Button(controls, text="Duplicar", command=self.duplicate_selected).grid(row=0, column=0, sticky="ew", padx=2)
        ttk.Button(controls, text="Eliminar", command=self.delete_selected).grid(row=0, column=1, sticky="ew", padx=2)
        ttk.Button(controls, text="↑", command=lambda: self.move_layer(1), width=3).grid(row=1, column=0, sticky="ew", padx=2, pady=3)
        ttk.Button(controls, text="↓", command=lambda: self.move_layer(-1), width=3).grid(row=1, column=1, sticky="ew", padx=2, pady=3)
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

    def _build_canvas(self) -> None:
        wrapper = ttk.Frame(self.center_frame)
        wrapper.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(wrapper, background="#20242B", highlightthickness=0, cursor="arrow")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.redraw())
        self.canvas.bind("<Button-1>", self._canvas_press)
        self.canvas.bind("<B1-Motion>", self._canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._canvas_release)
        self.canvas.bind("<Double-Button-1>", self._canvas_double_click)

    def _build_property_panel(self) -> None:
        ttk.Label(self.right_frame, text="Propiedades", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))
        rows = [
            ("ID", "id", "entry"),
            ("Padre", "parent", "parent"),
            ("Tipo", "type", "type"),
            ("Texto", "text", "entry"),
            ("Clave localización", "localizationKey", "entry"),
            ("Asset", "asset", "asset"),
            ("Color", "color", "color"),
            ("X", "x", "entry"),
            ("Y", "y", "entry"),
            ("Ancho", "width", "entry"),
            ("Alto", "height", "entry"),
            ("Fuente", "fontSize", "entry"),
            ("Acción", "action", "action"),
            ("Target", "target", "entry"),
            ("Value", "value", "entry"),
        ]
        self.property_widgets: dict[str, tk.Widget] = {}
        for row, (label, key, kind) in enumerate(rows, start=1):
            ttk.Label(self.right_frame, text=label).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 6))
            if kind == "type":
                widget = ttk.Combobox(self.right_frame, textvariable=self.property_vars[key], values=MENU_TYPES, state="readonly")
                widget.bind("<<ComboboxSelected>>", self._property_changed)
            elif kind == "action":
                widget = ttk.Combobox(self.right_frame, textvariable=self.property_vars[key], values=MENU_ACTIONS, state="readonly")
                widget.bind("<<ComboboxSelected>>", self._property_changed)
            elif kind == "parent":
                widget = ttk.Combobox(self.right_frame, textvariable=self.property_vars[key], state="readonly")
                widget.bind("<<ComboboxSelected>>", self._property_changed)
            else:
                widget = ttk.Entry(self.right_frame, textvariable=self.property_vars[key])
                widget.bind("<FocusOut>", self._property_changed)
                widget.bind("<Return>", self._property_changed)
            widget.grid(row=row, column=1, sticky="ew", pady=3)
            self.property_widgets[key] = widget

            if kind == "asset":
                ttk.Button(self.right_frame, text="…", width=3, command=self.import_asset).grid(row=row, column=2, padx=(4, 0))
            elif kind == "color":
                ttk.Button(self.right_frame, text="🎨", width=3, command=self.choose_color).grid(row=row, column=2, padx=(4, 0))

        self.right_frame.columnconfigure(1, weight=1)
        ttk.Label(
            self.right_frame,
            text="Arrastra para mover. Usa el cuadro inferior derecho para cambiar tamaño. Flechas mueven 1 px; Shift+flechas, 10 px.",
            wraplength=260,
            foreground="#666666",
        ).grid(row=len(rows) + 2, column=0, columnspan=3, sticky="ew", pady=(14, 0))

    def _bind_shortcuts(self) -> None:
        for sequence in ("<Control-s>", "<Command-s>"):
            self.root.bind_all(sequence, lambda _event: self.save())
        for sequence in ("<Control-n>", "<Command-n>"):
            self.root.bind_all(sequence, lambda _event: self.create_project())
        for sequence in ("<Control-d>", "<Command-d>"):
            self.root.bind_all(sequence, lambda _event: self.duplicate_selected())
        self.root.bind_all("<Delete>", self._delete_shortcut)
        self.root.bind_all("<Left>", lambda event: self._nudge_shortcut(event, -1, 0))
        self.root.bind_all("<Right>", lambda event: self._nudge_shortcut(event, 1, 0))
        self.root.bind_all("<Up>", lambda event: self._nudge_shortcut(event, 0, 1))
        self.root.bind_all("<Down>", lambda event: self._nudge_shortcut(event, 0, -1))
        self.root.protocol("WM_DELETE_WINDOW", self._close)


    def _delete_shortcut(self, event: tk.Event[Any]) -> str | None:
        if self._focus_is_text_input(event.widget):
            return None
        self.delete_selected()
        return "break"

    def _nudge_shortcut(self, event: tk.Event[Any], dx: int, dy: int) -> str | None:
        if self._focus_is_text_input(event.widget):
            return None
        amount = 10 if event.state & 0x1 else 1
        self.nudge_selected(dx * amount, dy * amount)
        return "break"

    @staticmethod
    def _focus_is_text_input(widget: tk.Misc) -> bool:
        return widget.winfo_class() in {"Entry", "TEntry", "Text", "TCombobox", "Spinbox", "TSpinbox"}

    # ------------------------- project operations -------------------------
    def open_initial(self, path: Path) -> None:
        path = path.expanduser().resolve()
        if path.is_dir():
            self._load_project(path)
        elif path.is_file():
            self._load_menu(path)

    def create_project(self) -> None:
        if not self._confirm_discard():
            return
        folder_raw = filedialog.askdirectory(title="Carpeta para el nuevo mod")
        if not folder_raw:
            return
        dialog = ProjectDialog(self.root)
        self.root.wait_window(dialog)
        if dialog.result is None:
            return
        try:
            menu_path = create_mod_project(Path(folder_raw), *dialog.result)
            self.mod_root = Path(folder_raw).resolve()
            self._load_menu(menu_path)
            self.status_var.set("Proyecto creado. Puedes mover y editar los elementos visualmente.")
        except Exception as exc:
            messagebox.showerror("No se pudo crear el proyecto", str(exc), parent=self.root)

    def open_project(self) -> None:
        if not self._confirm_discard():
            return
        folder_raw = filedialog.askdirectory(title="Abrir carpeta de mod JumpFall")
        if folder_raw:
            self._load_project(Path(folder_raw))

    def _load_project(self, folder: Path) -> None:
        folder = folder.resolve()
        if not (folder / MANIFEST_NAME).is_file():
            messagebox.showerror("Proyecto inválido", f"No se encontró {MANIFEST_NAME}.", parent=self.root)
            return
        menu_path = discover_menu_from_manifest(folder)
        self.mod_root = folder
        if menu_path is None:
            menu_path = folder / "content" / "menus" / "main-menu.json"
            self._set_layout(default_layout(), mark_dirty=True)
            self.menu_path = menu_path
            self.project_var.set(f"Proyecto: {folder}  |  Menú nuevo: {safe_relative_path(folder, menu_path)}")
            self.status_var.set("El manifiesto no tenía menús. Se creó un layout en memoria; guárdalo para registrarlo.")
            return
        self._load_menu(menu_path)

    def open_menu_file(self) -> None:
        if not self._confirm_discard():
            return
        path_raw = filedialog.askopenfilename(title="Abrir menú JSON", filetypes=(("JSON", "*.json"), ("Todos", "*.*")))
        if path_raw:
            self._load_menu(Path(path_raw))

    def _load_menu(self, path: Path) -> None:
        try:
            layout = load_layout_file(path)
        except Exception as exc:
            messagebox.showerror("Menú inválido", str(exc), parent=self.root)
            return

        path = path.resolve()
        self.menu_path = path
        current_root_matches = False
        if self.mod_root is not None:
            try:
                path.relative_to(self.mod_root.resolve())
                current_root_matches = True
            except ValueError:
                current_root_matches = False
        if not current_root_matches:
            self.mod_root = None
            for candidate in (path.parent.parent.parent, path.parent.parent, path.parent):
                if (candidate / MANIFEST_NAME).is_file():
                    self.mod_root = candidate.resolve()
                    break
        self._set_layout(layout, mark_dirty=False)
        self.project_var.set(self._project_label())
        self.status_var.set(f"Menú abierto: {path}")

    def save(self) -> bool:
        self._commit_layout_metadata()
        self._commit_property_values()
        if self.menu_path is None:
            return self.save_as()
        try:
            self._validate_document_before_save()
            save_layout_file(self.menu_path, self.layout)
            if self.mod_root is not None:
                ensure_manifest_registration(self.mod_root, self.menu_path, self._uses_assets())
            self.dirty = False
            self.project_var.set(self._project_label())
            self.status_var.set(f"Guardado: {self.menu_path}")
            return True
        except Exception as exc:
            messagebox.showerror("No se pudo guardar", str(exc), parent=self.root)
            return False

    def save_as(self) -> bool:
        initial_dir = self.mod_root / "content" / "menus" if self.mod_root else Path.home()
        path_raw = filedialog.asksaveasfilename(
            title="Guardar menú",
            initialdir=str(initial_dir),
            defaultextension=".json",
            filetypes=(("JSON", "*.json"),),
        )
        if not path_raw:
            return False
        path = Path(path_raw).resolve()
        if self.mod_root:
            try:
                path.relative_to(self.mod_root)
            except ValueError:
                messagebox.showerror("Ruta inválida", "El menú debe guardarse dentro de la carpeta del mod.", parent=self.root)
                return False
        self.menu_path = path
        return self.save()

    def validate_mod(self) -> None:
        if self.mod_root is None:
            messagebox.showwarning("Sin proyecto", "Abre o crea una carpeta de mod primero.", parent=self.root)
            return
        if not self.save():
            return
        try:
            sdk = self._load_sdk_module()
            validator = sdk.Validator(self.mod_root)
            valid = validator.validate()
            lines = [str(problem) for problem in validator.problems]
            if valid:
                lines.append(f"[OK] Mod válido para JumpFall SDK {sdk.SDK_VERSION}.")
            self._show_report("Validación", "\n".join(lines) or "Sin mensajes.", valid)
        except Exception as exc:
            messagebox.showerror("Error del SDK", str(exc), parent=self.root)

    def build_mod(self) -> None:
        if self.mod_root is None:
            messagebox.showwarning("Sin proyecto", "Abre o crea una carpeta de mod primero.", parent=self.root)
            return
        if not self.save():
            return
        manifest_path = self.mod_root / MANIFEST_NAME
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            default_name = f"{manifest.get('id', 'jumpfall-mod')}-{manifest.get('version', '1.0.0')}.jfmod"
        except Exception:
            default_name = "jumpfall-mod.jfmod"
        output_raw = filedialog.asksaveasfilename(
            title="Compilar .jfmod",
            initialfile=default_name,
            defaultextension=".jfmod",
            filetypes=(("JumpFall Mod", "*.jfmod"),),
        )
        if not output_raw:
            return
        try:
            sdk = self._load_sdk_module()
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                result = sdk.pack_command(self.mod_root, Path(output_raw))
            report = stream.getvalue().strip()
            self._show_report("Compilación", report, result == 0)
            if result == 0:
                self.status_var.set(f"Paquete creado: {output_raw}")
        except Exception as exc:
            messagebox.showerror("No se pudo compilar", str(exc), parent=self.root)

    def _load_sdk_module(self) -> Any:
        sdk_dir = Path(__file__).resolve().parent
        if str(sdk_dir) not in sys.path:
            sys.path.insert(0, str(sdk_dir))
        try:
            import jumpfall_sdk  # type: ignore
        except ImportError as exc:
            raise RuntimeError("jumpfall_sdk.py debe estar junto a jumpfall_menu_editor.py") from exc
        return jumpfall_sdk

    # ------------------------- layout / elements -------------------------
    def _set_layout(self, layout: dict[str, Any], mark_dirty: bool) -> None:
        self.layout = layout
        self.selected_id = ""
        self.dirty = mark_dirty
        self._load_layout_metadata()
        self._refresh_layers()
        elements = self.layout.get("elements", [])
        if elements:
            self.select_element(str(elements[-1].get("id", "")))
        else:
            self._clear_property_panel()
        self.redraw()

    def add_element(self, element_type: str) -> None:
        element_id = self._unique_id(element_type)
        element = default_element(element_type, element_id)
        if self.selected_id:
            selected = self._selected_element()
            if selected and selected.get("type") == "panel":
                element["parent"] = self.selected_id
        self.layout.setdefault("elements", []).append(element)
        self._mark_dirty()
        self._refresh_layers()
        self.select_element(element_id)

    def duplicate_selected(self) -> None:
        source = self._selected_element()
        if source is None:
            return
        clone = json.loads(json.dumps(source))
        clone["id"] = self._unique_id(str(source.get("id", "element")) + "-copy")
        clone["x"] = float(clone.get("x", 0)) + 20
        clone["y"] = float(clone.get("y", 0)) - 20
        self.layout["elements"].append(clone)
        self._mark_dirty()
        self._refresh_layers()
        self.select_element(clone["id"])

    def delete_selected(self) -> None:
        if not self.selected_id:
            return
        dependents = [element for element in self.layout["elements"] if element.get("parent") == self.selected_id]
        if dependents:
            names = ", ".join(str(item.get("id")) for item in dependents)
            if not messagebox.askyesno("Eliminar padre", f"Estos elementos dependen de {self.selected_id}: {names}.\nTambién serán eliminados. ¿Continuar?", parent=self.root):
                return
        remove_ids = {self.selected_id}
        changed = True
        while changed:
            changed = False
            for element in self.layout["elements"]:
                if element.get("parent") in remove_ids and element.get("id") not in remove_ids:
                    remove_ids.add(str(element.get("id")))
                    changed = True
        self.layout["elements"] = [element for element in self.layout["elements"] if element.get("id") not in remove_ids]
        self.selected_id = ""
        self._mark_dirty()
        self._refresh_layers()
        self._clear_property_panel()
        self.redraw()

    def move_layer(self, direction: int) -> None:
        if not self.selected_id:
            return
        elements = self.layout["elements"]
        index = next((i for i, element in enumerate(elements) if element.get("id") == self.selected_id), -1)
        if index < 0:
            return
        new_index = max(0, min(len(elements) - 1, index + direction))
        if new_index == index:
            return
        element = elements.pop(index)
        elements.insert(new_index, element)
        # Parent must remain before children. Repair invalid ordering by moving parent before element.
        self._repair_parent_order()
        self._mark_dirty()
        self._refresh_layers()
        self.select_element(self.selected_id)

    def nudge_selected(self, dx: float, dy: float) -> None:
        element = self._selected_element()
        if element is None:
            return
        element["x"] = float(element.get("x", 0)) + dx
        element["y"] = float(element.get("y", 0)) + dy
        self._mark_dirty()
        self._load_property_panel()
        self.redraw()

    def select_element(self, element_id: str) -> None:
        if not element_id or self._element_by_id(element_id) is None:
            return
        self.selected_id = element_id
        for index, element in enumerate(self.layout.get("elements", [])):
            if element.get("id") == element_id:
                self.layers_list.selection_clear(0, tk.END)
                self.layers_list.selection_set(index)
                self.layers_list.see(index)
                break
        self._load_property_panel()
        self.redraw()

    # ------------------------- property handling -------------------------
    def _load_layout_metadata(self) -> None:
        self.layout_vars["id"].set(str(self.layout.get("id", "main-menu")))
        self.layout_vars["surface"].set(str(self.layout.get("surface", "main")))
        self.layout_vars["scene"].set(str(self.layout.get("scene", "Menugame")))
        self.layout_vars["sortingOrder"].set(str(self.layout.get("sortingOrder", 500)))
        self.layout_vars["hideTargets"].set(", ".join(str(item) for item in self.layout.get("hideTargets", [])))

    def _commit_layout_metadata(self) -> None:
        self.layout["id"] = self.layout_vars["id"].get().strip() or "main-menu"
        surface = self.layout_vars["surface"].get().strip()
        self.layout["surface"] = surface if surface in {"main", "pause"} else "main"
        self.layout["scene"] = self.layout_vars["scene"].get().strip() or "Menugame"
        try:
            self.layout["sortingOrder"] = int(self.layout_vars["sortingOrder"].get())
        except ValueError:
            self.layout["sortingOrder"] = 500
        self.layout["hideTargets"] = [item.strip() for item in self.layout_vars["hideTargets"].get().split(",") if item.strip()]

    def _layout_changed(self, _event: tk.Event[Any] | None = None) -> None:
        self._commit_layout_metadata()
        self._mark_dirty()

    def _load_property_panel(self) -> None:
        element = self._selected_element()
        if element is None:
            self._clear_property_panel()
            return
        self._property_update_lock = True
        try:
            for key, variable in self.property_vars.items():
                variable.set(str(element.get(key, "")))
            parent_widget = self.property_widgets.get("parent")
            if isinstance(parent_widget, ttk.Combobox):
                elements = self.layout.get("elements", [])
                selected_index = next((i for i, item in enumerate(elements) if item.get("id") == self.selected_id), len(elements))
                parent_widget["values"] = [""] + [str(item.get("id")) for item in elements[:selected_index]]
        finally:
            self._property_update_lock = False

    def _clear_property_panel(self) -> None:
        self._property_update_lock = True
        try:
            for variable in self.property_vars.values():
                variable.set("")
        finally:
            self._property_update_lock = False

    def _property_changed(self, _event: tk.Event[Any] | None = None) -> None:
        if self._property_update_lock:
            return
        self._commit_property_values()

    def _commit_property_values(self) -> None:
        element = self._selected_element()
        if element is None:
            return
        old_id = str(element.get("id", ""))
        new_id = self.property_vars["id"].get().strip()
        if new_id and new_id != old_id:
            if not ID_PATTERN.fullmatch(new_id) or self._element_by_id(new_id) is not None:
                self.property_vars["id"].set(old_id)
                self.status_var.set("ID inválido o duplicado; se conservó el anterior.")
            else:
                element["id"] = new_id
                for child in self.layout["elements"]:
                    if child.get("parent") == old_id:
                        child["parent"] = new_id
                self.selected_id = new_id

        element["parent"] = self.property_vars["parent"].get().strip()
        element_type = self.property_vars["type"].get().strip()
        element["type"] = element_type if element_type in MENU_TYPES else "panel"
        for key in ("text", "localizationKey", "asset", "action", "target", "value"):
            element[key] = self.property_vars[key].get()
        element["color"] = normalize_color(self.property_vars["color"].get(), str(element.get("color", "#FFFFFFFF")))
        for key, fallback in (("x", 0.0), ("y", 0.0), ("width", 100.0), ("height", 50.0)):
            try:
                element[key] = float(self.property_vars[key].get())
            except ValueError:
                element[key] = fallback
        element["width"] = max(10.0, float(element["width"]))
        element["height"] = max(10.0, float(element["height"]))
        try:
            element["fontSize"] = max(8, min(160, int(float(self.property_vars["fontSize"].get()))))
        except ValueError:
            element["fontSize"] = 28
        if element.get("action") not in MENU_ACTIONS:
            element["action"] = ""
        self._repair_parent_order()
        self._mark_dirty()
        self._refresh_layers()
        self._load_property_panel()
        self.redraw()

    def choose_color(self) -> None:
        element = self._selected_element()
        if element is None:
            return
        result = colorchooser.askcolor(color=color_for_tk(str(element.get("color", "#FFFFFFFF"))), parent=self.root)
        if result[1]:
            alpha = normalize_color(str(element.get("color", "#FFFFFFFF")))[7:9]
            self.property_vars["color"].set(result[1].upper() + alpha)
            self._commit_property_values()

    def import_asset(self) -> None:
        element = self._selected_element()
        if element is None:
            return
        if self.mod_root is None:
            messagebox.showwarning("Sin proyecto", "Abre o crea un proyecto para importar imágenes.", parent=self.root)
            return
        source_raw = filedialog.askopenfilename(title="Importar imagen", filetypes=(("Imágenes", "*.png *.jpg *.jpeg"),))
        if not source_raw:
            return
        source = Path(source_raw)
        target_dir = self.mod_root / "assets" / "images"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        counter = 2
        while target.exists() and target.read_bytes() != source.read_bytes():
            target = target_dir / f"{source.stem}-{counter}{source.suffix.lower()}"
            counter += 1
        if not target.exists():
            shutil.copy2(source, target)
        relative = safe_relative_path(self.mod_root, target)
        self.property_vars["asset"].set(relative)
        if element.get("type") != "image":
            self.property_vars["type"].set("image")
        self.image_cache.clear()
        self._commit_property_values()

    # ------------------------- canvas -------------------------
    def redraw(self) -> None:
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("all")
        self.canvas_items.clear()
        self.element_items.clear()

        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        margin = 24
        self.scale = min((width - margin * 2) / REFERENCE_WIDTH, (height - margin * 2) / REFERENCE_HEIGHT)
        self.scale = max(0.05, self.scale)
        stage_w = REFERENCE_WIDTH * self.scale
        stage_h = REFERENCE_HEIGHT * self.scale
        self.offset_x = (width - stage_w) / 2
        self.offset_y = (height - stage_h) / 2

        self.canvas.create_rectangle(
            self.offset_x,
            self.offset_y,
            self.offset_x + stage_w,
            self.offset_y + stage_h,
            fill="#0D1117",
            outline="#AAB4C0",
            width=2,
        )
        self._draw_grid(stage_w, stage_h)

        for element in self.layout.get("elements", []):
            self._draw_element(element)

        selected = self._selected_element()
        if selected:
            x1, y1, x2, y2 = self._element_canvas_rect(selected)
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="#FFD54A", width=2, dash=(6, 3))
            handle_size = 12
            handle = self.canvas.create_rectangle(
                x2 - handle_size / 2,
                y2 - handle_size / 2,
                x2 + handle_size / 2,
                y2 + handle_size / 2,
                fill="#FFD54A",
                outline="#222222",
                tags=("resize-handle",),
            )
            self.canvas_items[handle] = self.selected_id

    def _draw_grid(self, stage_w: float, stage_h: float) -> None:
        grid = max(10, self.grid_size.get())
        step = grid * self.scale
        if step < 7:
            step *= max(1, round(7 / step))
        x = self.offset_x
        while x <= self.offset_x + stage_w:
            self.canvas.create_line(x, self.offset_y, x, self.offset_y + stage_h, fill="#1E2731")
            x += step
        y = self.offset_y
        while y <= self.offset_y + stage_h:
            self.canvas.create_line(self.offset_x, y, self.offset_x + stage_w, y, fill="#1E2731")
            y += step
        center_x = self.offset_x + stage_w / 2
        center_y = self.offset_y + stage_h / 2
        self.canvas.create_line(center_x, self.offset_y, center_x, self.offset_y + stage_h, fill="#40566E", width=2)
        self.canvas.create_line(self.offset_x, center_y, self.offset_x + stage_w, center_y, fill="#40566E", width=2)

    def _draw_element(self, element: dict[str, Any]) -> None:
        element_id = str(element.get("id", ""))
        x1, y1, x2, y2 = self._element_canvas_rect(element)
        element_type = str(element.get("type", "panel"))
        color = color_for_tk(str(element.get("color", "#FFFFFFFF")))
        items: list[int] = []

        if element_type == "panel":
            items.append(self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#788896", width=1))
        elif element_type == "button":
            items.append(self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#D7DEE5", width=2))
            items.append(self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=str(element.get("text", "Botón")), fill="#101010", width=max(1, x2 - x1 - 10), font=("TkDefaultFont", max(8, int(float(element.get("fontSize", 28)) * self.scale)))))
        elif element_type == "text":
            items.append(self.canvas.create_rectangle(x1, y1, x2, y2, fill="", outline="#52606D", dash=(3, 3)))
            items.append(self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=str(element.get("text", "Texto")), fill=color, width=max(1, x2 - x1 - 8), justify="center", font=("TkDefaultFont", max(8, int(float(element.get("fontSize", 28)) * self.scale)))))
        elif element_type == "image":
            photo = self._load_preview_image(str(element.get("asset", "")), max(1, int(x2 - x1)), max(1, int(y2 - y1)))
            if photo is not None:
                items.append(self.canvas.create_image((x1 + x2) / 2, (y1 + y2) / 2, image=photo))
            else:
                items.append(self.canvas.create_rectangle(x1, y1, x2, y2, fill="#1A2733", outline=color, width=2))
                items.append(self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=Path(str(element.get("asset", "Imagen"))).name or "Imagen", fill="#DCE6EE", width=max(1, x2 - x1 - 10)))

        for item in items:
            self.canvas_items[item] = element_id
        self.element_items[element_id] = items

    def _load_preview_image(self, asset: str, target_width: int, target_height: int) -> tk.PhotoImage | None:
        if not asset or self.mod_root is None:
            return None
        path = (self.mod_root / asset).resolve()
        try:
            path.relative_to(self.mod_root.resolve())
        except ValueError:
            return None
        if not path.is_file() or path.suffix.lower() != ".png":
            return None
        key = f"{path}:{target_width}x{target_height}"
        if key in self.image_cache:
            return self.image_cache[key]
        try:
            photo = tk.PhotoImage(file=str(path))
            factor = max(1, max(photo.width() // max(1, target_width), photo.height() // max(1, target_height)))
            if factor > 1:
                photo = photo.subsample(factor, factor)
            self.image_cache[key] = photo
            return photo
        except tk.TclError:
            return None

    def _canvas_press(self, event: tk.Event[Any]) -> None:
        current = self.canvas.find_withtag("current")
        if not current:
            self.selected_id = ""
            self._clear_property_panel()
            self.redraw()
            return
        item = current[0]
        element_id = self.canvas_items.get(item, "")
        if not element_id:
            return
        self.select_element(element_id)
        element = self._selected_element()
        if element is None:
            return
        tags = self.canvas.gettags(item)
        mode = "resize" if "resize-handle" in tags else "move"
        self.drag = DragState(
            element_id=element_id,
            mode=mode,
            start_canvas_x=event.x,
            start_canvas_y=event.y,
            start_x=float(element.get("x", 0)),
            start_y=float(element.get("y", 0)),
            start_width=float(element.get("width", 100)),
            start_height=float(element.get("height", 50)),
        )

    def _canvas_drag(self, event: tk.Event[Any]) -> None:
        if not self.drag.element_id:
            return
        element = self._element_by_id(self.drag.element_id)
        if element is None:
            return
        dx = (event.x - self.drag.start_canvas_x) / self.scale
        dy = (event.y - self.drag.start_canvas_y) / self.scale
        if self.drag.mode == "move":
            x = self.drag.start_x + dx
            y = self.drag.start_y - dy
            element["x"] = self._snap(x)
            element["y"] = self._snap(y)
        else:
            element["width"] = max(10.0, self._snap(self.drag.start_width + dx * 2))
            element["height"] = max(10.0, self._snap(self.drag.start_height + dy * 2))
        self._mark_dirty()
        self._load_property_panel()
        self.redraw()

    def _canvas_release(self, _event: tk.Event[Any]) -> None:
        self.drag = DragState()

    def _canvas_double_click(self, event: tk.Event[Any]) -> None:
        current = self.canvas.find_withtag("current")
        if not current:
            return
        element_id = self.canvas_items.get(current[0], "")
        element = self._element_by_id(element_id)
        if element is None or element.get("type") not in {"text", "button"}:
            return
        value = simpledialog.askstring("Editar texto", "Texto visible:", initialvalue=str(element.get("text", "")), parent=self.root)
        if value is not None:
            element["text"] = value
            self._mark_dirty()
            self._load_property_panel()
            self.redraw()

    # ------------------------- helpers -------------------------
    def _layer_selected(self, _event: tk.Event[Any]) -> None:
        selection = self.layers_list.curselection()
        if not selection:
            return
        index = selection[0]
        elements = self.layout.get("elements", [])
        if 0 <= index < len(elements):
            self.select_element(str(elements[index].get("id", "")))

    def _refresh_layers(self) -> None:
        current = self.selected_id
        self.layers_list.delete(0, tk.END)
        for element in self.layout.get("elements", []):
            parent = f" ↳ {element.get('parent')}" if element.get("parent") else ""
            self.layers_list.insert(tk.END, f"{element.get('id')}  [{element.get('type')}]{parent}")
        if current:
            for index, element in enumerate(self.layout.get("elements", [])):
                if element.get("id") == current:
                    self.layers_list.selection_set(index)
                    break

    def _absolute_center(self, element: dict[str, Any], visiting: set[str] | None = None) -> tuple[float, float]:
        visiting = visiting or set()
        element_id = str(element.get("id", ""))
        if element_id in visiting:
            return float(element.get("x", 0)), float(element.get("y", 0))
        visiting.add(element_id)
        x = float(element.get("x", 0))
        y = float(element.get("y", 0))
        parent_id = str(element.get("parent", ""))
        if parent_id:
            parent = self._element_by_id(parent_id)
            if parent is not None:
                px, py = self._absolute_center(parent, visiting)
                x += px
                y += py
        return x, y

    def _element_canvas_rect(self, element: dict[str, Any]) -> tuple[float, float, float, float]:
        x, y = self._absolute_center(element)
        width = max(10.0, float(element.get("width", 100)))
        height = max(10.0, float(element.get("height", 50)))
        cx = self.offset_x + (REFERENCE_WIDTH / 2 + x) * self.scale
        cy = self.offset_y + (REFERENCE_HEIGHT / 2 - y) * self.scale
        half_w = width * self.scale / 2
        half_h = height * self.scale / 2
        return cx - half_w, cy - half_h, cx + half_w, cy + half_h

    def _selected_element(self) -> dict[str, Any] | None:
        return self._element_by_id(self.selected_id)

    def _element_by_id(self, element_id: str) -> dict[str, Any] | None:
        for element in self.layout.get("elements", []):
            if str(element.get("id", "")) == element_id:
                return element
        return None

    def _unique_id(self, base: str) -> str:
        normalized = re.sub(r"[^a-z0-9._-]+", "-", base.lower()).strip("-._") or "element"
        if len(normalized) < 3:
            normalized = f"{normalized}-item"
        normalized = normalized[:56]
        existing = {str(element.get("id")) for element in self.layout.get("elements", [])}
        if normalized not in existing:
            return normalized
        counter = 2
        while f"{normalized}-{counter}" in existing:
            counter += 1
        return f"{normalized}-{counter}"

    def _repair_parent_order(self) -> None:
        elements = self.layout.get("elements", [])
        changed = True
        guard = 0
        while changed and guard < len(elements) * 2 + 1:
            changed = False
            guard += 1
            positions = {str(element.get("id")): index for index, element in enumerate(elements)}
            for index, element in enumerate(list(elements)):
                parent = str(element.get("parent", ""))
                if parent and parent in positions and positions[parent] > index:
                    parent_element = elements.pop(positions[parent])
                    elements.insert(index, parent_element)
                    changed = True
                    break

    def _uses_assets(self) -> bool:
        return any(bool(str(element.get("asset", "")).strip()) for element in self.layout.get("elements", []))

    def _snap(self, value: float) -> float:
        if not self.snap_enabled.get():
            return round(value, 2)
        grid = max(1, int(self.grid_size.get()))
        return round(value / grid) * grid

    def _mark_dirty(self) -> None:
        self.dirty = True
        self.project_var.set(self._project_label())

    def _project_label(self) -> str:
        project = str(self.mod_root) if self.mod_root else "Sin proyecto"
        menu = str(self.menu_path) if self.menu_path else "Sin archivo"
        marker = " *" if self.dirty else ""
        return f"Proyecto: {project}  |  Menú: {menu}{marker}"

    def _validate_document_before_save(self) -> None:
        elements = self.layout.get("elements", [])
        if not isinstance(elements, list) or len(elements) > 128:
            raise ValueError("El menú debe tener entre 0 y 128 elementos.")
        seen: set[str] = set()
        for index, element in enumerate(elements):
            element_id = str(element.get("id", ""))
            if not ID_PATTERN.fullmatch(element_id) or element_id in seen:
                raise ValueError(f"ID inválido o duplicado en el elemento {index}: {element_id}")
            parent = str(element.get("parent", ""))
            if parent and parent not in seen:
                raise ValueError(f"El padre '{parent}' debe aparecer antes que '{element_id}'.")
            if element.get("type") not in MENU_TYPES:
                raise ValueError(f"Tipo inválido: {element.get('type')}")
            if element.get("action", "") not in MENU_ACTIONS:
                raise ValueError(f"Acción inválida: {element.get('action')}")
            seen.add(element_id)

    def _confirm_discard(self) -> bool:
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Cambios sin guardar", "¿Quieres guardar los cambios antes de continuar?", parent=self.root)
        if answer is None:
            return False
        if answer:
            return self.save()
        return True

    def _show_report(self, title: str, report: str, success: bool) -> None:
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("760x460")
        window.transient(self.root)
        frame = ttk.Frame(window, padding=10)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Correcto" if success else "Se encontraron problemas", foreground="#187A2F" if success else "#A32929", font=("TkDefaultFont", 11, "bold")).pack(anchor="w", pady=(0, 6))
        text = tk.Text(frame, wrap="word", font=("TkFixedFont", 10))
        scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.config(yscrollcommand=scroll.set)
        text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        text.insert("1.0", report)
        text.config(state="disabled")

    def _close(self) -> None:
        if self._confirm_discard():
            self.root.destroy()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Visual editor for JumpFall Modding 1.0 menus.")
    parser.add_argument("path", nargs="?", type=Path, help="Optional mod folder or menu JSON to open.")
    parser.add_argument("--self-test", action="store_true", help="Run non-GUI structural tests.")
    return parser


def run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "test-mod"
        menu_path = create_mod_project(root, "com.test.menu", "Test Menu", "SDK Test")
        layout = load_layout_file(menu_path)
        layout["elements"].append(default_element("button", "extra-button"))
        save_layout_file(menu_path, layout)
        ensure_manifest_registration(root, menu_path, uses_assets=False)
        loaded = load_layout_file(menu_path)
        assert len(loaded["elements"]) == 4
        manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
        assert "menus" in manifest["capabilities"]
        assert "content/menus/main-menu.json" in manifest["content"]["menus"]
        assert normalize_color("#abcdef") == "#ABCDEFFF"
    print("[OK] JumpFall Visual Menu Editor self-test passed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        return run_self_test()
    root = tk.Tk()
    JumpFallMenuEditor(root, args.path)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
