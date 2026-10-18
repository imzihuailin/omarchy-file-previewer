/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 Andy Stewart */
/* Minimal wlr-virtual-pointer client, restricted by the test's Wayland socket. */
#include <linux/input-event-codes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <wayland-client.h>

static const struct wl_interface pointer_interface;
static const struct wl_interface *create_types[] = { &wl_seat_interface, &pointer_interface };
static const struct wl_message manager_requests[] = {
    { "create_virtual_pointer", "?on", create_types },
};
static const struct wl_interface manager_interface = {
    "zwlr_virtual_pointer_manager_v1", 1, 1, manager_requests, 0, NULL,
};
static const struct wl_message pointer_requests[] = {
    { "motion", "uff", NULL },
    { "motion_absolute", "uuuuu", NULL },
    { "button", "uuu", NULL },
    { "axis", "uuf", NULL },
    { "frame", "", NULL },
    { "axis_source", "u", NULL },
    { "axis_stop", "uu", NULL },
    { "axis_discrete", "uufi", NULL },
    { "destroy", "", NULL },
};
static const struct wl_interface pointer_interface = {
    "zwlr_virtual_pointer_v1", 1, 9, pointer_requests, 0, NULL,
};
static struct wl_proxy *manager;

static void global(void *data, struct wl_registry *registry, uint32_t name,
                   const char *interface, uint32_t version) {
    (void)data; (void)version;
    if (strcmp(interface, manager_interface.name) == 0)
        manager = wl_registry_bind(registry, name, &manager_interface, 1);
}
static void removed(void *data, struct wl_registry *registry, uint32_t name) {
    (void)data; (void)registry; (void)name;
}
static const struct wl_registry_listener listener = { global, removed };

static uint32_t now(void) {
    struct timespec value;
    clock_gettime(CLOCK_MONOTONIC, &value);
    return (uint32_t)(value.tv_sec * 1000 + value.tv_nsec / 1000000);
}
static void frame(struct wl_proxy *pointer, struct wl_display *display) {
    wl_proxy_marshal_flags(pointer, 4, NULL, 1, 0);
    wl_display_roundtrip(display);
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: pointer move|click|doubleclick X Y\n");
        return 2;
    }
    struct wl_display *display = wl_display_connect(NULL);
    if (!display) return 3;
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &listener, NULL);
    wl_display_roundtrip(display);
    if (!manager) return 4;
    struct wl_proxy *pointer = wl_proxy_marshal_flags(manager, 0,
        &pointer_interface, 1, 0, NULL, NULL);
    wl_proxy_marshal_flags(pointer, 1, NULL, 1, 0, now(),
        (uint32_t)atoi(argv[2]), (uint32_t)atoi(argv[3]), 1280u, 960u);
    frame(pointer, display);
    usleep(100000);
    int clicks = strcmp(argv[1], "doubleclick") == 0 ? 2 :
                 strcmp(argv[1], "click") == 0 ? 1 : 0;
    for (int i = 0; i < clicks; i++) {
        wl_proxy_marshal_flags(pointer, 2, NULL, 1, 0, now(), BTN_LEFT, 1u);
        frame(pointer, display);
        usleep(40000);
        wl_proxy_marshal_flags(pointer, 2, NULL, 1, 0, now(), BTN_LEFT, 0u);
        frame(pointer, display);
        usleep(60000);
    }
    wl_proxy_marshal_flags(pointer, 8, NULL, 1, WL_MARSHAL_FLAG_DESTROY);
    wl_display_roundtrip(display);
    wl_display_disconnect(display);
    return 0;
}
