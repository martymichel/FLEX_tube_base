"""
KI-Erkennungsmodul - einfach und robust
Verwaltet das YOLO-Modell und die Objekterkennung mit erweiterten Statistiken und Farbunterstuetzung
ERWEITERT: Verwendung von benutzerdefinierten Farben fuer Bounding Boxes
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
    logging.warning("ultralytics nicht verfuegbar - KI-Erkennung deaktiviert")

class DetectionEngine:
    """Einfache KI-Erkennungsengine mit erweiterten Statistiken und benutzerdefinierten Farben."""
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.class_names = {}
        self.confidence_threshold = 0.5
        
        # Standard-Farben (falls keine benutzerdefinierten Farben gesetzt sind)
        self.default_colors = [
            (0, 255, 0),    # Gruen
            (255, 0, 0),    # Rot  
            (0, 0, 255),    # Blau
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Gelb
            (128, 0, 128),  # Lila
            (255, 165, 0),  # Orange
        ]
        
        # Benutzerdefinierte Farben (werden aus Settings geladen)
        self.custom_colors = {}
    
    def load_model(self, model_path):
        """YOLO-Modell laden.
        
        Args:
            model_path (str): Pfad zur .pt Modelldatei
            
        Returns:
            bool: True wenn erfolgreich geladen
        """
        try:
            if not YOLO_AVAILABLE:
                logging.error("ultralytics nicht verfuegbar")
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
                # Fallback fuer aeltere Versionen
                self.class_names = {i: f"class_{i}" for i in range(80)}
            
            self.model_loaded = True
            logging.info(f"KI-Modell geladen: {model_path}")
            logging.info(f"Klassen im KI-Modell: {list(self.class_names.values())}")
            
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Laden des Modells: {e}")
            return False
    
    def set_class_colors(self, class_colors_dict):
        """Setze benutzerdefinierte Farben fuer Objekt-Klassen.
        
        Args:
            class_colors_dict (dict): Dictionary mit {class_id: color_hex_string}
        """
        self.custom_colors = {}
        for class_id, color_hex in class_colors_dict.items():
            try:
                # Konvertiere Hex-String zu BGR-Tupel (OpenCV Format)
                if color_hex.startswith('#'):
                    color_hex = color_hex[1:]
                
                # Hex zu RGB
                r = int(color_hex[0:2], 16)
                g = int(color_hex[2:4], 16)
                b = int(color_hex[4:6], 16)
                
                # RGB zu BGR (OpenCV)
                bgr_color = (b, g, r)
                self.custom_colors[int(class_id)] = bgr_color
                
            except Exception as e:
                logging.warning(f"Ungueltige Farbe fuer Klasse {class_id}: {color_hex} - {e}")
        
        logging.info(f"Benutzerdefinierte Farben fuer {len(self.custom_colors)} Klassen gesetzt")
    
    def set_class_colors_quietly(self, class_colors_dict):
        """Setze benutzerdefinierte Farben fuer Klassen OHNE Logging (fuer regelmaessige Updates).
        
        Args:
            class_colors_dict (dict): Dictionary mit {class_id: color_hex_string}
        """
        self.custom_colors = {}
        for class_id, color_hex in class_colors_dict.items():
            try:
                # Konvertiere Hex-String zu BGR-Tupel (OpenCV Format)
                if color_hex.startswith('#'):
                    color_hex = color_hex[1:]
                
                # Hex zu RGB
                r = int(color_hex[0:2], 16)
                g = int(color_hex[2:4], 16)
                b = int(color_hex[4:6], 16)
                
                # RGB zu BGR (OpenCV)
                bgr_color = (b, g, r)
                self.custom_colors[int(class_id)] = bgr_color
                
            except Exception:
                # Fehler still ignorieren bei quiet update
                pass
    
    def get_color_for_class(self, class_id):
        """Hole Farbe fuer eine bestimmte Klasse.
        
        Args:
            class_id (int): Klassen-ID
            
        Returns:
            tuple: BGR-Farbtupel fuer OpenCV
        """
        # Pruefe ob benutzerdefinierte Farbe vorhanden
        if class_id in self.custom_colors:
            return self.custom_colors[class_id]
        
        # Fallback auf Standard-Farben
        return self.default_colors[class_id % len(self.default_colors)]
    
    def detect(self, frame):
        """Objekterkennung durchfuehren.
        
        Args:
            frame: OpenCV-Frame (numpy array)
            
        Returns:
            list: Liste der Erkennungen [(x1, y1, x2, y2, confidence, class_id), ...]
        """
        if not self.model_loaded or frame is None:
            return []
        
        try:
            # Erkennung durchfuehren
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
        """Erkennungen auf Frame zeichnen mit benutzerdefinierten Farben.
        
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
            
            # Benutzerdefinierte oder Standard-Farbe waehlen
            color = self.get_color_for_class(class_id)
            
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
        """Klassennamen zurueckgeben.
        
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
    
    def get_detection_summary(self, detections):
        """Zusammenfassung der Erkennungen erstellen (wie komplexe App).
        
        Args:
            detections: Liste der Erkennungen
            
        Returns:
            dict: Zusammenfassung mit Klassenanzahl und Statistiken
        """
        summary = {}
        for detection in detections:
            _, _, _, _, confidence, class_id = detection
            class_name = self.class_names.get(class_id, f"Class {class_id}")
            
            if class_name not in summary:
                summary[class_name] = {
                    'count': 0,
                    'max_confidence': 0.0,
                    'avg_confidence': 0.0,
                    'confidences': [],
                    'class_id': class_id
                }
            
            summary[class_name]['count'] += 1
            summary[class_name]['confidences'].append(confidence)
            summary[class_name]['max_confidence'] = max(
                summary[class_name]['max_confidence'], confidence
            )
        
        # Durchschnittliche Konfidenz berechnen
        for class_name in summary:
            confidences = summary[class_name]['confidences']
            summary[class_name]['avg_confidence'] = sum(confidences) / len(confidences)
        
        return summary
    
    def analyze_detection_quality(self, detections):
        """Qualitaetsanalyse der Erkennungen (erweiterte Funktion).
        
        Args:
            detections: Liste der Erkennungen
            
        Returns:
            dict: Qualitaetsmetriken
        """
        if not detections:
            return {
                'total_detections': 0,
                'avg_confidence': 0.0,
                'high_confidence_count': 0,
                'quality_score': 0.0
            }
        
        confidences = [detection[4] for detection in detections]
        total_detections = len(detections)
        avg_confidence = sum(confidences) / total_detections
        high_confidence_count = len([c for c in confidences if c > 0.8])
        
        # Qualitaets-Score basierend auf Konfidenz und Anzahl
        quality_score = (avg_confidence * 0.7) + (high_confidence_count / total_detections * 0.3)
        
        return {
            'total_detections': total_detections,
            'avg_confidence': avg_confidence,
            'high_confidence_count': high_confidence_count,
            'quality_score': quality_score
        }