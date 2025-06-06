"""Visualization tab component for the threshold settings dialog."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox,
    QSlider, QGroupBox, QCheckBox
)
import os
from PyQt6.QtCore import Qt

def create_visual_tab(settings, parent=None):
    """Create the visualization tab contents.
    
    Args:
        settings: Dictionary of current settings
        parent: Parent widget
        
    Returns:
        QWidget: The visualization tab widget with all its controls
    """
    visual_tab = QWidget(parent)
    visual_layout = QVBoxLayout(visual_tab)
    visual_layout.setSpacing(20)
    
    # Add visualization settings
    visual_group = QGroupBox("Visualisierung")
    visual_layout_group = QVBoxLayout()
    visual_layout_group.setSpacing(16)
    
    # Font size setting
    font_layout = QHBoxLayout()
    font_layout.addWidget(QLabel("Label Schriftgrösse (0.0-1.5):"))
    font_size_slider = QSlider(Qt.Orientation.Horizontal)
    font_size_slider.setRange(3, 15)  # 0.3 to 1.5 in tenths
    default_font = int(settings.get('font_size', 0.7) * 10) if settings else 7
    font_size_slider.setValue(default_font)
    font_size_label = QLabel(f"{font_size_slider.value()/10:.1f}")
    font_size_slider.valueChanged.connect(lambda v: font_size_label.setText(f"{v/10:.1f}"))
    font_layout.addWidget(font_size_slider)
    font_layout.addWidget(font_size_label)
    visual_layout_group.addLayout(font_layout)
    
    # Line thickness setting
    line_layout = QHBoxLayout()
    line_layout.addWidget(QLabel("Bounding Box Liniendicke (1-5):"))
    line_thickness_slider = QSlider(Qt.Orientation.Horizontal)
    line_thickness_slider.setRange(1, 5)
    line_thickness_slider.setValue(settings.get('line_thickness', 2) if settings else 2)
    line_thickness_label = QLabel(f"{line_thickness_slider.value()}")
    line_thickness_slider.valueChanged.connect(lambda v: line_thickness_label.setText(f"{v}"))
    line_layout.addWidget(line_thickness_slider)
    line_layout.addWidget(line_thickness_label)
    visual_layout_group.addLayout(line_layout)
    
    # Text thickness setting
    text_layout = QHBoxLayout()
    text_layout.addWidget(QLabel("Confidence Textdicke (1-3):"))
    text_thickness_slider = QSlider(Qt.Orientation.Horizontal)
    text_thickness_slider.setRange(1, 3)
    text_thickness_slider.setValue(settings.get('text_thickness', 1) if settings else 1)
    text_thickness_label = QLabel(f"{text_thickness_slider.value()}")
    text_thickness_slider.valueChanged.connect(lambda v: text_thickness_label.setText(f"{v}"))
    text_layout.addWidget(text_thickness_slider)
    text_layout.addWidget(text_thickness_label)
    visual_layout_group.addLayout(text_layout)
    
    # Show labels checkbox
    show_labels_layout = QHBoxLayout()
    show_labels_checkbox = QCheckBox("Klassennamen und Konfidenz anzeigen")
    show_labels_checkbox.setChecked(settings.get('show_labels', True) if settings else True)
    show_labels_layout.addWidget(show_labels_checkbox)
    visual_layout_group.addLayout(show_labels_layout)
    
    visual_group.setLayout(visual_layout_group)
    visual_layout.addWidget(visual_group)
    
    # Overlay duration settings
    duration_group = QGroupBox("Overlay & Rahmen Dauer")
    duration_layout = QVBoxLayout()
    
    # Overlay duration
    overlay_layout = QHBoxLayout()
    overlay_layout.addWidget(QLabel("Overlay Anzeigedauer (Sekunden):"))
    overlay_duration_slider = QSlider(Qt.Orientation.Horizontal)
    overlay_duration_slider.setRange(10, 200)  # 1.0 to 20.0 seconds in tenths
    overlay_value = int(settings.get('overlay_duration', 5.0) * 10) if settings else 50
    overlay_duration_slider.setValue(overlay_value)
    overlay_duration_label = QLabel(f"{overlay_duration_slider.value()/10:.1f}s")
    overlay_duration_slider.valueChanged.connect(lambda v: overlay_duration_label.setText(f"{v/10:.1f}s"))
    overlay_layout.addWidget(overlay_duration_slider)
    overlay_layout.addWidget(overlay_duration_label)
    duration_layout.addLayout(overlay_layout)
    
    # Frame duration
    frame_layout = QHBoxLayout()
    frame_layout.addWidget(QLabel("Rahmen Anzeigedauer (Sekunden):"))
    frame_duration_slider = QSlider(Qt.Orientation.Horizontal)
    frame_duration_slider.setRange(5, 100)  # 0.5 to 10.0 seconds in tenths
    frame_value = int(settings.get('frame_duration', 1.0) * 10) if settings else 10
    frame_duration_slider.setValue(frame_value)
    frame_duration_label = QLabel(f"{frame_duration_slider.value()/10:.1f}s")
    frame_duration_slider.valueChanged.connect(lambda v: frame_duration_label.setText(f"{v/10:.1f}s"))
    frame_layout.addWidget(frame_duration_slider)
    frame_layout.addWidget(frame_duration_label)
    duration_layout.addLayout(frame_layout)
    
    duration_group.setLayout(duration_layout)
    visual_layout.addWidget(duration_group)

    # Camera configuration group
    camera_group = QGroupBox("IDS Kamera-Konfiguration")
    camera_layout = QVBoxLayout()
    
    camera_info = QLabel(
        "Wählen Sie eine IDS Peak Kamera-Konfigurationsdatei (.toml), um erweiterte "
        "Kameraeinstellungen wie Belichtung, Gamma und Weißabgleich zu verwenden."
    )
    camera_info.setWordWrap(True)
    camera_layout.addWidget(camera_info)
    
    # Camera config path display and browse button
    camera_path_layout = QHBoxLayout()
    camera_path = QLabel(settings.get('camera_config_path', 'Keine Konfiguration ausgewählt'))
    camera_path.setWordWrap(True)
    camera_path.setStyleSheet("""
        background-color: #34495e;
        color: #ecf0f1;
        padding: 8px;
        border-radius: 4px;
    """)
    camera_path_layout.addWidget(camera_path, 1)  # 1 = stretch
    
    camera_browse_btn = QPushButton("📁 Durchsuchen")
    camera_browse_btn.setFixedWidth(120)
    camera_path_layout.addWidget(camera_browse_btn)
    
    camera_layout.addLayout(camera_path_layout)

    # Function to handle camera config selection
    def handle_camera_config_selection():
        path, _ = QFileDialog.getOpenFileName(
            parent,
            "Kamera-Konfigurationsdatei auswählen",
            "",
            "TOML-Dateien (*.toml);;Alle Dateien (*)"
        )
        if path:
            # Store in the settings object for later retrieval
            if isinstance(settings, dict):
                settings['camera_config_path'] = path
                camera_path.setText(path)
                QMessageBox.information(
                    parent,
                    "Konfiguration geladen",
                    f"Kamera-Konfigurationsdatei ausgewählt:\n{path}"
                )
    
    # Connect the browse button
    camera_browse_btn.clicked.connect(handle_camera_config_selection)
    
    camera_group.setLayout(camera_layout)
    visual_layout.addWidget(camera_group)

    # Add stretch to push content to top
    visual_layout.addStretch()

    # Store references to the controls
    visual_tab.font_size_slider = font_size_slider
    visual_tab.line_thickness_slider = line_thickness_slider
    visual_tab.text_thickness_slider = text_thickness_slider
    visual_tab.show_labels_checkbox = show_labels_checkbox
    visual_tab.overlay_duration_slider = overlay_duration_slider
    visual_tab.frame_duration_slider = frame_duration_slider
    visual_tab.camera_path = camera_path

    return visual_tab