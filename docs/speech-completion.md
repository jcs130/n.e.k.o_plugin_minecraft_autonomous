# Speech completion — `neko_speech.py`

Each project-speech request retains its decision request ID and separate speech
correlation ID. Mirrored text and its TTS output use the same request. The caller
keeps `interrupt_audio=false` and enables the host's normal turn-end notification.
Disabling it leaves players that wait for both turn-end and audio-done dependent
on their stuck-speaking watchdog after audible playback finishes.

Hosts must route delayed completion by request identity when newer text can
arrive before older speech drains. An older end must not seal a newer bubble,
and duplicate or cancelled-session ends must not finish unrelated speech. A
completion notification never authorizes dropping buffered audio; audio-done
and actual scheduled-source completion remain separate barriers.

The asynchronous outbox, unknown-transport protection and existing host voice
are unchanged. HTTP success or synthesis delivery does not prove that a viewer
heard the line. Actual playback requires the player's own started/ended evidence.
