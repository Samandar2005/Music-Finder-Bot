import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, filters
import requests
import yt_dlp

# API kalitlar
LASTFM_API_KEY = "860f748cd287d0e9e9858f6ee3163347"
GENIUS_API_KEY = "VCIqD0Sm6UPxM5Xkgrtg3ZqrNjilsXMpqLNUjN2FrOHA6ODl65r8NgKQOntg8399exOL2apvcIn96D5N-iVdyg"

# Qo'shiqlar ro'yxatini saqlash uchun vaqtinchalik xotira
song_results = {}


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Xush kelibsiz! Siz:\n"
        "- Qo'shiq nomi yoki qo'shiqchining ismini kiriting.\n"
        "- Mos qo'shiqlarni qidiring.\n"
        "- Qo'shiqni tanlab, MP3 formatda yuklab oling.\n\n"
        "Harakat qilib ko'ring!"
    )


async def search_song(update: Update, context: CallbackContext) -> None:
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
        os.remove(mp3_file)
    else:
        await query.message.reply_text(
            "MP3 formatda yuklab olishda xatolik yuz berdi. Iltimos, boshqa qo'shiqni sinab ko'ring."
        )

def search_by_lyrics_or_name(query: str) -> list:
    """
    So'rov bo'yicha qo'shiqlarni qidiradi (Last.fm yoki Genius).
    Mos keladigan qo'shiqlarning ro'yxatini qaytaradi.
    """
    results = []

    # Last.fm API orqali qidirish
    lastfm_url = (
        f"http://ws.audioscrobbler.com/2.0/?method=track.search&track={query}"
        f"&api_key={LASTFM_API_KEY}&format=json"
    )
    response = requests.get(lastfm_url).json()

    if response['results']['trackmatches']['track']:
        tracks = response['results']['trackmatches']['track']
        results.extend(
            {"title": track["name"], "artist": track["artist"], "url": track["url"]}
            for track in tracks[:5]
        )

    return results


def download_youtube_to_mp3(url: str) -> str:
    """
    YouTube video URL'ini MP3 formatga yuklab oladi.
    """
    output_file = "downloaded_song.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_file,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Videoni yuklab olish
            info_dict = ydl.extract_info(url, download=False)
            if 'is_live' in info_dict and info_dict['is_live']:
                print("Ushbu video jonli efir, o'tkazib yuborilmoqda.")
                return None
            ydl.download([url])
        # Fayl mavjudligini tekshirish
        if os.path.exists(output_file):
            return output_file
        else:
            print("Yuklab olish muvaffaqiyatsiz.")
            return None
    except yt_dlp.utils.DownloadError as e:
        print(f"Yuklab olishda xatolik: {e}")
        return None


def main():
    application = Application.builder().token("7573018273:AAH8_XtkleOY566-VJ8jsZipgLOTpGQBwvI").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, search_song))
    application.add_handler(CallbackQueryHandler(download_mp3))

    application.run_polling()


if __name__ == "__main__":
    main()
