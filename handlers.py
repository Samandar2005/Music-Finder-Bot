import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import log_user_interaction, log_search, get_monthly_stats
from utils import search_by_lyrics_or_name, download_youtube_to_mp3


async def start(update: Update, context: CallbackContext) -> None:
    """Boshlang'ich xabar."""
    user = update.effective_user
    log_user_interaction(user)
    await update.message.reply_text(
        "Xush kelibsiz! Siz:\n"
        "- Qo'shiq nomi yoki qo'shiqchining ismini kiriting.\n"
        "- Yoki YouTube URL yuboring, men qo'shiqni MP3 formatda yuklab olaman.\n\n"
        "Harakat qilib ko'ring!"
    )


async def handle_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    song_results = context.user_data.get('song_results', {})
    selected_song = song_results.get(query.data)

    if selected_song:
        url = selected_song['url']
        await query.message.reply_text("MP3 formatda yuklanmoqda...")
        mp3_file = download_youtube_to_mp3(url)
        if mp3_file and os.path.exists(mp3_file):
            try:
                await query.message.reply_document(
                    open(mp3_file, "rb"), filename=os.path.basename(mp3_file)
                )
            finally:
                os.remove(mp3_file)
        else:
            await query.message.reply_text("Yuklab olishda xatolik yuz berdi.")
    else:
        await query.message.reply_text("Tanlangan qo'shiq topilmadi.")


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Foydalanuvchi yuborgan xabarni qayta ishlash."""
    user = update.effective_user
    query = update.message.text.strip()

    log_user_interaction(user)
    log_search(user.id, query)

    if query.startswith(("http://", "https://")) and ("youtube.com" in query or "youtu.be" in query):
        await download_from_url(update, context)
    else:
        await search_song(update, context)


async def search_song(update: Update, context: CallbackContext) -> None:
    """Foydalanuvchining so'roviga asoslangan qo'shiqni qidirish."""
    query = update.message.text.strip()
    if not query:
        await update.message.reply_text("Iltimos, qo'shiq yoki qo'shiqchi ismini kiriting.")
        return

    await update.message.reply_text(f"Qidirilmoqda: {query}")

    results = search_by_lyrics_or_name(query)
    if results:
        keyboard = [
            [InlineKeyboardButton(f"{song['title']} - {song['artist']}", callback_data=str(i))]
            for i, song in enumerate(results)
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.user_data['song_results'] = {str(i): song for i, song in enumerate(results)}

        await update.message.reply_text("Topilgan qo'shiqlar:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Hech qanday qo'shiq topilmadi. Iltimos, boshqa kalit so'zlarni sinab ko'ring.")


async def download_from_url(update: Update, context: CallbackContext) -> None:
    """Foydalanuvchi yuborgan URL orqali qo'shiqni yuklab olish."""
    url = update.message.text.strip()

    await update.message.reply_text("Qo'shiq MP3 formatda yuklanmoqda...")

    mp3_file = download_youtube_to_mp3(url)
    if mp3_file and os.path.exists(mp3_file):
        try:
            await update.message.reply_document(
                open(mp3_file, "rb"), filename=os.path.basename(mp3_file)
            )
        finally:
            os.remove(mp3_file)
    else:
        await update.message.reply_text(
            "Yuklab olishda xatolik yuz berdi. Iltimos, boshqa URL sinab ko'ring."
        )


async def statistics(update: Update, context: CallbackContext) -> None:
    """Statistikani chiqarish."""
    stats = get_monthly_stats()
    await update.message.reply_text(
        f"Oylik statistika:\n"
        f"- So'rovlar soni: {stats['search_count']}\n"
        f"- Faol foydalanuvchilar soni: {stats['active_users']}"
    )
