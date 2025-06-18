"""
Kamera-Manager - einfach und zuverlaessig - UPGRADED
Verwaltet Kamera-/Video-Eingabe mit Zeitstempel-Support und verbesserter IDS Peak Integration
VERBESSERT: Robuste IDS-Implementierung mit mehreren Versuchen und besserem Error-Handling
"""

import cv2
import os
import time
import logging
from datetime import datetime
from pathlib import Path
import numpy as np

try:
    import ids_peak.ids_peak as ids_peak
    IDS_AVAILABLE = True
except ImportError:
    IDS_AVAILABLE = False
    logging.warning("IDS Peak nicht verfuegbar - nur Standard-Kameras")

# Erweiterte IDS-Imports für bessere Bildkonvertierung
try:
    import ids_peak.ids_peak_ipl_extension as ids_ipl_extension
    import ids_peak_ipl.ids_peak_ipl as ids_ipl
    IDS_IPL_AVAILABLE = True
except ImportError:
    IDS_IPL_AVAILABLE = False
    logging.info("IDS IPL Extension nicht verfuegbar - verwende Basis-Konvertierung")

class CameraManager:
    """Einfacher Kamera-Manager mit Zeitstempel-Support und verbesserter IDS Peak Integration."""
    
    def __init__(self, camera_config_manager=None):
        self.camera = None
        self.camera_ready = False
        self.source_type = None  # 'webcam', 'ids', 'video'
        self.source_info = None
        self.current_frame = None
        self.start_time = None
        
        # IDS Kamera Setup - VERBESSERT
        self.ids_device = None
        self.ids_datastream = None
        self.remote_device_nodemap = None
        self.payload_size = None
        
        # Kamera-Konfigurationsmanager
        self.camera_config_manager = camera_config_manager
        
        # Auflösungs-Cache
        self._cached_width = None
        self._cached_height = None
    
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
                    logging.error("IDS Peak nicht verfuegbar")
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
            logging.error(f"Webcam {self.source_info} konnte nicht geoeffnet werden")
            return False
        
        # Aufloesung setzen
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1936) # 1280x720 Standard
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1216) # 1280x720 Standard
        
        logging.info(f"Webcam {self.source_info} gestartet")
        return True
    
    def _start_video(self):
        """Video-Datei starten."""
        self.camera = cv2.VideoCapture(self.source_info)
        if not self.camera.isOpened():
            logging.error(f"Video {self.source_info} konnte nicht geoeffnet werden")
            return False
        
        logging.info(f"Video {self.source_info} gestartet")
        return True
    
    def _start_ids_camera(self):
        """IDS Kamera starten - VERBESSERT mit robusterer Konfiguration."""
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
            self.ids_device = device_descriptor.OpenDevice(ids_peak.DeviceAccessType_Control)
            
            # VERBESSERT: Robustere Nodemap-Behandlung
            nodemaps = self.ids_device.RemoteDevice().NodeMaps()
            if len(nodemaps) > 1:
                # Verwende spezifische Nodemap (wie in Referenz-Code)
                self.remote_device_nodemap = nodemaps[1]
            else:
                # Fallback auf erste Nodemap
                self.remote_device_nodemap = nodemaps[0]
            
            # VERBESSERT: Erweiterte Basis-Konfiguration
            self._configure_ids_camera_advanced()
            
            # Kamera-Konfiguration anwenden (falls verfügbar)
            if self.camera_config_manager and self.camera_config_manager.is_loaded:
                try:
                    config_applied = self.camera_config_manager.apply_to_camera_nodemap(self.remote_device_nodemap)
                    if config_applied:
                        logging.info("IDS Peak Konfiguration erfolgreich angewendet")
                    else:
                        logging.warning("IDS Peak Konfiguration konnte nicht angewendet werden")
                except Exception as config_error:
                    logging.error(f"Fehler beim Anwenden der IDS Peak Konfiguration: {config_error}")
            
            # Datastream einrichten
            datastreams = self.ids_device.DataStreams()
            if not datastreams:
                logging.error("Keine IDS Datastreams verfügbar")
                return False
                
            self.ids_datastream = datastreams[0].OpenDataStream()
            
            # VERBESSERT: Payload-Size und Buffer-Management
            self.payload_size = self.remote_device_nodemap.FindNode("PayloadSize").Value()
            
            # Buffer für Datastream vorbereiten
            for i in range(self.ids_datastream.NumBuffersAnnouncedMinRequired()):
                buffer = self.ids_datastream.AllocAndAnnounceBuffer(self.payload_size)
                self.ids_datastream.QueueBuffer(buffer)
            
            # Acquisition starten
            self.ids_datastream.StartAcquisition()
            self.remote_device_nodemap.FindNode("AcquisitionStart").Execute()
            self.remote_device_nodemap.FindNode("AcquisitionStart").WaitUntilDone()
            
            # Auflösung ermitteln und cachen
            self._cache_camera_resolution()
            
            logging.info(f"IDS Kamera {self.source_info} erfolgreich gestartet")
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Starten der IDS Kamera: {e}")
            return False

    def _configure_ids_camera_advanced(self):
        """Erweiterte IDS-Kamera-Basis-Konfiguration."""
        try:
            # Trigger-Modus konfigurieren (kontinuierlich)
            self.remote_device_nodemap.FindNode("TriggerSelector").SetCurrentEntry("ExposureStart")
            self.remote_device_nodemap.FindNode("TriggerSource").SetCurrentEntry("Software")
            self.remote_device_nodemap.FindNode("TriggerMode").SetCurrentEntry("Off")
            
            # Spiegelung standardmässig aus
            self.remote_device_nodemap.FindNode("ReverseX").SetValue(False)
            self.remote_device_nodemap.FindNode("ReverseY").SetValue(False)
            
            # Wenn keine Einstellungen vorhanden sind, abbruch. Meldung ausgeben:"Laden Sie eine Kamera-Konfiguration, um Einstellungen anzuwenden."
            if not self.camera_config_manager or not self.camera_config_manager.is_loaded:
                logging.info("Laden Sie eine Kamera-Konfiguration, um Einstellungen anzuwenden.")
                return
            
        except Exception as e:
            logging.error(f"Fehler bei IDS-Kamera Basis-Konfiguration: {e}")
    
    def _cache_camera_resolution(self):
        """Kamera-Auflösung ermitteln und cachen."""
        if self.source_type == 'ids' and self.remote_device_nodemap:
            try:
                width_node = self.remote_device_nodemap.FindNode("Width")
                height_node = self.remote_device_nodemap.FindNode("Height")
                if width_node and height_node:
                    self._cached_width = width_node.Value()
                    self._cached_height = height_node.Value()
                    logging.info(f"IDS Kamera-Auflösung gecacht: {self._cached_width}x{self._cached_height}")
            except Exception as e:
                logging.warning(f"Konnte IDS-Auflösung nicht ermitteln: {e}")
    
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
            
        # Bei Video: Loop zurueck zum Anfang
        if self.source_type == 'video':
            self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.camera.read()
            if ret:
                self.current_frame = frame
                return frame
                
        return None
    
    def _get_ids_frame(self):
        """Frame von IDS Kamera holen - VERBESSERT mit mehreren Versuchen."""
        if not self.ids_datastream:
            return None
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Warten auf neues Bild mit Timeout
                buffer = self.ids_datastream.WaitForFinishedBuffer(10)  # 1s timeout
                
                # VERBESSERT: IDS IPL Extension für bessere Konvertierung
                if IDS_IPL_AVAILABLE:
                    try:
                        # Konvertierung mit IDS IPL (robuster)
                        raw_image = ids_ipl_extension.BufferToImage(buffer)
                        color_image = raw_image.ConvertTo(ids_ipl.PixelFormatName_RGB8)
                        
                        # Buffer wieder freigeben
                        self.ids_datastream.QueueBuffer(buffer)
                        
                        # Zu OpenCV-Format konvertieren
                        frame = color_image.get_numpy_3D()
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        frame_norm = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                        
                        self.current_frame = frame_norm.copy()
                        return self.current_frame
                        
                    except Exception as ipl_error:
                        logging.warning(f"IPL Extension Konvertierung fehlgeschlagen: {ipl_error}, verwende Fallback")
                        # Fallback auf alte Methode
                        self.ids_datastream.QueueBuffer(buffer)
                        continue
                
                # Fallback auf alte Methode wenn IPL Extension nicht verfügbar oder fehlschlägt
                try:
                    image = ids_peak.BufferTo_IplImage(buffer)
                    self.ids_datastream.QueueBuffer(buffer)
                    frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    self.current_frame = frame
                    return frame
                except Exception as fallback_error:
                    logging.error(f"Auch Fallback-Konvertierung fehlgeschlagen: {fallback_error}")
                    self.ids_datastream.QueueBuffer(buffer)
                    continue
                
            except Exception as e:
                logging.warning(f"IDS Frame-Capture Versuch {attempt+1}/{max_attempts} fehlgeschlagen: {e}")
                if attempt == max_attempts - 1:
                    logging.error("Alle IDS Frame-Capture Versuche fehlgeschlagen")
                    return None
                
        return None
    
    def stop(self):
        """Kamera/Video stoppen - VERBESSERT für IDS."""
        try:
            if self.source_type in ['webcam', 'video'] and self.camera:
                self.camera.release()
                self.camera = None
                
            elif self.source_type == 'ids':
                # VERBESSERT: Robusteres IDS-Cleanup
                try:
                    # Datastream stoppen
                    if self.ids_datastream:
                        try:
                            self.ids_datastream.StopAcquisition(ids_peak.AcquisitionStopMode.Default)
                        except Exception as e:
                            logging.error(f"Fehler beim Stoppen der IDS Acquisition: {e}")
                        self.ids_datastream = None
                    
                    # Acquisition stoppen
                    if self.remote_device_nodemap:
                        try:
                            self.remote_device_nodemap.FindNode("AcquisitionStop").Execute()
                        except Exception as e:
                            logging.error(f"Fehler beim Ausführen von AcquisitionStop: {e}")
                        self.remote_device_nodemap = None
                    
                    # Kurze Verzögerung für sauberes Cleanup
                    time.sleep(0.1)
                    
                    # Device freigeben
                    if self.ids_device:
                        self.ids_device = None
                    
                    # IDS Library schließen
                    try:
                        ids_peak.Library.Close()
                    except Exception as e:
                        logging.error(f"Fehler beim Schließen der IDS Library: {e}")
                        
                except Exception as e:
                    logging.error(f"Fehler beim IDS-Cleanup: {e}")
            
            # Cache zurücksetzen
            self._cached_width = None
            self._cached_height = None
            self.payload_size = None
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
        """Verfuegbare Kameras finden.
        
        Returns:
            list: Liste verfuegbarer Kameras [(type, index, name), ...]
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
                
                # IDS Library wieder schließen nach Suche
                ids_peak.Library.Close()
                    
            except Exception as e:
                logging.error(f"Fehler beim Suchen der IDS Kameras: {e}")
        
        return cameras
    
    def get_camera_info(self):
        """Informationen über die aktuelle Kamera.
        
        Returns:
            dict: Kamera-Informationen
        """
        info = {
            'source_type': self.source_type,
            'source_info': self.source_info,
            'camera_ready': self.camera_ready,
            'resolution': None
        }
        
        if self.source_type == 'ids' and self._cached_width and self._cached_height:
            info['resolution'] = f"{self._cached_width}x{self._cached_height}"
        elif self.source_type in ['webcam', 'video'] and self.camera:
            try:
                width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                info['resolution'] = f"{width}x{height}"
            except:
                pass

        return info

    def get_camera_temperature(self):
        """Aktuelle Kameratemperatur ermitteln (nur IDS)."""
        if self.source_type != 'ids' or not self.remote_device_nodemap:
            return None

        for node_name in ["DeviceTemperature", "SensorTemperature"]:
            try:
                node = self.remote_device_nodemap.FindNode(node_name)
                if node and node.IsValid():
                    return node.Value()
            except Exception:
                continue

        return None