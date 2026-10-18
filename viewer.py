#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Andy Stewart
"""Shared imv launcher for Nautilus preview and desktop file activation."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time

from gi.repository import Gio

ROOT = Path(__file__).resolve().parent
APP_ID = "io.github.manateelazycat.file-previewer"


def hyprctl(*args):
    # Pin every request to the compositor inherited by this viewer. In particular,
    # never let hyprctl fall back to instance 0 in a nested test session.
    instance = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    if not instance:
        raise RuntimeError("HYPRLAND_INSTANCE_SIGNATURE is not set")
    result = subprocess.run(
        ["hyprctl", "--instance", instance, *args],
        capture_output=True, text=True, timeout=5, check=True,
    )
    return result.stdout


def image_path(value):
    file = Gio.File.new_for_commandline_arg(value)
    path = file.get_path()
    if path is None:
        raise ValueError(f"Only local images are supported: {value}")
    path = Path(path).absolute()
    if not path.is_file():
        raise ValueError(f"Image does not exist: {path}")
    return path


def is_image(path):
    content_type, _ = Gio.content_type_guess(str(path), None)
    return bool(content_type and Gio.content_type_is_a(content_type, "image/*"))


def natural_key(path):
    return [int(part) if part.isdigit() else part.casefold()
            for part in re.split(r"(\d+)", path.name)]


def image_list(paths):
    selected = [image_path(value) for value in paths]
    if len(selected) > 1:
        return selected[0], list(dict.fromkeys(selected))
    first = selected[0]
    siblings = sorted(
        (path for path in first.parent.iterdir()
         if path.is_file() and is_image(path)
         and (not path.name.startswith(".") or path == first)),
        key=natural_key,
    )
    if first not in siblings:
        siblings.append(first)
    return first, siblings


def move(pid, direction):
    offsets = {"left": (-40, 0), "right": (40, 0),
               "up": (0, -40), "down": (0, 40)}
    # Move the originating imv by its PID, even if focus changes before this
    # command runs. A bare movewindowpixel would move an unrelated active app.
    clients = json.loads(hyprctl("-j", "clients"))
    window = next((w for w in clients
                   if w["pid"] == pid and w["class"] == APP_ID), None)
    if window is None or not window.get("floating") or window.get("fullscreen"):
        return
    dx, dy = offsets[direction]
    selector = json.dumps("address:" + window["address"])
    hyprctl("dispatch", "hl.dsp.window.move({"
            f"window={selector},x={dx},y={dy},relative=true" + "})")


def open_images(paths):
    first, images = image_list(paths)
    hyprctl("eval", f"dofile({json.dumps(str(ROOT / 'hyprland.lua'))})")
    command = ["imv", "-i", APP_ID, "-W", "875", "-H", "600",
               "-s", "shrink", "-n", str(first)]
    # Override imv's default h/l panning with an operation that leaves the view unchanged.
    bindings = {"h": "pan 0 0", "l": "pan 0 0", "j": "next", "k": "prev", "<minus>": "zoom -1",
                "<equal>": "zoom 1", "0": "zoom actual", "<Escape>": "quit"}
    launcher = shlex.quote(sys.executable) + " " + shlex.quote(str(ROOT / "viewer.py"))
    for key, direction in (("<Left>", "left"), ("<Right>", "right"),
                           ("<Up>", "up"), ("<Down>", "down")):
        bindings[key] = f'exec {launcher} move "$imv_pid" {direction}'
    for key, action in bindings.items():
        command += ["-c", f"bind {key} {action}"]
    command += ["--", *map(str, images)]
    child = subprocess.Popen(command)

    def terminate(_signum, _frame):
        if child.poll() is None:
            child.terminate()

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    # Focus by PID after mapping, regardless of where the pointer was left in
    # Nautilus. Do this only once; keyboard window switching remains possible.
    deadline = time.monotonic() + 5
    try:
        while child.poll() is None and time.monotonic() < deadline:
            clients = json.loads(hyprctl("-j", "clients"))
            window = next((w for w in clients if w["pid"] == child.pid), None)
            if window is not None:
                selector = json.dumps("address:" + window["address"])
                hyprctl("dispatch", f"hl.dsp.focus({{window={selector}}})")
                break
            time.sleep(0.05)
        return child.wait()
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("open").add_argument("images", nargs="+")
    moving = sub.add_parser("move")
    moving.add_argument("pid", type=int)
    moving.add_argument("direction", choices=["left", "right", "up", "down"])
    args = parser.parse_args()
    try:
        if args.action == "open":
            return open_images(args.images)
        move(args.pid, args.direction)
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"file-previewer: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
