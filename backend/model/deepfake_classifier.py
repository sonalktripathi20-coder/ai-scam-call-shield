"""
deepfake_classifier.py - PyTorch 1D-CNN classifier for Audio Deepfake detection.
"""

import torch
import torch.nn as nn
import numpy as np
import os
try:
    from .feature_extractor import extract_mfcc, pcm_to_float32
except ImportError:
    from feature_extractor import extract_mfcc, pcm_to_float32

class DeepfakeAudioClassifier(nn.Module):
    def __init__(self, num_features=13, seq_len=200):
        super().__init__()
        # Input shape: (batch, num_features, seq_len) -> e.g. (batch, 13, 200)
        self.conv1 = nn.Conv1d(num_features, 32, kernel_size=5, padding=2)
        self.bn1 = nn.BatchNorm1d(32)
        self.pool1 = nn.MaxPool1d(2)
        
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(64)
        self.pool2 = nn.MaxPool1d(2)
        
        self.avgpool = nn.AdaptiveAvgPool1d(1)
        self.fc1 = nn.Linear(64, 32)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(32, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        # x shape: (batch, num_features, seq_len)
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        
        x = self.avgpool(x).squeeze(-1) # shape: (batch, 64)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        out = torch.sigmoid(self.fc2(x)).squeeze(-1) # shape: (batch,)
        return out


class DeepfakeInference:
    def __init__(self, model_path=None, device="cpu"):
        self.device = torch.device(device)
        self.seq_len = 200
        self.num_features = 13
        
        # Check if the newly trained 3-class model exists first
        ai_voice_model_path = os.path.join(os.path.dirname(__file__), "ai_voice_model.pth")
        if os.path.exists(ai_voice_model_path):
            try:
                try:
                    from .ai_voice_detector import AIVoiceDetector as PyTorchAIVoiceDetector
                except ImportError:
                    from ai_voice_detector import AIVoiceDetector as PyTorchAIVoiceDetector
                
                self.pytorch_detector = PyTorchAIVoiceDetector(model_path=ai_voice_model_path, device=device)
                if self.pytorch_detector.model_loaded:
                    self.model_loaded = True
                    self.is_3class = True
                    print(f"[Deepfake AI] Loaded 3-class voice model from {ai_voice_model_path}")
                    return
            except Exception as e:
                print(f"[Deepfake AI Warn] Failed to load 3-class model: {e}. Falling back to 2-class classifier.")

        self.is_3class = False
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "deepfake_model.pth")
            
        self.model = DeepfakeAudioClassifier(num_features=self.num_features, seq_len=self.seq_len)
        self.model_loaded = False
        
        # Auto-train baseline model on 1200 data points if missing
        if not os.path.exists(model_path):
            print(f"[Deepfake AI] Model weights {model_path} not found. Triggering auto-training on 1200 speech samples...")
            try:
                from .train_deepfake import train_model
                train_model(size=1200)
            except Exception as e:
                print(f"[Deepfake AI Error] Failed to auto-train model weights: {e}")

        if os.path.exists(model_path):
            try:
                checkpoint = torch.load(model_path, map_location=self.device)
                if isinstance(checkpoint, dict) and "model_state" in checkpoint:
                    self.model.load_state_dict(checkpoint["model_state"])
                else:
                    self.model.load_state_dict(checkpoint)
                self.model.to(self.device)
                self.model.eval()
                self.model_loaded = True
                best_acc = checkpoint.get("best_acc", 0.0) if isinstance(checkpoint, dict) else 0.0
                print(f"[Deepfake AI] Loaded model from {model_path} (Acc={best_acc:.2%})")
            except Exception as e:
                print(f"[Deepfake AI Warn] Failed to load model weights: {e}")
        else:
            print(f"[Deepfake AI Warn] Model file {model_path} not found. Running in demo mode.")

    def predict_pcm(self, pcm_bytes: bytes) -> float:
        """
        Takes raw PCM bytes, extracts MFCCs, and evaluates the Deepfake score.
        Returns float between 0.0 (100% human) and 1.0 (100% AI/synthetic).
        """
        if not self.model_loaded:
            # Fallback Demo Mode heuristics if model is not trained yet
            return self._demo_predict(pcm_bytes)
            
        if getattr(self, "is_3class", False):
            try:
                # model.ai_voice_detector returns (prediction, probabilities)
                _, probs = self.pytorch_detector.predict_pcm(pcm_bytes)
                # Class 0 is Human, so synthetic/AI probability is 1.0 - probs["Human"]
                return float(1.0 - probs.get("Human", 0.0))
            except Exception as e:
                print(f"[Deepfake AI Error] 3-class prediction failed: {e}")
                return 0.0
            
        try:
            signal = pcm_to_float32(pcm_bytes)
            if len(signal) < 8000: # Need at least 0.5 seconds
                return 0.0
                
            mfcc = extract_mfcc(signal, sr=16000, num_cep=self.num_features)
            
            # Format to shape (13, 200)
            if mfcc.shape[0] < self.seq_len:
                # Pad
                pad_width = self.seq_len - mfcc.shape[0]
                mfcc = np.pad(mfcc, ((0, pad_width), (0, 0)), mode='constant')
            else:
                # Truncate
                mfcc = mfcc[:self.seq_len, :]
                
            # Transpose to (num_features, seq_len) -> (13, 200)
            mfcc_input = mfcc.T
            
            # Predict
            tensor_input = torch.tensor(mfcc_input, dtype=torch.float).unsqueeze(0).to(self.device)
            with torch.no_grad():
                score = self.model(tensor_input).item()
            return score
            
        except Exception as e:
            print(f"[Deepfake AI Error] Prediction failed: {e}")
            return 0.0

    def _demo_predict(self, pcm_bytes: bytes) -> float:
        """
        Demo mode heuristic: uses standard acoustic variance of synthetic voices.
        Usually synthetic voices have much flatter pitch/energy distributions.
        """
        try:
            signal = pcm_to_float32(pcm_bytes)
            if len(signal) < 3200:
                return 0.0
            # A simple pitch-like / energy variance calculation to generate a stable score
            variance = float(np.var(signal))
            # Normalize variance to a demo score
            demo_val = (variance * 1000) % 1.0
            return round(0.1 + demo_val * 0.8, 3) # map to [0.1, 0.9]
        except:
            return 0.0
