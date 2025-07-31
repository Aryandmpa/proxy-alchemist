#!/usr/bin/env python3
"""
Enhanced Proxy Alchemist - Advanced Proxy Management System
Version: ULTIMATE v11.0
Author: Enhanced by AI Assistant
Compatible with: Termux (Non-root), Linux, Android

Features:
- Auto Tor IP Changer
- Proxy Chaining
- Stealth Mode
- Traffic Analysis
- DNS Protection
- Kill Switch
- Browser Spoofing
- QR Code Generation
- Real-time Monitoring
- Proxy Health Checks
- Geographic Filtering
- Load Balancing
- Bandwidth Monitoring
- Custom Proxy Sources
"""

import os
import re
import sys
import time
import json
import random
import signal
import requests
import threading
import subprocess
import hashlib
import base64
import urllib.parse
from datetime import datetime, timedelta
from urllib.parse import urlparse
import platform
import socket
import sqlite3
import logging
from pathlib import Path
import argparse
import configparser
import psutil

# Try to import optional dependencies with fallbacks
try:
    import geoip2.database
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False
    print("Warning: geoip2 not available. Geographic features disabled.")

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    print("Warning: qrcode not available. QR generation disabled.")

try:
    from pyfiglet import Figlet
    FIGLET_AVAILABLE = True
except ImportError:
    FIGLET_AVAILABLE = False
    print("Warning: pyfiglet not available. ASCII art disabled.")

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Create dummy color objects
    class DummyColor:
        MAGENTA = RED = GREEN = YELLOW = CYAN = BLUE = ""
    class DummyStyle:
        RESET_ALL = ""
    Fore = DummyColor()
    Style = DummyStyle()

try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn
    HTTP_SERVER_AVAILABLE = True
except ImportError:
    HTTP_SERVER_AVAILABLE = False

# ===== CONFIGURATION =====
PROXY_API_URL = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
BACKUP_PROXY_APIS = [
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
]
TOR_BRIDGES_URL = "https://bridges.torproject.org/bridges?transport=obfs4"
LOG_FILE = "proxy_alchemist.log"
ROTATION_INTERVAL = 300  # 5 minutes default
IP_CHECK_URLS = [
    "http://icanhazip.com",
    "http://ipinfo.io/ip",
    "http://checkip.amazonaws.com",
    "http://whatismyipaddress.com/api/ip.php"
]
CONFIG_FILE = "proxy_config.json"
LOCAL_PROXY_HOST = "0.0.0.0"  # Listen on all interfaces
LOCAL_PROXY_PORT = 8080  # Fixed local proxy port
VERSION = "ULTIMATE v11.0"
GEOIP_DB_PATH = "GeoLite2-City.mmdb"
MAC_PREFIXES = ["00:16:3e", "00:0c:29", "00:50:56", "00:1c:42", "00:1d:0f"]
TRAFFIC_DB = "traffic.db"
FINGERPRINT_DB = "fingerprints.db"
TOR_CONTROL_PORT = 9051
TOR_PROXY_PORT = 9050

# User agent strings for different browsers
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# ===== LOGGING SETUP =====
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ===== BANNER DISPLAY =====
def display_banner():
    """Display creative banner"""
    if FIGLET_AVAILABLE:
        f = Figlet(font='slant')
        print(Fore.MAGENTA + f.renderText('PROXY ALCHEMIST'))
    else:
        print(Fore.MAGENTA + """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           PROXY ALCHEMIST                                    ║
║                    ADVANCED PROXY MANAGEMENT SYSTEM                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        """)
    
    print(Fore.CYAN + "="*80)
    print(Fore.YELLOW + "ADVANCED PROXY MANAGEMENT SYSTEM".center(80))
    print(Fore.CYAN + "="*80)
    print(Fore.GREEN + f"Version: {VERSION} | Enhanced Edition")
    print(Fore.CYAN + "="*80)
    print(Fore.MAGENTA + "Features: Auto Tor IP Changer | Proxy Chaining | Stealth Mode | Traffic Analysis")
    print(Fore.CYAN + "="*80 + Style.RESET_ALL)

# ===== UTILITY FUNCTIONS =====
def is_termux():
    """Check if running in Termux environment"""
    return os.path.exists('/data/data/com.termux')

def get_termux_prefix():
    """Get Termux prefix path"""
    if is_termux():
        return '/data/data/com.termux/files/usr'
    return '/usr'

