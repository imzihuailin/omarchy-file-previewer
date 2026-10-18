#!/usr/bin/gjs
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Andy Stewart
// Extend the installed Sushi service instead of duplicating its D-Bus protocol
// or its non-image renderers. Sushi 50 supplies NautilusPreviewer2 and tokens.
// GJS normally derives the resource basename from the executable filename.
// Our entry point has a different filename, but uses Sushi's original resources.
imports.package._findEffectiveEntryPointName = () => 'org.gnome.NautilusPreviewer';
imports.package.init({
    name: 'sushi', version: '50.0', prefix: '/usr', libdir: '/usr/lib',
});
const Main = imports.ui.main;
const {Gio, GLib} = imports.gi;
const Application = imports.ui.application.Application;
const originalShowFile = Application.prototype.showFile;
const originalClose = Application.prototype.close;
const pluginDir = GLib.path_get_dirname(GLib.canonicalize_filename(
    imports.system.programPath, null));

function notifyVisible(app, visible) {
    app._skeleton2.impl.emit_property_changed('Visible', new GLib.Variant('b', visible));
}

function stopImage(app) {
    if (!app._imageProcess)
        return;
    const process = app._imageProcess;
    app._imageProcess = null;
    app._imageUri = null;
    process.send_signal(15);
    notifyVisible(app, false);
}

Application.prototype.showFile = function (uri, parent, toggle, token = '') {
    const file = Gio.File.new_for_uri(uri);
    const path = file.get_path();
    const [type] = Gio.content_type_guess(path || uri, null);
    if (!path || !type || !Gio.content_type_is_a(type, 'image/*')) {
        stopImage(this);
        return originalShowFile.call(this, uri, parent, toggle, token);
    }
    if (toggle && this._imageProcess && this._imageUri === uri) {
        stopImage(this);
        return;
    }
    stopImage(this);
    originalClose.call(this);
    const launcher = new Gio.SubprocessLauncher({flags: Gio.SubprocessFlags.NONE});
    if (token)
        launcher.setenv('XDG_ACTIVATION_TOKEN', token, true);
    const process = launcher.spawnv(['/usr/bin/python', `${pluginDir}/viewer.py`, 'open', path]);
    this._imageProcess = process;
    this._imageUri = uri;
    this.hold();
    this.updateParentHandle(parent);
    notifyVisible(this, true);
    process.wait_async(null, (proc, result) => {
        proc.wait_finish(result);
        if (this._imageProcess === proc) {
            this._imageProcess = null;
            this._imageUri = null;
            notifyVisible(this, false);
        }
        this.release();
    });
};

Application.prototype.close = function () {
    stopImage(this);
    return originalClose.call(this);
};

imports.package.run(Main);
