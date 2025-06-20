"""
IDS Peak Kamera-Konfigurationsmanager
Laedt und wendet .cset-Konfigurationsdateien (GenICam XML) fuer IDS Peak Kameras an
20.06.25: Unterstützung für .cset Dateien anstelle von .toml
"""

import logging
import os
import traceback
import xml.etree.ElementTree as ET

class CameraConfigManager:
    """
    Handling of IDS Peak camera configuration using .cset files (GenICam XML format).
    
    This class parses .cset configuration files created by IDS Peak software
    and provides interfaces for applying these settings to the camera.
    """
    
    def __init__(self):
        """Initialize the camera configuration handler."""
        self.config_data = None
        self.config_path = None
        self.is_loaded = False
        self.genicam_parameters = {}
    
    def load_config(self, cset_path):
        """
        Load a .cset configuration file (GenICam XML format).
        
        Args:
            cset_path (str): Path to the .cset configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not cset_path or not os.path.exists(cset_path):
                logging.error(f"Konfigurationsdatei nicht gefunden: {cset_path}")
                return False
            
            if not cset_path.lower().endswith('.cset'):
                logging.error(f"Ungültiges Dateiformat. Erwartet .cset Datei: {cset_path}")
                return False
                
            # Parse XML-Datei
            tree = ET.parse(cset_path)
            root = tree.getroot()
            
            # GenICam Parameter extrahieren
            self.genicam_parameters = {}
            self._parse_genicam_xml(root)
            
            self.config_path = cset_path
            self.is_loaded = True
            
            logging.info(f"IDS Peak .cset Konfiguration geladen: {cset_path}")
            logging.info(f"Gefundene Parameter: {len(self.genicam_parameters)}")
            
            return True
            
        except ET.ParseError as e:
            logging.error(f"XML Parse-Fehler in .cset Datei: {e}")
            self.config_data = None
            self.config_path = None
            self.is_loaded = False
            return False
        except Exception as e:
            logging.error(f"Fehler beim Laden der Kamera-Konfiguration: {e}")
            logging.error(traceback.format_exc())
            self.config_data = None
            self.config_path = None
            self.is_loaded = False
            return False
    
    def _parse_genicam_xml(self, root):
        """
        Parse GenICam XML structure and extract parameter values.
        
        Args:
            root: XML root element
        """
        # Verschiedene XML-Strukturen unterstützen
        # Suche nach GenICam-typischen Elementen
        
        # Methode 1: Direkte Parameter-Nodes
        for param in root.findall(".//Parameter"):
            name = param.get('Name')
            value = param.get('Value')
            if name and value is not None:
                self.genicam_parameters[name] = value
                logging.debug(f"Parameter gefunden: {name} = {value}")
        
        # Methode 2: Node-basierte Struktur
        for node in root.findall(".//Node"):
            name = node.get('Name')
            value_elem = node.find('Value')
            if name and value_elem is not None:
                value = value_elem.text
                if value is not None:
                    self.genicam_parameters[name] = value
                    logging.debug(f"Node gefunden: {name} = {value}")
        
        # Methode 3: Feature-basierte Struktur
        for feature in root.findall(".//Feature"):
            name = feature.get('Name')
            value = feature.get('Value') or feature.text
            if name and value is not None:
                self.genicam_parameters[name] = value
                logging.debug(f"Feature gefunden: {name} = {value}")
        
        # Methode 4: Allgemeine Elementsuche für bekannte Parameter
        known_params = [
            'Width', 'Height', 'PixelFormat', 'ExposureTime', 'Gain',
            'AcquisitionFrameRate', 'TriggerMode', 'TriggerSource',
            'GainAuto', 'ExposureAuto', 'ReverseX', 'ReverseY', 'Gamma',
            'SharpnessEnhancement', 'BinningHorizontal', 'BinningVertical',
            'OffsetX', 'OffsetY', 'BlackLevel'
        ]
        
        for param_name in known_params:
            # Suche in verschiedenen möglichen XML-Strukturen
            elements = root.findall(f".//{param_name}")
            for elem in elements:
                value = elem.get('value') or elem.text
                if value is not None and param_name not in self.genicam_parameters:
                    self.genicam_parameters[param_name] = value
                    logging.debug(f"Bekannter Parameter gefunden: {param_name} = {value}")
                    break
    
    def apply_to_camera_nodemap(self, remote_device_nodemap):
        """
        Apply the GenICam parameters directly to camera nodemap.
        
        This method applies settings directly using the camera's nodemap API
        with comprehensive parameter support.
        
        Args:
            remote_device_nodemap: IDS Peak camera nodemap
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_loaded or not self.genicam_parameters or not remote_device_nodemap:
            logging.debug("Keine Konfiguration geladen oder kein Nodemap verfuegbar")
            return False
            
        try:
            settings_applied = 0
            settings_failed = 0
            
            # Parameter in empfohlener Reihenfolge anwenden (laut IDS Peak Anleitung)
            parameter_order = [
                # Bildformat zuerst
                'Width', 'Height', 'PixelFormat',
                'OffsetX', 'OffsetY',
                'BinningHorizontal', 'BinningVertical',
                
                # Belichtung und Verstärkung
                'ExposureTime', 'Gain',
                'ExposureAuto', 'GainAuto',
                
                # Frame Rate
                'AcquisitionFrameRate',
                
                # Trigger-Einstellungen
                'TriggerMode', 'TriggerSource',
                
                # Bildverbesserungen
                'Gamma', 'BlackLevel', 'SharpnessEnhancement',
                
                # Bildorientierung
                'ReverseX', 'ReverseY'
            ]
            
            # Geordnete Parameter zuerst anwenden
            for param_name in parameter_order:
                if param_name in self.genicam_parameters:
                    if self._apply_single_parameter(remote_device_nodemap, param_name, 
                                                  self.genicam_parameters[param_name]):
                        settings_applied += 1
                    else:
                        settings_failed += 1
            
            # Restliche Parameter anwenden
            for param_name, param_value in self.genicam_parameters.items():
                if param_name not in parameter_order:
                    if self._apply_single_parameter(remote_device_nodemap, param_name, param_value):
                        settings_applied += 1
                    else:
                        settings_failed += 1
            
            logging.info(f"IDS Peak .cset Konfiguration angewendet: {settings_applied} erfolgreich, {settings_failed} fehlgeschlagen")
            
            return settings_applied > 0
            
        except Exception as e:
            logging.error(f"Fehler beim Anwenden der Kamera-Konfiguration: {e}")
            logging.error(traceback.format_exc())
            return False
    
    def _apply_single_parameter(self, nodemap, param_name, param_value):
        """
        Apply a single parameter to the camera nodemap.
        
        Args:
            nodemap: Camera nodemap
            param_name (str): Parameter name
            param_value (str): Parameter value
            
        Returns:
            bool: True if successful
        """
        try:
            node = nodemap.FindNode(param_name)
            if not node:
                logging.debug(f"Parameter {param_name} nicht im Nodemap gefunden")
                return False
            
            if not node.IsAccessible():
                logging.debug(f"Parameter {param_name} nicht zugaenglich")
                return False
            
            if not node.IsWritable():
                logging.debug(f"Parameter {param_name} ist schreibgeschuetzt")
                return False
            
            # Verschiedene Node-Typen handhaben
            if hasattr(node, 'SetValue'):
                # Numerische oder Boolean-Parameter
                try:
                    # Versuche verschiedene Datentypen
                    if param_value.lower() in ['true', 'false']:
                        # Boolean
                        bool_value = param_value.lower() == 'true'
                        node.SetValue(bool_value)
                    elif '.' in param_value:
                        # Float
                        float_value = float(param_value)
                        node.SetValue(float_value)
                    else:
                        # Integer
                        int_value = int(param_value)
                        node.SetValue(int_value)
                    
                    logging.debug(f"Parameter {param_name} auf {param_value} gesetzt")
                    return True
                    
                except (ValueError, TypeError):
                    logging.warning(f"Ungueltige Wertkonvertierung fuer {param_name}: {param_value}")
                    return False
                    
            elif hasattr(node, 'SetCurrentEntry'):
                # Enumeration-Parameter
                try:
                    node.SetCurrentEntry(str(param_value))
                    logging.debug(f"Enumeration {param_name} auf {param_value} gesetzt")
                    return True
                except Exception as e:
                    logging.warning(f"Fehler beim Setzen der Enumeration {param_name}: {e}")
                    return False
                    
            elif hasattr(node, 'Execute'):
                # Command-Parameter
                try:
                    node.Execute()
                    logging.debug(f"Command {param_name} ausgefuehrt")
                    return True
                except Exception as e:
                    logging.warning(f"Fehler beim Ausfuehren des Commands {param_name}: {e}")
                    return False
            
            else:
                logging.warning(f"Unbekannter Node-Typ fuer Parameter {param_name}")
                return False
                
        except Exception as e:
            logging.warning(f"Fehler beim Anwenden von Parameter {param_name}: {e}")
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
            "type": "GenICam XML (.cset)",
            "settings_count": len(self.genicam_parameters),
            "parameters": list(self.genicam_parameters.keys())
        }
        
        return info
    
    def get_parameter_value(self, param_name):
        """
        Get value of a specific parameter.
        
        Args:
            param_name (str): Parameter name
            
        Returns:
            str or None: Parameter value
        """
        return self.genicam_parameters.get(param_name)
    
    def list_all_parameters(self):
        """
        List all loaded parameters.
        
        Returns:
            dict: All parameters and their values
        """
        return self.genicam_parameters.copy()
    
    def clear_config(self):
        """Clear the loaded configuration."""
        self.config_data = None
        self.config_path = None
        self.is_loaded = False
        self.genicam_parameters = {}
        logging.info("Kamera-Konfiguration geleert")