import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, filters
import requests
import yt_dlp
import re
from youtubesearchpython import VideosSearch

# API kalitlari
LASTFM_API_KEY = "860f748cd287d0e9e9858f6ee3163347"

# Qo'shiqlar ro'yxatini saqlash uchun vaqtinchalik xotira
song_results = {}


def sanitize_filename(name: str) -> str:
    """Fayl nomidagi noqonuniy belgilarni tozalash."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


async def start(update: Update, context: CallbackContext) -> None:
    """Botning boshlang'ich xabari."""
    await update.message.reply_text(
        "Xush kelibsiz! Siz:\n"
        "- Qo'shiq nomi yoki qo'shiqchining ismini kiriting.\n"
        "- Yoki YouTube URL yuboring, men qo'shiqni MP3 formatda yuklab olaman.\n\n"
        "Harakat qilib ko'ring!"
    )


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Foydalanuvchi yuborgan xabarni tekshirib, mos funksiya chaqiradi."""
    query = update.message.text.strip()

    # Agar URL bo'lsa, uni yuklab olishga urinadi
    if query.startswith(("http://", "https://")) and ("youtube.com" in query or "youtu.be" in query):
        await download_from_url(update, context)
    else:
        # Aks holda qo'shiqni qidiradi
        await search_song(update, context)


async def search_song(update: Update, context: CallbackContext) -> None:
    """Foydalanuvchining so'roviga asoslangan qo'shiqni qidirish."""
    query = update.message.text.strip()
    if not query:
        await update.message.reply_text("Iltimos, qo'shiq yoki qo'shiqchi ismini kiriting.")
        return

    await update.message.reply_text(f"Qidirilmoqda: {query}")

    # Qo'shiqlarni qidirish
    results = search_by_lyrics_or_name(query)
    if results:
        # Inline tugmalar bilan qo'shiq ro'yxati
        keyboard = [
            [InlineKeyboardButton(f"{song['title']} - {song['artist']}", callback_data=str(i))]
            for i, song in enumerate(results)
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Qo'shiq ro'yxatini saqlash
        global song_results
        song_results = {str(i): song for i, song in enumerate(results)}

        await update.message.reply_text("Topilgan qo'shiqlar:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Hech qanday qo'shiq topilmadi. Iltimos, boshqa kalit so'zlarni sinab ko'ring.")


async def download_from_url(update: Update, context: CallbackContext) -> None:
    """Foydalanuvchi yuborgan URL orqali qo'shiqni yuklab olish."""
    url = update.message.text.strip()

    await update.message.reply_text("Qo'shiq MP3 formatda yuklanmoqda...")

    # YouTube URL'ni yuklab olish
    mp3_file = download_youtube_to_mp3(url)
    if mp3_file:
        await update.message.reply_document(
            open(mp3_file, "rb"), filename=os.path.basename(mp3_file)
        )
        os.remove(mp3_file)  # Yuklab olingan faylni o'chirish
    else:
        await update.message.reply_text(
            "Yuklab olishda xatolik yuz berdi. Iltimos, boshqa URL sinab ko'ring."
        )


async def download_mp3(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    song_id = query.data
    song = song_results.get(song_id)

    if not song:
        await query.message.reply_text("Qo'shiq ma'lumotlari topilmadi.")
        return

    await query.message.reply_text(f"{song['title']} - {song['artist']} MP3 yuklanmoqda...")

    mp3_file = download_youtube_to_mp3(song["url"])
    if mp3_file:
        await query.message.reply_document(
            open(mp3_file, "rb"), filename=os.path.basename(mp3_file)
        )
        os.remove(mp3_file)  # Faylni o‘chirib tashlash
    else:
        await query.message.reply_text(
            "MP3 formatda yuklab olishda xatolik yuz berdi. Iltimos, boshqa qo'shiqni sinab ko'ring."
        )


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
    YouTube URL ni yuklab olib, qo'shiqning haqiqiy nomi bilan saqlaydi.
    """
    if not url:
        print("Ogohlantirish: URL qiymati yo'q.")
        return None

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            track_title = info_dict.get("title", "downloaded_song")
            track_title = sanitize_filename(track_title)
            output_file = f"{track_title}.mp3"

            ydl_opts['outtmpl'] = track_title
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                ydl_download.download([url])

            if os.path.exists(output_file):
                return output_file
    except yt_dlp.utils.DownloadError as e:
        print(f"Yuklab olishda xatolik: {e}")
    return None


def main():
    """Botni ishga tushirish."""
    application = Application.builder().token("7573018273:AAH8_XtkleOY566-VJ8jsZipgLOTpGQBwvI").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(download_mp3))

    application.run_polling()


if __name__ == "__main__":
    main()
