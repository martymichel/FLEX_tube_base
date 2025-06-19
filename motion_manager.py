"""Motion Manager fuer robuste Bewegungserkennung."""

import cv2
import numpy as np
import logging


class MotionManager:
    """Berechnet Bewegungslevel und trifft Entscheidungslogik."""

    def __init__(self, settings, update_callback=None):
        self.settings = settings
        self.update_callback = update_callback
        self.bg_subtractor = None
        self.motion_history = []
        self.motion_values = []
        self.smoothed_motion_pixels = 0
        self.current_motion_value = 0.0
        self.motion_stable_count = 0

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

    def update(self, frame):
        """Aktualisiert Motion-Wert und prueft auf stabile Bewegung.

        Args:
            frame: Aktueller Videoframe.

        Returns:
            bool: True, wenn stabile Bewegung erkannt wurde.
        """
        if self.bg_subtractor is None or frame is None:
            return False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        fg_mask = self.bg_subtractor.apply(gray)

        # Rauschen unterdruecken
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

        # Wert skalieren, um kurze Spitzen abzuflachen
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