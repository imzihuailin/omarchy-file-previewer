// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Andy Stewart
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io

Item {
    id: root
    property var shell: null
    property bool rulesApplied: false
    property bool applyPending: false
    readonly property string instance: Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE")
    readonly property string rulesPath: decodeURIComponent(String(Qt.resolvedUrl("hyprland.lua")).replace(/^file:\/\//, ""))

    // The D-Bus and desktop entries are installed explicitly by install.py.
    // Loading this service never rewrites the user's application entries.
    function applyRules() {
        if (!instance) return;
        if (applyProcess.running) {
            applyPending = true;
            return;
        }
        applyPending = false;
        rulesApplied = false;
        applyProcess.command = ["hyprctl", "--instance", instance, "eval",
            "dofile(" + JSON.stringify(rulesPath) + ")"];
        applyProcess.running = true;
    }

    Process {
        id: applyProcess
        stderr: StdioCollector {
            onStreamFinished: if (text.trim()) console.warn("File Previewer: " + text.trim())
        }
        onExited: function(exitCode) {
            root.rulesApplied = exitCode === 0;
            if (root.applyPending) applyTimer.restart();
        }
    }
    Timer {
        id: applyTimer
        interval: 100
        onTriggered: root.applyRules()
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (String(event.name).toLowerCase() === "configreloaded") {
                root.rulesApplied = false;
                applyTimer.restart();
            }
        }
    }
    IpcHandler {
        target: "io.github.manateelazycat.file-previewer"
        function status(): string {
            return JSON.stringify({rulesApplied: root.rulesApplied, manualSetupRequired: true});
        }
    }
    Component.onCompleted: applyTimer.start()
}
