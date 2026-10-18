# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Andy Stewart
"""Load the real side-panel DockSurface and coordinator in the private session."""

import os
from pathlib import Path
import re
import shutil


def prepare(directory):
    source = Path(os.environ.get("SIDE_PANEL_SOURCE", Path.home() / "omarchy-side-panel"))
    if not source.is_dir():
        return None
    omarchy = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy"))
    root = directory / "side-panel"
    plugin = root / "Plugin"
    plugin.mkdir(parents=True)
    for path in (*source.glob("*.qml"), *source.glob("*.js")):
        shutil.copy2(path, plugin / path.name)
    for name in ("CompatUi", "Ui", "Icons"):
        shutil.copytree(source / name, plugin / name)
    (root / "Commons").symlink_to(omarchy / "shell/Commons", target_is_directory=True)
    shutil.copytree(omarchy / "shell/Ui", root / "Ui")
    # Use the panel's existing Qt theme compatibility files, as its own tests do.
    for name in ("PopupCard.qml", "ThemeBorder.qml", "BorderGeometry.js"):
        shutil.copy2(source / "CompatUi" / name, root / "Ui" / name)
    keyboard = (omarchy / "shell/Ui/KeyboardPanel.qml").read_text()
    keyboard = keyboard.replace("import qs.Commons\n", 'import qs.Commons as Commons\nimport "." as LocalUi\n')
    keyboard = re.sub(r"\b(Color|Style|Util)\.", r"Commons.\1.", keyboard)
    keyboard = re.sub(r"\bBorder\.", "LocalUi.ThemeBorder.", keyboard)
    (root / "Ui/KeyboardPanel.qml").write_text(keyboard)
    with (root / "Ui/qmldir").open("a") as stream:
        stream.write("\nsingleton ThemeBorder 1.0 ThemeBorder.qml\n")
    for package in (plugin, plugin / "Ui"):
        with (package / "qmldir").open("a") as stream:
            for path in package.glob("*.qml"):
                if path.stem != "PopupAppearance":
                    stream.write(f"{path.stem} 1.0 {path.name}\n")
    # Reuse the side-panel's minimal host. Its actual surfaces, input masks,
    # layer, hover handlers, reveal timers and animations remain unchanged.
    fixture = (source / "tests/qml/dock-edges.qml").read_text().split("    TestCase { id: input;", 1)[0]
    fixture = fixture.replace("import QtTest\n", "import Quickshell.Io\n")
    fixture += '''
    IpcHandler {
        target: "previewerDockTest"
        function status(): string {
            return JSON.stringify(testHost.surfaces.map(function(surface) {
                return {shown: surface.shown, side: surface.dockSide,
                    hovered: surface.pointerHovered, edge: surface.edgeSide,
                    progress: surface.revealProgress};
            }));
        }
    }
}
'''
    (root / "shell.qml").write_text(fixture)
    return root
