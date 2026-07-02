import numpy as np

try:
    # Attempt to load torch and silero-vad
    import torch
    SILERO_AVAILABLE = True
except ImportError:
    SILERO_AVAILABLE = False

class VoiceActivityDetector:
    def __init__(self, sample_rate: int = 16000, frame_duration_ms: int = 30, threshold: float = 0.5):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
        self.use_silero = False
        
        # Silence tracking variables
        self.is_speaking_state = False
        self.silence_frames_count = 0
        self.speech_frames_count = 0
        
        # Max silence frames before declaring utterance complete
        self.silence_limit = int(1500 / frame_duration_ms) # 1.5 seconds of silence
        self.speech_confirm_limit = int(150 / frame_duration_ms) # 150 ms of speech to trigger speaking

        if SILERO_AVAILABLE:
            try:
                # Load silero model using torch hub
                self.model, utils = torch.hub.load(
                    repo_or_dir='snakers4/silero-vad',
                    model='silero_vad',
                    force_reload=False,
                    trust_repo=True
                )
                self.get_speech_timestamps = utils[0]
                self.use_silero = True
                print("Silero VAD successfully loaded.")
            except Exception as e:
                print(f"Could not load Silero VAD via torch hub: {e}. Using RMS Energy fallback.")
        else:
            print("PyTorch/Silero VAD not available. Using RMS Energy fallback.")

        # Baseline noise floor for RMS fallback
        self.rms_threshold = 0.02 # Adjusted threshold for raw float32 PCM (-1.0 to 1.0)

    def process_frame(self, frame: np.ndarray) -> Tuple[bool, bool]:
        """
        Processes a small audio frame (e.g. 30ms or 480 samples).
        Returns a tuple: (is_currently_speaking, has_utterance_finished)
        """
        # Ensure we have the right data type
        if frame.dtype != np.float32:
            frame = frame.astype(np.float32)

        # 1. Determine if the frame has speech activity
        has_activity = False
        if self.use_silero:
            try:
                # Convert array to tensor and get speech probability
                tensor_frame = torch.from_numpy(frame)
                speech_prob = self.model(tensor_frame, self.sample_rate).item()
                has_activity = speech_prob > self.threshold
            except Exception as e:
                # Fallback to RMS if model execution fails
                has_activity = self._rms_activity(frame)
        else:
            has_activity = self._rms_activity(frame)

        # 2. State Machine for speech / silence segmentation
        if has_activity:
            self.speech_frames_count += 1
            self.silence_frames_count = 0
            if not self.is_speaking_state and self.speech_frames_count >= self.speech_confirm_limit:
                self.is_speaking_state = True
                print("[VAD] User started speaking...")
        else:
            self.silence_frames_count += 1
            if self.is_speaking_state and self.silence_frames_count >= self.silence_limit:
                # User has stopped speaking
                self.is_speaking_state = False
                self.speech_frames_count = 0
                self.silence_frames_count = 0
                print("[VAD] Utterance complete (silence threshold met).")
                return False, True # (is_speaking=False, utterance_finished=True)

        return self.is_speaking_state, False

    def _rms_activity(self, frame: np.ndarray) -> bool:
        """
        Calculates Root-Mean-Square energy of the frame.
        """
        if len(frame) == 0:
            return False
        rms = np.sqrt(np.mean(frame ** 2))
        return rms > self.rms_threshold

    def reset(self):
        self.is_speaking_state = False
        self.silence_frames_count = 0
        self.speech_frames_count = 0
