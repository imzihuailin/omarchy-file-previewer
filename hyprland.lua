-- SPDX-License-Identifier: GPL-3.0-only
-- Copyright (C) 2026 Andy Stewart
-- Loaded on demand into the viewer's own compositor, without a config reload.
-- Migrate the old rule: stay_focused also captures pointer motion before
-- Hyprland can deliver it to top-layer panels and their edge triggers.
if _G.omarchy_file_previewer_rule then
  _G.omarchy_file_previewer_rule:set_enabled(false)
  _G.omarchy_file_previewer_rule = nil
end

local app_id = "io.github.manateelazycat.file-previewer"
if not _G.omarchy_file_previewer then
  local state = {}
  _G.omarchy_file_previewer = state
  state.window_rule = hl.window_rule({
    match = { class = "^io.github.manateelazycat.file-previewer$" },
    float = true,
    center = true,
    size = { 875, 600 },
    no_initial_focus = false,
    focus_on_activate = true,
    opacity = "1 1",
  })

  -- Suppress hover-driven keyboard focus changes only while an image is
  -- active. Pointer delivery to windows/layers and deliberate clicks keep
  -- working, and disabling this rule restores every app's existing rules.
  state.hover_rule = hl.window_rule({
    match = { class = ".*" },
    no_follow_mouse = true,
  })
  state.update_focus = function(window)
    local focused = window ~= nil and window.class == app_id
    if state.focused ~= focused then
      state.focused = focused
      state.hover_rule:set_enabled(focused)
    end
  end
  state.focus_listener = hl.on("window.active", state.update_focus)
end

_G.omarchy_file_previewer.update_focus(hl.get_active_window())
