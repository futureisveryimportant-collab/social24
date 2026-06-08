import os
import shutil
import threading
import time
import requests
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from yt_dlp import YoutubeDL

app = FastAPI(title="Universal Master Downloader API")

# --- ১. জিরো স্টোরেজ মেকানিজম (অটো-ক্লিন) ---
def clean_storage():
    """সার্ভারের ক্যাশ এবং টেম্প ফোল্ডার সবসময় খালি রাখে"""
    temp_dir = './temp_downloads'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

# --- ২. অ্যান্টি-স্লিপ (সার্ভারকে অমর করে রাখা) ---
def keep_alive():
    """রেন্ডারকে ঘুমাতে না দেওয়ার জন্য ১০ মিনিট পর পর অটো-পিং"""
    app_url = os.getenv("RENDER_EXTERNAL_URL")
    if not app_url: return
    while True:
        try:
            # নিজের হোম পেজে রিকোয়েস্ট পাঠানো
            requests.get(app_url, timeout=10)
            print("Server Activity: Keeping the engine awake!")
        except:
            pass
        time.sleep(600) # ১০ মিনিট

@app.on_event("startup")
async def startup_event():
    clean_storage()
    threading.Thread(target=keep_alive, daemon=True).start()

# --- ৩. মূল ইউনিভার্সাল এপিআই লজিক ---
@app.get("/")
def home():
    return {"status": "Online", "engine": "Universal Master Downloader ready."}

@app.get("/download")
async def universal_api(
    url: str = Query(..., description="Video URL from any platform"),
    format: str = Query("mp4", description="Output format: mp4 or mp3"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # রিকোয়েস্ট শেষ হলে ব্যাকগ্রাউন্ডে স্টোরেজ ক্লিন করবে
    background_tasks.add_task(clean_storage)

    # yt-dlp প্রফেশনাল কনফিগারেশন
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo+bestaudio/best', # সর্বোচ্চ কোয়ালিটি নিশ্চিত করে
        'noplaylist': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # মেটাডেটা এবং ডিরেক্ট লিঙ্ক এক্সট্রাক্ট করা
            info = ydl.extract_info(url, download=False)
            
            # অডিও লিঙ্ক গ্র্যাব করার নিরাপদ লজিক
            formats = info.get('formats', [])
            audio_url = next(
                (f['url'] for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none'),
                info.get('url') # যদি আলাদা অডিও না থাকে তবে মেইন লিঙ্ক
            )

            # প্রফেশনাল আউটপুট রেসপন্স
            return {
                "status": "success",
                "platform": info.get('extractor_key'),
                "metadata": {
                    "title": info.get('title'),
                    "author": info.get('uploader') or info.get('uploader_id'),
                    "thumbnail": info.get('thumbnail'),
                    "duration_seconds": info.get('duration'),
                    "stats": {
                        "views": info.get('view_count', 0),
                        "likes": info.get('like_count', 0)
                    }
                },
                "download_info": {
                    "format_requested": format,
                    "quality": "Best Available (HD/4K)",
                    "download_link": audio_url if format == "mp3" else info.get('url')
                },
                "server_status": "Storage Cleaned / Active"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": "Platform not supported or Invalid URL",
            "details": str(e)
        }
