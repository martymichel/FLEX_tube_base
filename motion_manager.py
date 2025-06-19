"""Motion Manager fuer robuste Bewegungserkennung."""

import cv2
import numpy as np
import logging
from simple_motion_detector import SimpleMotionDetector


class MotionManager:
    """Berechnet Bewegungslevel und trifft Entscheidungslogik."""

    def __init__(self, settings, update_callback=None, status_callback=None):
        self.settings = settings
        self.update_callback = update_callback
        self.status_callback = status_callback
        self.bg_subtractor = None
        self.motion_history = []
        self.motion_values = []
        self.smoothed_motion_pixels = 0
        self.current_motion_value = 0.0
        self.motion_stable_count = 0

        # Neuer lernender Motion-Detector
        learning_seconds = self.settings.get('motion_learning_seconds', 60.0)
        baseline = self.settings.get('motion_noise_baseline', 2.0)
        scaling = self.settings.get('motion_scaling_factor', 8.0)
        calibrated = self.settings.get('motion_calibrated', False)
        self.detector = SimpleMotionDetector(
            fps=30.0,
            learning_seconds=learning_seconds,
            noise_baseline=baseline,
            scaling_factor=scaling,
            start_learning=not calibrated,
        )
        self.use_new_method = calibrated and not self.detector.is_learning_phase()

        # Status-Callback initial aktualisieren
        if self.status_callback:
            if calibrated and not self.detector.is_learning_phase():
                self.status_callback("Kalibriert OK")
            elif self.detector.is_learning_phase():
                self.status_callback("Lernt...")
            else:
                self.status_callback("Unkalibriert")

    def initialize(self):
        """Initialisiert Background-Subtractor und setzt Zustaende zurueck."""
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=False,
            varThreshold=150,
            history=400,
        )
        self.motion_history = []
        self.motion_values = []
        self.smoothed_motion_pixels = 0
        self.current_motion_value = 0.0
        self.motion_stable_count = 0
        # Detector-Zustand zurücksetzen (ohne Lernphase neu zu starten)
        self.detector.prev_frame_small = None
        self.detector.motion_history.clear()

    def update(self, frame):
        """Aktualisiert Motion-Wert und prueft auf stabile Bewegung.

        Args:
            frame: Aktueller Videoframe.

        Returns:
            bool: True, wenn stabile Bewegung erkannt wurde.
        """
        if self.bg_subtractor is None or frame is None:
            return False

        # Immer auch den lernenden Detector fuettern
        new_value = self.detector.process_frame(frame)

        if not self.detector.is_learning_phase() and not self.use_new_method:
            self.use_new_method = True
            self.settings.set('motion_noise_baseline', float(self.detector.noise_baseline))
            self.settings.set('motion_scaling_factor', float(self.detector.scaling_factor))
            self.settings.set('motion_calibrated', True)
            self.settings.save()
            logging.info('Motion calibration completed')
            if self.status_callback:
                self.status_callback("Kalibriert OK")

        if self.detector.is_learning_phase() or not self.use_new_method:
            return self._update_default(frame)

        self.current_motion_value = new_value
        if self.update_callback:
            try:
                self.update_callback(self.current_motion_value)
            except Exception as exc:  # noqa: broad-except
                logging.error(f"Motion update callback failed: {exc}")

        motion_threshold = self.settings.get('motion_threshold', 110)
        has_motion = self.current_motion_value > motion_threshold

        self.motion_history.append(has_motion)
        if len(self.motion_history) > 5:
            self.motion_history.pop(0)

        stable_motion = sum(self.motion_history) >= 3

        if stable_motion:
            self.motion_stable_count += 1
        else:
            self.motion_stable_count = 0

        return self.motion_stable_count >= 3

    def start_calibration(self, duration=None):
        """Starte manuelle Motion-Kalibrierung."""
        if duration is None:
            duration = self.settings.get('motion_learning_seconds', 60.0)
        self.detector.learning_frames = int(self.detector.fps * duration)
        self.detector.reset_learning()
        self.use_new_method = False
        self.settings.set('motion_learning_seconds', duration)
        self.settings.set('motion_calibrated', False)
        if self.status_callback:
            self.status_callback("Lernt...")

    def _update_default(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        fg_mask = self.bg_subtractor.apply(gray)

        _, fg_mask = cv2.threshold(fg_mask, 150, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        motion_pixels = cv2.countNonZero(fg_mask)

        self.motion_values.append(motion_pixels)
        if len(self.motion_values) > 3:
            self.motion_values.pop(0)

        avg_motion = np.median(self.motion_values)
        self.smoothed_motion_pixels = avg_motion

        scaled = np.sqrt(avg_motion) * 1.5
        current_motion = min(255, scaled)
        self.current_motion_value = current_motion

        if self.update_callback:
            try:
                self.update_callback(self.current_motion_value)
            except Exception as exc:  # noqa: broad-except
                logging.error(f"Motion update callback failed: {exc}")

        motion_threshold = self.settings.get('motion_threshold', 110)
        has_motion = current_motion > motion_threshold

        self.motion_history.append(has_motion)
        if len(self.motion_history) > 5:
            self.motion_history.pop(0)

        stable_motion = sum(self.motion_history) >= 3

        if stable_motion:
            self.motion_stable_count += 1
        else:
            self.motion_stable_count = 0

        return self.motion_stable_count >= 3