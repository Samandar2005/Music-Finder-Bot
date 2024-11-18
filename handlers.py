import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from utils import search_by_lyrics_or_name, download_youtube_to_mp3

song_results = {}


async def start(update: Update, context: CallbackContext) -> None:
    """Boshlang'ich xabar."""
    user = update.effective_user
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


async def statistics(update: Update, context: CallbackContext) -> None:
    """Statistikani chiqarish."""
    stats = {"search_count": 10, "active_users": 5}  # replace with real logic to fetch stats
    await update.message.reply_text(
        f"Oylik statistika:\n"
        f"- So'rovlar soni: {stats['search_count']}\n"
        f"- Faol foydalanuvchilar soni: {stats['active_users']}"
    )
