import os
import re
import requests
from youtubesearchpython import VideosSearch
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")


def sanitize_filename(name: str) -> str:
    """Fayl nomidagi noqonuniy belgilarni tozalash."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def search_by_lyrics_or_name(query: str) -> list:
    """
    So'rov bo'yicha qo'shiqlarni qidiradi (Last.fm va YouTube orqali).
    Mos keladigan qo'shiqlarning ro'yxatini qaytaradi.
    """
    results = []

    # Last.fm API orqali qidirish
    lastfm_url = (
        f"http://ws.audioscrobbler.com/2.0/?method=track.search&track={query}"
        f"&api_key={LASTFM_API_KEY}&format=json"
    )
    response = requests.get(lastfm_url).json()

    if 'results' in response and 'trackmatches' in response['results']:
        tracks = response['results']['trackmatches'].get('track', [])
        if not isinstance(tracks, list):
            tracks = [tracks]
        results.extend(
            {"title": track["name"], "artist": track["artist"],
             "url": get_youtube_url(f"{track['name']} {track['artist']}")}
            for track in tracks[:5]
        )

    # Agar Last.fm natija bermasa, YouTube orqali qidiring
    if not results:
        youtube_url = get_youtube_url(query)
        if youtube_url:
            results.append({"title": query, "artist": "YouTube", "url": youtube_url})

    return results


def get_youtube_url(query: str) -> str:
    """YouTube'dan so'rov bo'yicha birinchi video URL'ini qaytaradi."""
    try:
        videos_search = VideosSearch(query, limit=1)
        result = videos_search.result()
        if result["result"]:
            return result["result"][0]["link"]
    except Exception as e:
        print(f"YouTube URL qidirishda xatolik: {e}")
    return None


def download_youtube_to_mp3(url: str) -> str:
    """
    YouTube URL ni yuklab olib, qo'shiqni MP3 formatida saqlaydi.
    """
    if not url:
        print("Ogohlantirish: URL qiymati yo'q.")
        return None

    # Yuklab olish sozlamalari
    options = {
        'format': 'bestaudio/best',
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
        ],
        'outtmpl': '%(title)s.%(ext)s',  # Fayl nomi qo'shiq nomi bilan belgilanadi
        'noplaylist': True,  # Faqat bitta videoni yuklab olish
        'quiet': True,  # Loglarni minimallashtirish
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info_dict).replace(".webm", ".mp3").replace(".m4a", ".mp3")

            # Fayl nomini sanitizatsiya qilish
            sanitized_name = sanitize_filename(file_name)
            if sanitized_name != file_name:
                os.rename(file_name, sanitized_name)

            return sanitized_name
    except yt_dlp.utils.DownloadError as e:
        print(f"Yuklab olishda xatolik: {e}")
    return None