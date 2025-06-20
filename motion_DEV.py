import cv2
import numpy as np
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import webbrowser
from collections import deque
import base64

class LightweightMotionDetector:
    def __init__(self, 
                 stabilization_window: float = 0.3,
                 fps: float = 30.0,
                 learning_duration: float = 60.0,
                 downsample_factor: int = 4,
                 roi_size: float = 0.6):
        """
        Ultra-ressourcenschonender Motion Detector
        
        Args:
            downsample_factor: Verkleinerungsfaktor (4 = 1/16 der Pixel)
            roi_size: Region of Interest (0.6 = nur 60% der Bildmitte)
        """
        self.fps = fps
        self.stabilization_window = stabilization_window
        self.window_size = max(1, int(fps * stabilization_window))
        self.learning_duration = learning_duration
        self.learning_frames = int(fps * learning_duration)
        
        # Ressourcensparende Parameter
        self.downsample_factor = downsample_factor
        self.roi_size = roi_size
        self.frame_skip = 1  # Jeden N-ten Frame verarbeiten
        self.process_counter = 0
        
        # Basis Motion Detection
        self.prev_frame_small = None
        self.motion_value = 0
        self.motion_history = deque(maxlen=self.window_size)
        
        # Vereinfachte Lernphase - nur essenzielle Daten
        self.is_learning = True
        self.learning_frame_count = 0
        self.motion_samples = deque(maxlen=min(300, self.learning_frames // 2))  # Nur jeder 2. Frame
        
        # Optimierte Parameter (werden während Lernphase gesetzt)
        self.noise_baseline = 2.0
        self.scaling_factor = 8.0
        self.motion_threshold = 5.0
        
        # ROI Cache für bessere Performance
        self.roi_slice = None
        self.frame_size = None
        
        print(f"⚡ LIGHTWEIGHT MOTION DETECTION")
        print(f"🔧 Downsample: 1/{downsample_factor**2} Pixel ({downsample_factor}x{downsample_factor})")
        print(f"🎯 ROI: {roi_size*100:.0f}% der Bildmitte")
        print(f"💡 Helligkeits-immun: CLAHE + Gradienten + Normalisierung")
        print(f"📚 Vereinfachte Lernphase: {learning_duration}s")
    
    def _get_roi_slice(self, frame_shape):
        """Berechnet ROI-Slice nur einmal für bessere Performance"""
        if self.roi_slice is None or self.frame_size != frame_shape:
            h, w = frame_shape[:2]
            self.frame_size = frame_shape
            
            # ROI in der Bildmitte
            roi_h = int(h * self.roi_size)
            roi_w = int(w * self.roi_size)
            start_y = (h - roi_h) // 2
            start_x = (w - roi_w) // 2
            
            self.roi_slice = (slice(start_y, start_y + roi_h), 
                             slice(start_x, start_x + roi_w))
            
            print(f"🎯 ROI Cache: {roi_w}x{roi_h} bei ({start_x},{start_y})")
        
        return self.roi_slice
    
    def _preprocess_frame_fast(self, frame: np.ndarray) -> np.ndarray:
        """Ultra-schnelle Frame-Vorverarbeitung mit Helligkeits-Normalisierung"""
        # 1. ROI extrahieren (nur Bildmitte)
        roi_slice = self._get_roi_slice(frame.shape)
        roi_frame = frame[roi_slice[0], roi_slice[1]]
        
        # 2. Zu Graustufen (schnellste Methode)
        if len(roi_frame.shape) == 3:
            gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi_frame
        
        # 3. Downsampling für deutlich weniger Pixel
        small = gray[::self.downsample_factor, ::self.downsample_factor]
        
        # 4. HELLIGKEITS-NORMALISIERUNG (Adaptive Histogram Equalization)
        # Verwendet CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))
        normalized = clahe.apply(small.astype(np.uint8))
        
        # 5. Minimaler Blur nach Normalisierung
        blurred = cv2.blur(normalized, (3, 3))
        
        return blurred.astype(np.float32)
    
    def calculate_motion_intensity(self, frame: np.ndarray) -> int:
        """Hauptfunktion - optimiert für minimale CPU-Last und Helligkeits-immun"""
        # Frame-Skipping für noch weniger CPU-Last
        self.process_counter += 1
        if self.process_counter % self.frame_skip != 0:
            return self.motion_value  # Letzten Wert wiederverwenden
        
        # Schnelle Frame-Verarbeitung mit Helligkeits-Normalisierung
        current_small = self._preprocess_frame_fast(frame)
        
        if self.prev_frame_small is None:
            self.prev_frame_small = current_small
            return 0
        
        # HELLIGKEITS-IMMUNE BEWEGUNGSERKENNUNG
        
        # Methode 1: Strukturelle Ähnlichkeit statt einfacher Differenz
        # Berechnet lokale Gradienten die unabhängig von Gesamthelligkeit sind
        
        # Gradienten des aktuellen Frames
        grad_x_curr = cv2.Sobel(current_small, cv2.CV_32F, 1, 0, ksize=3)
        grad_y_curr = cv2.Sobel(current_small, cv2.CV_32F, 0, 1, ksize=3)
        
        # Gradienten des vorherigen Frames
        grad_x_prev = cv2.Sobel(self.prev_frame_small, cv2.CV_32F, 1, 0, ksize=3)
        grad_y_prev = cv2.Sobel(self.prev_frame_small, cv2.CV_32F, 0, 1, ksize=3)
        
        # Gradient-Magnitude (Kantenstärke) - unabhängig von Helligkeit
        mag_curr = np.sqrt(grad_x_curr**2 + grad_y_curr**2)
        mag_prev = np.sqrt(grad_x_prev**2 + grad_y_prev**2)
        
        # Methode 2: Relative Änderung statt absolute Differenz
        # Normalisierung durch lokale Mittelwerte
        mean_curr = np.mean(current_small)
        mean_prev = np.mean(self.prev_frame_small)
        
        if mean_prev > 0 and mean_curr > 0:
            # Normalisierte Frames (Helligkeit ausgeglichen)
            norm_curr = current_small / mean_curr
            norm_prev = self.prev_frame_small / mean_prev
            
            # Differenz der normalisierten Frames
            normalized_diff = np.abs(norm_curr - norm_prev)
            normalized_motion = np.mean(normalized_diff) * 100  # Skalierung
        else:
            normalized_motion = 0
        
        # Methode 3: Kantendifferenz (sehr robust gegen Helligkeitsänderungen)
        edge_diff = np.abs(mag_curr - mag_prev)
        edge_motion = np.mean(edge_diff)
        
        # Kombinierte Bewegungsberechnung (gewichteter Durchschnitt)
        raw_motion = (
            normalized_motion * 0.6 +    # Normalisierte Differenz (Hauptgewicht)
            edge_motion * 0.4             # Kantendifferenz (Stabilisierung)
        )
        
        # Lernphase - nur essenzielle Daten sammeln
        if self.is_learning:
            self._learn_fast(raw_motion)
            self.prev_frame_small = current_small
            return 0
        
        # Nach Lernphase: Schnelle Motion Detection
        motion_value = self._calculate_motion_fast(raw_motion)
        
        self.prev_frame_small = current_small
        return motion_value
    
    def _learn_fast(self, raw_motion: float):
        """Vereinfachte, schnelle Lernphase"""
        # Nur jeden 2. Frame in Lernphase verarbeiten
        if self.learning_frame_count % 2 == 0:
            self.motion_samples.append(raw_motion)
        
        self.learning_frame_count += 1
        
        # Progress (weniger häufig)
        if self.learning_frame_count % 60 == 0:  # Alle 2 Sekunden
            progress = (self.learning_frame_count / self.learning_frames) * 100
            print(f"\r⚡ Lernfortschritt: {progress:.0f}% | Samples: {len(self.motion_samples)}", end="", flush=True)
        
        # Lernphase beenden
        if self.learning_frame_count >= self.learning_frames:
            self._complete_learning_fast()
    
    def _complete_learning_fast(self):
        """Schnelle Lernphase-Auswertung ohne komplexe Statistiken"""
        if not self.motion_samples:
            self.is_learning = False
            return
        
        samples = np.array(self.motion_samples)
        
        # Einfache Statistiken
        min_val = np.min(samples)
        max_val = np.max(samples)
        mean_val = np.mean(samples)
        
        # Schnelle Perzentil-Berechnung (nur die wichtigsten)
        p10 = np.percentile(samples, 10)
        p90 = np.percentile(samples, 90)
        
        # Einfache Parameter-Setzung
        self.noise_baseline = p10
        self.motion_threshold = mean_val
        effective_range = max(1.0, p90 - p10)
        self.scaling_factor = 255.0 / effective_range
        
        # Lernphase beenden
        self.is_learning = False
        
        print(f"\n✅ Lernphase abgeschlossen")
        print(f"📊 {len(samples)} Samples | Range: {min_val:.1f}-{max_val:.1f}")
        print(f"⚙️  Baseline: {self.noise_baseline:.1f} | Skala: {self.scaling_factor:.1f}")
        print("=" * 50)
    
    def _calculate_motion_fast(self, raw_motion: float) -> int:
        """Schnelle Motion-Berechnung nach Lernphase"""
        # 1. Rauschunterdrückung
        if raw_motion <= self.noise_baseline:
            cleaned_motion = 0
        else:
            cleaned_motion = raw_motion - self.noise_baseline
        
        # 2. Skalierung auf 0-255
        scaled_motion = min(255, int(cleaned_motion * self.scaling_factor))
        
        # 3. Einfache Glättung (nur Durchschnitt über Zeitfenster)
        self.motion_history.append(scaled_motion)
        if len(self.motion_history) > 0:
            self.motion_value = int(np.mean(self.motion_history))
        else:
            self.motion_value = scaled_motion
        
        return self.motion_value
    
    def get_status(self) -> dict:
        """Vereinfachter Status - alle Werte JSON-serialisierbar"""
        if self.is_learning:
            progress = float((self.learning_frame_count / self.learning_frames) * 100)
            return {
                'phase': 'learning',
                'progress': progress,
                'frames_learned': int(self.learning_frame_count),
                'samples_collected': int(len(self.motion_samples))
            }
        else:
            return {
                'phase': 'detection',
                'noise_baseline': float(self.noise_baseline),
                'scaling_factor': float(self.scaling_factor),
                'downsample_factor': int(self.downsample_factor),
                'roi_size': float(self.roi_size)
            }
    
    def adjust_performance(self, cpu_usage_high: bool):
        """Dynamische Performance-Anpassung"""
        if cpu_usage_high:
            self.frame_skip = min(3, self.frame_skip + 1)
            print(f"🔥 CPU-Last hoch -> Frame-Skip: {self.frame_skip}")
        else:
            self.frame_skip = max(1, self.frame_skip - 1)

class LightweightWebServer:
    def __init__(self, detector: LightweightMotionDetector, port: int = 8000):
        """Minimaler Web-Server für Live-Anzeige"""
        self.detector = detector
        self.port = port
        self.current_frame = None
        self.motion_value = 0
        self.frame_count = 0
        self.total_frames = 0
        self.fps = 0
        self.current_time = 0
        self.is_playing = True
        
        # Performance-Optimierungen
        self.last_frame_time = 0
        self.frame_update_interval = 0.1  # Nur alle 100ms Frame-Update
        self.jpeg_quality = 70  # Niedrigere JPEG-Qualität für weniger CPU-Last
    
    def create_simple_overlay(self, frame: np.ndarray, motion_value: int) -> np.ndarray:
        """Minimales Overlay für weniger CPU-Last"""
        display = frame.copy()
        h, w = display.shape[:2]
        
        # Nur essenzielle Informationen
        status = self.detector.get_status()
        
        if status['phase'] == 'learning':
            # Einfacher Lernphase-Indikator
            progress = status['progress']
            cv2.rectangle(display, (10, 10), (w-10, 50), (0, 100, 200), -1)
            cv2.putText(display, f"LERNT: {progress:.0f}%", (20, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            # Minimale Motion-Anzeige
            cv2.putText(display, f"Motion: {motion_value}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Einfacher Status
            if motion_value < 50:
                status_text = "STILL"
                color = (0, 255, 0)
            elif motion_value < 150:
                status_text = "BEWEGT"
                color = (0, 255, 255)
            else:
                status_text = "STARK"
                color = (0, 0, 255)
            
            cv2.putText(display, status_text, (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        return display
    
    def frame_to_base64_fast(self, frame: np.ndarray) -> str:
        """Schnelle Frame-Konvertierung mit niedriger Qualität"""
        # Kleinere Auflösung für Web-Übertragung
        height, width = frame.shape[:2]
        if width > 640:  # Nur bei grossen Frames verkleinern
            new_width = 640
            new_height = int(height * (new_width / width))
            frame_small = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        else:
            frame_small = frame
        
        # Niedrige JPEG-Qualität für weniger CPU-Last
        _, buffer = cv2.imencode('.jpg', frame_small, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{frame_base64}"
    
    def get_minimal_html(self) -> str:
        """Minimale HTML-Seite ohne schwere Animationen"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Lightweight Motion Detection</title>
    <style>
        body { margin:0; padding:20px; background:#222; color:white; font-family:Arial; }
        .container { max-width:800px; margin:0 auto; }
        #videoFrame { max-width:100%; border:2px solid #666; }
        .controls { text-align:center; margin:20px 0; }
        .btn { background:#444; color:white; border:none; padding:10px 20px; margin:5px; cursor:pointer; }
        .stats { display:flex; justify-content:space-around; margin:20px 0; }
        .stat { background:#333; padding:15px; border-radius:5px; }
        .motion-bar { width:100%; height:20px; background:#444; margin:10px 0; }
        .motion-fill { height:100%; background:linear-gradient(90deg, #0f0, #ff0, #f00); transition:width 0.3s; }
        .console { background:#000; padding:10px; height:150px; overflow-y:auto; font-family:monospace; font-size:12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Lightweight Motion Detection</h1>
        
        <div style="text-align:center;">
            <img id="videoFrame" src="" alt="Video">
        </div>
        
        <div class="controls">
            <button class="btn" onclick="togglePlay()">⏯️ Play/Pause</button>
            <button class="btn" onclick="resetLearning()">🔄 Reset</button>
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>Motion: <span id="motionValue">0</span></h3>
                <div class="motion-bar"><div id="motionFill" class="motion-fill" style="width:0%;"></div></div>
                <div id="status">Initialisierung...</div>
            </div>
            <div class="stat">
                <h3>Performance</h3>
                <div>Frame: <span id="frameCount">0</span></div>
                <div>Zeit: <span id="time">0</span>s</div>
                <div>Phase: <span id="phase">-</span></div>
            </div>
        </div>
        
        <div class="console" id="console">
            <div>⚡ Lightweight Motion Detection Console</div>
        </div>
    </div>
    
    <script>
        let updateInterval = 200; // Langsamere Updates für weniger CPU-Last
        
        function updateFrame() {
            fetch('/frame')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('videoFrame').src = data.frame;
                    
                    const motion = data.motion_value;
                    document.getElementById('motionValue').textContent = motion;
                    document.getElementById('motionFill').style.width = (motion/255*100) + '%';
                    document.getElementById('frameCount').textContent = data.frame_count;
                    document.getElementById('time').textContent = data.current_time.toFixed(1);
                    
                    if (data.status.phase === 'learning') {
                        document.getElementById('phase').textContent = 'Lernt ' + data.status.progress.toFixed(0) + '%';
                        document.getElementById('status').textContent = 'Lernphase aktiv...';
                    } else {
                        document.getElementById('phase').textContent = 'Erkennung';
                        document.getElementById('status').textContent = motion < 50 ? 'Stillstand' : motion < 150 ? 'Bewegung' : 'Starke Bewegung';
                    }
                })
                .catch(e => console.error(e));
        }
        
        function togglePlay() {
            fetch('/control', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'toggle'})});
        }
        
        function resetLearning() {
            fetch('/control', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'reset'})});
        }
        
        function addLog(msg) {
            const console = document.getElementById('console');
            console.innerHTML += '<div>' + new Date().toLocaleTimeString() + ' ' + msg + '</div>';
            console.scrollTop = console.scrollHeight;
        }
        
        // Langsamere Updates für weniger CPU-Last
        setInterval(updateFrame, updateInterval);
        updateFrame();
        addLog('⚡ Lightweight System gestartet');
    </script>
</body>
</html>
        """

class SimpleHandler(BaseHTTPRequestHandler):
    server_instance = None
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.server_instance.get_minimal_html().encode())
        
        elif self.path == '/frame':
            # Frame-Rate-Limiting für weniger CPU-Last
            current_time = time.time()
            if current_time - self.server_instance.last_frame_time < self.server_instance.frame_update_interval:
                # Zu früh für Update, sende cached response
                self.send_response(304)  # Not Modified
                self.end_headers()
                return
            
            self.server_instance.last_frame_time = current_time
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            if self.server_instance.current_frame is not None:
                data = {
                    'frame': self.server_instance.frame_to_base64_fast(self.server_instance.current_frame),
                    'motion_value': int(self.server_instance.motion_value),  # Zu int konvertieren
                    'frame_count': int(self.server_instance.frame_count),    # Zu int konvertieren  
                    'current_time': float(self.server_instance.current_time), # Zu float konvertieren
                    'status': self._serialize_status(self.server_instance.detector.get_status())
                }
                self.wfile.write(json.dumps(data).encode())
    
    def do_POST(self):
        if self.path == '/control':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if data.get('action') == 'toggle':
                self.server_instance.is_playing = not self.server_instance.is_playing
            elif data.get('action') == 'reset':
                detector = self.server_instance.detector
                detector.is_learning = True
                detector.learning_frame_count = 0
                detector.motion_samples.clear()
                detector.motion_history.clear()
                print("\n🔄 Lernphase zurückgesetzt")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
    
    def _serialize_status(self, status):
        """Konvertiert NumPy-Typen zu JSON-serialisierbaren Typen"""
        serialized = {}
        for key, value in status.items():
            if isinstance(value, np.floating):
                serialized[key] = float(value)
            elif isinstance(value, np.integer):
                serialized[key] = int(value)
            elif isinstance(value, (list, tuple)):
                serialized[key] = [float(x) if isinstance(x, np.floating) else 
                                 int(x) if isinstance(x, np.integer) else x for x in value]
            else:
                serialized[key] = value
        return serialized
    
    def log_message(self, format, *args):
        pass

class LightweightPlayer:
    def __init__(self, detector: LightweightMotionDetector, web_server: LightweightWebServer):
        self.detector = detector
        self.web_server = web_server
        
    def play_video_optimized(self, video_path: str):
        """Ultra-optimierte Video-Wiedergabe"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video nicht gefunden: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Video konnte nicht geöffnet werden")
        
        # Video-Parameter
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_delay = 1.0 / fps if fps > 0 else 0.033
        
        # Detector konfigurieren
        self.detector.fps = fps
        self.detector.learning_frames = int(fps * self.detector.learning_duration)
        
        self.web_server.fps = fps
        self.web_server.total_frames = total_frames
        
        print(f"⚡ LIGHTWEIGHT MODUS AKTIV")
        print(f"📺 Video: {os.path.basename(video_path)}")
        print(f"📊 {fps:.1f} FPS, {total_frames} Frames")
        print(f"🎯 ROI: {self.detector.roi_size*100:.0f}% | Downsample: 1/{self.detector.downsample_factor**2}")
        print(f"🌐 http://localhost:{self.web_server.port}")
        print("=" * 50)
        
        frame_count = 0
        last_log_time = 0
        
        try:
            while True:
                if self.web_server.is_playing:
                    ret, frame = cap.read()
                    if not ret:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        frame_count = 0
                        continue
                    
                    # Motion Detection (optimiert)
                    motion_value = self.detector.calculate_motion_intensity(frame)
                    
                    # Minimales Overlay (weniger CPU-Last)
                    if frame_count % 5 == 0:  # Nur jeder 5. Frame
                        display_frame = self.web_server.create_simple_overlay(frame, motion_value)
                        self.web_server.current_frame = display_frame
                    
                    # Web-Server Update (sichere Konvertierung)
                    self.web_server.motion_value = int(motion_value)
                    self.web_server.frame_count = int(frame_count)
                    self.web_server.current_time = float(frame_count / fps) if fps > 0 else 0.0
                    
                    # Seltene Console-Ausgabe für weniger CPU-Last
                    current_time = time.time()
                    if current_time - last_log_time > 2.0:  # Alle 2 Sekunden
                        if self.detector.is_learning:
                            progress = (self.detector.learning_frame_count / self.detector.learning_frames) * 100
                            print(f"\r⚡ Frame {frame_count} | Lernt: {progress:.0f}%", end="", flush=True)
                        else:
                            cpu_indicator = "🔥" if motion_value > 150 else "⚡"
                            print(f"\r{cpu_indicator} Frame {frame_count} | Motion: {motion_value:3d}/255", end="", flush=True)
                        last_log_time = current_time
                    
                    frame_count += 1
                    time.sleep(frame_delay)
                else:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print(f"\n🛑 Beendet bei Frame {frame_count}")
        finally:
            cap.release()

def start_lightweight_server(web_server):
    """Startet minimalen Web-Server"""
    SimpleHandler.server_instance = web_server
    httpd = HTTPServer(('localhost', web_server.port), SimpleHandler)
    print(f"⚡ Lightweight Web-Server auf Port {web_server.port}")
    httpd.serve_forever()

def main():
    print("⚡ ULTRA-RESSOURCENSCHONENDE MOTION DETECTION")
    print("🚀 Optimiert für minimale CPU-Belastung")
    print("=" * 50)
    
    # Ultra-optimierte Einstellungen
    detector = LightweightMotionDetector(
        stabilization_window=0.3,
        fps=30.0,
        learning_duration=60.0,
        downsample_factor=4,     # 1/16 der Pixel (75% weniger Berechnung)
        roi_size=0.6             # Nur 60% der Bildmitte (36% der Pixel)
    )
    
    web_server = LightweightWebServer(detector, port=8000)
    player = LightweightPlayer(detector, web_server)
    
    video_path = r"C:\Users\Michel\Videos\video_20250619_141029.mp4"
    
    print("⚡ Performance-Optimierungen:")
    print(f"   • Downsample: 1/{detector.downsample_factor**2} Pixel")
    print(f"   • ROI: {detector.roi_size*100:.0f}% der Bildmitte")
    print("   • Helligkeits-Immunität: CLAHE + Gradienten")
    print("   • Frame-Skipping bei hoher CPU-Last")
    print("   • Reduzierte Web-Update-Rate")
    print("   • Minimale Overlays")
    print("   • Niedrige JPEG-Qualität")
    print("   • Vereinfachte Lernphase")
    print("=" * 50)
    
    # Server starten
    server_thread = threading.Thread(target=start_lightweight_server, args=(web_server,), daemon=True)
    server_thread.start()
    
    time.sleep(1)
    webbrowser.open(f'http://localhost:{web_server.port}')
    
    try:
        player.play_video_optimized(video_path)
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    main()