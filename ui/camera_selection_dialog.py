"""
Kamera-Auswahl Dialog
Ermöglicht die Auswahl zwischen Webcams, Videos und IDS-Kameras
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, 
    QListWidgetItem, QFileDialog, QMessageBox, QGroupBox, QRadioButton,
    QButtonGroup, QTextEdit, QTabWidget, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class CameraSelectionDialog(QDialog):
    """Dialog zur Auswahl der Kamera/Video-Quelle."""
    
    def __init__(self, camera_manager, parent=None):
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.selected_source = None
        
        self.setWindowTitle("Kamera/Video-Quelle auswählen")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.refresh_cameras()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        
        # Tab Widget für verschiedene Quellen
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Webcam Tab
        self.setup_webcam_tab()
        
        # Video Tab
        self.setup_video_tab()
        
        # IDS Kamera Tab
        self.setup_ids_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Aktualisieren")
        self.refresh_btn.clicked.connect(self.refresh_cameras)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def setup_webcam_tab(self):
        """Webcam-Tab einrichten."""
        webcam_widget = QWidget()
        layout = QVBoxLayout(webcam_widget)
        
        # Info-Label
        info_label = QLabel("Verfügbare Webcams:")
        info_label.setFont(QFont("", 10, QFont.Weight.Bold))
        layout.addWidget(info_label)
        
        # Webcam-Liste
        self.webcam_list = QListWidget()
        self.webcam_list.itemClicked.connect(self.on_webcam_selected)
        layout.addWidget(self.webcam_list)
        
        # Test-Button
        self.test_webcam_btn = QPushButton("📹 Webcam testen")
        self.test_webcam_btn.clicked.connect(self.test_webcam)
        self.test_webcam_btn.setEnabled(False)
        layout.addWidget(self.test_webcam_btn)
        
        self.tab_widget.addTab(webcam_widget, "Webcams")
    
    def setup_video_tab(self):
        """Video-Tab einrichten."""
        video_widget = QWidget()
        layout = QVBoxLayout(video_widget)
        
        # Info-Label
        info_label = QLabel("Video-Datei auswählen:")
        info_label.setFont(QFont("", 10, QFont.Weight.Bold))
        layout.addWidget(info_label)
        
        # Video-Auswahl
        video_selection_layout = QHBoxLayout()
        
        self.video_path_label = QLabel("Keine Datei ausgewählt")
        self.video_path_label.setStyleSheet("padding: 8px; border: 1px solid gray; border-radius: 4px;")
        video_selection_layout.addWidget(self.video_path_label)
        
        self.browse_video_btn = QPushButton("📁 Durchsuchen")
        self.browse_video_btn.clicked.connect(self.browse_video)
        video_selection_layout.addWidget(self.browse_video_btn)
        
        layout.addLayout(video_selection_layout)
        
        # Video-Info
        self.video_info = QTextEdit()
        self.video_info.setMaximumHeight(100)
        self.video_info.setReadOnly(True)
        self.video_info.setPlaceholderText("Video-Informationen werden hier angezeigt...")
        layout.addWidget(self.video_info)
        
        # Test-Button
        self.test_video_btn = QPushButton("▶ Video testen")
        self.test_video_btn.clicked.connect(self.test_video)
        self.test_video_btn.setEnabled(False)
        layout.addWidget(self.test_video_btn)
        
        layout.addStretch()
        
        self.tab_widget.addTab(video_widget, "Video-Dateien")
    
    def setup_ids_tab(self):
        """IDS-Kamera-Tab einrichten."""
        ids_widget = QWidget()
        layout = QVBoxLayout(ids_widget)
        
        # IDS Peak Verfügbarkeit prüfen
        try:
            import ids_peak.ids_peak as ids_peak
            ids_available = True
        except ImportError:
            ids_available = False
        
        if not ids_available:
            # IDS nicht verfügbar
            warning_label = QLabel("⚠️ IDS Peak nicht verfügbar")
            warning_label.setStyleSheet("color: orange; font-weight: bold; padding: 10px;")
            layout.addWidget(warning_label)
            
            info_text = QTextEdit()
            info_text.setReadOnly(True)
            info_text.setMaximumHeight(150)
            info_text.setText(
                "IDS Peak SDK ist nicht installiert oder nicht verfügbar.\n\n"
                "Für die Verwendung von IDS-Kameras ist die Installation "
                "des IDS Peak SDK erforderlich.\n\n"
                "Weitere Informationen: https://www.ids-imaging.com/downloads.html"
            )
            layout.addWidget(info_text)
        else:
            # Info-Label
            info_label = QLabel("Verfügbare IDS Peak Kameras:")
            info_label.setFont(QFont("", 10, QFont.Weight.Bold))
            layout.addWidget(info_label)
            
            # IDS-Kamera-Liste
            self.ids_list = QListWidget()
            self.ids_list.itemClicked.connect(self.on_ids_selected)
            layout.addWidget(self.ids_list)
            
            # Kamera-Info
            self.ids_info = QTextEdit()
            self.ids_info.setMaximumHeight(100)
            self.ids_info.setReadOnly(True)
            self.ids_info.setPlaceholderText("Kamera-Informationen werden hier angezeigt...")
            layout.addWidget(self.ids_info)
            
            # Test-Button
            self.test_ids_btn = QPushButton("📷 IDS-Kamera testen")
            self.test_ids_btn.clicked.connect(self.test_ids)
            self.test_ids_btn.setEnabled(False)
            layout.addWidget(self.test_ids_btn)
        
        layout.addStretch()
        
        self.tab_widget.addTab(ids_widget, "IDS Peak Kameras")
    
    def refresh_cameras(self):
        """Verfügbare Kameras aktualisieren."""
        try:
            # Webcams aktualisieren
            self.webcam_list.clear()
            
            # Standard-Webcams suchen
            for i in range(5):
                try:
                    import cv2
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        item = QListWidgetItem(f"Webcam {i}")
                        item.setData(Qt.ItemDataRole.UserRole, ('webcam', i))
                        self.webcam_list.addItem(item)
                        cap.release()
                except Exception:
                    continue
            
            if self.webcam_list.count() == 0:
                item = QListWidgetItem("Keine Webcams gefunden")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.webcam_list.addItem(item)
            
            # IDS-Kameras aktualisieren (falls verfügbar)
            self._refresh_ids_cameras()
            
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Aktualisieren der Kameras:\n{str(e)}")
    
    def _refresh_ids_cameras(self):
        """IDS-Kameras aktualisieren."""
        try:
            import ids_peak.ids_peak as ids_peak
            
            if hasattr(self, 'ids_list'):
                self.ids_list.clear()
                
                # IDS Peak initialisieren
                ids_peak.Library.Initialize()
                device_manager = ids_peak.DeviceManager.Instance()
                device_manager.Update()
                devices = device_manager.Devices()
                
                if devices:
                    for i, device in enumerate(devices):
                        name = device.DisplayName()
                        serial = device.SerialNumber()
                        item = QListWidgetItem(f"IDS {i}: {name} (SN: {serial})")
                        item.setData(Qt.ItemDataRole.UserRole, ('ids', i, name, serial))
                        self.ids_list.addItem(item)
                else:
                    item = QListWidgetItem("Keine IDS-Kameras gefunden")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.ids_list.addItem(item)
                
                # IDS Library wieder schließen
                ids_peak.Library.Close()
                
        except ImportError:
            pass  # IDS nicht verfügbar
        except Exception as e:
            if hasattr(self, 'ids_list'):
                self.ids_list.clear()
                item = QListWidgetItem(f"Fehler: {str(e)}")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.ids_list.addItem(item)
    
    def on_webcam_selected(self, item):
        """Webcam ausgewählt."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and data[0] == 'webcam':
            self.selected_source = data[1]  # Webcam-Index
            self.test_webcam_btn.setEnabled(True)
            self.ok_btn.setEnabled(True)
    
    def on_ids_selected(self, item):
        """IDS-Kamera ausgewählt."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and data[0] == 'ids':
            self.selected_source = ('ids', data[1])  # ('ids', index)
            self.test_ids_btn.setEnabled(True)
            self.ok_btn.setEnabled(True)
            
            # Kamera-Info anzeigen
            name, serial = data[2], data[3]
            self.ids_info.setText(f"Name: {name}\nSerial: {serial}\nIndex: {data[1]}")
    
    def browse_video(self):
        """Video-Datei durchsuchen."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Video-Datei auswählen",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;All Files (*)"
        )
        
        if file_path:
            self.selected_source = file_path
            self.video_path_label.setText(os.path.basename(file_path))
            self.video_path_label.setToolTip(file_path)
            self.test_video_btn.setEnabled(True)
            self.ok_btn.setEnabled(True)
            
            # Video-Info anzeigen
            self._show_video_info(file_path)
    
    def _show_video_info(self, file_path):
        """Video-Informationen anzeigen."""
        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                
                info_text = (
                    f"Datei: {os.path.basename(file_path)}\n"
                    f"Auflösung: {width} x {height}\n"
                    f"FPS: {fps:.2f}\n"
                    f"Frames: {frame_count}\n"
                    f"Dauer: {duration:.1f} Sekunden"
                )
                
                self.video_info.setText(info_text)
                cap.release()
            else:
                self.video_info.setText("Fehler beim Laden der Video-Informationen")
                
        except Exception as e:
            self.video_info.setText(f"Fehler: {str(e)}")
    
    def test_webcam(self):
        """Webcam testen."""
        try:
            import cv2
            cap = cv2.VideoCapture(self.selected_source)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    QMessageBox.information(self, "Test erfolgreich", 
                                          f"Webcam {self.selected_source} funktioniert!")
                else:
                    QMessageBox.warning(self, "Test fehlgeschlagen", 
                                      "Kann kein Bild von der Webcam abrufen")
                cap.release()
            else:
                QMessageBox.warning(self, "Test fehlgeschlagen", 
                                  "Kann Webcam nicht öffnen")
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Testen der Webcam:\n{str(e)}")
    
    def test_video(self):
        """Video testen."""
        try:
            import cv2
            cap = cv2.VideoCapture(self.selected_source)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    QMessageBox.information(self, "Test erfolgreich", 
                                          "Video kann gelesen werden!")
                else:
                    QMessageBox.warning(self, "Test fehlgeschlagen", 
                                      "Kann kein Frame aus dem Video lesen")
                cap.release()
            else:
                QMessageBox.warning(self, "Test fehlgeschlagen", 
                                  "Kann Video-Datei nicht öffnen")
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Testen des Videos:\n{str(e)}")
    
    def test_ids(self):
        """IDS-Kamera testen."""
        try:
            import ids_peak.ids_peak as ids_peak
            
            # Kurzer Test
            ids_peak.Library.Initialize()
            device_manager = ids_peak.DeviceManager.Instance()
            device_manager.Update()
            devices = device_manager.Devices()
            
            if self.selected_source[1] < len(devices):
                QMessageBox.information(self, "Test erfolgreich", 
                                      f"IDS-Kamera {self.selected_source[1]} ist verfügbar!")
            else:
                QMessageBox.warning(self, "Test fehlgeschlagen", 
                                  "IDS-Kamera nicht gefunden")
            
            ids_peak.Library.Close()
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Testen der IDS-Kamera:\n{str(e)}")
    
    def get_selected_source(self):
        """Ausgewählte Quelle zurückgeben."""
        return self.selected_source