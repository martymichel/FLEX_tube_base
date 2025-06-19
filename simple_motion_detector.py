import cv2
import numpy as np
from collections import deque

class SimpleMotionDetector:
    """Helligkeits-unabhängige Bewegungserkennung mit Lernphase."""

    def __init__(self, fps=30.0, learning_seconds=60.0,
                 noise_baseline=2.0, scaling_factor=8.0, start_learning=True):
        self.fps = fps
        self.learning_frames = int(fps * learning_seconds)
        self.downsample_factor = 4
        self.roi_size = 0.6

        # Zustand
        self.prev_frame_small = None
        self.motion_value = 0
        self.motion_history = deque(maxlen=int(fps * 0.3))

        # Lernphase
        self.is_learning = start_learning
        self.learning_frame_count = 0
        self.motion_samples = deque(maxlen=300)

        # Parameter
        self.noise_baseline = noise_baseline
        self.scaling_factor = scaling_factor

        # ROI Cache
        self.roi_slice = None
        self.frame_size = None

        # CLAHE für Helligkeits-Normalisierung
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))

    def process_frame(self, frame):
        processed = self._preprocess_frame(frame)

        if self.prev_frame_small is None:
            self.prev_frame_small = processed
            return 0

        raw_motion = self._calculate_raw_motion(processed, self.prev_frame_small)

        if self.is_learning:
            self._learn(raw_motion)
            self.prev_frame_small = processed
            return 0

        motion_value = self._calculate_final_motion(raw_motion)
        self.prev_frame_small = processed
        return motion_value

    def _preprocess_frame(self, frame):
        if self.roi_slice is None:
            h, w = frame.shape[:2]
            roi_h, roi_w = int(h * self.roi_size), int(w * self.roi_size)
            start_y, start_x = (h - roi_h) // 2, (w - roi_w) // 2
            self.roi_slice = (slice(start_y, start_y + roi_h),
                              slice(start_x, start_x + roi_w))

        roi = frame[self.roi_slice[0], self.roi_slice[1]]

        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi

        small = gray[::self.downsample_factor, ::self.downsample_factor]
        normalized = self.clahe.apply(small.astype(np.uint8))
        return normalized.astype(np.float32)

    def _calculate_raw_motion(self, current, previous):
        grad_x_curr = cv2.Sobel(current, cv2.CV_32F, 1, 0, ksize=3)
        grad_y_curr = cv2.Sobel(current, cv2.CV_32F, 0, 1, ksize=3)
        grad_x_prev = cv2.Sobel(previous, cv2.CV_32F, 1, 0, ksize=3)
        grad_y_prev = cv2.Sobel(previous, cv2.CV_32F, 0, 1, ksize=3)

        mag_curr = np.sqrt(grad_x_curr ** 2 + grad_y_curr ** 2)
        mag_prev = np.sqrt(grad_x_prev ** 2 + grad_y_prev ** 2)

        mean_curr, mean_prev = np.mean(current), np.mean(previous)
        if mean_prev > 0 and mean_curr > 0:
            norm_curr = current / mean_curr
            norm_prev = previous / mean_prev
            normalized_motion = np.mean(np.abs(norm_curr - norm_prev)) * 100
        else:
            normalized_motion = 0

        edge_motion = np.mean(np.abs(mag_curr - mag_prev))

        return normalized_motion * 0.6 + edge_motion * 0.4

    def _learn(self, raw_motion):
        if self.learning_frame_count % 2 == 0:
            self.motion_samples.append(raw_motion)
        self.learning_frame_count += 1
        if self.learning_frame_count >= self.learning_frames:
            self._complete_learning()

    def _complete_learning(self):
        if self.motion_samples:
            samples = np.array(self.motion_samples)
            self.noise_baseline = np.percentile(samples, 10)
            p90 = np.percentile(samples, 90)
            effective_range = max(1.0, p90 - self.noise_baseline)
            self.scaling_factor = 255.0 / effective_range
        self.is_learning = False
        print(
            f"\u2705 Lernphase abgeschlossen - Baseline: {self.noise_baseline:.1f}, Skala: {self.scaling_factor:.1f}")

    def _calculate_final_motion(self, raw_motion):
        if raw_motion <= self.noise_baseline:
            cleaned = 0
        else:
            cleaned = raw_motion - self.noise_baseline
        scaled = min(255, int(cleaned * self.scaling_factor))
        self.motion_history.append(scaled)
        self.motion_value = int(np.mean(self.motion_history)) if self.motion_history else scaled
        return self.motion_value

    def is_learning_phase(self):
        return self.is_learning

    def get_learning_progress(self):
        return (self.learning_frame_count / self.learning_frames) * 100 if self.is_learning else 100

    def reset_learning(self):
        self.is_learning = True
        self.learning_frame_count = 0
        self.motion_samples.clear()
        self.motion_history.clear()
        self.prev_frame_small = None