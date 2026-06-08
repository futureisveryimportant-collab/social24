import os
import shutil
import threading
import time
import requests
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from yt_dlp import YoutubeDL

app = FastAPI(title="Ultimate Universal Downloader")

# স্টোরেজ ক্লিনার
def clean_storage():
    temp_dir = './temp_downloads'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

# অ্যান্টি-স্লিপ
def keep_alive():
    app_url = os.getenv("RENDER_EXTERNAL_URL")
    if not app_url: return
    while True:
        try:
            requests.get(app_url, timeout=10)
        except: pass
        time.sleep(600)

@app.on_event("startup")
async def startup_event():
    clean_storage()
    threading.Thread(target=keep_alive, daemon=True).start()

@app.get("/")
def home():
    return {"status": "Online", "engine": "Universal Master Engine Active"}

@app.get("/download")
async def download_api(
    url: str = Query(..., description="Video URL"),
    format: str = Query("mp4", description="mp4 or mp3"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    background_tasks.add_task(clean_storage)

    # অত্যন্ত শক্তিশালী কনফিগারেশন
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'noplaylist': True,
        'extract_flat': False,
        # এই হেডারগুলো ফেসবুক ও ইউটিউবের জন্য গুরুত্বপূর্ণ
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
        },
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'geo_bypass': True, # লোকাল ব্লকিং এড়াতে
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # সরাসরি ইনফরমেশন এক্সট্রাক্ট করা
            info = ydl.extract_info(url, download=False)
            
            # প্রফেশনাল রেসপন্স তৈরি
            return {
                "status": "success",
                "platform": info.get('extractor_key'),
                "metadata": {
                    "title": info.get('title'),
                    "thumbnail": info.get('thumbnail'),
                    "duration": info.get('duration'),
                    "uploader": info.get('uploader') or info.get('uploader_id')
                },
                "download_link": info.get('url'),
                "note": "If link doesn't work, ensure the video is public."
            }

    except Exception as e:
        return {
            "status": "error",
            "message": "Platform security blocked the request or invalid URL.",
            "details": str(e)
        }
