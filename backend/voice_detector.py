"""
voice_detector.py - AI Voice Detection Module
Extracts acoustic features and classifies voice as Human, AI Generated, or Uncertain.
"""

import os
import io
import wave
import numpy as np
try:
    from scipy.fftpack import dct
except ImportError:
    dct = None

# Try importing av for advanced container formats decoding
try:
    import av
    AV_AVAILABLE = True
except ImportError:
    AV_AVAILABLE = False


def decode_audio_to_pcm(file_bytes: bytes) -> bytes:
    """
    Decode audio of any container format (WAV, MP3, M4A, etc.) to 16kHz, 16-bit mono PCM.
    Uses multiple fallback strategies to ensure MP3/M4A files are decoded.
    """
    if not file_bytes:
        return b""

    # Strategy 1: PyAV (handles all formats if installed)
    if AV_AVAILABLE:
        try:
            input_file = io.BytesIO(file_bytes)
            container = av.open(input_file)
            audio_stream = next((s for s in container.streams if s.type == 'audio'), None)
            
            if not audio_stream:
                raise ValueError("No audio stream found in container")
                
            resampler = av.AudioResampler(
                format='s16',
                layout='mono',
                rate=16000
            )
            
            pcm_data = bytearray()
            for frame in container.decode(audio_stream):
                resampled_frames = resampler.resample(frame)
                for rf in resampled_frames:
                    pcm_data.extend(bytes(rf.planes[0]))
            if len(pcm_data) > 0:
                print(f"[Audio Decode] PyAV success: {len(pcm_data)} bytes PCM")
                return bytes(pcm_data)
            else:
                raise ValueError("PyAV returned empty audio")
        except Exception as e:
            print(f"[Audio Decode] PyAV failed: {e}. Trying next decoder...")

    # Strategy 2: soundfile (handles WAV, FLAC, OGG; limited MP3 support)
    try:
        import soundfile as sf
        audio_io = io.BytesIO(file_bytes)
        data, samplerate = sf.read(audio_io, dtype='int16')
        if len(data.shape) > 1:
            data = data.mean(axis=1).astype(np.int16)
        if samplerate != 16000:
            duration = len(data) / samplerate
            new_len = int(duration * 16000)
            data = np.interp(
                np.linspace(0, len(data) - 1, new_len),
                np.arange(len(data)), data
            ).astype(np.int16)
        if len(data) > 0:
            print(f"[Audio Decode] soundfile success: {len(data)*2} bytes PCM")
            return data.tobytes()
    except Exception as e:
        print(f"[Audio Decode] soundfile failed: {e}. Trying next decoder...")

    # Strategy 3: ffmpeg subprocess (universal decoder)
    try:
        import subprocess
        import sys
        import tempfile

        # Write input to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.audio') as tmp_in:
            tmp_in.write(file_bytes)
            tmp_in_path = tmp_in.name

        tmp_out_path = tmp_in_path + '.wav'

        try:
            # Try ffmpeg
            result = subprocess.run(
                ['ffmpeg', '-y', '-i', tmp_in_path,
                 '-ar', '16000', '-ac', '1', '-f', 's16le', '-acodec', 'pcm_s16le',
                 tmp_out_path],
                capture_output=True, timeout=30
            )
            if result.returncode == 0 and os.path.exists(tmp_out_path):
                with open(tmp_out_path, 'rb') as f:
                    pcm_data = f.read()
                if len(pcm_data) > 0:
                    print(f"[Audio Decode] ffmpeg success: {len(pcm_data)} bytes PCM")
                    return pcm_data
        except FileNotFoundError:
            print("[Audio Decode] ffmpeg not found. Trying next decoder...")
        except Exception as e:
            print(f"[Audio Decode] ffmpeg error: {e}")
        finally:
            for p in [tmp_in_path, tmp_out_path]:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except:
                    pass
    except Exception as e:
        print(f"[Audio Decode] ffmpeg strategy failed: {e}")

    # Strategy 4: pydub (if installed, handles MP3 natively)
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(io.BytesIO(file_bytes))
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        pcm_data = audio.raw_data
        if len(pcm_data) > 0:
            print(f"[Audio Decode] pydub success: {len(pcm_data)} bytes PCM")
            return pcm_data
    except Exception as e:
        print(f"[Audio Decode] pydub failed: {e}. Trying wave fallback...")

    # Strategy 5: Standard wave library (WAV only)
    try:
        with wave.open(io.BytesIO(file_bytes), 'rb') as wav:
            params = wav.getparams()
            raw = wav.readframes(params.nframes)
            
            if params.framerate == 16000 and params.sampwidth == 2 and params.nchannels == 1:
                return raw
                
            signal = np.frombuffer(raw, dtype=np.int16)
            if params.nchannels > 1:
                signal = signal.reshape(-1, params.nchannels).mean(axis=1).astype(np.int16)
                
            if params.framerate != 16000:
                duration = len(signal) / params.framerate
                new_len = int(duration * 16000)
                signal = np.interp(
                    np.linspace(0, len(signal) - 1, new_len),
                    np.arange(len(signal)),
                    signal
                ).astype(np.int16)
                
            return signal.tobytes()
    except Exception as ex:
        print(f"[Audio Decode] Wave decoder failed: {ex}")

    # Strategy 6: Raw byte interpretation as last resort
    # If file starts with RIFF header, try to parse manually
    if file_bytes[:4] == b'RIFF':
        try:
            # Skip WAV header (typically 44 bytes) and treat rest as PCM
            pcm_data = file_bytes[44:]
            if len(pcm_data) > 1000:
                print(f"[Audio Decode] Raw RIFF fallback: {len(pcm_data)} bytes")
                return pcm_data
        except:
            pass

    print("[Audio Decode] ALL DECODERS FAILED. Returning empty audio.")
    return b""


