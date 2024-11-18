import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from utils import search_by_lyrics_or_name, download_youtube_to_mp3
from database import get_monthly_stats, log_search, log_user_interaction
song_results = {}


async def start(update: Update, context: CallbackContext) -> None:
    """Boshlang'ich xabar va tugmalar."""
    user = update.effective_user

    log_user_interaction(user)

    # Reply tugmalarni yaratish
    keyboard = [["Start"]]  # Faqat Start tugmasi
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    # Tugma bilan xabar yuborish
    await update.message.reply_text(
        f"🎵 Salom, {user.first_name}! 🎶\n\n"
        "Bo'riyev Samandarning **Music Finder Bot**-iga xush kelibsiz! 🎉\n"
        "Endi sizga eng sevimli qo'shiqlaringizni topish va yuklab olishda yordam beraman! 🎧\n\n"
        "Qo'shiqni izlash uchun 'Start' tugmasini bosing va musiqa sayohatingizni boshlang! 🚀",
        reply_markup=reply_markup
    )


async def handle_start_command(update: Update, context: CallbackContext) -> None:
    """Start tugmasini bosganda yuboriladigan xabar."""

    keyboard = [["Statistika"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text(
        "Salom, musiqasevar! 🎶\n\n"
        "Menga sizga qo'shiqni topish uchun yordam bera olaman. Menga:\n"
        "- Qo'shiq nomini yoki ijrochi ismini yozing.\n"
        "- Yoki YouTube'dan URL yuboring, men siz uchun qo'shiqni MP3 formatda tayyorlayman.\n\n"
        "Endi qanday qilib musiqaning haqiqiy sehrini sezishni boshlaysiz? 😉",
        reply_markup=reply_markup
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

        # Har bir qo'shiqni bazaga saqlash
        for song in results:
            # Har bir qo'shiqni "searches" jadvaliga qo'shish
            log_search(update.effective_user.id, song['title'])

        await update.message.reply_text("Topilgan qo'shiqlar:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Hech qanday qo'shiq topilmadi. Iltimos, boshqa kalit so'zlarni sinab ko'ring.")


async def download_from_url(update: Update, context: CallbackContext) -> None:
    """Foydalanuvchi yuborgan URL orqali qo'shiqni yuklab olish."""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    log_search(user_id, url)

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
    stats = get_monthly_stats()  # Haqiqiy statistikani olish
    if stats:
        await update.message.reply_text(
            f"🎉 *Oylik statistikangiz*:\n\n"
            f"🔍 *So'rovlar soni*: {stats['search_count']} ta qo'shiqni izlashdi!\n"
            f"👥 *Faol foydalanuvchilar*: {stats['active_users']} ta musiqa ixlosmandi hali ham botdan foydalanmoqda!\n\n"
            "Agar ko'proq musiqa kashf etmoqchi bo'lsangiz, davom eting! 🎶"
        )
    else:
        await update.message.reply_text("Statistika olishda xatolik yuz berdi.")

