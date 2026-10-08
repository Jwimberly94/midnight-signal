# Channel Hopper

A small Linux desktop player for Toonami Aftermath and RetroBlast live streams.

## Requirements

- Python 3.10 or newer
- VLC media player and its native libVLC library

On Debian or Ubuntu, install the system player with:

```sh
sudo apt install vlc
```

On Wayland, the launcher uses XWayland when available because VLC's Linux video embedding API expects an X11 window. Without XWayland, VLC may open video in a separate window.

For a one-command launch from a terminal, run:

```sh
./run.sh
```

The script uses the project's `.venv` and installs the Python dependencies there if needed. You do not need to activate the environment manually.

The `midnight-signal` command launches the app from any directory when installed in `~/.local/bin`.

The Schedules tab embeds the Toonami Aftermath schedule and RetroBlast's public Google Sheet. If either schedule URL changes, update `SCHEDULES` in `channel_hopper/schedules.py`.

The Toonami playlist URLs are the endpoints provided for East, West, Movies, and Radio. RetroBlast uses the public Owncast HLS path. If a service changes its stream endpoint, update `CHANNELS` in `channel_hopper/channels.py`.
