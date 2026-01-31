
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import threading
import webbrowser
from collections import deque
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from engine.gemini_utils import set_gemini_api_key, transcribe_audio_from_mic, extract_segmentation_masks

# --- Configuration ---
POLL_INTERVAL_SECS = 1.0
EVENT_RETENTION_MINS = 10
MAX_EVENTS = int((EVENT_RETENTION_MINS * 60) / POLL_INTERVAL_SECS)
WEB_SERVER_PORT = 8655
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memact_activity.log')
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots')

APP_ALIAS_MAP = {
    'chrome': 'Chrome',
    'edge': 'Edge',
    'firefox': 'Firefox',
    'code': 'Code Editor',
}

IS_DEBUG_MODE = '--debug' in sys.argv

try:
    import win32gui
    import win32process
    import psutil
    from PIL import ImageGrab
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

def write_to_log(message):
    try:
        with open(LOG_FILE_PATH, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except Exception as e:
        print(f"[CRITICAL] Could not write to log file: {e}", file=sys.stderr, flush=True)

# --- Screenshot Monitor ---
class ScreenshotMonitor:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def capture_active_window(self):
        if not IS_WINDOWS:
            return None
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            
            rect = win32gui.GetWindowRect(hwnd)
            x, y, w, h = rect
            if w <= 0 or h <= 0:
                return None

            screenshot = ImageGrab.grab(bbox=(x, y, w, h))
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            screenshot.save(filepath)
            return filepath
        except Exception as e:
            write_to_log(f"ERROR in capture_active_window: {e}")
            return None

# --- Platform Monitoring Abstraction ---
class PlatformMonitor:
    def __init__(self, event_callback, error_callback):
        self.event_callback = event_callback
        self.error_callback = error_callback
        self._monitor_thread = None
        self._stop_event = threading.Event()

    def start(self):
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop(self):
        self._stop_event.set()

    def _monitor_loop(self):
        pass

class WindowsMonitor(PlatformMonitor):
    def __init__(self, event_callback, error_callback, screenshot_monitor):
        super().__init__(event_callback, error_callback)
        self.screenshot_monitor = screenshot_monitor

    def _monitor_loop(self):
        last_event_ids = None
        while not self._stop_event.is_set():
            try:
                hwnd = win32gui.GetForegroundWindow()
                if not hwnd: 
                    time.sleep(POLL_INTERVAL_SECS)
                    continue
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                proc_name = proc.name().lower()
                title = win32gui.GetWindowText(hwnd)
                
                if any(browser in proc_name for browser in ['chrome', 'edge', 'firefox']):
                    time.sleep(POLL_INTERVAL_SECS)
                    continue
                
                app_name = proc_name.split('.')[0].capitalize()

                current_event_ids = (app_name, title)
                if title and app_name and current_event_ids != last_event_ids:
                    screenshot_path = self.screenshot_monitor.capture_active_window()
                    context = {'type': 'window_title', 'value': title, 'source': 'monitor', 'screenshot': screenshot_path}
                    self.event_callback((time.time(), app_name, title, context))
                    last_event_ids = current_event_ids
            except (psutil.NoSuchProcess, win32gui.error): pass
            except Exception as e:
                write_to_log(f"ERROR in monitor loop: {e}")
            time.sleep(POLL_INTERVAL_SECS)

# --- Core Engine ---
class ContextReconstructionEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.events = deque(maxlen=MAX_EVENTS)
        self.monitor = None
        self.web_server_thread = None
        self.screenshot_monitor = ScreenshotMonitor(SCREENSHOT_DIR)
        self._initialized = True
        write_to_log("Engine initialized.")

    def _handle_event(self, event_data):
        with self._lock:
            if self.events and event_data[2] == self.events[-1][2]: return
            self.events.append(event_data)
            write_to_log(f"Handled Event: App: {event_data[1]}, Title: {event_data[2]}")

    def start_services(self):
        set_gemini_api_key()
        if IS_WINDOWS:
            self.monitor = WindowsMonitor(self._handle_event, self._send_error, self.screenshot_monitor)
            self.monitor.start()
        self.web_server_thread = threading.Thread(target=self._start_web_server, daemon=True)
        self.web_server_thread.start()

    def _start_web_server(self):
        engine_instance = self
        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith('/screenshots/'):
                    try:
                        filepath = os.path.join(SCREENSHOT_DIR, self.path[len('/screenshots/'):])
                        with open(filepath, 'rb') as f:
                            self.send_response(200)
                            self.send_header('Content-type', 'image/png')
                            self.end_headers()
                            self.wfile.write(f.read())
                    except FileNotFoundError:
                        self.send_error(404, 'File Not Found')
                else:
                    self.send_error(404, 'File Not Found')

            def do_POST(self):
                if self.path == '/log':
                    try:
                        content_length = int(self.headers['Content-Length'])
                        data = json.loads(self.rfile.read(content_length))
                        write_to_log(f"SUCCESS: Received data from extension: {data.get('url')}")
                        app_name = data.get('browser', 'Browser')
                        context = {'type': 'url', 'value': data.get('url'), 'source': 'extension'}
                        engine_instance._handle_event((time.time(), app_name, data.get('title', 'Unknown Tab'), context))
                        self.send_response(200); self.end_headers()
                    except Exception as e:
                        write_to_log(f"ERROR: Failed to process data: {e}")
                        self.send_response(500); self.end_headers()
                else: self.send_response(404); self.end_headers()
            def log_message(self, format, *args): return
        try:
            server = HTTPServer(('', WEB_SERVER_PORT), RequestHandler)
            server.serve_forever()
        except Exception as e:
            write_to_log(f"CRITICAL: Server failed: {e}")

    def open_context(self, context):
        if context and context.get('type') == 'url':
            url = context.get('value')
            if url and isinstance(url, str) and url.startswith('http'):
                write_to_log(f"Opening URL: {url}")
                webbrowser.open(url)

    def get_timeline(self):
        with self._lock:
            events_copy = list(self.events)
        
        timeline_for_ui = []
        now = time.time()
        for i, event in enumerate(reversed(events_copy)):
            ts, app, title, context = event
            display_path = None
            if context and context.get('type') == 'url' and context.get('value'):
                try: display_path = urlparse(context.get('value')).netloc
                except: pass

            timeline_for_ui.append({
                "id": i,
                "time_str": self._get_formatted_time(now - ts),
                "app": app,
                "title": title,
                "display_path": display_path,
                "context": context
            })
        return {"timeline": timeline_for_ui}

    def _get_formatted_time(self, seconds_ago):
        if seconds_ago < 5: return "just now"
        if seconds_ago < 60: return f"{int(seconds_ago)}s ago"
        minutes = seconds_ago / 60
        if minutes < 60: return f"{int(minutes)}m ago"
        hours = minutes / 60
        if hours < 24: return f"{int(hours)}h ago"
        days = hours / 24
        return f"{int(days)}d ago"

    def get_screenshots(self):
        screenshot_files = []
        if os.path.exists(SCREENSHOT_DIR):
            for f in os.listdir(SCREENSHOT_DIR):
                if f.endswith(".png"):
                    screenshot_files.append(os.path.join(SCREENSHOT_DIR, f))
        return {"screenshots": screenshot_files}

    def _send_message(self, msg_type, payload):
        print(json.dumps({"type": msg_type, "payload": payload}), flush=True)

    def _send_error(self, error_message):
        self._send_debug_message(f"ERROR: {error_message}")

    def _send_debug_message(self, debug_message):
        if IS_DEBUG_MODE: print(f"[Python Debug] {debug_message}", file=sys.stderr, flush=True)

    def stop_services(self):
        if self.monitor:
            self.monitor.stop()

def main():
    if os.path.exists(LOG_FILE_PATH):
        try: os.remove(LOG_FILE_PATH)
        except: pass
    write_to_log("Main function started.")
    engine = ContextReconstructionEngine()
    engine.start_services()
    try:
        for line in sys.stdin:
            try:
                message = json.loads(line)
                msg_type = message.get('type')
                if msg_type == 'get_timeline':
                    timeline = engine.get_timeline()
                    engine._send_message('timeline_response', timeline)
                elif msg_type == 'open_context':
                    engine.open_context(message.get('payload'))
                elif msg_type == 'transcribe_audio':
                    transcribe_audio_from_mic()
                elif msg_type == 'extract_visuals':
                    image_path = message.get('payload', {}).get('image_path')
                    if image_path:
                        extract_segmentation_masks(image_path)
                elif msg_type == 'get_screenshots':
                    screenshots = engine.get_screenshots()
                    engine._send_message('screenshot_response', screenshots)
            except Exception as e:
                write_to_log(f"ERROR in main loop: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop_services()

if __name__ == '__main__':
    main()
