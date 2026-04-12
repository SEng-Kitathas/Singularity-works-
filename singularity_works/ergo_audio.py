from __future__ import annotations
# complexity_justified: CPU-side generative boot synth couples phase-aware tone beds, deterministic wav synthesis, and optional async playback.

from dataclasses import dataclass
from io import BytesIO
import math
import tempfile
import threading
import wave

from .ergo_kerr import BootPhase, boot_frames, total_boot_duration

try:
    import winsound  # type: ignore
except Exception:  # pragma: no cover - platform dependent
    winsound = None


@dataclass(frozen=True)
class BootAudioConfig:
    sample_rate: int = 22050
    master_gain: float = 0.22
    enable_async: bool = True


@dataclass(frozen=True)
class BootAudioState:
    phase: BootPhase
    progress: float
    frequency_hz: float
    shimmer_hz: float
    gain: float


def _state_for_time(t: float, total: float) -> BootAudioState:
    frame = boot_frames(t)
    progress = min(1.0, max(0.0, t / max(total, 0.001)))
    if frame.phase is BootPhase.COLD_BOOT:
        return BootAudioState(frame.phase, progress, 46.0 + frame.progress * 8.0, 92.0, 0.16)
    if frame.phase is BootPhase.SINGULARITY_IGNITION:
        return BootAudioState(frame.phase, progress, 58.0 + frame.progress * 18.0, 174.0, 0.20)
    if frame.phase is BootPhase.ERGOSPHERE_FORMATION:
        return BootAudioState(frame.phase, progress, 74.0 + frame.progress * 26.0, 248.0, 0.24)
    if frame.phase is BootPhase.ORBIT_LOCK:
        return BootAudioState(frame.phase, progress, 98.0, 196.0, 0.18)
    return BootAudioState(frame.phase, progress, 131.0, 262.0, 0.14)


def synth_boot_wav(config: BootAudioConfig = BootAudioConfig()) -> bytes:
    total = total_boot_duration() + 0.24
    sample_count = int(total * config.sample_rate)
    pcm = bytearray()
    for i in range(sample_count):
        t = i / config.sample_rate
        state = _state_for_time(t, total)
        phase_gate = math.sin(2.0 * math.pi * state.frequency_hz * t)
        shimmer = 0.45 * math.sin(2.0 * math.pi * state.shimmer_hz * t + state.progress * 1.7)
        sub = 0.65 * math.sin(2.0 * math.pi * (state.frequency_hz * 0.5) * t)
        envelope = min(1.0, t / 0.12) * min(1.0, (total - t) / 0.20)
        sample = (phase_gate * 0.42 + shimmer * 0.22 + sub * 0.36) * state.gain * config.master_gain * envelope
        value = max(-32767, min(32767, int(sample * 32767.0)))
        pcm.extend(int(value).to_bytes(2, 'little', signed=True))
    buf = BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(config.sample_rate)
        wf.writeframes(bytes(pcm))
    return buf.getvalue()


def play_boot_sound(config: BootAudioConfig = BootAudioConfig()) -> bool:
    if winsound is None:
        return False
    wav_bytes = synth_boot_wav(config)
    if config.enable_async:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            tmp.write(wav_bytes)
            wav_path = tmp.name
        winsound.PlaySound(wav_path, winsound.SND_ASYNC | winsound.SND_NODEFAULT | winsound.SND_FILENAME)
        return True
    winsound.PlaySound(wav_bytes, winsound.SND_MEMORY | winsound.SND_NODEFAULT)
    return True


def play_boot_sound_async(config: BootAudioConfig = BootAudioConfig()) -> bool:
    if winsound is None:
        return False
    thread = threading.Thread(target=play_boot_sound, args=(config,), daemon=True)
    thread.start()
    return True
