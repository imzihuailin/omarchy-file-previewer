# Omarchy File Previewer

English | [简体中文](README.zh-CN.md)

https://github.com/user-attachments/assets/a7b1f2da-a173-4cde-a321-61574c0c9bbf

Use the same **imv** image viewer for Nautilus Space previews and double-clicks, with keyboard navigation and focus that stays put while the pointer moves.

## Requirements

- Omarchy with Hyprland 0.56 and its Lua configuration, Nautilus 50, Sushi 50, and imv 5.
- `python-gobject`, `gjs`, and `desktop-file-utils`, normally included in Omarchy.
- The Omarchy service also uses the built-in Quickshell runtime.

## Interaction

- Select an image in Nautilus and press `Space`, or double-click it, to open imv.
- The image window opens centered and floating, takes keyboard focus immediately, and keeps it when the pointer moves outside the window.
- Move the pointer to either screen edge to reveal `omarchy-side-panel`. Hovering over the panel leaves image shortcuts working; clicking another window switches focus normally.
- Opening one image loads the other images in its directory in natural filename order (`1`, `2`, `10`). Opening multiple selected images limits navigation to that selection.
- Text, PDF, video, and other non-image files continue using Sushi for Space previews.
- Existing imv configuration is preserved. These key overrides apply only to windows opened through this project.

| Key | Action |
| --- | --- |
| `j` / `k` | Next / previous image |
| `h` / `l` | Disabled; do not pan the image |
| `-` / `=` | Zoom out / in |
| `0` | Actual size, 1:1 |
| `↑` `↓` `←` `→` | Move the window by 40 pixels |
| `Esc` / `q` | Close the image window |

## Install

Install and enable the plugin, then explicitly install the Nautilus and imv integration:

```bash
omarchy plugin add https://github.com/manateelazycat/omarchy-file-previewer.git --enable --yes
python ~/.config/omarchy/plugins/io.github.manateelazycat.file-previewer/install.py
```

The second command is required manual setup. The service keeps the preview focus rules available across Hyprland configuration reloads; enabling it does not automatically change application associations or desktop entries.

For a standalone installation without the Omarchy service, clone the repository and run the same installer:

```bash
git clone https://github.com/manateelazycat/omarchy-file-previewer.git
cd omarchy-file-previewer
python install.py
```

Keep the repository at the same path after installation. Two user-level entry points refer to its code:

- `~/.local/share/applications/imv.desktop`
- `~/.local/share/dbus-1/services/org.gnome.NautilusPreviewer.service`

The default image application ID remains `imv.desktop`. The installer backs up existing entries to `~/.local/state/omarchy-file-previewer/install.json` and can be run again. It does not edit system files, global mouse settings, or Hyprland user configuration files, and Nautilus does not need to restart.

If the original Sushi service is already running, the new entry takes effect after its preview closes and the idle service exits. Network URI previews remain with Sushi; directory navigation targets local images.

## Remove

For an Omarchy plugin installation, restore the application entries before removing the plugin:

```bash
python ~/.config/omarchy/plugins/io.github.manateelazycat.file-previewer/install.py --uninstall
omarchy plugin remove io.github.manateelazycat.file-previewer --yes
```

For a standalone installation, run this from the original checkout:

```bash
python install.py --uninstall
```

This restores the previous entry points. Files edited manually after installation are preserved, with their paths printed for review.

## Development

```bash
omarchy plugin validate .
python -m unittest discover -s tests -p 'test_*.py'
python tests/nested.py
```

Integration tests require Weston, `wtype`, `grim`, a C compiler, and Wayland development headers. For an unpacked Weston installation, use `WESTON_PREFIX=/path/to/unpacked/usr python tests/nested.py`.

Tests run Hyprland nested inside a headless Weston, with a dedicated virtual output and isolated Wayland socket, D-Bus, configuration, cache, and data directories. They verify service loading and recovery after a configuration reload, actual Nautilus Space and double-click input, image navigation, zoom, focus, window movement, non-image previews, and uninstall recovery.

When `~/omarchy-side-panel` exists, the tests also load its real dock components and verify both screen edges, keyboard focus, and explicit window switching during previews. Set `SIDE_PANEL_SOURCE` to use a different source directory. No test input reaches the current desktop. Screenshots and logs are stored in the ignored `test-results/` directory.

Focus and movement use [Hyprland window rules](https://wiki.hypr.land/Configuring/Basics/Window-Rules/) and [Lua dispatchers](https://wiki.hypr.land/configuring/core/dispatchers/). Window layout rules match the dedicated imv app ID. Hover focus protection is enabled only while an image window is active, and previous rules resume when focus switches or the window closes.

## License

Omarchy File Previewer is licensed under the GNU General Public License version 3.0 only (`GPL-3.0-only`). See [LICENSE](LICENSE).
