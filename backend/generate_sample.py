# backend/generate_sample.py
import math
import struct
import wave
import os

def create_sample_wav():
    # Generate a 2-second synthetic tone (440Hz sine wave)
    # This represents a highly structured/stable frequency (like synthetic TTS)
    sample_rate = 16000
    duration = 2.0
    num_samples = int(sample_rate * duration)
    frequency = 440.0
    
    audio_data = []
    for i in range(num_samples):
        t = float(i) / sample_rate
        # Generate sine wave sample normalized to 16-bit range
        sample = int(32767.0 * math.sin(2.0 * math.pi * frequency * t))
        audio_data.append(sample)
    
    output_path = os.path.join(os.path.dirname(__file__), "sample_audio.wav")
    
    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(1)       # Mono channel
        wav_file.setsampwidth(2)      # 16-bit PCM (2 bytes per sample)
        wav_file.setframerate(sample_rate)
        
        # Write frames to WAV file
        for sample in audio_data:
            wav_file.writeframesraw(struct.pack("<h", sample))
            
    print(f"[SUCCESS] Generated sample WAV file at: {output_path}")

if __name__ == "__main__":
    create_sample_wav()
