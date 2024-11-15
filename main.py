import asyncio
import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from yt_dlp import YoutubeDL
import config  # config.py faylidan import qilish
from aiogram import F, Router
from aiogram.types import InputFile

router = Router()

# Telegram Bot token va Last.fm API key
BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
LASTFM_API_KEY = config.LASTFM_API_KEY
LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/"

# Botni yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(lambda message: message.text.startswith("http"))
async def download_command(message: types.Message):
    youtube_url = message.text
    try:
        await message.answer("Musiqa yuklanmoqda... ⏳")
        mp3_file = download_mp3(youtube_url)

        # Audio faylni InputFile sifatida yuborish
        audio = InputFile(mp3_file)  # Faylni InputFile sifatida o'zgartirish
        await message.answer_audio(audio, caption="Mana MP3 formatdagi musiqangiz!")
        os.remove(mp3_file)  # Faylni o'chirish
    except Exception as e:
        await message.answer(f"Yuklashda xatolik yuz berdi: {e}")

# Qo'shiq qidirish funksiyasi
def search_song(artist_or_lyrics):
    params = {
        "method": "track.search",
        "track": artist_or_lyrics,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }
    response = requests.get(LASTFM_API_URL, params=params)
    data = response.json()
    tracks = data.get("results", {}).get("trackmatches", {}).get("track", [])
    return tracks[:5]  # Birinchi 5 ta qo'shiqni qaytaradi


# MP3 yuklash funksiyasi
def download_mp3(youtube_url, output_file="downloaded_music.mp3"):
    # Ensure the directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "outtmpl": output_file,
        "ffmpeg_location": "D:\\ffmpeg\\bin\\ffmpeg.exe",  # Path to ffmpeg
        "geo_bypass": True,  # To bypass geographical restrictions
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([youtube_url])
        except Exception as e:
            if 'Video unavailable' in str(e):
                raise Exception("Video unavailable. It may be private, age-restricted, or region-blocked.")
            else:
                raise Exception(f"Video download error: {e}")

    return output_file
    return output_file
def check_video_validity(url):
    try:
        response = requests.head(url)
        if response.status_code == 200:
            print("Video mavjud!")
        else:
            print("Video topilmadi yoki cheklangan.")
            raise Exception("Video topilmadi yoki cheklangan.")
    except requests.exceptions.RequestException as e:
        print(f"Xatolik: {e}")
        raise Exception(f"Xatolik: {e}")




# /start komandasi
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Salom! Qo'shiqni qidirish uchun matn yoki qo'shiqchi ismini yuboring.\nYouTube link yuborsangiz, musiqani MP3 formatda yuklab beraman!")


@dp.message(lambda message: not message.text.startswith("http"))
async def search_command(message: types.Message):
    query = message.text
    songs = search_song(query)
    if not songs:
        await message.answer("Qo'shiq topilmadi 😞. Boshqa matnni kiriting.")
    else:
        # Tugmalarni yaratish
        buttons = [
            [InlineKeyboardButton(
                text=f"{song['name']} - {song['artist']}",
                callback_data=f"song_{i}"  # Har bir qo'shiq uchun unikal identifikator
            )]
            for i, song in enumerate(songs)
        ]
        # InlineKeyboardMarkup yaratish
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Foydalanuvchiga xabar yuborish
        await message.answer("Topilgan qo'shiqlar:\nTanlash uchun ustiga bosing:", reply_markup=keyboard)

        # Qo‘shiqlarni keyinchalik yuklab olish uchun saqlash
        global song_data
        song_data = {f"song_{i}": song for i, song in enumerate(songs)}

# Inline tugma bosilganda yuklash
@dp.callback_query(lambda call: call.data.startswith("song_"))
async def handle_song_download(callback_query: types.CallbackQuery):
    song_id = callback_query.data
    print(f"Received song_id: {song_id}")  # Debug xabari
    song = song_data.get(song_id)

    if song:
        print(f"Song found: {song}")  # Debug xabari
        youtube_url = song.get("url")
        if youtube_url:
            try:
                await callback_query.message.answer("Musiqa yuklanmoqda... ⏳")
                mp3_file = download_mp3(youtube_url)
                with open(mp3_file, "rb") as audio:
                    await callback_query.message.answer_audio(audio, caption="Mana MP3 formatdagi musiqangiz!")
                os.remove(mp3_file)
            except Exception as e:
                await callback_query.message.answer(f"Yuklashda xatolik yuz berdi: {e}")
        else:
            await callback_query.message.answer("YouTube URL topilmadi.")
    else:
        await callback_query.message.answer("Xato: Qo'shiq topilmadi.")


# Inline tugma bosilganda yuklash
@dp.callback_query(lambda call: call.data.startswith("download:"))
async def callback_download(call: types.CallbackQuery):
    youtube_url = call.data.split("download:")[1]
    try:
        await call.message.answer("Musiqa yuklanmoqda... ⏳")
        mp3_file = download_mp3(youtube_url)
        with open(mp3_file, "rb") as audio:
            await call.message.answer_audio(audio, caption="Mana MP3 formatdagi musiqangiz!")
        os.remove(mp3_file)  # Faylni o'chirish
    except Exception as e:
        await call.message.answer(f"Yuklashda xatolik yuz berdi: {e}")


# YouTube link orqali musiqa yuklash
def download_mp3(youtube_url, output_file="downloaded_music.mp3"):
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "outtmpl": output_file,
        "ffmpeg_location": "D:\\ffmpeg\\bin\\ffmpeg.exe",  # ffmpeg joylashuvini ko'rsatish
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([youtube_url])
        except Exception as e:
            raise Exception(f"Video yuklab olishda xatolik yuz berdi: {e}")
    return output_file

def check_video_validity(url):
    try:
        response = requests.head(url)
        if response.status_code == 200:
            print("Video mavjud!")
        else:
            print("Video topilmadi yoki cheklangan.")
    except requests.exceptions.RequestException as e:
        print(f"Xatolik: {e}")


# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
