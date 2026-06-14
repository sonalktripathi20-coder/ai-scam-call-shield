"""
ai_voice_detector.py - Enhanced classifier for detecting Human vs AI-Generated voices
Supports detection of:
- Human speakers (natural voice with vocal characteristics)
- AI-Generated voices (ElevenLabs, Google TTS, Amazon Polly, etc.)
- Deepfake/Synthetic voices (vocoder-based)
"""

import torch
import torch.nn as nn
import numpy as np
import os
from typing import Tuple, Dict, List

try:
    from .feature_extractor import extract_mfcc, pcm_to_float32
except ImportError:
    from feature_extractor import extract_mfcc, pcm_to_float32


class AIVoiceClassifier(nn.Module):
    """
    3-class classifier:
    Class 0: Human voice
    Class 1: AI-Generated (ElevenLabs, Google TTS, etc.)
    Class 2: Deepfake/Synthetic (Vocoder-based)
    """
    def __init__(self, num_features=13, seq_len=200):
        super().__init__()
        # Input shape: (batch, num_features, seq_len)
        
        # Feature extraction layers
        self.conv1 = nn.Conv1d(num_features, 32, kernel_size=5, padding=2)
        self.bn1 = nn.BatchNorm1d(32)
        self.pool1 = nn.MaxPool1d(2)
        
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(64)
        self.pool2 = nn.MaxPool1d(2)
        
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm1d(128)
        self.pool3 = nn.MaxPool1d(2)
        
        # Global average pooling + FC layers
        self.avgpool = nn.AdaptiveAvgPool1d(1)
        self.fc1 = nn.Linear(128, 64)
        self.dropout1 = nn.Dropout(0.4)
        self.fc2 = nn.Linear(64, 32)
        self.dropout2 = nn.Dropout(0.3)
        
        # Output: 3 classes
        self.fc3 = nn.Linear(32, 3)
        self.relu = nn.ReLU()

    def forward(self, x):
        # x shape: (batch, num_features, seq_len)
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        
        x = self.avgpool(x).squeeze(-1)  # shape: (batch, 128)
        x = self.relu(self.fc1(x))
        x = self.dropout1(x)
        x = self.relu(self.fc2(x))
        x = self.dropout2(x)
        
        out = self.fc3(x)  # shape: (batch, 3)
        return out


