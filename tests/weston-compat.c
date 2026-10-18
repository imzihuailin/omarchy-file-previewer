/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 Andy Stewart */
/* Aquamarine 0.15 binds wl_compositor/xdg_wm_base v6 and wl_seat v9
 * unconditionally. Weston 15 advertises older versions. These updates add no
 * requests, so this parent-only
 * shim enables nested tests. Never preload it into Hyprland or production apps.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <string.h>
#include <stdlib.h>
#include <wayland-server.h>

static const struct wl_interface *versioned(const struct wl_interface *interface,
                                             int version) {
    if (interface->version >= version)
        return interface;
    struct wl_interface *copy = malloc(sizeof(*copy));
    *copy = *interface;
    copy->version = version;
    return copy; /* Interfaces must outlive the parent compositor's resources. */
}

struct wl_global *wl_global_create(struct wl_display *display,
                                  const struct wl_interface *interface,
                                  int version, void *data,
                                  wl_global_bind_func_t bind) {
    static struct wl_global *(*original)(struct wl_display *,
        const struct wl_interface *, int, void *, wl_global_bind_func_t);
    if (!original)
        original = dlsym(RTLD_NEXT, "wl_global_create");
    if ((strcmp(interface->name, "wl_compositor") == 0 ||
         strcmp(interface->name, "xdg_wm_base") == 0) && version == 5)
        version = 6;
    if (strcmp(interface->name, "wl_seat") == 0 && version == 7)
        version = 9;
    return original(display, versioned(interface, version), version, data, bind);
}

struct wl_resource *wl_resource_create(struct wl_client *client,
                                      const struct wl_interface *interface,
                                      int version, uint32_t id) {
    static struct wl_resource *(*original)(struct wl_client *,
        const struct wl_interface *, int, uint32_t);
    if (!original)
        original = dlsym(RTLD_NEXT, "wl_resource_create");
    return original(client, versioned(interface, version), version, id);
}