def extract_acoustic_features(signal: np.ndarray, sr: int = 16000) -> dict:
    """
    Extract advanced acoustic features for AI voice detection.
    Includes spectral flatness, harmonic regularity, temporal smoothness,
    and spectral flux — features that catch modern neural TTS (ElevenLabs, etc.)
    """
    _empty = {
        "pitch_variance": 0.0, "speaking_rate": 0.0, "pause_frequency": 0.0,
        "energy_variation": 0.0, "spectral_entropy": 0.0, "jitter": 0.0,
        "shimmer": 0.0, "voice_stability": 0.0, "breathing_detected": 0.0,
        "prosody_score": 0.0, "mfcc_variance": 0.0,
        "spectral_flatness": 0.0, "spectral_flux_std": 0.0,
        "harmonic_ratio": 0.0, "temporal_smoothness": 0.0,
        "micro_modulation": 0.0, "hnr": 0.0
    }
    if len(signal) == 0:
        return _empty

    frame_len = int(0.025 * sr)
    frame_step = int(0.010 * sr)

    if len(signal) < frame_len:
        signal = np.pad(signal, (0, frame_len - len(signal)), mode='constant')

    num_frames = 1 + (len(signal) - frame_len) // frame_step
    frames = []
    for i in range(num_frames):
        start = i * frame_step
        frames.append(signal[start:start + frame_len])
    frames = np.array(frames)

    # --- Energy ---
    energies = np.sum(frames ** 2, axis=1)
    energy_variation = float(np.var(energies)) if len(energies) > 1 else 0.0

    # --- Pitch (F0) via autocorrelation ---
    min_lag = int(sr / 350)
    max_lag = int(sr / 60)
    pitches, periods, amplitudes = [], [], []
    for f in frames:
        corr = np.correlate(f, f, mode='full')
        corr = corr[len(corr) // 2:]
        if len(corr) > max_lag:
            lag_region = corr[min_lag:max_lag]
            if len(lag_region) > 0 and np.max(lag_region) > 0.05 * corr[0]:
                peak_lag = np.argmax(lag_region) + min_lag
                pitches.append(sr / peak_lag)
                periods.append(peak_lag)
                amplitudes.append(float(np.max(f) - np.min(f)))
            else:
                pitches.append(0.0); periods.append(0.0); amplitudes.append(0.0)
        else:
            pitches.append(0.0); periods.append(0.0); amplitudes.append(0.0)

    pitches = np.array(pitches)
    valid_pitches = pitches[pitches > 0]
    pitch_variance = float(np.var(valid_pitches)) if len(valid_pitches) > 1 else 0.0

    # --- Jitter ---
    valid_periods = [p for p in periods if p > 0]
    if len(valid_periods) > 1:
        mean_period = np.mean(valid_periods)
        jitter = float(np.mean(np.abs(np.diff(valid_periods))) / mean_period) if mean_period > 0 else 0.0
    else:
        jitter = 0.0

    # --- Shimmer ---
    valid_amps = [a for a in amplitudes if a > 0]
    if len(valid_amps) > 1:
        mean_amp = np.mean(valid_amps)
        shimmer = float(np.mean(np.abs(np.diff(valid_amps))) / mean_amp) if mean_amp > 0 else 0.0
    else:
        shimmer = 0.0

    # --- Speaking rate & Pause frequency ---
    mean_energy = np.mean(energies)
    silence_threshold = 0.05 * mean_energy if mean_energy > 0 else 0.0001
    silent_frames = energies < silence_threshold
    pause_frequency = float(np.mean(silent_frames))
    energy_peaks, in_peak = 0, False
    for i, e in enumerate(energies):
        if e > mean_energy and not silent_frames[i]:
            if not in_peak: energy_peaks += 1; in_peak = True
        else:
            in_peak = False
    duration_s = len(signal) / sr
    speaking_rate = float(energy_peaks / duration_s) if duration_s > 0 else 0.0

    # --- Spectral Entropy ---
    nfft = 512
    entropies = []
    power_spectra = []
    for f in frames:
        fft_vals = np.fft.rfft(f * np.hamming(frame_len), nfft)
        pow_vals = np.abs(fft_vals) ** 2
        power_spectra.append(pow_vals)
        sum_pow = np.sum(pow_vals)
        if sum_pow > 0:
            p = pow_vals / sum_pow
            p = np.where(p == 0, np.finfo(float).eps, p)
            entropies.append(-np.sum(p * np.log2(p)))
        else:
            entropies.append(0.0)
    spectral_entropy = float(np.mean(entropies))
    power_spectra = np.array(power_spectra)

    # --- Voice Stability ---
    stability = 1.0 / (1.0 + jitter * 6.0 + shimmer * 3.0 + (pitch_variance / 2000.0))
    voice_stability = float(np.clip(stability, 0.0, 1.0))

    # --- Breathing detection ---
    zcrs = []
    for i, f in enumerate(frames):
        if silent_frames[i]:
            zcrs.append(np.mean(np.abs(np.diff(np.sign(f)))) / 2)
    breathing_detected = float(np.mean(zcrs)) if zcrs else 0.0

    # --- Prosody ---
    prosody_score = float(np.std(valid_pitches) / (np.mean(valid_pitches) + 1e-5)) if len(valid_pitches) > 0 else 0.0

    # --- MFCC variance ---
    try:
        from model.feature_extractor import extract_mfcc
        mfccs = extract_mfcc(signal, sr=sr)
        mfcc_variance = float(np.var(mfccs)) if mfccs.size > 0 else 0.0
    except Exception:
        mfcc_variance = 0.0

    # ====================================================================
    # NEW FEATURES: Catches modern neural TTS (ElevenLabs, Play.ht, etc.)
    # ====================================================================

    # --- Spectral Flatness (Wiener entropy) ---
    # AI voices have LOWER spectral flatness (too-clean harmonics)
    flatness_vals = []
    for ps in power_spectra:
        ps_pos = ps[ps > 0]
        if len(ps_pos) > 0:
            geo_mean = np.exp(np.mean(np.log(ps_pos + 1e-20)))
            arith_mean = np.mean(ps_pos)
            flatness_vals.append(geo_mean / (arith_mean + 1e-20))
    spectral_flatness = float(np.mean(flatness_vals)) if flatness_vals else 0.0

    # --- Spectral Flux Consistency ---
    # AI voices have MORE UNIFORM spectral changes frame-to-frame
    if len(power_spectra) > 1:
        flux_values = []
        for i in range(1, len(power_spectra)):
            diff = power_spectra[i] - power_spectra[i - 1]
            flux_values.append(np.sqrt(np.sum(diff ** 2)))
        spectral_flux_std = float(np.std(flux_values) / (np.mean(flux_values) + 1e-10))
    else:
        spectral_flux_std = 0.0

    # --- Harmonic-to-Noise Ratio (HNR) ---
    # AI voices are TOO CLEAN — very high HNR
    hnr_values = []
    for f in frames[:min(100, len(frames))]:
        corr = np.correlate(f, f, mode='full')
        corr = corr[len(corr) // 2:]
        if len(corr) > max_lag and corr[0] > 0:
            peak = np.max(corr[min_lag:max_lag])
            noise = corr[0] - peak
            if noise > 1e-9 and peak > 0:
                hnr_values.append(10 * np.log10(max(1e-9, peak) / max(1e-9, noise)))
    hnr = float(np.mean(hnr_values)) if hnr_values else 0.0

    # --- Harmonic Regularity ---
    # AI voices have very regular harmonic spacing
    harmonic_ratios = []
    for ps in power_spectra[:min(50, len(power_spectra))]:
        peaks_idx = []
        for j in range(1, len(ps) - 1):
            if ps[j] > ps[j - 1] and ps[j] > ps[j + 1] and ps[j] > np.mean(ps) * 2:
                peaks_idx.append(j)
        if len(peaks_idx) >= 3:
            spacings = np.diff(peaks_idx)
            if np.mean(spacings) > 0:
                harmonic_ratios.append(float(np.std(spacings) / np.mean(spacings)))
    harmonic_ratio = float(np.mean(harmonic_ratios)) if harmonic_ratios else 0.5

    # --- Temporal Envelope Smoothness ---
    # AI voices have smoother amplitude envelopes
    if len(energies) > 2:
        energy_diff = np.abs(np.diff(energies))
        energy_diff2 = np.abs(np.diff(energy_diff)) if len(energy_diff) > 1 else np.array([0])
        temporal_smoothness = float(1.0 / (1.0 + np.mean(energy_diff2) * 1000))
    else:
        temporal_smoothness = 0.0

    # --- Micro-modulation depth ---
    # Human voices have more frame-level amplitude micro-variations
    if len(valid_amps) > 5:
        amp_arr = np.array(valid_amps)
        # High-pass filter the amplitude envelope
        amp_detrended = amp_arr - np.convolve(amp_arr, np.ones(5) / 5, mode='same')
        micro_modulation = float(np.std(amp_detrended) / (np.mean(amp_arr) + 1e-10))
    else:
        micro_modulation = 0.0

    ret = {
        "pitch_variance": round(pitch_variance, 2),
        "speaking_rate": round(speaking_rate, 2),
        "pause_frequency": round(pause_frequency, 2),
        "energy_variation": round(energy_variation, 4),
        "spectral_entropy": round(spectral_entropy, 2),
        "jitter": round(jitter, 4),
        "shimmer": round(shimmer, 4),
        "voice_stability": round(voice_stability, 2),
        "breathing_detected": round(breathing_detected, 3),
        "prosody_score": round(prosody_score, 2),
        "mfcc_variance": round(mfcc_variance, 2),
        "spectral_flatness": round(spectral_flatness, 4),
        "spectral_flux_std": round(spectral_flux_std, 4),
        "harmonic_ratio": round(harmonic_ratio, 4),
        "temporal_smoothness": round(temporal_smoothness, 4),
        "micro_modulation": round(micro_modulation, 4),
        "hnr": round(hnr, 2)
    }
    for k, v in ret.items():
        if np.isnan(v) or np.isinf(v):
            ret[k] = 0.0
    return ret


def classify_voice_from_features(features: dict) -> tuple[float, str, float]:
    """
    Advanced multi-factor AI voice classifier.
    Designed to detect modern neural TTS (ElevenLabs, Play.ht, Google, etc.)
    Returns (ai_voice_score, classification, confidence)
    """
    score = 0.0
    evidence = []

    # ──────── CLASSIC FEATURES (30 pts max) ────────

    # 1. Pitch variance — AI can have natural-range variance but less micro-variation
    pv = features.get("pitch_variance", 500)
    if pv < 80:
        score += 12; evidence.append("very_low_pitch_var")
    elif pv < 250:
        score += 6; evidence.append("low_pitch_var")

    # 2. Jitter — AI voices have lower jitter
    jit = features.get("jitter", 0.02)
    if jit < 0.008:
        score += 10; evidence.append("low_jitter")
    elif jit < 0.018:
        score += 5; evidence.append("moderate_jitter")

    # 3. Shimmer — AI voices have lower shimmer
    shim = features.get("shimmer", 0.1)
    if shim < 0.03:
        score += 8; evidence.append("low_shimmer")
    elif shim < 0.07:
        score += 4; evidence.append("moderate_shimmer")

    # ──────── NEW AI-CATCHING FEATURES (70 pts max) ────────

    # 4. Spectral Flatness — AI voices are TOO harmonically clean (very robust to noise)
    sf = features.get("spectral_flatness", 0.1)
    if sf < 0.035:
        score += 25; evidence.append("very_clean_spectrum")
    elif sf < 0.065:
        score += 20; evidence.append("clean_spectrum")
    elif sf < 0.12:
        score += 12; evidence.append("moderate_spectrum")

    # 5. Spectral Flux Consistency — AI has uniform spectral transitions
    sfs = features.get("spectral_flux_std", 1.0)
    if sfs < 0.45:
        score += 20; evidence.append("uniform_spectral_flux")
    elif sfs < 0.85:
        score += 15; evidence.append("smooth_spectral_flux")
    elif sfs < 1.35:
        score += 10; evidence.append("moderate_spectral_flux")

    # 6. HNR — AI voices are too clean (high HNR)
    hnr = features.get("hnr", 5.0)
    if hnr > 18:
        score += 15; evidence.append("very_high_hnr")
    elif hnr > 11:
        score += 10; evidence.append("high_hnr")
    elif hnr > 6.0:
        score += 5; evidence.append("moderate_hnr")

    # 7. Temporal Smoothness — AI envelopes are too smooth
    ts = features.get("temporal_smoothness", 0.3)
    if ts > 0.75:
        score += 15; evidence.append("very_smooth_envelope")
    elif ts > 0.50:
        score += 12; evidence.append("smooth_envelope")
    elif ts > 0.32:
        score += 8; evidence.append("moderate_envelope")

    # 8. Harmonic Regularity — AI has perfectly spaced harmonics
    hr = features.get("harmonic_ratio", 0.5)
    if hr < 0.12:
        score += 15; evidence.append("perfect_harmonics")
    elif hr < 0.24:
        score += 12; evidence.append("regular_harmonics")
    elif hr < 0.35:
        score += 8; evidence.append("moderate_harmonics")

    # 9. Micro-modulation — AI lacks natural micro-amplitude variations
    mm = features.get("micro_modulation", 0.1)
    if mm < 0.02:
        score += 12; evidence.append("no_micro_modulation")
    elif mm < 0.075:
        score += 10; evidence.append("low_micro_modulation")

    # 10. Breathing absence — AI rarely generates breathing
    bd = features.get("breathing_detected", 0.03)
    if bd < 0.005:
        score += 8; evidence.append("no_breathing")
    elif bd < 0.018:
        score += 4; evidence.append("minimal_breathing")

    # 11. Prosody score — AI has less natural prosodic variation
    ps = features.get("prosody_score", 0.15)
    if ps < 0.04:
        score += 5; evidence.append("flat_prosody")
    elif ps < 0.08:
        score += 3; evidence.append("low_prosody")

    # ──────── Evidence-based boosting ────────
    # If multiple independent AI indicators fire, boost confidence
    ai_indicators = len(evidence)
    if ai_indicators >= 8:
        score = min(score * 1.15, 100)
    elif ai_indicators >= 6:
        score = min(score * 1.08, 100)

    ai_score = float(np.clip(score, 0.0, 100.0))

    # Classify
    if ai_score >= 55:
        classification = "Likely AI Generated"
        confidence = float(np.clip(55 + (ai_score - 55) * 0.95, 60.0, 98.0))
    elif ai_score >= 30:
        classification = "Uncertain"
        confidence = float(50.0 + (50 - abs(ai_score - 42)) * 0.35)
    else:
        classification = "Likely Human"
        confidence = float(np.clip(55 + (30 - ai_score) * 1.4, 60.0, 98.0))

    return round(ai_score, 1), classification, round(confidence, 1)


def sanitize_dict_floats(d: dict) -> dict:
    """Recursively replaces NaN, inf, and -inf float values in a dictionary with safe values (0.0)."""
    sanitized = {}
    for k, v in d.items():
        if isinstance(v, dict):
            sanitized[k] = sanitize_dict_floats(v)
        elif isinstance(v, (float, np.float32, np.float64)):
            if np.isnan(v) or np.isinf(v):
                sanitized[k] = 0.0
            else:
                sanitized[k] = float(v)
        elif isinstance(v, list):
            sanitized_list = []
            for item in v:
                if isinstance(item, (float, np.float32, np.float64)):
                    if np.isnan(item) or np.isinf(item):
                        sanitized_list.append(0.0)
                    else:
                        sanitized_list.append(float(item))
                else:
                    sanitized_list.append(item)
            sanitized[k] = sanitized_list
        else:
            sanitized[k] = v
    return sanitized


class AIVoiceDetector:
    def __init__(self):
        # Priority chain: ML Model (pkl) → PyTorch → Heuristic
        self.ml_predictor = None
        self.ml_loaded = False
        self.pytorch_loaded = False
        self.pytorch_detector = None

        # 1. Try loading trained ML model (Random Forest / XGBoost / LightGBM)
        try:
            from model.predict_voice import VoicePredictor
            self.ml_predictor = VoicePredictor()
            if self.ml_predictor.model_loaded:
                self.ml_loaded = True
                print(f"[AIVoiceDetector] ✅ ML model loaded: {self.ml_predictor.model_name}")
        except Exception as e:
            print(f"[AIVoiceDetector] ML model not available: {e}")
            self.ml_predictor = None

        # 2. Try PyTorch engine as secondary classifier
        if self._check_safe("torch"):
            try:
                from model.deepfake_classifier import DeepfakeInference
                self.pytorch_detector = DeepfakeInference()
                if hasattr(self.pytorch_detector, 'model_loaded') and self.pytorch_detector.model_loaded:
                    self.pytorch_loaded = True
            except Exception as e:
                print(f"[AIVoiceDetector] PyTorch model initialization bypassed: {e}")
                self.pytorch_detector = None
        else:
            print("[AIVoiceDetector] PyTorch is unavailable or unstable on this system. Bypassing PyTorch detector.")

        # Log detection strategy
        if self.ml_loaded:
            print("[AIVoiceDetector] Strategy: ML Model (primary) → Heuristic (fallback)")
        elif self.pytorch_loaded:
            print("[AIVoiceDetector] Strategy: PyTorch (primary) → Heuristic (fallback)")
        else:
            print("[AIVoiceDetector] Strategy: Heuristic only (no trained models available)")

    def _check_safe(self, module_name: str) -> bool:
        try:
            import importlib
            importlib.import_module(module_name)
            return True
        except Exception:
            return False

    def analyze_audio_bytes(self, file_bytes: bytes) -> dict:
        """
        Accepts any audio file format bytes, decodes it, extracts features,
        and computes AI Voice Detection report.
        """
        pcm_bytes = decode_audio_to_pcm(file_bytes)
        if not pcm_bytes:
            # Fallback for empty or corrupt audio
            result = {
                "ai_voice_score": 0.0,
                "risk_level": "Likely Human",
                "voice_classification": "Likely Human",
                "confidence_score": 90.0,
                "human_voice_probability": 100.0,
                "ai_voice_probability": 0.0,
                "features": extract_acoustic_features(np.zeros(0)),
                "reasoning": "Could not extract audio features. Defaulting to safe human classification."
            }
            return sanitize_dict_floats(result)

        signal = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # Check for silence/empty signal
        if len(signal) == 0 or np.max(np.abs(signal)) < 0.001:
            result = {
                "ai_voice_score": 0.0,
                "risk_level": "Safe Call",
                "voice_classification": "Likely Human",
                "confidence_score": 95.0,
                "human_voice_probability": 100.0,
                "ai_voice_probability": 0.0,
                "features": extract_acoustic_features(np.zeros(0)),
                "reasoning": "Silence or insufficient voice signal detected. Defaulting to safe human classification."
            }
            return sanitize_dict_floats(result)

        features = extract_acoustic_features(signal, sr=16000)

        # === Always run heuristic classifier (uses new advanced features) ===
        heuristic_score, heuristic_class, heuristic_conf = classify_voice_from_features(features)

        # === Try PyTorch Deepfake Model as primary model signal ===
        pytorch_score = None
        if self.pytorch_loaded and self.pytorch_detector is not None:
            try:
                raw_score = self.pytorch_detector.predict_pcm(pcm_bytes)
                pytorch_score = round(raw_score * 100.0, 1)
                print(f"[AIVoiceDetector] PyTorch Deepfake={pytorch_score}%, Heuristic={heuristic_score}%")
            except Exception as e:
                print(f"[AIVoiceDetector Warn] PyTorch model failed: {e}")
                pytorch_score = None

        # === Try ML Model (Random Forest) as fallback model signal ===
        ml_score = None
        if pytorch_score is None and self.ml_loaded and self.ml_predictor is not None:
            try:
                ml_result = self.ml_predictor.predict_bytes(file_bytes)
                ml_score = round(ml_result["ai_probability"] * 100.0, 1)
                print(f"[AIVoiceDetector] ML={ml_score}%, Heuristic={heuristic_score}%")
            except Exception as e:
                print(f"[AIVoiceDetector Warn] ML model failed: {e}")
                ml_score = None

        # === Combine scores: Heuristic model is highly calibrated for real mic physics ===
        if pytorch_score is not None:
            # Blend PyTorch CNN (50%) and Heuristic (50%)
            blended_score = round(pytorch_score * 0.50 + heuristic_score * 0.50, 1)
            # If PyTorch model is extremely confident, trust it
            if pytorch_score >= 80.0:
                ai_score = max(blended_score, pytorch_score)
            else:
                ai_score = blended_score
        elif ml_score is not None:
            # Blend ML model (40%) and Heuristic (60%) for high real-world stability
            blended_score = round(ml_score * 0.40 + heuristic_score * 0.60, 1)
            ai_score = blended_score
            
            # Ground the ML model prediction using the heuristic baseline:
            # If physical heuristics strongly indicate a real human (score < 15%),
            # cap the combined score to prevent simulated-data ML model baseline drift.
            # But do NOT cap if individual features show strong indicators of AI synthesis.
            if heuristic_score < 15.0:
                is_suspicious_ai = (
                    features.get("spectral_flatness", 1.0) < 0.12 or
                    features.get("harmonic_ratio", 1.0) < 0.35 or
                    features.get("temporal_smoothness", 0.0) > 0.32 or
                    features.get("spectral_flux_std", 1.0) < 1.35 or
                    features.get("hnr", 0.0) > 6.0 or
                    features.get("micro_modulation", 1.0) < 0.075 or
                    features.get("breathing_detected", 1.0) < 0.018 or
                    features.get("prosody_score", 1.0) < 0.08
                )
                if not is_suspicious_ai:
                    ai_score = min(blended_score, round(heuristic_score + 5.0, 1))
            
            # Trust the heuristic score as a high-confidence lower bound
            ai_score = max(heuristic_score, ai_score)
        else:
            ai_score = heuristic_score

        # Use heuristic classification (it has the new thresholds)
        classification = heuristic_class
        confidence = heuristic_conf

        # Re-classify based on combined score
        if ai_score >= 55:
            classification = "Likely AI Generated"
            confidence = round(min(55 + (ai_score - 55) * 0.95, 98.0), 1)
        elif ai_score >= 30:
            classification = "Uncertain"
            confidence = round(50.0 + (50 - abs(ai_score - 42)) * 0.35, 1)
        else:
            classification = "Likely Human"
            confidence = round(min(55 + (30 - ai_score) * 1.4, 98.0), 1)

        # Calculate probabilities
        ai_prob = ai_score
        human_prob = round(100.0 - ai_prob, 1)

        # Generate reasoning based on features (including new ones)
        reasons = []

        # Spectral analysis reasoning
        sf = features.get("spectral_flatness", 0.1)
        if sf < 0.06:
            reasons.append("Unnaturally clean spectral profile typical of neural voice synthesis.")
        else:
            reasons.append("Natural spectral complexity consistent with human vocal tract.")

        hnr = features.get("hnr", 5.0)
        if hnr > 12:
            reasons.append(f"Very high harmonic-to-noise ratio ({hnr:.1f}dB) indicating digitally clean signal.")
        else:
            reasons.append("Normal harmonic-to-noise ratio consistent with natural voice production.")

        hr = features.get("harmonic_ratio", 0.5)
        if hr < 0.18:
            reasons.append("Suspiciously regular harmonic spacing typical of vocoder synthesis.")

        ts = features.get("temporal_smoothness", 0.3)
        if ts > 0.65:
            reasons.append("Overly smooth amplitude envelope lacking natural vocal irregularities.")

        if features["breathing_detected"] < 0.01:
            reasons.append("Absence of breathing/respiration noise signatures.")
        else:
            reasons.append("Natural breathing pauses detected.")

        # Add model info to reasoning
        if pytorch_score is not None:
            reasons.append(f"[Combined analysis: Heuristic={heuristic_score}% + PyTorch={pytorch_score}%]")
        elif ml_score is not None:
            reasons.append(f"[Combined analysis: Heuristic={heuristic_score}% + ML={ml_score}%]")
        else:
            reasons.append("[Analysis by advanced acoustic heuristic engine]")

        reasoning = " ".join(reasons)

        result = {
            "ai_voice_score": ai_score,
            "risk_level": "Likely AI Generated" if ai_score >= 55 else ("Uncertain" if ai_score >= 30 else "Likely Human"),
            "voice_classification": classification,
            "confidence_score": confidence,
            "human_voice_probability": human_prob,
            "ai_voice_probability": ai_prob,
            "features": features,
            "reasoning": reasoning
        }
        return sanitize_dict_floats(result)

    def _fallback_classify(self, file_bytes, pcm_bytes, signal, features):
        """Fallback classification chain: PyTorch → Heuristic"""
        if self.pytorch_loaded:
            try:
                raw_score = self.pytorch_detector.predict_pcm(pcm_bytes)
                ai_score = round(raw_score * 100.0, 1)

                if ai_score >= 61:
                    classification = "Likely AI Generated"
                    confidence = round(50.0 + (ai_score - 60) * 1.2, 1)
                elif ai_score >= 31:
                    classification = "Uncertain"
                    confidence = round(50.0 + (50 - abs(ai_score - 45)) * 0.4, 1)
                else:
                    classification = "Likely Human"
                    confidence = round(50.0 + (30 - ai_score) * 1.5, 1)

                return ai_score, classification, confidence
            except Exception as e:
                print(f"[AIVoiceDetector Warn] PyTorch run failed: {e}. Using heuristic.")

        return classify_voice_from_features(features)
