# ur_voice_cmd

Microphone to speech-to-text to robot command. `voice_cmd_node` publishes transcripts as text commands on `/llm_planner/command` for `ur_llm_planner`.

## Interface

- Publishes `/llm_planner/command` and `/voice_cmd/transcript` (String).
- Backends tried in order with `backend:=auto`: faster-whisper (offline), then speech_recognition with the Google Web API, then Sphinx.
- Params and launch args: `backend`, `whisper_model` (`base`), `language` (`en`), `energy_threshold` (300); node also has `pause_threshold` and `publish_raw`.

## Run

```bash
pip install faster-whisper   # or SpeechRecognition pyaudio
ros2 launch ur_voice_cmd voice_cmd.launch.py backend:=whisper
```

Run `ur_llm_planner` alongside it.
