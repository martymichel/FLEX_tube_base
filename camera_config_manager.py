"""
IDS Peak Kamera-Konfigurationsmanager
Laedt und wendet TOML-Konfigurationsdateien fuer IDS Peak Kameras an
"""

import logging
import os
import traceback

try:
    import tomli
    TOMLI_AVAILABLE = True
except ImportError:
    TOMLI_AVAILABLE = False
    logging.warning("tomli nicht verfuegbar - TOML-Konfigurationsdateien koennen nicht geladen werden")

class CameraConfigManager:
    """
    Handling of IDS Peak camera configuration using TOML files.
    
    This class parses TOML configuration files created by IDS Peak software
    and provides interfaces for applying these settings to the camera.
    """
    
    def __init__(self):
        """Initialize the camera configuration handler."""
        self.config_data = None
        self.config_path = None
        self.is_loaded = False
    
    def load_config(self, toml_path):
        """
        Load a TOML configuration file.
        
        Args:
            toml_path (str): Path to the TOML configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not TOMLI_AVAILABLE:
            logging.error("tomli nicht verfuegbar - kann TOML-Datei nicht laden")
            return False
            
        try:
            if not toml_path or not os.path.exists(toml_path):
                logging.error(f"Konfigurationsdatei nicht gefunden: {toml_path}")
                return False
                
            with open(toml_path, "rb") as f:
                self.config_data = tomli.load(f)
                
            self.config_path = toml_path
            self.is_loaded = True
            logging.info(f"IDS Peak Konfiguration geladen: {toml_path}")
            
            # Verify that this is an IDS Peak config file
            if self.config_data.get('type') != 'ImgProc':
                logging.warning(f"Die geladene TOML-Datei ist moeglicherweise keine gueltige IDS Peak Konfiguration: {toml_path}")
                
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Laden der Kamera-Konfiguration: {e}")
            logging.error(traceback.format_exc())
            self.config_data = None
            self.config_path = None
            self.is_loaded = False
            return False
    
    def apply_to_camera_nodemap(self, remote_device_nodemap):
        """
        Apply the settings directly to camera nodemap.
        
        This method applies settings directly using the camera's nodemap API.
        
        Args:
            remote_device_nodemap: IDS Peak camera nodemap
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_loaded or not self.config_data or not remote_device_nodemap:
            logging.debug("Keine Konfiguration geladen oder kein Nodemap verfuegbar")
            return False
            
        try:
            settings_applied = 0
            
            # Apply transformation settings (mirrors, rotation)
            if transformation := self.config_data.get('Transformation', [None])[0]:
                try:
                    if 'mirrorLeftRight' in transformation:
                        reverse_x_node = remote_device_nodemap.FindNode("ReverseX")
                        if reverse_x_node and reverse_x_node.IsWritable():
                            reverse_x_node.SetValue(transformation['mirrorLeftRight'])
                            settings_applied += 1
                            logging.debug(f"Mirror links/rechts: {transformation['mirrorLeftRight']}")
                            
                    if 'mirrorUpDown' in transformation:
                        reverse_y_node = remote_device_nodemap.FindNode("ReverseY")
                        if reverse_y_node and reverse_y_node.IsWritable():
                            reverse_y_node.SetValue(transformation['mirrorUpDown'])
                            settings_applied += 1
                            logging.debug(f"Mirror oben/unten: {transformation['mirrorUpDown']}")
                except Exception as e:
                    logging.warning(f"Fehler bei Transformation-Einstellungen: {e}")
            
            # Apply Gamma settings
            if gamma := self.config_data.get('Gamma', [None])[0]:
                try:
                    if 'enable' in gamma and 'factor' in gamma and gamma['enable']:
                        gamma_node = remote_device_nodemap.FindNode("Gamma")
                        if gamma_node and gamma_node.IsWritable():
                            gamma_node.SetValue(gamma['factor'])
                            settings_applied += 1
                            logging.info(f"Gamma auf {gamma['factor']} gesetzt")
                except Exception as e:
                    logging.warning(f"Fehler bei Gamma-Einstellungen: {e}")
            
            # Apply gain settings
            if gain := self.config_data.get('Gain', [None])[0]:
                try:
                    if 'master' in gain:
                        gain_node = remote_device_nodemap.FindNode("Gain")
                        if gain_node and gain_node.IsWritable():
                            gain_node.SetValue(float(gain['master']))
                            settings_applied += 1
                            logging.info(f"Gain auf {gain['master']} gesetzt")
                except Exception as e:
                    logging.warning(f"Fehler bei Gain-Einstellungen: {e}")
            
            # Apply sharpening if enabled
            if sharpness := self.config_data.get('Sharpness', [None])[0]:
                try:
                    if 'enable' in sharpness and sharpness['enable']:
                        sharpening_node = remote_device_nodemap.FindNode("SharpnessEnhancement")
                        if sharpening_node and sharpening_node.IsWritable():
                            # Default to a medium value if factor is not specified
                            sharpening_value = sharpening_node.Maximum() / 2
                            if 'factor' in sharpness:
                                # Use the provided factor if available
                                sharpening_value = min(sharpness['factor'], sharpening_node.Maximum())
                            sharpening_node.SetValue(sharpening_value)
                            settings_applied += 1
                            logging.info(f"Sharpening auf {sharpening_value} gesetzt")
                except Exception as e:
                    logging.warning(f"Fehler bei Sharpening-Einstellungen: {e}")
            
            if settings_applied > 0:
                logging.info(f"IDS Peak Konfiguration angewendet: {settings_applied} Einstellungen")
            else:
                logging.info("Keine anwendbaren Kameraeinstellungen in der Konfiguration gefunden")
            
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Anwenden der Kamera-Konfiguration: {e}")
            logging.error(traceback.format_exc())
            return False
    
    def get_config_info(self):
        """
        Get information about the loaded configuration.
        
        Returns:
            dict: Configuration information
        """
        if not self.is_loaded:
            return {"loaded": False, "path": None}
        
        info = {
            "loaded": True,
            "path": self.config_path,
            "type": self.config_data.get('type', 'Unknown') if self.config_data else 'Unknown',
            "settings_count": 0
        }
        
        if self.config_data:
            # Count available settings
            for section in ['Transformation', 'Gamma', 'Gain', 'Sharpness']:
                if self.config_data.get(section):
                    info["settings_count"] += 1
        
        return info
    
    def clear_config(self):
        """Clear the loaded configuration."""
        self.config_data = None
        self.config_path = None
        self.is_loaded = False
        logging.info("Kamera-Konfiguration geleert")