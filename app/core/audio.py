import numpy as np
import io
import wave
from typing import Tuple

class AudioRingBuffer:
    def __init__(self, sample_rate: int = 16000, max_seconds: int = 30):
        self.sample_rate = sample_rate
        self.max_samples = sample_rate * max_seconds
        self.buffer = np.zeros(self.max_samples, dtype=np.float32)
        self.write_index = 0
        self.total_samples_written = 0

    def append(self, pcm_bytes: bytes, bytes_per_sample: int = 4):
        """
        Appends PCM Float32 audio bytes to the buffer.
        """
        if bytes_per_sample == 4:
            # Float32 bytes
            new_samples = np.frombuffer(pcm_bytes, dtype=np.float32)
        elif bytes_per_sample == 2:
            # Int16 bytes
            new_samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            raise ValueError("Unsupported bytes_per_sample: must be 2 (Int16) or 4 (Float32)")
        
        num_new = len(new_samples)
        if num_new == 0:
            return
            
        if num_new > self.max_samples:
            # Crop the new samples if they are larger than the entire buffer
            new_samples = new_samples[-self.max_samples:]
            num_new = len(new_samples)

        # Calculate space to write
        end_pos = (self.write_index + num_new) % self.max_samples
        if self.write_index + num_new <= self.max_samples:
            # Direct write
            self.buffer[self.write_index:self.write_index+num_new] = new_samples
        else:
            # Wrapped write
            first_part = self.max_samples - self.write_index
            self.buffer[self.write_index:] = new_samples[:first_part]
            self.buffer[:end_pos] = new_samples[first_part:]

        self.write_index = end_pos
        self.total_samples_written += num_new

    def get_audio_data(self) -> np.ndarray:
        """
        Returns all samples in order (oldest to newest).
        """
        if self.total_samples_written < self.max_samples:
            return self.buffer[:self.write_index].copy()
        else:
            # Return wrapped
            return np.concatenate((self.buffer[self.write_index:], self.buffer[:self.write_index]))

    def clear(self):
        """
        Clears the buffer.
        """
        self.buffer.fill(0)
        self.write_index = 0
        self.total_samples_written = 0

def convert_float32_to_wav(samples: np.ndarray, sample_rate: int = 16000) -> bytes:
    """
    Converts a float32 numpy array of audio samples into standard WAV bytes (Int16).
    """
    # Scale to int16 range and clip
    int_samples = np.clip(samples * 32767.0, -32768, 32767).astype(np.int16)
    
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int_samples.tobytes())
    return wav_io.getvalue()
