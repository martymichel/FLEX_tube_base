"""Class settings tab component for the threshold settings dialog."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QSlider, QComboBox, QPushButton, QGroupBox, QScrollArea,
    QSizePolicy, QColorDialog, QFrame, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

def create_class_tab(class_names, settings, parent=None):
    """Create the class settings tab contents.
    
    Args:
        class_names: Dictionary of class IDs to class names
        settings: Dictionary of current settings
        parent: Parent widget
        
    Returns:
        QWidget: The class tab widget with all its controls
    """
    class_tab = QScrollArea(parent)
    class_tab.setStyleSheet("background-color: #2c3e50;")
    
    class_content = QWidget()
    class_content.setStyleSheet("background-color: #2c3e50;")
    class_layout = QVBoxLayout(class_content)
    class_layout.setSpacing(16)
    
    # Frame thresholds - Add this at the top for important general settings
    threshold_group = QGroupBox("Rahmen Schwellwerte")
    threshold_layout = QGridLayout()
    threshold_layout.setVerticalSpacing(12)
    threshold_layout.setHorizontalSpacing(16)
    
    # Green threshold
    threshold_layout.addWidget(QLabel("Grüner Rahmen Min:"), 0, 0)
    green_threshold = QSpinBox()
    green_threshold.setRange(1, 20)
    green_threshold.setValue(settings.get('green_threshold', 4) if settings else 4)
    threshold_layout.addWidget(green_threshold, 0, 1)
    
    # Red threshold
    threshold_layout.addWidget(QLabel("Roter Rahmen Min:"), 1, 0)
    red_threshold = QSpinBox()
    red_threshold.setRange(1, 20)
    red_threshold.setValue(settings.get('red_threshold', 1) if settings else 1)
    threshold_layout.addWidget(red_threshold, 1, 1)
    
    threshold_group.setLayout(threshold_layout)
    class_layout.addWidget(threshold_group)
    
    # Setup class settings with color selection
    class_settings = {}
    class_colors = {}
    
    default_colors = [
        "#14ff39",  # neon green
        "#ff0000",  # red
        "#ee82ee",  # violet
        "#ffbf00",  # deep sky blue
        "#00ffff",  # yellow
        "#ff00ff",  # magenta
        "#ff8000",  # cyan
        "#8000ff",  # orange
        "#7fff00",  # chartreuse
        "#ff1493",  # deep pink
        "#00fa9a",  # medium spring green
        "#ffd700",  # gold
        "#1e90ff",  # dodger blue
        "#ff4500",  # orange red
        "#32cd32",  # lime green
        "#8a2be2"   # blue violet
    ]
    
    for class_id, class_name in class_names.items():
        group = QGroupBox(f"Klasse {class_id}: {class_name}")
        
        # Use HBoxLayout for more flexible sizing instead of grid
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)
        
        # Confidence section
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("Konfidenz:"))
        
        # Confidence slider - make it narrower but allow it to stretch
        conf_slider = QSlider(Qt.Orientation.Horizontal)
        conf_slider.setRange(1, 99)
        default_conf = int(settings.get('class_thresholds', {}).get(str(class_id), 0.7) * 100) if settings else 70
        conf_slider.setValue(default_conf)
        conf_slider.setMinimumWidth(80)  # Minimum width
        conf_layout.addWidget(conf_slider, 1)  # 1 = stretch factor
        
        conf_label = QLabel(f"{default_conf/100:.2f}")
        conf_label.setMinimumWidth(40)  # Ensure label has minimum width
        conf_slider.valueChanged.connect(lambda v, l=conf_label: l.setText(f"{v/100:.2f}"))
        conf_layout.addWidget(conf_label)
        
        row_layout.addLayout(conf_layout, 3)  # Give more space to confidence (stretch factor 3)
        
        # Frame assignment section
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel("Rahmen:"))
        
        color_combo = QComboBox()
        color_combo.addItems(["Keine", "Grün", "Rot"])
        default_color = settings.get('frame_assignments', {}).get(str(class_id), "Keine")
        if default_color == "Green Frame": default_color = "Grün"
        elif default_color == "Red Frame": default_color = "Rot"
        color_combo.setCurrentText(default_color)
        frame_layout.addWidget(color_combo)
        
        row_layout.addLayout(frame_layout, 2)  # Stretch factor 2
        
        # Box color section
        box_color_layout = QHBoxLayout()
        box_color_layout.addWidget(QLabel("Box-Farbe:"))
        
        # Use a container frame to ensure the circular button stays within bounds
        color_container = QFrame()
        color_container.setFixedSize(28, 28)
        color_container.setLayout(QHBoxLayout())
        color_container.layout().setContentsMargins(0, 0, 0, 0)
        
        # Color button as a perfect circle that fits within its container
        color_btn = QPushButton()
        color_btn.setFixedSize(24, 24)
        saved_color = settings.get('class_colors', {}).get(str(class_id))
        current_color = QColor(saved_color if saved_color else default_colors[int(class_id) % len(default_colors)])
        class_colors[class_id] = current_color
        
        # Make button a perfect circle
        color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_color.name()};
                border: 1px solid #34495e;
                border-radius: 12px;
            }}
        """)
        
        color_container.layout().addWidget(color_btn)
        box_color_layout.addWidget(color_container)
        
        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(60)
        box_color_layout.addWidget(reset_btn)
        
        row_layout.addLayout(box_color_layout, 2)  # Stretch factor 2
        
        # Set up connections for color picker and reset
        def make_pick_color(button, color_id):
            def pick_color():
                color = QColorDialog.getColor(class_colors[color_id], parent)
                if color.isValid():
                    class_colors[color_id] = color
                    button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {color.name()};
                            border: 1px solid #34495e;
                            border-radius: 12px;
                        }}
                    """)
            return pick_color
        
        def make_reset_color(button, color_id, default_color):
            def reset_color():
                color = QColor(default_colors[int(color_id) % len(default_colors)])
                class_colors[color_id] = color
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color.name()};
                        border: 1px solid #34495e;
                        border-radius: 12px;
                    }}
                """)
            return reset_color
        
        color_btn.clicked.connect(make_pick_color(color_btn, class_id))
        reset_btn.clicked.connect(make_reset_color(
            color_btn, class_id, default_colors[int(class_id) % len(default_colors)]
        ))
        
        # Set layout for the group
        group.setLayout(row_layout)
        class_layout.addWidget(group)
        
        # Save references to settings controls
        class_settings[class_id] = {
            'confidence': conf_slider,
            'color': color_combo
        }
    
    class_content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    class_tab.setWidget(class_content)
    class_tab.setWidgetResizable(True)
    
    # Store references to controls and data
    class_tab.green_threshold = green_threshold
    class_tab.red_threshold = red_threshold
    class_tab.class_settings = class_settings
    class_tab.class_colors = class_colors
    
    return class_tab