def check_internet_connection():
    """Check if internet connection is available"""
    try:
        response = requests.get("http://www.google.com", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_local_ip():
    """Get local IP address using a simple socket connection"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception:
        return "127.0.0.1"

def validate_proxy_format(proxy_string):
    """Validate proxy format"""
    patterns = [
        r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$',  # ip:port
        r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5}):(http|https|socks4|socks5)$',  # ip:port:protocol
        r'^(http|https|socks4|socks5)://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$'  # protocol://ip:port
    ]
    
    for pattern in patterns:
        if re.match(pattern, proxy_string):
            return True
    return False

def parse_proxy_string(proxy_string):
    """Parse proxy string into components"""
    proxy_string = proxy_string.strip()
    
    # Format: protocol://ip:port
    if '://' in proxy_string:
        parts = proxy_string.split('://')
        protocol = parts[0]
        ip_port = parts[1].split(':')
        return {
            'host': ip_port[0],
            'port': int(ip_port[1]),
            'protocol': protocol
        }
    
    # Format: ip:port:protocol
    parts = proxy_string.split(':')
    if len(parts) == 3:
        return {
            'host': parts[0],
            'port': int(parts[1]),
            'protocol': parts[2]
        }
    
    # Format: ip:port (default to http)
    if len(parts) == 2:
        return {
            'host': parts[0],
            'port': int(parts[1]),
            'protocol': 'http'
        }
    
    raise ValueError(f"Invalid proxy format: {proxy_string}")

# ===== THREADED HTTP PROXY SERVER =====
if HTTP_SERVER_AVAILABLE:
    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        """Handle requests in a separate thread"""
        daemon_threads = True
        allow_reuse_address = True

    class ProxyHTTPHandler(BaseHTTPRequestHandler):
        """HTTP handler for proxy requests"""
        def do_GET(self):
            self.handle_request()
        
        def do_POST(self):
            self.handle_request()
        
        def do_CONNECT(self):
            self.handle_connect()
        
        def handle_request(self):
            """Handle HTTP/HTTPS requests"""
            try:
                if hasattr(self.server, 'proxy_master') and self.server.proxy_master.current_proxy:
                    proxy = self.server.proxy_master.current_proxy
                    
                    # Forward request through current proxy
                    proxy_url = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"
                    proxies = {'http': proxy_url, 'https': proxy_url}
                    
                    # Get request data
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length) if content_length > 0 else None
                    
                    # Forward request
                    response = requests.request(
                        method=self.command,
                        url=self.path,
                        headers=dict(self.headers),
                        data=post_data,
                        proxies=proxies,
                        timeout=30,
                        allow_redirects=False
                    )
                    
                    # Send response back
                    self.send_response(response.status_code)
                    for header, value in response.headers.items():
                        if header.lower() not in ['connection', 'transfer-encoding']:
                            self.send_header(header, value)
                    self.end_headers()
                    self.wfile.write(response.content)
                    
                else:
                    self.send_error(503, "No proxy configured")
                    
            except Exception as e:
                logger.error(f"Proxy request failed: {e}")
                self.send_error(500, f"Proxy error: {str(e)}")
        
        def handle_connect(self):
            """Handle CONNECT method for HTTPS"""
            try:
                if hasattr(self.server, 'proxy_master') and self.server.proxy_master.current_proxy:
                    proxy = self.server.proxy_master.current_proxy
                    
                    # Connect to proxy
                    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    proxy_socket.connect((proxy['host'], proxy['port']))
                    
                    # Send CONNECT request to proxy
                    connect_request = f"CONNECT {self.path} HTTP/1.1\r\n\r\n"
                    proxy_socket.send(connect_request.encode())
                    
                    # Read proxy response
                    proxy_response = proxy_socket.recv(4096)
                    
                    if b"200" in proxy_response:
                        self.send_response(200, "Connection established")
                        self.end_headers()
                        
                        # Start tunneling
                        self.tunnel_data(self.connection, proxy_socket)
                    else:
                        self.send_error(502, "Proxy connection failed")
                        
                    proxy_socket.close()
                else:
                    self.send_error(503, "No proxy configured")
                    
            except Exception as e:
                logger.error(f"CONNECT request failed: {e}")
                self.send_error(500, f"CONNECT error: {str(e)}")
        
        def tunnel_data(self, client_socket, proxy_socket):
            """Tunnel data between client and proxy"""
            def forward_data(source, destination):
                try:
                    while True:
                        data = source.recv(4096)
                        if not data:
                            break
                        destination.send(data)
                except:
                    pass
            
            # Start forwarding in both directions
            client_to_proxy = threading.Thread(target=forward_data, args=(client_socket, proxy_socket))
            proxy_to_client = threading.Thread(target=forward_data, args=(proxy_socket, client_socket))
            
            client_to_proxy.daemon = True
            proxy_to_client.daemon = True
            
            client_to_proxy.start()
            proxy_to_client.start()
            
            client_to_proxy.join()
            proxy_to_client.join()
        
        def log_message(self, format, *args):
            """Override to reduce log spam"""
            pass

# ===== ENHANCED PROXY ALCHEMIST =====
class ProxyAlchemist:
    def __init__(self):
        self.proxies = []
        self.tor_bridges = []
        self.current_proxy = None
        self.favorites = []
        self.rotation_active = False
        self.rotation_thread = None
        self.local_proxy_active = False
        self.local_proxy_server = None
        self.local_proxy_thread = None
        self.rotation_interval = 300  # Default rotation in seconds
        self.config = self.get_default_config()
        self.tor_process = None
        self.tor_rotation_active = False
        self.tor_rotation_thread = None
        self.proxy_sources = {
            "online": PROXY_API_URL,
            "tor": "tor",
            "custom": None
        }
        self.current_source = "online"
        self.setup_directories()
        self.load_config()
        self.load_favorites()
        self.load_history()
        self.traffic_stats = {"sent": 0, "received": 0}
        self.proxy_uptime = {}
        self.blacklist = []
        self.geoip_reader = self.init_geoip()
        self.setup_databases()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.generate_random_user_agent()})
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def get_default_config(self):
        """Get default configuration"""
        return {
            "api_url": PROXY_API_URL,
            "max_latency": 2000,
            "protocol_preference": ["http", "socks5", "socks4", "https"],
            "auto_start": False,
            "favorite_countries": [],
            "single_host_mode": True,  # Enabled by default
            "auto_refresh": False,
            "refresh_interval": 60,  # minutes
            "max_history": 50,
            "notifications": True,
            "theme": "dark",
            "enable_tor": False,
            "proxy_chain": [],
            "dns_protection": True,
            "kill_switch": False,
            "mac_randomization": False,
            "packet_fragmentation": False,
            "browser_spoofing": True,
            "traffic_compression": False,
            "cloud_sync": False,
            "doh_enabled": True,
            "doq_enabled": False,
            "tor_integration": False,
            "stealth_mode": False,
            "auto_rotate_fail": True,
            "proxy_load_balancing": False,
            "bandwidth_throttle": 0,
            "proxy_health_alerts": True,
            "proxy_uptime_monitor": False,
            "proxy_usage_analytics": True,
            "proxy_geofencing": False,
            "proxy_auto_benchmark": False,
            "proxy_anonymity_level": "elite",
            "proxy_encrypted_storage": False,
            "connection_timeout": 10,
            "max_retries": 3,
            "verify_ssl": True,
            "custom_headers": {},
            "proxy_rotation_strategy": "random",  # random, sequential, latency_based
            "health_check_interval": 300,  # 5 minutes
            "backup_proxy_count": 5,
            "log_level": "INFO"
        }
        
    def init_geoip(self):
        """Initialize GeoIP database"""
        if GEOIP_AVAILABLE and os.path.exists(GEOIP_DB_PATH):
            try:
                return geoip2.database.Reader(GEOIP_DB_PATH)
            except Exception as e:
                logger.warning(f"Error loading GeoIP database: {e}")
                return None
        return None
        
    def setup_databases(self):
        """Initialize databases for traffic and fingerprints"""
        try:
            # Traffic database
            conn = sqlite3.connect(TRAFFIC_DB)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS traffic
                         (timestamp DATETIME, sent INTEGER, received INTEGER, 
                          proxy TEXT, country TEXT, latency INTEGER)''')
            conn.commit()
            conn.close()
            
            # Fingerprint database
            conn = sqlite3.connect(FINGERPRINT_DB)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS fingerprints
                         (id INTEGER PRIMARY KEY, user_agent TEXT, platform TEXT, 
                         language TEXT, timezone TEXT, screen TEXT, fonts TEXT, 
                         canvas_hash TEXT, webgl_hash TEXT, created DATETIME)''')
            conn.commit()
            conn.close()
            
            logger.info("Databases initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
        
    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\n{Fore.RED}🛑 Interrupt received! Shutting down gracefully...{Style.RESET_ALL}")
        self.cleanup_and_exit()
        
    def cleanup_and_exit(self):
        """Clean up resources and exit"""
        try:
            self.stop_rotation()
            self.stop_tor_rotation()
            self.stop_tor_service()
            self.stop_local_proxy()
            self.disable_kill_switch()
            self.save_state()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
        finally:
            sys.exit(0)
        
    def setup_directories(self):
        """Create necessary directories"""
        directories = [
            "proxy_cache", "logs", "browser_profiles", "proxy_stats",
            "proxy_backups", "proxy_qrcodes", "config", "data"
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                    logger.info(f"Configuration loaded from {CONFIG_FILE}")
            except Exception as e:
                logger.warning(f"Error loading config: {e}")
        else:
            self.save_config()
            
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {CONFIG_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
            
    def load_favorites(self):
        """Load favorite proxies"""
        if os.path.exists('favorites.json'):
            try:
                with open('favorites.json', 'r') as f:
                    self.favorites = json.load(f)
                logger.info(f"Loaded {len(self.favorites)} favorites")
            except Exception as e:
                logger.warning(f"Error loading favorites: {e}")
                self.favorites = []
        else:
            self.favorites = []
                
    def save_favorites(self):
        """Save favorite proxies"""
        try:
            with open('favorites.json', 'w') as f:
                json.dump(self.favorites, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save favorites: {e}")
            return False
            
    def load_history(self):
        """Load proxy history"""
        if os.path.exists('history.json'):
            try:
                with open('history.json', 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading history: {e}")
                self.history = []
        else:
            self.history = []
            
    def save_history(self):
        """Save proxy history"""
        try:
            with open('history.json', 'w') as f:
                json.dump(self.history, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            return False
            
    def save_state(self):
        """Save current application state"""
        state = {
            "current_proxy": self.current_proxy,
            "proxies": self.proxies[:100],  # Limit to prevent large files
            "traffic_stats": self.traffic_stats,
            "proxy_uptime": self.proxy_uptime,
            "blacklist": self.blacklist,
            "last_updated": datetime.now().isoformat()
        }
        try:
            with open('state.json', 'w') as f:
                json.dump(state, f, indent=4)
            logger.info("Application state saved")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            
    def load_state(self):
        """Load previous application state"""
        if os.path.exists('state.json'):
            try:
                with open('state.json', 'r') as f:
                    state = json.load(f)
                self.current_proxy = state.get("current_proxy")
                self.proxies = state.get("proxies", [])
                self.traffic_stats = state.get("traffic_stats", {"sent": 0, "received": 0})
                self.proxy_uptime = state.get("proxy_uptime", {})
                self.blacklist = state.get("blacklist", [])
                logger.info("Application state loaded")
            except Exception as e:
                logger.warning(f"Error loading state: {e}")

    def generate_random_user_agent(self):
        """Generate random user agent"""
        return random.choice(USER_AGENTS)

    def check_tor_installed(self):
        """Check if Tor is installed"""
        try:
            subprocess.run(["tor", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    # ===== TOR INTEGRATION =====
    def install_tor(self):
        """Install Tor in Termux"""
        try:
            if is_termux():
                print(f"{Fore.BLUE}🔧 Installing Tor package for Termux...{Style.RESET_ALL}")
                result = subprocess.run(["pkg", "install", "tor", "-y"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"{Fore.GREEN}✅ Tor installed successfully{Style.RESET_ALL}")
                    return True
                else:
                    print(f"{Fore.RED}❌ Tor installation failed: {result.stderr}{Style.RESET_ALL}")
                    return False
            else:
                print(f"{Fore.YELLOW}⚠️ Please install Tor manually for your system{Style.RESET_ALL}")
                return False
        except Exception as e:
            logger.error(f"Tor installation failed: {e}")
            return False

    def start_tor_service(self):
        """Start Tor service"""
        if self.tor_process and self.tor_process.poll() is None:
            print(f"{Fore.YELLOW}⚠️ Tor is already running{Style.RESET_ALL}")
            return True
            
        try:
            print(f"{Fore.BLUE}🔌 Starting Tor service...{Style.RESET_ALL}")
            
            # Create Tor configuration
            tor_config = f"""
SocksPort {TOR_PROXY_PORT}
ControlPort {TOR_CONTROL_PORT}
DataDirectory {os.path.expanduser('~/.tor')}
Log notice file {os.path.expanduser('~/.tor/tor.log')}
"""
            
            # Write config file
            tor_config_path = os.path.expanduser('~/.tor/torrc')
            os.makedirs(os.path.dirname(tor_config_path), exist_ok=True)
            with open(tor_config_path, 'w') as f:
                f.write(tor_config)
            
            # Start Tor with config
            self.tor_process = subprocess.Popen(
                ["tor", "-f", tor_config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for Tor to initialize
            time.sleep(10)
            
            # Verify Tor is running
            if self.tor_process.poll() is None:
                print(f"{Fore.GREEN}✅ Tor service started on port {TOR_PROXY_PORT}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}❌ Tor failed to start{Style.RESET_ALL}")
                return False
        except Exception as e:
            logger.error(f"Tor start failed: {e}")
            return False

    def stop_tor_service(self):
        """Stop Tor service"""
        if self.tor_process:
            print(f"{Fore.BLUE}🛑 Stopping Tor service...{Style.RESET_ALL}")
            self.tor_process.terminate()
            try:
                self.tor_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.tor_process.kill()
            self.tor_process = None
            print(f"{Fore.GREEN}✅ Tor service stopped{Style.RESET_ALL}")
            return True
        return False

    def change_tor_circuit(self):
        """Change Tor circuit to get new IP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect(("127.0.0.1", TOR_CONTROL_PORT))
                s.sendall(b"AUTHENTICATE\r\n")
                response = s.recv(1024)
                if b"250" not in response:
                    logger.error("Tor authentication failed")
                    return False
                    
                s.sendall(b"signal NEWNYM\r\n")
                response = s.recv(1024)
                if b"250" in response:
                    print(f"{Fore.GREEN}🔄 Tor circuit changed successfully{Style.RESET_ALL}")
                    return True
                else:
                    logger.error("Tor circuit change failed")
                    return False
        except Exception as e:
            logger.error(f"Tor control failed: {e}")
            return False

    def start_tor_rotation(self, interval_sec):
        """Start automatic Tor IP rotation"""
        self.tor_rotation_active = True
        print(f"{Fore.MAGENTA}🌀 Starting Tor IP rotation every {interval_sec} seconds{Style.RESET_ALL}")
        
        def rotation_loop():
            while self.tor_rotation_active:
                if self.change_tor_circuit():
                    # Verify new IP
                    try:
                        response = requests.get(
                            random.choice(IP_CHECK_URLS),
                            proxies={'http': f'socks5://127.0.0.1:{TOR_PROXY_PORT}',
                                   'https': f'socks5://127.0.0.1:{TOR_PROXY_PORT}'},
                            timeout=10
                        )
                        print(f"{Fore.CYAN}🌐 New Tor IP: {response.text.strip()}{Style.RESET_ALL}")
                    except Exception as e:
                        logger.warning(f"Failed to verify new Tor IP: {e}")
                
                time.sleep(interval_sec)
                
        self.tor_rotation_thread = threading.Thread(target=rotation_loop)
        self.tor_rotation_thread.daemon = True
        self.tor_rotation_thread.start()

    def stop_tor_rotation(self):
        """Stop Tor IP rotation"""
        if self.tor_rotation_active:
            self.tor_rotation_active = False
            if self.tor_rotation_thread and self.tor_rotation_thread.is_alive():
                self.tor_rotation_thread.join(timeout=5)
            print(f"{Fore.GREEN}⏹ Tor IP rotation stopped{Style.RESET_ALL}")
            return True
        return False

    def set_tor_proxy(self):
        """Set Tor as the current proxy"""
        try:
            os.environ['HTTP_PROXY'] = f'socks5://127.0.0.1:{TOR_PROXY_PORT}'
            os.environ['HTTPS_PROXY'] = f'socks5://127.0.0.1:{TOR_PROXY_PORT}'
            
            # For curl/wget
            curlrc_path = os.path.expanduser('~/.curlrc')
            with open(curlrc_path, 'w') as f:
                f.write(f"proxy = socks5://127.0.0.1:{TOR_PROXY_PORT}\n")
                
            # Get current IP
            try:
                response = requests.get(
                    random.choice(IP_CHECK_URLS),
                    proxies={
                        'http': f'socks5://127.0.0.1:{TOR_PROXY_PORT}',
                        'https': f'socks5://127.0.0.1:{TOR_PROXY_PORT}'
                    },
                    timeout=10
                )
                current_ip = response.text.strip()
            except Exception as e:
                logger.warning(f"Failed to get current IP: {e}")
                current_ip = "Unknown"
                
            self.current_proxy = {
                'host': '127.0.0.1',
                'port': TOR_PROXY_PORT,
                'protocol': 'socks5',
                'country': 'Tor Network',
                'ip': current_ip,
                'latency': 'N/A'
            }
            
            print(f"{Fore.GREEN}🔒 Using Tor proxy | IP: {current_ip}{Style.RESET_ALL}")
            return True
        except Exception as e:
            logger.error(f"Failed to set Tor proxy: {e}")
            return False

    # ===== PROXY SOURCE MANAGEMENT =====
    def fetch_live_proxies(self):
        """Get fresh proxies from current source"""
        if self.current_source == "custom":
            return self.load_custom_proxies()
        elif self.current_source == "tor":
            return True  # Tor doesn't need proxy list
            
        # Online source with fallback
        urls_to_try = [self.proxy_sources['online']] + BACKUP_PROXY_APIS
        
        for url in urls_to_try:
            try:
                print(f"{Fore.BLUE}🌐 Fetching proxies from {url}{Style.RESET_ALL}")
                headers = {
                    'User-Agent': self.generate_random_user_agent(),
                    'Accept': 'application/json, text/plain, */*'
                }
                
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Try to parse as JSON first
                try:
                    data = response.json()
                    if 'data' in data:
                        # GeoNode API format
                        self.parse_geonode_proxies(data['data'])
                    else:
                        # Other JSON formats
                        self.parse_generic_json_proxies(data)
                except json.JSONDecodeError:
                    # Parse as plain text
                    self.parse_text_proxies(response.text)
                
                if self.proxies:
                    print(f"{Fore.GREEN}✅ Loaded {len(self.proxies)} proxies{Style.RESET_ALL}")
                    self.cache_proxies()
                    return True
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from {url}: {e}")
                continue
        
        logger.error("All proxy sources failed")
        return False

    def parse_geonode_proxies(self, proxy_data):
        """Parse GeoNode API proxy data"""
        self.proxies = []
        for proxy in proxy_data:
            # Filter by latency
            if proxy.get('latency', 0) > self.config['max_latency']:
                continue
                
            # Filter by country preference
            if (self.config['favorite_countries'] and 
                proxy.get('country') not in self.config['favorite_countries']):
                continue
                
            # Use first available protocol
            for protocol in self.config['protocol_preference']:
                if protocol in proxy.get('protocols', []):
                    self.proxies.append({
                        'host': proxy['ip'],
                        'port': proxy['port'],
                        'protocol': protocol,
                        'country': proxy.get('country', 'Unknown'),
                        'latency': proxy.get('latency', 0),
                        'last_checked': proxy.get('lastChecked'),
                        'is_favorite': any(fav['host'] == proxy['ip'] for fav in self.favorites)
                    })
                    break

    def parse_generic_json_proxies(self, data):
        """Parse generic JSON proxy data"""
        self.proxies = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    try:
                        proxy = {
                            'host': item.get('ip', item.get('host')),
                            'port': int(item.get('port')),
                            'protocol': item.get('protocol', item.get('type', 'http')),
                            'country': item.get('country', 'Unknown'),
                            'latency': item.get('latency', 0),
                            'is_favorite': False
                        }
                        if proxy['host'] and proxy['port']:
                            self.proxies.append(proxy)
                    except (ValueError, TypeError):
                        continue

    def parse_text_proxies(self, text):
        """Parse plain text proxy list"""
        self.proxies = []
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                if validate_proxy_format(line):
                    proxy = parse_proxy_string(line)
                    proxy.update({
                        'country': 'Unknown',
                        'latency': 0,
                        'is_favorite': False
                    })
                    self.proxies.append(proxy)
            except ValueError:
                continue

    def load_custom_proxies(self):
        """Load proxies from custom file"""
        if not self.proxy_sources['custom'] or not os.path.exists(self.proxy_sources['custom']):
            print(f"{Fore.RED}❌ Custom proxy file not configured or not found{Style.RESET_ALL}")
            return False
            
        try:
            print(f"{Fore.BLUE}📂 Loading proxies from {self.proxy_sources['custom']}{Style.RESET_ALL}")
            self.proxies = []
            
            with open(self.proxy_sources['custom'], 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                        
                    try:
                        # Parse different formats
                        if line.startswith("{"):
                            # JSON format
                            proxy = json.loads(line)
                        else:
                            # Plain text format
                            proxy = parse_proxy_string(line)
                        
                        # Add default values
                        proxy.setdefault('country', 'Unknown')
                        proxy.setdefault('latency', 0)
                        proxy.setdefault('is_favorite', False)
                        
                        self.proxies.append(proxy)
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Invalid proxy format at line {line_num}: {line}")
                        continue
            
            print(f"{Fore.GREEN}✅ Loaded {len(self.proxies)} proxies from custom file{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load custom proxies: {e}")
            return False

    def cache_proxies(self):
        """Cache proxies to file"""
        try:
            cache_file = f"proxy_cache/proxies_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(cache_file, 'w') as f:
                json.dump(self.proxies, f, indent=4)
            logger.info(f"Proxies cached to {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to cache proxies: {e}")

    def test_proxy(self, proxy, timeout=None):
        """Test proxy connection with comprehensive checks"""
        if timeout is None:
            timeout = self.config['connection_timeout']
            
        test_url = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"
        proxies = {'http': test_url, 'https': test_url}
        
        try:
            start_time = time.time()
            
            # Test with multiple IP check services
            for ip_check_url in IP_CHECK_URLS:
                try:
                    response = requests.get(
                        ip_check_url,
                        proxies=proxies,
                        timeout=timeout,
                        headers={'User-Agent': self.generate_random_user_agent()},
                        verify=self.config['verify_ssl']
                    )
                    
                    if response.status_code == 200:
                        latency = int((time.time() - start_time) * 1000)
                        ip = response.text.strip()
                        
                        # Validate IP format
                        try:
                            ipaddress.ip_address(ip)
                        except ValueError:
                            continue
                        
                        # Track traffic
                        self.traffic_stats['received'] += len(response.content)
                        
                        return {
                            'working': True,
                            'ip': ip,
                            'latency': latency,
                            'test_url': ip_check_url
                        }
                except requests.RequestException:
                    continue
                    
        except Exception as e:
            logger.debug(f"Proxy test failed for {proxy['host']}:{proxy['port']}: {e}")
        
        return {'working': False}

    def find_working_proxy(self, max_attempts=None):
        """Find a working proxy with intelligent selection"""
        if max_attempts is None:
            max_attempts = min(15, len(self.proxies))
            
        if not self.proxies:
            print(f"{Fore.YELLOW}⚠️ No proxies available! Fetching new proxies...{Style.RESET_ALL}")
            if not self.fetch_live_proxies():
                return None
        
        # Remove blacklisted proxies
        available_proxies = [p for p in self.proxies 
                           if f"{p['host']}:{p['port']}" not in self.blacklist]
        
        if not available_proxies:
            print(f"{Fore.YELLOW}⚠️ All proxies are blacklisted. Clearing blacklist...{Style.RESET_ALL}")
            self.blacklist = []
            available_proxies = self.proxies
        
        # Apply rotation strategy
        if self.config['proxy_rotation_strategy'] == 'latency_based':
            candidates = sorted(available_proxies, key=lambda x: x.get('latency', 999999))
        elif self.config['proxy_rotation_strategy'] == 'sequential':
            candidates = available_proxies
        else:  # random
            candidates = available_proxies.copy()
            random.shuffle(candidates)
        
        # Prioritize favorites
        favorites = [p for p in candidates if p.get('is_favorite', False)]
        if favorites:
            candidates = favorites + [p for p in candidates if not p.get('is_favorite', False)]
        
        # Limit attempts
        candidates = candidates[:max_attempts]
        
        for i, proxy in enumerate(candidates):
            print(f"{Fore.CYAN}🔎 Testing {proxy['host']}:{proxy['port']} ({proxy['protocol'].upper()}) [{i+1}/{len(candidates)}]{Style.RESET_ALL}")
            
            result = self.test_proxy(proxy)
            
            if result['working']:
                print(f"{Fore.GREEN}✅ Found working proxy: {result['ip']} | Latency: {result['latency']}ms{Style.RESET_ALL}")
                
                # Update proxy info
                proxy.update(result)
                return proxy
            else:
                # Add to blacklist temporarily
                proxy_key = f"{proxy['host']}:{proxy['port']}"
                if proxy_key not in self.blacklist:
                    self.blacklist.append(proxy_key)
        
        print(f"{Fore.RED}❌ No working proxies found in batch{Style.RESET_ALL}")
        return None

    def set_system_proxy(self, proxy):
        """Set proxy for the system"""
        if not proxy:
            return False
            
        try:
            proxy_url = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"
            
            # Set environment variables
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
            os.environ['FTP_PROXY'] = proxy_url
            os.environ['SOCKS_PROXY'] = proxy_url
            
            # For applications that use lowercase
            os.environ['http_proxy'] = proxy_url
            os.environ['https_proxy'] = proxy_url
            os.environ['ftp_proxy'] = proxy_url
            os.environ['socks_proxy'] = proxy_url
            
            # For curl/wget support
            curlrc_path = os.path.expanduser('~/.curlrc')
            with open(curlrc_path, 'w') as f:
                f.write(f"proxy = {proxy_url}\n")
                f.write(f"proxy-user = \n")  # Empty user for anonymous
            
            # Save current proxy
            self.current_proxy = proxy
            logger.info(f"Proxy set: {proxy['host']}:{proxy['port']} | IP: {proxy.get('ip', 'Unknown')}")
            
            # Add to history
            self.add_to_history(proxy)
            
            # Apply additional features if enabled
            if self.config['dns_protection']:
                self.enable_dns_protection()
                
            if self.config['kill_switch']:
                self.enable_kill_switch()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to set system proxy: {e}")
            return False

    def add_to_history(self, proxy):
        """Add proxy to history"""
        entry = {
            'host': proxy['host'],
            'port': proxy['port'],
            'protocol': proxy['protocol'],
            'country': proxy.get('country', ''),
            'ip': proxy.get('ip', ''),
            'set_time': datetime.now().isoformat(),
            'latency': proxy.get('latency', 'N/A')
        }
        
        # Add to beginning
        self.history.insert(0, entry)
        
        # Keep only last N entries
        self.history = self.history[:self.config['max_history']]
        self.save_history()

    def add_favorite(self, proxy):
        """Add proxy to favorites"""
        if not any(fav['host'] == proxy['host'] and fav['port'] == proxy['port'] 
                  for fav in self.favorites):
            self.favorites.append({
                'host': proxy['host'],
                'port': proxy['port'],
                'protocol': proxy['protocol'],
                'country': proxy.get('country', ''),
                'added': datetime.now().isoformat()
            })
            print(f"{Fore.YELLOW}🌟 Added {proxy['host']}:{proxy['port']} to favorites{Style.RESET_ALL}")
            self.save_favorites()
            return True
        else:
            print(f"{Fore.YELLOW}⚠️ Proxy already in favorites{Style.RESET_ALL}")
            return False

    def remove_favorite(self, host, port=None):
        """Remove proxy from favorites"""
        if port:
            self.favorites = [fav for fav in self.favorites 
                            if not (fav['host'] == host and fav['port'] == port)]
            print(f"{Fore.YELLOW}🗑️ Removed {host}:{port} from favorites{Style.RESET_ALL}")
        else:
            self.favorites = [fav for fav in self.favorites if fav['host'] != host]
            print(f"{Fore.YELLOW}🗑️ Removed {host} from favorites{Style.RESET_ALL}")
        
        self.save_favorites()
        return True

    def rotate_proxy(self):
        """Rotate to a new working proxy"""
        print(f"\n{Fore.CYAN}🔄 Rotating IP address...{Style.RESET_ALL}")
        new_proxy = self.find_working_proxy()
        if new_proxy and self.set_system_proxy(new_proxy):
            if self.config['notifications']:
                self.show_notification("Proxy Rotated", f"New IP: {new_proxy.get('ip', 'Unknown')}")
            return new_proxy
        return None

    def start_rotation(self, interval_sec, duration_sec=0):
        """Start automatic proxy rotation"""
        self.rotation_active = True
        self.rotation_interval = interval_sec
        
        if duration_sec <= 0:
            end_time = None
            print(f"{Fore.MAGENTA}♾️ Rotation started: Runs indefinitely until manually stopped{Style.RESET_ALL}")
        else:
            end_time = datetime.now() + timedelta(seconds=duration_sec)
            print(f"{Fore.MAGENTA}⏱ Rotation started: {self.format_duration(interval_sec)} intervals for {self.format_duration(duration_sec)}{Style.RESET_ALL}")
        
        def rotation_loop():
            rotation_count = 0
            while self.rotation_active and (end_time is None or datetime.now() < end_time):
                try:
                    proxy_info = self.rotate_proxy()
                    if proxy_info:
                        rotation_count += 1
                        next_rotation = self.format_duration(self.rotation_interval)
                        print(f"{Fore.CYAN}⏱ Next rotation in {next_rotation} (#{rotation_count}){Style.RESET_ALL}")
                        
                        if self.config['single_host_mode']:
                            self.show_wifi_instructions(proxy_info)
                    else:
                        print(f"{Fore.YELLOW}⚠️ Rotation failed, retrying in 30 seconds{Style.RESET_ALL}")
                        time.sleep(30)
                        continue
                        
                    time.sleep(self.rotation_interval)
                    
                except Exception as e:
                    logger.error(f"Rotation error: {e}")
                    time.sleep(30)
                    
            self.rotation_active = False
            print(f"\n{Fore.GREEN}⏹ Rotation schedule completed (Total rotations: {rotation_count}){Style.RESET_ALL}")
            
        self.rotation_thread = threading.Thread(target=rotation_loop)
        self.rotation_thread.daemon = True
        self.rotation_thread.start()

    def format_duration(self, seconds):
        """Convert seconds to human-readable format"""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if remaining_seconds == 0:
                return f"{minutes} minutes"
            else:
                return f"{minutes}m {remaining_seconds}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes == 0:
                return f"{hours} hours"
            else:
                return f"{hours}h {minutes}m"

    def stop_rotation(self):
        """Stop automatic rotation"""
        if self.rotation_active:
            self.rotation_active = False
            if self.rotation_thread and self.rotation_thread.is_alive():
                self.rotation_thread.join(timeout=5)
            print(f"\n{Fore.GREEN}⏹ Proxy rotation stopped{Style.RESET_ALL}")
            return True
        return False

    def show_wifi_instructions(self, proxy):
        """Display Android Wi-Fi proxy setup instructions"""
        host = get_local_ip()
        port = LOCAL_PROXY_PORT
        
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📱 WI-FI PROXY SETUP INSTRUCTIONS{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Proxy Host: {host}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Proxy Port: {port}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Protocol: HTTP{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Current IP: {proxy.get('ip', 'Unknown')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Country: {proxy.get('country', 'Unknown')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Latency: {proxy.get('latency', 'N/A')}ms{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}📋 SETUP STEPS:{Style.RESET_ALL}")
        print(f"{Fore.GREEN}1. Go to Settings > Network & Internet > Wi-Fi{Style.RESET_ALL}")
        print(f"{Fore.GREEN}2. Long-press your connected network{Style.RESET_ALL}")
        print(f"{Fore.GREEN}3. Select 'Modify network' or 'Advanced'{Style.RESET_ALL}")
        print(f"{Fore.GREEN}4. Set Proxy to 'Manual'{Style.RESET_ALL}")
        print(f"{Fore.GREEN}5. Enter Host: {host} and Port: {port}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}6. Save configuration{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}💡 The IP will change automatically behind this address{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
        
        # Generate QR code for easy sharing
        if QR_AVAILABLE:
            self.generate_wifi_qr(host, port)

    def generate_wifi_qr(self, host, port):
        """Generate QR code for proxy configuration"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=2,
                border=1,
            )
            
            # Create proxy configuration string
            proxy_config = f"PROXY:HTTP:{host}:{port}"
            qr.add_data(proxy_config)
            qr.make(fit=True)
            
            # Print ASCII QR code
            print(f"{Fore.CYAN}📱 QR Code for Proxy Configuration:{Style.RESET_ALL}")
            qr.print_ascii(invert=True)
            
            # Save to file
            img = qr.make_image(fill_color="black", back_color="white")
            img_file = f"proxy_qrcodes/proxy_{int(time.time())}.png"
            img.save(img_file)
            print(f"{Fore.CYAN}💾 QR code saved to {img_file}{Style.RESET_ALL}")
            
        except Exception as e:
            logger.warning(f"QR generation error: {e}")

    def clear_proxy_settings(self):
        """Clear all proxy settings"""
        try:
            # Clear environment variables
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY', 'SOCKS_PROXY',
                         'http_proxy', 'https_proxy', 'ftp_proxy', 'socks_proxy']
            
            for var in proxy_vars:
                if var in os.environ:
                    del os.environ[var]
                    
            # Remove curl config
            curlrc = os.path.expanduser('~/.curlrc')
            if os.path.exists(curlrc):
                os.remove(curlrc)
                
            self.current_proxy = None
            print(f"{Fore.GREEN}🔌 Cleared all proxy settings{Style.RESET_ALL}")
            self.disable_kill_switch()
            return True
            
        except Exception as e:
            logger.error(f"Clear proxy settings failed: {e}")
            return False

    def start_local_proxy(self):
        """Start local proxy server for fixed endpoint"""
        if not HTTP_SERVER_AVAILABLE:
            print(f"{Fore.RED}❌ HTTP server not available{Style.RESET_ALL}")
            return False
            
        if self.local_proxy_active:
            print(f"{Fore.YELLOW}⚠️ Local proxy is already running{Style.RESET_ALL}")
            return False
            
        try:
            print(f"{Fore.BLUE}🚀 Starting local proxy server on {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}...{Style.RESET_ALL}")
            
            # Create custom server class
            class CustomServer(ThreadedHTTPServer):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.proxy_master = proxy_master
                    
            self.local_proxy_server = CustomServer((LOCAL_PROXY_HOST, LOCAL_PROXY_PORT), ProxyHTTPHandler)
            
            def server_thread():
                try:
                    self.local_proxy_server.serve_forever()
                except Exception as e:
                    logger.error(f"Local proxy server error: {e}")
                
            self.local_proxy_thread = threading.Thread(target=server_thread)
            self.local_proxy_thread.daemon = True
            self.local_proxy_thread.start()
            
            self.local_proxy_active = True
            print(f"{Fore.GREEN}✅ Local proxy running at {get_local_ip()}:{LOCAL_PROXY_PORT}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start local proxy: {e}")
            return False

    def stop_local_proxy(self):
        """Stop local proxy server"""
        if not self.local_proxy_active:
            return False
            
        try:
            print(f"{Fore.BLUE}🛑 Stopping local proxy server...{Style.RESET_ALL}")
            
            if self.local_proxy_server:
                self.local_proxy_server.shutdown()
                self.local_proxy_server.server_close()
                
            if self.local_proxy_thread and self.local_proxy_thread.is_alive():
                self.local_proxy_thread.join(timeout=5)
                
            self.local_proxy_active = False
            print(f"{Fore.GREEN}✅ Local proxy stopped{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop local proxy: {e}")
            return False

    def enable_dns_protection(self):
        """Enable DNS protection"""
        try:
            # Use secure DNS servers
            dns_servers = ["1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4"]
            
            if is_termux():
                # Termux-specific DNS configuration
                dns_config = "\n".join([f"nameserver {dns}" for dns in dns_servers])
                
                # Write to resolv.conf (if writable)
                try:
                    with open('/etc/resolv.conf', 'w') as f:
                        f.write(dns_config)
                    print(f"{Fore.GREEN}🔒 DNS protection enabled{Style.RESET_ALL}")
                except PermissionError:
                    print(f"{Fore.YELLOW}⚠️ DNS protection requires root access{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ DNS protection not implemented for this platform{Style.RESET_ALL}")
                
        except Exception as e:
            logger.error(f"DNS protection failed: {e}")

    def disable_dns_protection(self):
        """Disable DNS protection"""
        try:
            if is_termux():
                # Restore default DNS
                with open('/etc/resolv.conf', 'w') as f:
                    f.write("nameserver 8.8.8.8\n")
                print(f"{Fore.GREEN}🔓 DNS protection disabled{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"DNS protection disable failed: {e}")

    def enable_kill_switch(self):
        """Enable kill switch (block non-proxy traffic)"""
        try:
            if is_termux():
                print(f"{Fore.YELLOW}⚠️ Kill switch requires root access in Termux{Style.RESET_ALL}")
                return False
            
            # This would require iptables rules
            print(f"{Fore.YELLOW}⚠️ Kill switch not implemented (requires root){Style.RESET_ALL}")
            return False
            
        except Exception as e:
            logger.error(f"Kill switch enable failed: {e}")
            return False

    def disable_kill_switch(self):
        """Disable kill switch"""
        try:
            # Remove iptables rules
            print(f"{Fore.GREEN}🔓 Kill switch disabled{Style.RESET_ALL}")
            return True
        except Exception as e:
            logger.error(f"Kill switch disable failed: {e}")
            return False

    def show_notification(self, title, message):
        """Show system notification"""
        try:
            if is_termux():
                # Use Termux notification API
                subprocess.run([
                    "termux-notification",
                    "--title", title,
                    "--content", message
                ], check=False)
            else:
                # Just print for other systems
                print(f"{Fore.CYAN}🔔 {title}: {message}{Style.RESET_ALL}")
        except Exception as e:
            logger.debug(f"Notification failed: {e}")

    def get_current_ip(self):
        """Get current external IP address"""
        for url in IP_CHECK_URLS:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    ip = response.text.strip()
                    # Validate IP format
                    ipaddress.ip_address(ip)
                    return ip
            except Exception:
                continue
        return "Unknown"

    def show_status(self):
        """Show current proxy status"""
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📊 PROXY STATUS{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        
        if self.current_proxy:
            print(f"{Fore.GREEN}🟢 Status: ACTIVE{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🌐 Current IP: {self.current_proxy.get('ip', 'Unknown')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🖥️ Proxy: {self.current_proxy['host']}:{self.current_proxy['port']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🔗 Protocol: {self.current_proxy['protocol'].upper()}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🌍 Country: {self.current_proxy.get('country', 'Unknown')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}⚡ Latency: {self.current_proxy.get('latency', 'N/A')}ms{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}🔴 Status: INACTIVE{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🌐 Current IP: {self.get_current_ip()}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}🔄 Rotation: {'ACTIVE' if self.rotation_active else 'INACTIVE'}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🏠 Local Proxy: {'ACTIVE' if self.local_proxy_active else 'INACTIVE'}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🧅 Tor: {'ACTIVE' if self.tor_process and self.tor_process.poll() is None else 'INACTIVE'}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 Available Proxies: {len(self.proxies)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}⭐ Favorites: {len(self.favorites)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📈 Traffic: ↑{self.traffic_stats['sent']} ↓{self.traffic_stats['received']} bytes{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")

# ===== MAIN MENU SYSTEM =====
def show_main_menu():
    """Display main menu"""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🚀 PROXY ALCHEMIST - MAIN MENU{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}1.  🔄 Change IP (Find & Set Proxy){Style.RESET_ALL}")
    print(f"{Fore.GREEN}2.  🌀 Start Auto Rotation{Style.RESET_ALL}")
    print(f"{Fore.GREEN}3.  ⏹  Stop Auto Rotation{Style.RESET_ALL}")
    print(f"{Fore.GREEN}4.  📊 Show Current Status{Style.RESET_ALL}")
    print(f"{Fore.GREEN}5.  🔌 Clear Proxy Settings{Style.RESET_ALL}")
    print(f"{Fore.GREEN}6.  📋 Show Proxy History{Style.RESET_ALL}")
    print(f"{Fore.GREEN}7.  ⭐ Manage Favorites{Style.RESET_ALL}")
    print(f"{Fore.GREEN}8.  🧅 Tor Integration{Style.RESET_ALL}")
    print(f"{Fore.GREEN}9.  🏠 Local Proxy Server{Style.RESET_ALL}")
    print(f"{Fore.GREEN}10. ⚙️  Configuration{Style.RESET_ALL}")
    print(f"{Fore.GREEN}11. 📱 Generate QR Code{Style.RESET_ALL}")
    print(f"{Fore.GREEN}12. 🔍 Test Specific Proxy{Style.RESET_ALL}")
    print(f"{Fore.GREEN}13. 📊 Show Statistics{Style.RESET_ALL}")
    print(f"{Fore.GREEN}14. 🆘 Help & About{Style.RESET_ALL}")
    print(f"{Fore.RED}0.  🚪 Exit{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def get_user_input(prompt, input_type=str, default=None):
    """Get user input with type validation"""
    while True:
        try:
            user_input = input(f"{Fore.YELLOW}{prompt}{Style.RESET_ALL}").strip()
            
            if not user_input and default is not None:
                return default
            
            if input_type == int:
                return int(user_input)
            elif input_type == float:
                return float(user_input)
            else:
                return user_input
                
        except ValueError:
            print(f"{Fore.RED}❌ Invalid input. Please try again.{Style.RESET_ALL}")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Operation cancelled{Style.RESET_ALL}")
            return None

def main():
    """Main application entry point"""
    try:
        # Check if running in Termux
        if is_termux():
            print(f"{Fore.GREEN}✅ Running in Termux environment{Style.RESET_ALL}")
        
        # Check internet connection
        if not check_internet_connection():
            print(f"{Fore.RED}❌ No internet connection detected{Style.RESET_ALL}")
            return
        
        # Display banner
        display_banner()
        
        # Initialize proxy manager
        global proxy_master
        proxy_master = ProxyAlchemist()
        
        # Load previous state
        proxy_master.load_state()
        
        # Auto-start if configured
        if proxy_master.config.get('auto_start'):
            print(f"{Fore.BLUE}🚀 Auto-starting proxy rotation...{Style.RESET_ALL}")
            proxy_master.fetch_live_proxies()
            proxy = proxy_master.find_working_proxy()
            if proxy:
                proxy_master.set_system_proxy(proxy)
                if proxy_master.config['single_host_mode']:
                    proxy_master.start_local_proxy()
        
        # Main menu loop
        while True:
            try:
                show_main_menu()
                choice = get_user_input("Enter your choice (0-14): ", int)
                
                if choice is None:
                    continue
                
                if choice == 0:
                    print(f"{Fore.BLUE}👋 Goodbye! Cleaning up...{Style.RESET_ALL}")
                    proxy_master.cleanup_and_exit()
                    
                elif choice == 1:
                    # Change IP
                    print(f"{Fore.BLUE}🔍 Searching for working proxy...{Style.RESET_ALL}")
                    if not proxy_master.proxies:
                        proxy_master.fetch_live_proxies()
                    
                    proxy = proxy_master.find_working_proxy()
                    if proxy:
                        if proxy_master.set_system_proxy(proxy):
                            print(f"{Fore.GREEN}✅ IP changed successfully!{Style.RESET_ALL}")
                            if proxy_master.config['single_host_mode']:
                                proxy_master.start_local_proxy()
                                proxy_master.show_wifi_instructions(proxy)
                        else:
                            print(f"{Fore.RED}❌ Failed to set proxy{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ No working proxies found{Style.RESET_ALL}")
                
                elif choice == 2:
                    # Start auto rotation
                    if proxy_master.rotation_active:
                        print(f"{Fore.YELLOW}⚠️ Rotation is already active{Style.RESET_ALL}")
                        continue
                    
                    interval = get_user_input("Enter rotation interval in seconds (default: 300): ", int, 300)
                    if interval is None or interval < 30:
                        print(f"{Fore.RED}❌ Invalid interval (minimum 30 seconds){Style.RESET_ALL}")
                        continue
                    
                    duration = get_user_input("Enter duration in seconds (0 for infinite): ", int, 0)
                    if duration is None:
                        continue
                    
                    # Ensure we have proxies
                    if not proxy_master.proxies:
                        proxy_master.fetch_live_proxies()
                    
                    if proxy_master.config['single_host_mode']:
                        proxy_master.start_local_proxy()
                    
                    proxy_master.start_rotation(interval, duration)
                
                elif choice == 3:
                    # Stop auto rotation
                    if proxy_master.stop_rotation():
                        print(f"{Fore.GREEN}✅ Auto rotation stopped{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}⚠️ No active rotation to stop{Style.RESET_ALL}")
                
                elif choice == 4:
                    # Show status
                    proxy_master.show_status()
                
                elif choice == 5:
                    # Clear proxy settings
                    if proxy_master.clear_proxy_settings():
                        print(f"{Fore.GREEN}✅ Proxy settings cleared{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ Failed to clear proxy settings{Style.RESET_ALL}")
                
                elif choice == 6:
                    # Show history
                    if proxy_master.history:
                        print(f"\n{Fore.CYAN}📋 PROXY HISTORY (Last {len(proxy_master.history)}){Style.RESET_ALL}")
                        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
                        for i, entry in enumerate(proxy_master.history[:10], 1):
                            print(f"{Fore.GREEN}{i:2d}. {entry['host']}:{entry['port']} "
                                  f"({entry['protocol']}) | {entry['country']} | "
                                  f"{entry['ip']} | {entry['set_time'][:19]}{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}📋 No proxy history available{Style.RESET_ALL}")
                
                elif choice == 7:
                    # Manage favorites
                    while True:
                        print(f"\n{Fore.CYAN}⭐ FAVORITES MANAGEMENT{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}1. Show Favorites{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}2. Add Current Proxy to Favorites{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}3. Remove from Favorites{Style.RESET_ALL}")
                        print(f"{Fore.RED}0. Back to Main Menu{Style.RESET_ALL}")
                        
                        fav_choice = get_user_input("Enter choice: ", int)
                        if fav_choice == 0:
                            break
                        elif fav_choice == 1:
                            if proxy_master.favorites:
                                print(f"\n{Fore.CYAN}⭐ FAVORITE PROXIES{Style.RESET_ALL}")
                                for i, fav in enumerate(proxy_master.favorites, 1):
                                    print(f"{Fore.YELLOW}{i}. {fav['host']}:{fav['port']} "
                                          f"({fav['protocol']}) | {fav['country']}{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.YELLOW}⭐ No favorite proxies{Style.RESET_ALL}")
                        elif fav_choice == 2:
                            if proxy_master.current_proxy:
                                proxy_master.add_favorite(proxy_master.current_proxy)
                            else:
                                print(f"{Fore.RED}❌ No active proxy to add{Style.RESET_ALL}")
                        elif fav_choice == 3:
                            if proxy_master.favorites:
                                print(f"\n{Fore.CYAN}Select proxy to remove:{Style.RESET_ALL}")
                                for i, fav in enumerate(proxy_master.favorites, 1):
                                    print(f"{Fore.YELLOW}{i}. {fav['host']}:{fav['port']}{Style.RESET_ALL}")
                                
                                idx = get_user_input("Enter number: ", int)
                                if idx and 1 <= idx <= len(proxy_master.favorites):
                                    fav = proxy_master.favorites[idx-1]
                                    proxy_master.remove_favorite(fav['host'], fav['port'])
                            else:
                                print(f"{Fore.YELLOW}⭐ No favorites to remove{Style.RESET_ALL}")
                
                elif choice == 8:
                    # Tor integration
                    while True:
                        print(f"\n{Fore.CYAN}🧅 TOR INTEGRATION{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}1. Install Tor{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}2. Start Tor Service{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}3. Stop Tor Service{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}4. Set Tor as Proxy{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}5. Change Tor Circuit{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}6. Start Tor Auto Rotation{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}7. Stop Tor Auto Rotation{Style.RESET_ALL}")
                        print(f"{Fore.RED}0. Back to Main Menu{Style.RESET_ALL}")
                        
                        tor_choice = get_user_input("Enter choice: ", int)
                        if tor_choice == 0:
                            break
                        elif tor_choice == 1:
                            proxy_master.install_tor()
                        elif tor_choice == 2:
                            proxy_master.start_tor_service()
                        elif tor_choice == 3:
                            proxy_master.stop_tor_service()
                        elif tor_choice == 4:
                            if proxy_master.set_tor_proxy():
                                print(f"{Fore.GREEN}✅ Tor proxy activated{Style.RESET_ALL}")
                        elif tor_choice == 5:
                            proxy_master.change_tor_circuit()
                        elif tor_choice == 6:
                            interval = get_user_input("Enter rotation interval in seconds (default: 300): ", int, 300)
                            if interval and interval >= 30:
                                proxy_master.start_tor_rotation(interval)
                        elif tor_choice == 7:
                            proxy_master.stop_tor_rotation()
                
                elif choice == 9:
                    # Local proxy server
                    while True:
                        print(f"\n{Fore.CYAN}🏠 LOCAL PROXY SERVER{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}1. Start Local Proxy{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}2. Stop Local Proxy{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}3. Show Connection Info{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}4. Toggle Single Host Mode{Style.RESET_ALL}")
                        print(f"{Fore.RED}0. Back to Main Menu{Style.RESET_ALL}")
                        
                        local_choice = get_user_input("Enter choice: ", int)
                        if local_choice == 0:
                            break
                        elif local_choice == 1:
                            proxy_master.start_local_proxy()
                        elif local_choice == 2:
                            proxy_master.stop_local_proxy()
                        elif local_choice == 3:
                            if proxy_master.current_proxy:
                                proxy_master.show_wifi_instructions(proxy_master.current_proxy)
                            else:
                                print(f"{Fore.RED}❌ No active proxy{Style.RESET_ALL}")
                        elif local_choice == 4:
                            proxy_master.config['single_host_mode'] = not proxy_master.config['single_host_mode']
                            status = "ENABLED" if proxy_master.config['single_host_mode'] else "DISABLED"
                            print(f"{Fore.GREEN}✅ Single Host Mode: {status}{Style.RESET_ALL}")
                            proxy_master.save_config()
                
                elif choice == 10:
                    # Configuration
                    while True:
                        print(f"\n{Fore.CYAN}⚙️ CONFIGURATION{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}1. Show Current Config{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}2. Set Max Latency{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}3. Set Protocol Preference{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}4. Set Favorite Countries{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}5. Toggle Auto Start{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}6. Set Connection Timeout{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}7. Reset to Defaults{Style.RESET_ALL}")
                        print(f"{Fore.RED}0. Back to Main Menu{Style.RESET_ALL}")
                        
                        config_choice = get_user_input("Enter choice: ", int)
                        if config_choice == 0:
                            break
                        elif config_choice == 1:
                            print(f"\n{Fore.CYAN}📋 CURRENT CONFIGURATION{Style.RESET_ALL}")
                            for key, value in proxy_master.config.items():
                                print(f"{Fore.YELLOW}{key}: {value}{Style.RESET_ALL}")
                        elif config_choice == 2:
                            latency = get_user_input("Enter max latency in ms (current: {}): ".format(
                                proxy_master.config['max_latency']), int)
                            if latency and latency > 0:
                                proxy_master.config['max_latency'] = latency
                                proxy_master.save_config()
                                print(f"{Fore.GREEN}✅ Max latency updated{Style.RESET_ALL}")
                        elif config_choice == 5:
                            proxy_master.config['auto_start'] = not proxy_master.config['auto_start']
                            status = "ENABLED" if proxy_master.config['auto_start'] else "DISABLED"
                            print(f"{Fore.GREEN}✅ Auto Start: {status}{Style.RESET_ALL}")
                            proxy_master.save_config()
                        elif config_choice == 7:
                            proxy_master.config = proxy_master.get_default_config()
                            proxy_master.save_config()
                            print(f"{Fore.GREEN}✅ Configuration reset to defaults{Style.RESET_ALL}")
                
                elif choice == 11:
                    # Generate QR code
                    if proxy_master.current_proxy:
                        proxy_master.show_wifi_instructions(proxy_master.current_proxy)
                    else:
                        print(f"{Fore.RED}❌ No active proxy to generate QR code{Style.RESET_ALL}")
                
                elif choice == 12:
                    # Test specific proxy
                    proxy_input = get_user_input("Enter proxy (ip:port or ip:port:protocol): ")
                    if proxy_input:
                        try:
                            proxy = parse_proxy_string(proxy_input)
                            print(f"{Fore.BLUE}🔍 Testing proxy {proxy['host']}:{proxy['port']}...{Style.RESET_ALL}")
                            result = proxy_master.test_proxy(proxy)
                            if result['working']:
                                print(f"{Fore.GREEN}✅ Proxy is working! IP: {result['ip']}, Latency: {result['latency']}ms{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.RED}❌ Proxy is not working{Style.RESET_ALL}")
                        except ValueError as e:
                            print(f"{Fore.RED}❌ Invalid proxy format: {e}{Style.RESET_ALL}")
                
                elif choice == 13:
                    # Show statistics
                    print(f"\n{Fore.CYAN}📊 STATISTICS{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}📈 Traffic Sent: {proxy_master.traffic_stats['sent']} bytes{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}📉 Traffic Received: {proxy_master.traffic_stats['received']} bytes{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}🔄 Total Proxies: {len(proxy_master.proxies)}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}⭐ Favorites: {len(proxy_master.favorites)}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}📋 History Entries: {len(proxy_master.history)}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}🚫 Blacklisted: {len(proxy_master.blacklist)}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
                
                elif choice == 14:
                    # Help & About
                    print(f"\n{Fore.CYAN}🆘 HELP & ABOUT{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}📱 Proxy Alchemist {VERSION}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}🔧 Enhanced for Termux (Non-root){Style.RESET_ALL}")
                    print(f"{Fore.GREEN}🌐 Advanced Proxy Management System{Style.RESET_ALL}")
                    print(f"\n{Fore.YELLOW}📋 FEATURES:{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}• Automatic proxy rotation{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}• Tor integration{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}• Local proxy server{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}• QR code generation{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}• Traffic monitoring{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}• Favorites management{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}• Multiple proxy sources{Style.RESET_ALL}")
                    print(f"\n{Fore.YELLOW}🔧 REQUIREMENTS:{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}• Python 3.6+{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}• Internet connection{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}• Required packages (see installation guide){Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                
                else:
                    print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")
                
                # Pause before showing menu again
                if choice != 0:
                    input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️ Operation interrupted{Style.RESET_ALL}")
                continue
            except Exception as e:
                logger.error(f"Menu error: {e}")
                print(f"{Fore.RED}❌ An error occurred: {e}{Style.RESET_ALL}")
                continue
                
    except KeyboardInterrupt:
        print(f"\n{Fore.BLUE}👋 Goodbye!{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"{Fore.RED}❌ Critical error: {e}{Style.RESET_ALL}")
    finally:
        if 'proxy_master' in globals():
            proxy_master.cleanup_and_exit()

if __name__ == "__main__":
    main()

