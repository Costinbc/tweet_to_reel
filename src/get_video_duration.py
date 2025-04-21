import subprocess
import json

def get_video_duration(path):
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "json",
        path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        return duration
    except Exception:
        return 0.0

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python get_video_duration.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    duration = get_video_duration(video_path)
    print(f"Video duration: {duration} seconds")