class AIVoiceDetector:
    """
    Inference wrapper for AI voice detection.
    Returns probabilities and predictions for voice classification.
    """
    
    CLASS_LABELS = {
        0: "Human",
        1: "AI-Generated",
        2: "Deepfake/Synthetic"
    }
    
    def __init__(self, model_path=None, device="cpu"):
        self.device = torch.device(device)
        self.seq_len = 200
        self.num_features = 13
        
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(__file__), 
                "ai_voice_model.pth"
            )
        
        self.model = AIVoiceClassifier(
            num_features=self.num_features, 
            seq_len=self.seq_len
        )
        self.model_path = model_path
        self.model_loaded = False
        
        # Try to load model
        if os.path.exists(model_path):
            self._load_model()
        else:
            print(f"[AI Voice Detector] Model not found at {model_path}")
            print(f"[AI Voice Detector] Run training to create model")

    def _load_model(self):
        """Load trained model weights"""
        try:
            checkpoint = torch.load(self.model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint["model_state"])
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            accuracy = checkpoint.get("best_acc", 0.0)
            print(f"[AI Voice Detector] Model loaded (Accuracy: {accuracy:.2%})")
        except Exception as e:
            print(f"[AI Voice Detector] Failed to load model: {e}")
            self.model_loaded = False

    def predict_pcm(self, pcm_bytes: bytes) -> Tuple[str, Dict[str, float]]:
        """
        Predict voice type from PCM audio bytes.
        
        Args:
            pcm_bytes: Raw 16-bit PCM audio data
            
        Returns:
            Tuple of:
            - predicted_class: "Human", "AI-Generated", or "Deepfake/Synthetic"
            - probabilities: Dict with probabilities for each class
        """
        if not self.model_loaded:
            return self._demo_predict(pcm_bytes)
        
        try:
            signal = pcm_to_float32(pcm_bytes)
            if len(signal) < 8000:  # Need at least 0.5 seconds
                return "Unknown", {
                    "Human": 0.0,
                    "AI-Generated": 0.0,
                    "Deepfake/Synthetic": 1.0
                }
            
            # Extract MFCC features
            mfcc = extract_mfcc(signal, sr=16000, num_cep=self.num_features)
            
            # Format to shape (13, 200)
            if mfcc.shape[0] < self.seq_len:
                pad_width = self.seq_len - mfcc.shape[0]
                mfcc = np.pad(
                    mfcc, 
                    ((0, pad_width), (0, 0)), 
                    mode="constant"
                )
            else:
                mfcc = mfcc[:self.seq_len]
            
            # Convert to tensor with shape (1, num_features, seq_len) -> (1, 13, 200)
            x = torch.tensor(mfcc.T, dtype=torch.float32).unsqueeze(0).to(self.device)
            
            # Inference
            with torch.no_grad():
                logits = self.model(x)
                probs = torch.softmax(logits, dim=1)[0]
            
            pred_idx = torch.argmax(probs).item()
            pred_label = self.CLASS_LABELS[pred_idx]
            
            probabilities = {
                "Human": probs[0].item(),
                "AI-Generated": probs[1].item(),
                "Deepfake/Synthetic": probs[2].item()
            }
            
            return pred_label, probabilities
            
        except Exception as e:
            print(f"[AI Voice Detector] Prediction error: {e}")
            return "Unknown", {
                "Human": 0.33,
                "AI-Generated": 0.33,
                "Deepfake/Synthetic": 0.34
            }

    def predict_file(self, audio_file_path: str) -> Tuple[str, Dict[str, float]]:
        """
        Predict voice type from an audio file.
        Supports: WAV, MP3, OGG formats.
        """
        try:
            import soundfile as sf
            signal, sr = sf.read(audio_file_path)
            
            if sr != 16000:
                from scipy import signal as scipy_signal
                num_samples = int(len(signal) * 16000 / sr)
                signal = scipy_signal.resample(signal, num_samples)
            
            pcm_bytes = (signal * 32768).astype(np.int16).tobytes()
            return self.predict_pcm(pcm_bytes)
            
        except ImportError:
            print("[AI Voice Detector] soundfile library required for file input")
            print("[AI Voice Detector] Install: pip install soundfile")
            return "Unknown", {}
        except Exception as e:
            print(f"[AI Voice Detector] File prediction error: {e}")
            return "Unknown", {}

    def _demo_predict(self, pcm_bytes: bytes) -> Tuple[str, Dict[str, float]]:
        """Fallback demo prediction if model not loaded"""
        # Simple heuristic based on signal characteristics
        signal = pcm_to_float32(pcm_bytes)
        
        if len(signal) < 8000:
            return "Unknown", {
                "Human": 0.0,
                "AI-Generated": 0.0,
                "Deepfake/Synthetic": 1.0
            }
        
        # Calculate signal statistics
        variance = np.var(signal)
        energy = np.sqrt(np.mean(signal ** 2))
        
        # Simple heuristics (replace with trained model)
        if variance > 0.02:
            return "Human", {
                "Human": 0.7,
                "AI-Generated": 0.2,
                "Deepfake/Synthetic": 0.1
            }
        elif variance > 0.01:
            return "AI-Generated", {
                "Human": 0.2,
                "AI-Generated": 0.6,
                "Deepfake/Synthetic": 0.2
            }
        else:
            return "Deepfake/Synthetic", {
                "Human": 0.1,
                "AI-Generated": 0.2,
                "Deepfake/Synthetic": 0.7
            }
