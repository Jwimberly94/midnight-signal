"""Live stream metadata for the app's available channels.

This module holds the stream URLs used by the channel buttons in the sidebar.
Each entry maps a display name to its HLS playlist endpoint.
"""

# Channel configuration: each key is a user-facing channel name and each value is the feed URL.
CHANNELS = {
    "Toonami East": "http://api.toonamiaftermath.com:3000/est/playlist.m3u8",
    "Toonami West": "http://api.toonamiaftermath.com:3000/pst/playlist.m3u8",
    "Movies": "http://api.toonamiaftermath.com:3000/movies/playlist.m3u8",
    "Radio": "http://api.toonamiaftermath.com:3000/radio/playlist.m3u8",
    "RetroBlast": "https://retroblast.tv/hls/stream.m3u8",
}
