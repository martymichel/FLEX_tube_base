"""
UI-Stylesheets - Zentrale Style-Definitionen
Alle QSS-Styles für eine übersichtlichere main_ui.py
"""

class UIStyles:
    """Zentrale Style-Definitionen für die UI-Komponenten."""
    
    # =============================================================================
    # SIDEBAR STYLES
    # =============================================================================
    
    @staticmethod
    def get_sidebar_base_style():
        """Basis-Style für die Sidebar."""
        return """
            QFrame {
                background-color: #2c3e50;
                color: white;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-height: 25px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
            QLabel {
                color: white;
                font-size: 12px;
                background-color: transparent;
            }
        """
    
    @staticmethod
    def get_sidebar_flash_style():
        """Rotes Blink-Style für die Sidebar - GLEICHE MARGINS/PADDINGS."""
        return """
            QFrame {
                background-color: #e74c3c !important;
                color: white;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #c0392b !important;
                color: white !important;
                border: 2px solid #a93226 !important;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-height: 25px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #a93226 !important;
            }
            QPushButton:pressed {
                background-color: #922b21 !important;
            }
            QLabel {
                color: white;
                font-size: 12px;
                background-color: transparent;
            }
        """
    
    # =============================================================================
    # LOGIN STATUS BUTTON STYLES
    # =============================================================================
    
    @staticmethod
    def get_login_button_operator_style():
        """Style für Login-Button im Operator-Modus."""
        return """
            QPushButton {
                background-color: #34495e;
                color: white;
                border: 2px solid #5d6d7e;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #3498db;
                border-color: #2e86de;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """
    
    @staticmethod
    def get_login_button_admin_style():
        """Style für Login-Button im Admin-Modus."""
        return """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: 2px solid #229954;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
                border-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """
    
    # =============================================================================
    # MODEL & CAMERA BUTTON STYLES
    # =============================================================================
    
    @staticmethod
    def get_model_button_inactive_style():
        """Style für Model-Button wenn inaktiv."""
        return """
            QPushButton {
                background-color: #34495e;
                color: #bdc3c7;
                border: 2px solid #5d6d7e;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #3498db;
                border-color: #2e86de;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
                border-color: #95a5a6;
            }
        """
    
    @staticmethod
    def get_model_button_active_style():
        """Style für Model-Button wenn aktiv."""
        return """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: 2px solid #2980b9;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #5dade2;
                border-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
                border-color: #95a5a6;
            }
        """
    
    @staticmethod
    def get_camera_button_inactive_style():
        """Style für Camera-Button wenn inaktiv."""
        return """
            QPushButton {
                background-color: #34495e;
                color: #bdc3c7;
                border: 2px solid #5d6d7e;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #3498db;
                border-color: #2e86de;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
                border-color: #95a5a6;
            }
        """
    
    @staticmethod
    def get_camera_button_active_style():
        """Style für Camera-Button wenn aktiv."""
        return """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: 2px solid #2980b9;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #5dade2;
                border-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
                border-color: #95a5a6;
            }
        """
    
    # =============================================================================
    # ACTION BUTTON STYLES
    # =============================================================================
    
    @staticmethod
    def get_start_button_style():
        """Style für Start-Button."""
        return """
            QPushButton {
                background-color: #27ae60;
                font-size: 14px;
                font-weight: bold;
                min-height: 35px;
                padding: 8px 20px;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """
    
    @staticmethod
    def get_stop_button_style():
        """Style für Stop-Button."""
        return """
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                        stop: 0 #3498db, stop: 1 #2980b9);
                font-size: 18px;
                font-weight: bold;
                min-height: 45px;
                padding: 15px 25px;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                        stop: 0 #5dade2, stop: 1 #3498db);
            }
        """
    
    @staticmethod
    def get_snapshot_button_style():
        """Style für Snapshot-Button."""
        return """
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """
    
    # =============================================================================
    # MAIN AREA STYLES
    # =============================================================================
    
    @staticmethod
    def get_main_area_base_style():
        """Basis-Style für Main Area."""
        return """
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
            }
        """
    
    @staticmethod
    def get_main_area_flash_style():
        """Rotes Blink-Style für Main Area - GLEICHE MARGINS/PADDINGS."""
        return """
            QFrame {
                background-color: #e74c3c;
                border-radius: 8px;
            }
        """
    
    @staticmethod
    def get_video_label_base_style():
        """Basis-Style für Video-Label."""
        return """
            QLabel {
                background-color: #34495e;
                color: white;
                border-radius: 8px;
                font-size: 18px;
            }
        """
    
    @staticmethod
    def get_video_label_flash_style():
        """Rotes Blink-Style für Video-Label - GLEICHE MARGINS/PADDINGS."""
        return """
            QLabel {
                background-color: #e74c3c;
                color: white;
                border-radius: 8px;
                font-size: 18px;
            }
        """
    
    # =============================================================================
    # HEADER BUTTON STYLES
    # =============================================================================
    
    @staticmethod
    def get_sidebar_toggle_button_style():
        """Style für Sidebar Toggle Button."""
        return """
            QToolButton {
                background-color: #3498db;
                color: white;
                border: none;
                font-size: 20px;
                padding: 8px;
                border-radius: 4px;
                min-width: 60px;
                min-height: 60px;
            }
            QToolButton:hover {
                background-color: #2980b9;
            }
        """
    
    @staticmethod
    def get_settings_button_style():
        """Style für Settings Button."""
        return """
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                font-size: 20px;
                padding: 8px;
                border-radius: 4px;
                min-width: 60px;
                min-height: 60px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
            QPushButton:pressed {
                background-color: #6c3483;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
        """
    
    @staticmethod
    def get_quit_button_style():
        """Style für Quit Button."""
        return """
            QPushButton {
                background-color: #152b4a;
                color: white;
                font-size: 12px;
                font-weight: bold;
                min-height: 30px;
                border: 2px solid #0d1b2e;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0d1b2e;
                border: 2px solid #0d1b2e;
            }
            QPushButton:pressed {
                background-color: #0d1b2e;
            }
        """
    
    # =============================================================================
    # STATUS & COUNTER STYLES
    # =============================================================================
    
    @staticmethod
    def get_counter_frame_style():
        """Style für Counter Frame."""
        return """
            QFrame {
                background-color: #34495e;
                border-radius: 8px;
                padding: 4px 8px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                background: transparent;
            }
        """
    
    @staticmethod
    def get_reset_counter_button_style():
        """Style für Reset Counter Button."""
        return """
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
            QPushButton:disabled {
                background-color: #5d6d7e;
                color: #bdc3c7;
            }
        """
    
    @staticmethod
    def get_status_label_style(color):
        """Style für Status Label mit variabler Farbe."""
        return f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 15px;
                border-radius: 8px;
            }}
        """
    
    # =============================================================================
    # STATUS INDICATOR STYLES  
    # =============================================================================
    
    @staticmethod
    def get_workflow_status_style(color):
        """Style für Workflow Status mit variabler Farbe."""
        return f"""
            background-color: {color};
            color: white;
            padding: 8px 15px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
        """
    
    @staticmethod
    def get_motion_brightness_style(color):
        """Style für Motion/Brightness Anzeige."""
        return f"""
            background-color: {color};
            color: white;
            padding: 8px 15px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            min-width: 50px;
            max-width: 50px;
        """

    @staticmethod
    def get_motion_status_style(color):
        """Style für Motion-Kalibrierungsstatus."""
        return f"""
            background-color: {color};
            color: white;
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 10px;
        """
        
    @staticmethod
    def get_brightness_warning_style():
        """Style für Brightness Warning."""
        return """
            background-color: #e74c3c;
            color: white;
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 10px;
        """
    
    # =============================================================================
    # MODBUS STATUS STYLES
    # =============================================================================
    
    @staticmethod
    def get_modbus_status_connected_style():
        """Style für verbundenen Modbus Status."""
        return """
            background-color: #27ae60;
            color: white;
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 10px;
        """
    
    @staticmethod
    def get_modbus_status_disconnected_style():
        """Style für getrennten Modbus Status."""
        return """
            background-color: #e74c3c;
            color: white;
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 10px;
        """
    
    @staticmethod
    def get_modbus_ip_style():
        """Style für Modbus IP Anzeige."""
        return """
            background-color: #34495e;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 10px;
        """
    
    @staticmethod
    def get_coil_indicator_active_style():
        """Style für aktiven Coil Indikator."""
        return """
            background-color: #27ae60;
            color: white;
            border-radius: 9px;
            font-weight: bold;
            font-size: 8px;
        """
    
    @staticmethod
    def get_coil_indicator_reject_active_style():
        """Style für aktiven Reject Coil Indikator."""
        return """
            background-color: #e74c3c;
            color: white;
            border-radius: 9px;
            font-weight: bold;
            font-size: 8px;
        """
    
    @staticmethod
    def get_coil_indicator_inactive_style():
        """Style für inaktiven Coil Indikator."""
        return """
            background-color: #7f8c8d;
            color: white;
            border-radius: 9px;
            font-weight: bold;
            font-size: 8px;
        """
    
    # =============================================================================
    # TABLE STYLES
    # =============================================================================
    
    @staticmethod
    def get_stats_table_style():
        """Style für Statistics Table."""
        return """
            QTableWidget {
                background: rgba(255, 255, 255, 0.05);
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                font-size: 9px;
                gridline-color: rgba(255, 255, 255, 0.1);
            }
            QHeaderView::section {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #4a5568, stop: 1 #2d3748);
                color: white;
                border: none;
                padding: 3px;
                font-size: 9px;
                font-weight: 600;
                text-transform: uppercase;
            }
            QTableWidget::item {
                padding: 2px 3px;
                border: none;
            }
            QTableWidget::item:selected {
                background: rgba(255, 255, 255, 0.1);
            }
        """
    
    # =============================================================================
    # FOOTER STYLES
    # =============================================================================
    
    @staticmethod
    def get_footer_button_style():
        """Style für Footer Button."""
        return """
            QPushButton {
                background-color: transparent;
                color: #7f8c8d;
                border: none;
                font-size: 10px;
                padding: 8px;
                text-align: center;
            }
            QPushButton:hover {
                color: #3498db;
            }
            QPushButton:pressed {
                color: #2980b9;
            }
        """
    
    @staticmethod
    def get_esc_hint_style():
        """Style für ESC Hint Label."""
        return """
            color: #7f8c8d;
            font-style: italic;
            font-size: 10px;
            padding: 8px;
            margin: 8px 0;
        """
    
    # =============================================================================
    # UTILITY STYLES
    # =============================================================================
    
    @staticmethod
    def get_compact_status_label_style():
        """Style für kompakte Status Labels."""
        return """
            color: white;
            background: transparent;
            font-size: 11px;
        """