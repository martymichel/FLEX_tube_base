"""
Kamera-Manager - einfach und zuverlässig
Verwaltet Kamera-/Video-Eingabe mit Zeitstempel-Support
"""

import cv2
import os
import time
import logging
from datetime import datetime
from pathlib import Path

try:
    import ids_peak.ids_peak as ids_peak
    IDS_AVAILABLE = True
except ImportError:
    IDS_AVAILABLE = False
    logging.warning("IDS Peak nicht verfügbar - nur Standard-Kameras")

class CameraManager:
    """Einfacher Kamera-Manager mit Zeitstempel-Support."""
    
    def __init__(self):
        self.camera = None
        self.camera_ready = False
        self.source_type = None  # 'webcam', 'ids', 'video'
        self.source_info = None
        self.current_frame = None
        self.start_time = None
        
        # IDS Kamera Setup
        self.ids_device = None
        self.ids_datastream = None
    
    def set_source(self, source):
        """Kamera/Video-Quelle setzen.
        
        Args:
            source: Quelle - kann sein:
                    - int (Webcam-Index)
                    - str (Video-Pfad)
                    - tuple ('ids', device_index)
                    
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            # Aktuelle Quelle stoppen
            self.stop()
            
            if isinstance(source, int):
                # Standard-Webcam
                self.source_type = 'webcam'
                self.source_info = source
                
            elif isinstance(source, str):
                # Video-Datei
                if os.path.exists(source):
                    self.source_type = 'video'
                    self.source_info = source
                else:
                    logging.error(f"Video-Datei nicht gefunden: {source}")
                    return False
                    
            elif isinstance(source, tuple) and source[0] == 'ids':
                # IDS Kamera
                if not IDS_AVAILABLE:
                    logging.error("IDS Peak nicht verfügbar")
                    return False
                self.source_type = 'ids'
                self.source_info = source[1]
                
            else:
                logging.error(f"Unbekannte Quelle: {source}")
                return False
            
            self.camera_ready = True
            logging.info(f"Quelle gesetzt: {self.source_type} - {self.source_info}")
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Setzen der Quelle: {e}")
            return False
    
    def start(self):
        """Kamera/Video starten.
        
        Returns:
            bool: True wenn erfolgreich gestartet
        """
        try:
            if not self.camera_ready:
                logging.error("Keine Quelle gesetzt")
                return False
            
            self.start_time = time.time()
            
            if self.source_type == 'webcam':
                return self._start_webcam()
            elif self.source_type == 'video':
                return self._start_video()
            elif self.source_type == 'ids':
                return self._start_ids_camera()
            
            return False
            
        except Exception as e:
            logging.error(f"Fehler beim Starten: {e}")
            return False
    
    def get_current_time(self):
        """Aktuelle Zeit seit Start.
        
        Returns:
            float: Sekunden seit Start
        """
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time
    
    def _start_webcam(self):
        """Standard-Webcam starten."""
        self.camera = cv2.VideoCapture(self.source_info)
        if not self.camera.isOpened():
            logging.error(f"Webcam {self.source_info} konnte nicht geöffnet werden")
            return False
        
        # Auflösung setzen
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        logging.info(f"Webcam {self.source_info} gestartet")
        return True
    
    def _start_video(self):
        """Video-Datei starten."""
        self.camera = cv2.VideoCapture(self.source_info)
        if not self.camera.isOpened():
            logging.error(f"Video {self.source_info} konnte nicht geöffnet werden")
            return False
        
        logging.info(f"Video {self.source_info} gestartet")
        return True
    
    def _start_ids_camera(self):
        """IDS Kamera starten."""
        if not IDS_AVAILABLE:
            return False
            
        try:
            # IDS Peak initialisieren
            ids_peak.Library.Initialize()
            
            # Device Manager
            device_manager = ids_peak.DeviceManager.Instance()
            device_manager.Update()
            
            # Verfügbare Geräte
            devices = device_manager.Devices()
            if self.source_info >= len(devices):
                logging.error(f"IDS Kamera {self.source_info} nicht gefunden")
                return False
            
            # Gerät öffnen
            device_descriptor = devices[self.source_info]
            self.ids_device = device_descriptor.OpenDevice(ids_peak.DeviceAccessType.Control)
            
            # Datastream einrichten
            datastreams = self.ids_device.DataStreams()
            if not datastreams:
                logging.error("Keine IDS Datastreams verfügbar")
                return False
                
            self.ids_datastream = datastreams[0].OpenDataStream()
            
            # Acquisition starten
            self.ids_device.RemoteDevice().NodeMaps()[0].FindNode("AcquisitionStart").Execute()
            
            logging.info(f"IDS Kamera {self.source_info} gestartet")
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Starten der IDS Kamera: {e}")
            return False
    
    def get_frame(self):
        """Aktuelles Frame holen.
        
        Returns:
            numpy.ndarray oder None: Frame als OpenCV-Array
        """
        try:
            if self.source_type in ['webcam', 'video']:
                return self._get_opencv_frame()
            elif self.source_type == 'ids':
                return self._get_ids_frame()
                
        except Exception as e:
            logging.error(f"Fehler beim Frame-Abruf: {e}")
            
        return None
    
    def _get_opencv_frame(self):
        """Frame von OpenCV-Kamera/Video holen."""
        if not self.camera or not self.camera.isOpened():
            return None
            
        ret, frame = self.camera.read()
        if ret:
            self.current_frame = frame
            return frame
            
        # Bei Video: Loop zurück zum Anfang
        if self.source_type == 'video':
            self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.camera.read()
            if ret:
                self.current_frame = frame
                return frame
                
        return None
    
    def _get_ids_frame(self):
        """Frame von IDS Kamera holen."""
        if not self.ids_datastream:
            return None
            
        try:
            # Warten auf neues Bild
            buffer = self.ids_datastream.WaitForFinishedBuffer(1000)  # 1s timeout
            
            # Bild konvertieren
            image = ids_peak.BufferTo_IplImage(buffer)
            
            # Buffer wieder freigeben
            self.ids_datastream.QueueBuffer(buffer)
            
            # OpenCV-Format konvertieren
            frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            self.current_frame = frame
            return frame
            
        except Exception as e:
            logging.error(f"Fehler beim IDS Frame-Abruf: {e}")
            return None
    
    def stop(self):
        """Kamera/Video stoppen."""
        try:
            if self.source_type in ['webcam', 'video'] and self.camera:
                self.camera.release()
                self.camera = None
                
            elif self.source_type == 'ids':
                if self.ids_device:
                    try:
                        self.ids_device.RemoteDevice().NodeMaps()[0].FindNode("AcquisitionStop").Execute()
                    except:
                        pass
                    self.ids_device = None
                    
                if self.ids_datastream:
                    self.ids_datastream = None
            
            self.start_time = None
            logging.info("Kamera gestoppt")
            
        except Exception as e:
            logging.error(f"Fehler beim Stoppen: {e}")
    
    def save_snapshot(self, frame):
        """Schnappschuss speichern.
        
        Args:
            frame: Frame zum Speichern
            
        Returns:
            str oder None: Dateiname wenn erfolgreich
        """
        try:
            if frame is None:
                return None
            
            # Verzeichnis erstellen
            snapshot_dir = Path("snapshots")
            snapshot_dir.mkdir(exist_ok=True)
            
            # Dateiname mit Zeitstempel
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = snapshot_dir / f"snapshot_{timestamp}.jpg"
            
            # Speichern
            success = cv2.imwrite(str(filename), frame)
            
            if success:
                logging.info(f"Schnappschuss gespeichert: {filename}")
                return str(filename)
            else:
                logging.error("Fehler beim Speichern des Schnappschusses")
                return None
                
        except Exception as e:
            logging.error(f"Fehler beim Speichern: {e}")
            return None
    
    def get_available_cameras(self):
        """Verfügbare Kameras finden.
        
        Returns:
            list: Liste verfügbarer Kameras [(type, index, name), ...]
        """
        cameras = []
        
        # Standard-Webcams suchen
        for i in range(5):  # Teste bis zu 5 Webcams
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append(('webcam', i, f"Webcam {i}"))
                cap.release()
        
        # IDS Kameras suchen
        if IDS_AVAILABLE:
            try:
                ids_peak.Library.Initialize()
                device_manager = ids_peak.DeviceManager.Instance()
                device_manager.Update()
                devices = device_manager.Devices()
                
                for i, device in enumerate(devices):
                    name = device.DisplayName()
                    cameras.append(('ids', i, f"IDS: {name}"))
                    
            except Exception as e:
                logging.error(f"Fehler beim Suchen der IDS Kameras: {e}")
        
        return cameras