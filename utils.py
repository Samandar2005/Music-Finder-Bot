import os
import re
import requests
from youtubesearchpython import VideosSearch
import yt_dlp

LASTFM_API_KEY = "860f748cd287d0e9e9858f6ee3163347"

def sanitize_filename(name: str) -> str:
    """Fayl nomidagi noqonuniy belgilarni tozalash."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def search_by_lyrics_or_name(query: str) -> list:
    """So'rov bo'yicha qo'shiqlarni qidiradi."""
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

    # Agar Last.fm natija bermasa, YouTube orqali qidirish
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
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            track_title = sanitize_filename(info_dict.get("title", "downloaded_song"))
            output_file = f"{track_title}.mp3"

            ydl_opts['outtmpl'] = output_file
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                ydl_download.download([url])

            if os.path.exists(output_file):
                return output_file
    except yt_dlp.utils.DownloadError as e:
        print(f"Yuklab olishda xatolik: {e}")
    return None
