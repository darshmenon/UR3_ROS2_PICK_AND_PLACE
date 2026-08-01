#!/usr/bin/env python3
"""
Voice command node: microphone → STT → /llm_planner/command

Backends (tried in order):
  1. faster-whisper  (offline, best quality)   pip install faster-whisper
  2. speech_recognition + Google Web API       pip install SpeechRecognition pyaudio
  3. speech_recognition + Sphinx               (fully offline, lower accuracy)

Usage:
    ros2 run ur_voice_cmd voice_cmd_node.py
    ros2 launch ur_voice_cmd voice_cmd.launch.py backend:=whisper
"""

import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# ── optional imports ──────────────────────────────────────────────────────────

try:
    from faster_whisper import WhisperModel
    _FASTER_WHISPER = True
except ImportError:
    _FASTER_WHISPER = False

try:
    import speech_recognition as sr
    _SR = True
except ImportError:
    _SR = False

try:
    import pyaudio  # noqa: F401  (just checking availability)
    _PYAUDIO = True
except ImportError:
    _PYAUDIO = False


class VoiceCmdNode(Node):
    """
    Continuously listens on the microphone and publishes transcriptions
    to /llm_planner/command so the existing LLM planner can execute them.
    """

    def __init__(self):
        super().__init__("voice_cmd_node")

        self.declare_parameter("backend", "auto")
        self.declare_parameter("whisper_model", "base")
        self.declare_parameter("language", "en")
        self.declare_parameter("energy_threshold", 300)
        self.declare_parameter("pause_threshold", 0.8)
        self.declare_parameter("publish_raw", True)

        backend = self.get_parameter("backend").value
        whisper_model_size = self.get_parameter("whisper_model").value
        self._language = self.get_parameter("language").value
        self._publish_raw = self.get_parameter("publish_raw").value

        self._cmd_pub = self.create_publisher(String, "/llm_planner/command", 10)
        self._transcript_pub = self.create_publisher(String, "/voice_cmd/transcript", 10)

        self._backend = self._resolve_backend(backend)
        self.get_logger().info(f"Voice backend: {self._backend}")

        if self._backend == "whisper":
            self._whisper = WhisperModel(whisper_model_size, device="cpu", compute_type="int8")
            self.get_logger().info(f"Loaded faster-whisper model '{whisper_model_size}'")

        if self._backend in ("whisper", "google", "sphinx"):
            if not _SR:
                self.get_logger().error("speech_recognition not installed. pip install SpeechRecognition pyaudio")
                return
            self._recognizer = sr.Recognizer()
            energy = self.get_parameter("energy_threshold").value
            pause = self.get_parameter("pause_threshold").value
            self._recognizer.energy_threshold = energy
            self._recognizer.pause_threshold = pause

        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        self.get_logger().info("Listening… speak a command at any time.")

    # ── public interface ──────────────────────────────────────────────────────

    def _resolve_backend(self, requested: str) -> str:
        if requested == "auto":
            if _FASTER_WHISPER:
                return "whisper"
            if _SR and _PYAUDIO:
                return "google"
            return "none"
        return requested

    # ── listen loop (runs in background thread) ───────────────────────────────

    def _listen_loop(self):
        if self._backend == "none":
            self.get_logger().error(
                "No STT backend available.\n"
                "  Install faster-whisper:  pip install faster-whisper\n"
                "  Install SpeechRecognition + PyAudio:  pip install SpeechRecognition pyaudio"
            )
            return

        if not _SR or not _PYAUDIO:
            self.get_logger().error("PyAudio not available — cannot open microphone.")
            return

        import speech_recognition as sr  # noqa: F811

        with sr.Microphone() as source:
            self.get_logger().info("Microphone open. Adjusting for ambient noise (1 s)…")
            self._recognizer.adjust_for_ambient_noise(source, duration=1)
            self.get_logger().info("Ready. Speak your command.")

            while rclpy.ok():
                try:
                    audio = self._recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    text = self._transcribe(audio)
                    if text:
                        self.get_logger().info(f'Heard: "{text}"')
                        self._publish(text)
                except sr.WaitTimeoutError:
                    pass  # silence — loop again
                except Exception as exc:
                    self.get_logger().warn(f"Listen error: {exc}")

    def _transcribe(self, audio) -> str:
        import io
        import speech_recognition as sr  # noqa: F811

        if self._backend == "whisper":
            wav_bytes = audio.get_wav_data()
            import numpy as np
            pcm = np.frombuffer(wav_bytes[44:], dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = self._whisper.transcribe(pcm, language=self._language)
            return " ".join(s.text.strip() for s in segments).strip()

        if self._backend == "google":
            return self._recognizer.recognize_google(audio, language=self._language)

        if self._backend == "sphinx":
            return self._recognizer.recognize_sphinx(audio)

        return ""

    def _publish(self, text: str):
        msg = String()
        msg.data = text
        self._cmd_pub.publish(msg)
        if self._publish_raw:
            self._transcript_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = VoiceCmdNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
