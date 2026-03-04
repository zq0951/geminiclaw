#!/usr/bin/env python3
import argparse
import subprocess
import os
import time
import json
import shutil

# 默认保存路径
MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

def check_env():
    """Check if ffmpeg and the device exist."""
    if not shutil.which("ffmpeg"):
        return False, "ffmpeg command not found. Please install it with 'sudo apt install ffmpeg'."
    return True, None

def take_snapshot(device="/dev/video0", resolution="3840x2160"):
    """使用 ffmpeg 从指定设备截取一张图片"""
    ok, err = check_env()
    if not ok: return {"status": "error", "message": err}
    
    if not os.path.exists(device):
        return {"status": "error", "message": f"Device {device} not found."}

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(MEDIA_DIR, f"snapshot_{timestamp}.jpg")
    
    cmd = [
        "ffmpeg", "-y", "-f", "v4l2", "-video_size", resolution, 
        "-i", device, "-frames:v", "1", "-q:v", "2", output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return {"status": "success", "file": output_path, "type": "image"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr.decode()}

def record_video(device="/dev/video0", resolution="3840x2160", duration=5, fps=30):
    """录制指定时长的视频"""
    ok, err = check_env()
    if not ok: return {"status": "error", "message": err}
    
    if not os.path.exists(device):
        return {"status": "error", "message": f"Device {device} not found."}

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(MEDIA_DIR, f"record_{timestamp}.mp4")
    
    cmd = [
        "ffmpeg", "-y", "-f", "v4l2", "-video_size", resolution, "-framerate", str(fps),
        "-i", device, "-t", str(duration), "-c:v", "libx264", "-preset", "ultrafast", output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return {"status": "success", "file": output_path, "type": "video"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr.decode()}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="4K USB Camera Skill")
    parser.add_argument("action", choices=["snapshot", "record"], help="Action to perform")
    parser.add_argument("--device", default="/dev/video0", help="Camera device path")
    parser.add_argument("--resolution", default="3840x2160", help="Camera resolution")
    parser.add_argument("--duration", type=int, default=5, help="Video recording duration in seconds")
    
    args = parser.parse_args()
    
    if args.action == "snapshot":
        result = take_snapshot(args.device, args.resolution)
    else:
        result = record_video(args.device, args.resolution, args.duration)
        
    print(json.dumps(result, indent=2))
