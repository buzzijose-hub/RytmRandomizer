# Versioned appliance presentation assets

These user-systemd templates present the existing React production build using
Chromium in the operator's established labwc/Wayland session. They do not create
a compositor, modify boot files, change groups, enable GPIO or grant MIDI output.

`scripts/pi_appliance.py install` expands the release paths. Start using the
documented `session-start` helper from the graphical session, which imports its
display environment before starting the target. Enabling desktop startup is an
operator step; see `docs/PI_APPLIANCE_DEPLOYMENT.md`.

Both services allow five failures in five minutes with ten seconds between
restarts. SIGTERM provides a fifteen-second graceful shutdown window, and the
existing Cockpit teardown disarms its output handle. Backend logs rotate at
2 MiB with three retained backups. Runtime credentials live in a mode-0700
runtime directory and are deleted on graceful shutdown. Saved profiles, captures,
library and Show Bank files continue to use the shared Cockpit storage.
