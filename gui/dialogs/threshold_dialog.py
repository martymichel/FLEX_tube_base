"""
Threshold Settings Dialog with improved touch support and component integration.

This dialog provides an optimized user interface for touch devices with
larger controls and simplified layout. It properly integrates modular components
from threshold_components/ for better maintainability.
"""

import logging
import traceback
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, 
    QTabWidget, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QCoreApplication

# Import modular tab components
from gui.dialogs.threshold_components import (
    create_motion_tab,
    create_visual_tab,
    create_logs_tab,
    create_session_tab, 
    create_class_tab,
    create_brightness_tab,
    THRESHOLD_DIALOG_STYLE,
    TABWIDGET_STYLE
)

# Import brightness handler
from gui.dialogs.threshold_components.brightness_handler import BrightnessHandler


class ThresholdSettingsDialog(QDialog):
    """Optimized settings dialog specifically for touch displays with modular components."""

    def __init__(self, class_names, settings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.setMinimumSize(1000, 800)  # Larger for touch interaction
        self.setModal(True)
        self.setObjectName("ThresholdSettingsDialog")  # Important for identification
        
        # Apply improved styling for touch interaction
        self.setStyleSheet(THRESHOLD_DIALOG_STYLE + TABWIDGET_STYLE)
        
        self.class_names = class_names or {}
        self.settings = settings or {}
        
        # Set up UI
        self._create_layout()
        self._populate_tabs()
        
        # Set up brightness handler
        self.brightness_handler = BrightnessHandler(self.brightness_tab)
        
        logging.info(f"ThresholdSettingsDialog initialized with {len(self.class_names)} classes")
    
    def _create_layout(self):
        """Create the main layout of the dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        layout.addWidget(self.tab_widget)
        
        # Button bar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        self.save_btn = QPushButton("💾 Speichern")
        self.save_btn.setStyleSheet("""
            QPushButton { 
                background: #27ae60; 
                min-height: 70px;
                min-width: 200px;
                font-size: 18px;
            } 
            QPushButton:hover { 
                background: #2ecc71; 
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("❌ Abbrechen")
        self.cancel_btn.setStyleSheet("""
            QPushButton { 
                background: #c0392b; 
                min-height: 70px;
                min-width: 200px;
                font-size: 18px;
            } 
            QPushButton:hover { 
                background: #e74c3c; 
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
    
    def _create_tab_scroll_container(self, tab_widget):
        """Create a scroll container for a tab widget."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(tab_widget)
        return scroll
    
    def _populate_tabs(self):
        """Fill the tabs with content using modular components."""
        # Motion tab
        self.motion_tab = create_motion_tab(self.settings, self)
        motion_scroll = self._create_tab_scroll_container(self.motion_tab)
        self.tab_widget.addTab(motion_scroll, "🎯 Bewegung")
        
        # Detection tab (Class settings)
        self.class_tab = create_class_tab(self.class_names, self.settings, self)
        self.tab_widget.addTab(self.class_tab, "🔍 Erkennung")
        
        # Files tab
        self.files_tab = create_logs_tab(self.settings, self)
        files_scroll = self._create_tab_scroll_container(self.files_tab)
        self.tab_widget.addTab(files_scroll, "📁 Dateien")
        
        # Visual tab
        self.visual_tab = create_visual_tab(self.settings, self)
        visual_scroll = self._create_tab_scroll_container(self.visual_tab)
        self.tab_widget.addTab(visual_scroll, "🖥️ Anzeige")
        
        # System tab
        self.session_tab = create_session_tab(self.settings, self)
        session_scroll = self._create_tab_scroll_container(self.session_tab)
        self.tab_widget.addTab(session_scroll, "⚙️ System")
        
        # Brightness tab
        self.brightness_tab = create_brightness_tab(self.settings, self)
        brightness_scroll = self._create_tab_scroll_container(self.brightness_tab)
        self.tab_widget.addTab(brightness_scroll, "💡 Beleuchtung")
    
    def get_settings(self):
        """Extract settings from all tabs.
        
        Returns:
            dict: Dictionary with all settings
        """
        try:
            settings = {}
            
            # Process events before extracting settings to ensure all UI updates are applied
            QCoreApplication.processEvents()
            
            # Motion tab settings
            self._extract_motion_tab_settings(settings)
            
            # Class tab settings
            self._extract_class_tab_settings(settings)
            
            # Files tab settings
            self._extract_files_tab_settings(settings)
            
            # Visual tab settings
            self._extract_visual_tab_settings(settings)
            
            # Session tab settings
            self._extract_session_tab_settings(settings)
            
            # Brightness tab settings
            self._extract_brightness_tab_settings(settings)
            
            # Log the extraction success
            logging.info(f"Successfully extracted {len(settings)} settings from dialog")
            return settings
            
        except Exception as e:
            error_msg = f"Error extracting settings: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            
            # Show error message
            QMessageBox.critical(
                self,
                "Fehler beim Lesen der Einstellungen",
                f"Die Einstellungen konnten nicht korrekt ausgelesen werden: {str(e)}\n\n"
                f"Die Einstellungen werden nicht gespeichert."
            )
            
            # Return None to indicate failure
            return None
    
    def _extract_motion_tab_settings(self, settings):
        """Extract settings from motion tab.
        
        Args:
            settings (dict): Settings dictionary to update
        """
        try:
            # Check if the tab exists and has the expected attributes
            if not hasattr(self, 'motion_tab') or not self.motion_tab:
                logging.warning("Motion tab not found or is None")
                return
                
            # Motion settings - safely access attributes
            if hasattr(self.motion_tab, 'motion_spin'):
                settings['motion_threshold'] = self.motion_tab.motion_spin.value()
                
            if hasattr(self.motion_tab, 'settling_spin'):
                settings['settling_time'] = self.motion_tab.settling_spin.value()
                
            if hasattr(self.motion_tab, 'capture_spin'):
                settings['capture_time'] = self.motion_tab.capture_spin.value()
                
            if hasattr(self.motion_tab, 'frame_duration_spin'):
                settings['frame_duration'] = self.motion_tab.frame_duration_spin.value()
                
            if hasattr(self.motion_tab, 'clearing_time_spin'):
                settings['clearing_time'] = self.motion_tab.clearing_time_spin.value()
            
            # IoU threshold
            if hasattr(self.motion_tab, 'iou_slider'):
                iou_value = self.motion_tab.iou_slider.value()
                settings['iou_threshold'] = float(iou_value) / 100.0
            
        except Exception as e:
            logging.error(f"Error extracting motion tab settings: {e}")
            raise ValueError(f"Fehler in Bewegungs-Einstellungen: {str(e)}")
    
    def _extract_class_tab_settings(self, settings):
        """Extract settings from class tab.
        
        Args:
            settings (dict): Settings dictionary to update
        """
        try:
            # Check if the tab exists
            if not hasattr(self, 'class_tab') or not self.class_tab:
                logging.warning("Class tab not found or is None")
                return
                
            # Frame thresholds
            if hasattr(self.class_tab, 'green_threshold'):
                settings['green_threshold'] = self.class_tab.green_threshold.value()
                
            if hasattr(self.class_tab, 'red_threshold'):
                settings['red_threshold'] = self.class_tab.red_threshold.value()
            
            # Class settings - ensure attributes exist
            if hasattr(self.class_tab, 'class_settings') and hasattr(self.class_tab, 'class_colors'):
                class_settings = self.class_tab.class_settings
                class_colors = self.class_tab.class_colors
                
                # Initialize containers
                class_thresholds = {}
                frame_assignments = {}
                colors = {}
                
                # Process each class
                for class_id, controls in class_settings.items():
                    # Confidence threshold - safely handle
                    if 'confidence' in controls and hasattr(controls['confidence'], 'value'):
                        confidence = controls['confidence'].value()
                        class_thresholds[str(class_id)] = float(confidence) / 100.0
                    
                    # Frame assignment - safely handle
                    if 'color' in controls and hasattr(controls['color'], 'currentText'):
                        frame_text = controls['color'].currentText()
                        if frame_text == "Grün":
                            frame_assignments[str(class_id)] = "Green Frame"
                        elif frame_text == "Rot":
                            frame_assignments[str(class_id)] = "Red Frame"
                    
                    # Class color - safely handle
                    if class_id in class_colors:
                        try:
                            color = class_colors[class_id]
                            if hasattr(color, 'name'):
                                colors[str(class_id)] = color.name().upper()
                        except Exception as color_error:
                            logging.warning(f"Could not get color name for class {class_id}: {color_error}")
                
                settings['class_thresholds'] = class_thresholds
                settings['frame_assignments'] = frame_assignments
                settings['class_colors'] = colors
            
        except Exception as e:
            logging.error(f"Error extracting class tab settings: {e}")
            raise ValueError(f"Fehler in Klassen-Einstellungen: {str(e)}")
    
    def _extract_files_tab_settings(self, settings):
        """Extract settings from files tab.
        
        Args:
            settings (dict): Settings dictionary to update
        """
        try:
            # Check if the tab exists
            if not hasattr(self, 'files_tab') or not self.files_tab:
                logging.warning("Files tab not found or is None")
                return
                
            # File saving settings
            if hasattr(self.files_tab, 'save_bad_images') and hasattr(self.files_tab.save_bad_images, 'isChecked'):
                settings['save_bad_images'] = self.files_tab.save_bad_images.isChecked()
                
            if hasattr(self.files_tab, 'save_good_images') and hasattr(self.files_tab.save_good_images, 'isChecked'):
                settings['save_good_images'] = self.files_tab.save_good_images.isChecked()
                
            if hasattr(self.files_tab, 'bad_images_dir_path') and hasattr(self.files_tab.bad_images_dir_path, 'text'):
                settings['bad_images_directory'] = self.files_tab.bad_images_dir_path.text()
            
            # Max files setting
            if hasattr(self.files_tab, 'max_files_spinbox') and hasattr(self.files_tab.max_files_spinbox, 'value'):
                settings['max_image_files'] = self.files_tab.max_files_spinbox.value()
            
            # Parquet directory
            if hasattr(self.files_tab, 'parquet_dir_path') and hasattr(self.files_tab.parquet_dir_path, 'text'):
                settings['parquet_directory'] = self.files_tab.parquet_dir_path.text()
            
        except Exception as e:
            logging.error(f"Error extracting files tab settings: {e}")
            raise ValueError(f"Fehler in Datei-Einstellungen: {str(e)}")
    
    def _extract_visual_tab_settings(self, settings):
        """Extract settings from visual tab.
        
        Args:
            settings (dict): Settings dictionary to update
        """
        try:
            # Check if the tab exists
            if not hasattr(self, 'visual_tab') or not self.visual_tab:
                logging.warning("Visual tab not found or is None")
                return
                
            # Visual settings - safely access attributes
            if hasattr(self.visual_tab, 'font_size_slider') and hasattr(self.visual_tab.font_size_slider, 'value'):
                font_value = self.visual_tab.font_size_slider.value()
                settings['font_size'] = float(font_value) / 10.0
                
            if hasattr(self.visual_tab, 'line_thickness_slider') and hasattr(self.visual_tab.line_thickness_slider, 'value'):
                settings['line_thickness'] = self.visual_tab.line_thickness_slider.value()
                
            if hasattr(self.visual_tab, 'text_thickness_slider') and hasattr(self.visual_tab.text_thickness_slider, 'value'):
                settings['text_thickness'] = self.visual_tab.text_thickness_slider.value()
                
            if hasattr(self.visual_tab, 'show_labels_checkbox') and hasattr(self.visual_tab.show_labels_checkbox, 'isChecked'):
                settings['show_labels'] = self.visual_tab.show_labels_checkbox.isChecked()
                
            if hasattr(self.visual_tab, 'overlay_duration_slider') and hasattr(self.visual_tab.overlay_duration_slider, 'value'):
                overlay_value = self.visual_tab.overlay_duration_slider.value()
                settings['overlay_duration'] = float(overlay_value) / 10.0
                
            if hasattr(self.visual_tab, 'frame_duration_slider') and hasattr(self.visual_tab.frame_duration_slider, 'value'):
                frame_value = self.visual_tab.frame_duration_slider.value()
                settings['frame_duration'] = float(frame_value) / 10.0
                
            # Camera config path - special case
            if hasattr(self.visual_tab, 'camera_path') and hasattr(self.visual_tab.camera_path, 'text'):
                camera_path_text = self.visual_tab.camera_path.text()
                if camera_path_text and camera_path_text != 'Keine Konfiguration ausgewählt':
                    settings['camera_config_path'] = camera_path_text
            
        except Exception as e:
            logging.error(f"Error extracting visual tab settings: {e}")
            raise ValueError(f"Fehler in Anzeige-Einstellungen: {str(e)}")
    
    def _extract_session_tab_settings(self, settings):
        """Extract settings from session tab.
        
        Args:
            settings (dict): Settings dictionary to update
        """
        try:
            # Check if the tab exists
            if not hasattr(self, 'session_tab') or not self.session_tab:
                logging.warning("Session tab not found or is None")
                return
                
            # Session settings - safely access attributes
            if hasattr(self.session_tab, 'timeout_spin') and hasattr(self.session_tab.timeout_spin, 'value'):
                settings['session_timeout_minutes'] = self.session_tab.timeout_spin.value()
                
            if hasattr(self.session_tab, 'model_dir_path') and hasattr(self.session_tab.model_dir_path, 'text'):
                settings['default_model_directory'] = self.session_tab.model_dir_path.text()
            
        except Exception as e:
            logging.error(f"Error extracting session tab settings: {e}")
            raise ValueError(f"Fehler in System-Einstellungen: {str(e)}")
    
    def _extract_brightness_tab_settings(self, settings):
        """Extract settings from brightness tab.
        
        Args:
            settings (dict): Settings dictionary to update
        """
        try:
            # Check if the tab exists
            if not hasattr(self, 'brightness_tab') or not self.brightness_tab:
                logging.warning("Brightness tab not found or is None")
                return
                
            # Brightness settings - safely access attributes
            if hasattr(self.brightness_tab, 'low_threshold') and hasattr(self.brightness_tab.low_threshold, 'value'):
                settings['brightness_low_threshold'] = self.brightness_tab.low_threshold.value()
                
            if hasattr(self.brightness_tab, 'high_threshold') and hasattr(self.brightness_tab.high_threshold, 'value'):
                settings['brightness_high_threshold'] = self.brightness_tab.high_threshold.value()
                
            if hasattr(self.brightness_tab, 'duration_spin') and hasattr(self.brightness_tab.duration_spin, 'value'):
                settings['brightness_duration_threshold'] = self.brightness_tab.duration_spin.value()
            
        except Exception as e:
            logging.error(f"Error extracting brightness tab settings: {e}")
            raise ValueError(f"Fehler in Helligkeits-Einstellungen: {str(e)}")
