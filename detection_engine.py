"""
KI-Erkennungsmodul - einfach und robust
Verwaltet das YOLO-Modell und die Objekterkennung
"""

import cv2
import torch
import numpy as np
import logging
from pathlib import Path

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("ultralytics nicht verfügbar - KI-Erkennung deaktiviert")

class DetectionEngine:
    """Einfache KI-Erkennungsengine."""
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.class_names = {}
        self.confidence_threshold = 0.5
        self.colors = [
            (0, 255, 0),    # Grün
            (255, 0, 0),    # Rot  
            (0, 0, 255),    # Blau
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Gelb
        ]
    
    def load_model(self, model_path):
        """YOLO-Modell laden.
        
        Args:
            model_path (str): Pfad zur .pt Modelldatei
            
        Returns:
            bool: True wenn erfolgreich geladen
        """
        try:
            if not YOLO_AVAILABLE:
                logging.error("ultralytics nicht verfügbar")
                return False
                
            if not Path(model_path).exists():
                logging.error(f"Modelldatei nicht gefunden: {model_path}")
                return False
            
            # Modell laden
            self.model = YOLO(model_path)
            
            # Klassen extrahieren
            if hasattr(self.model, 'names'):
                self.class_names = self.model.names
            else:
                # Fallback für ältere Versionen
                self.class_names = {i: f"class_{i}" for i in range(80)}
            
            self.model_loaded = True
            logging.info(f"Modell geladen: {model_path}")
            logging.info(f"Klassen: {list(self.class_names.values())}")
            
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Laden des Modells: {e}")
            return False
    
    def detect(self, frame):
        """Objekterkennung durchführen.
        
        Args:
            frame: OpenCV-Frame (numpy array)
            
        Returns:
            list: Liste der Erkennungen [(x1, y1, x2, y2, confidence, class_id), ...]
        """
        if not self.model_loaded or frame is None:
            return []
        
        try:
            # Erkennung durchführen
            results = self.model(frame, verbose=False)
            
            detections = []
            for result in results:
                if hasattr(result, 'boxes') and result.boxes is not None:
                    boxes = result.boxes
                    
                    # Boxen extrahieren
                    if len(boxes) > 0:
                        # Koordinaten
                        coords = boxes.xyxy.cpu().numpy()
                        # Konfidenz
                        confidences = boxes.conf.cpu().numpy()
                        # Klassen
                        classes = boxes.cls.cpu().numpy().astype(int)
                        
                        for i in range(len(coords)):
                            conf = confidences[i]
                            if conf >= self.confidence_threshold:
                                x1, y1, x2, y2 = coords[i]
                                class_id = classes[i]
                                
                                detections.append((
                                    int(x1), int(y1), int(x2), int(y2),
                                    float(conf), int(class_id)
                                ))
            
            return detections
            
        except Exception as e:
            logging.error(f"Fehler bei der Erkennung: {e}")
            return []
    
    def draw_detections(self, frame, detections):
        """Erkennungen auf Frame zeichnen.
        
        Args:
            frame: Original-Frame
            detections: Liste der Erkennungen
            
        Returns:
            numpy.ndarray: Frame mit Erkennungen
        """
        if not detections:
            return frame
        
        # Kopie erstellen
        annotated = frame.copy()
        
        for detection in detections:
            x1, y1, x2, y2, confidence, class_id = detection
            
            # Farbe wählen
            color = self.colors[class_id % len(self.colors)]
            
            # Bounding Box zeichnen
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Label erstellen
            class_name = self.class_names.get(class_id, f"Class {class_id}")
            label = f"{class_name}: {confidence:.2f}"
            
            # Label-Hintergrund
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(annotated, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
            
            # Label-Text
            cv2.putText(annotated, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return annotated
    
    def get_class_names(self):
        """Klassennamen zurückgeben.
        
        Returns:
            dict: {class_id: class_name}
        """
        return self.class_names.copy()
    
    def set_confidence_threshold(self, threshold):
        """Konfidenz-Schwellwert setzen.
        
        Args:
            threshold (float): Schwellwert zwischen 0.0 und 1.0
        """
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        logging.info(f"Konfidenz-Schwellwert auf {self.confidence_threshold} gesetzt")