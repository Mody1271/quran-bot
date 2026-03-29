import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = os.getenv("TOKEN")

ADMIN_ID = 123456789  # 👈 حط ايديك
DEV_USERNAME = "YourUsername"

# --------- تخزين ---------
user_reader = {}
user_page = {}
user_surah = {}
user_counter = {}
user_points = {}
users = set()

READERS = {
    "husary": "الحصري",
    "abdulbasit": "عبد الباسط",
    "minshawi": "المنشاوي",
    "qhtani": "ياسر القحطاني",
    "dossary": "ياسر الدوسري",
    "qattami": "ناصر القطامي"
}

AZKAR = [
    "سبحان الله",
    "الحمد لله",
    "الله أكبر",
    "لا إله إلا الله",
    "أستغفر الله",
    "اللهم صل على محمد"
]

broadcast_mode = {}

# --------- أدوات ---------
def add_points(user_id, amount=1):
    user_points[user_id] = user_points.get(user_id, 0) + amount

# --------- واجهات ---------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 القرآن", callback_data="quran")],
        [InlineKeyboardButton("🔊 القارئ", callback_data="reader")],
        [InlineKeyboardButton("🧿 أذكار", callback_data="azkar")],
        [InlineKeyboardButton("🏆 نقاطي", callback_data="points")],
        [InlineKeyboardButton("👑 المطور", url=f"https://t.me/{DEV_USERNAME}")]
    ])

def readers_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"reader_{k}")]
        for k, name in READERS.items()
    ] + [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]])

def azkar_menu(uid):
    count = user_counter.get(uid, 0)
    zekr = AZKAR[count % len(AZKAR)]
    return zekr, InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📿 {count}", callback_data="tasbeeh")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
    ])

# --------- أوامر ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name

    users.add(uid)
    add_points(uid, 1)

    await update.message.reply_text(
        f"🤍 أهلا يا {name}\n\nبوت نور القرآن\n\n"
        "👑 تطوير: أحمد المهدي - قنا الحجيرات",
        reply_markup=main_menu()
    )

# --------- القرآن ---------
async def send_ayat(query, uid):
    surah = user_surah.get(uid, "1")
    page = user_page.get(uid, 0)

    url = f"https://api.alquran.cloud/v1/surah/{surah}"
    data = requests.get(url).json()

    ayat = data["data"]["ayahs"]
    selected = ayat[page*10:(page*10)+10]

    text = "\n\n".join([f"{a['numberInSurah']}. {a['text']}" for a in selected])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️", callback_data="prev"),
             InlineKeyboardButton("➡️", callback_data="next")],
            [InlineKeyboardButton("🔊 صوت", callback_data="audio")],
            [InlineKeyboardButton("🔙", callback_data="back")]
        ])
    )

# --------- الصوت ---------
async def send_audio(query, uid):
    surah = user_surah.get(uid, "1")
    reader = user_reader.get(uid, "husary")

    url = f"https://server8.mp3quran.net/{reader}/{int(surah):03}.mp3"
    await query.message.reply_audio(url)

# --------- لوحة المشرف ---------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        f"👑 لوحة التحكم\n\nالمستخدمين: {len(users)}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 إذاعة", callback_data="broadcast")]
        ])
    )

# --------- الإذاعة ---------
async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if uid != ADMIN_ID:
        return

    if query.data == "broadcast":
        broadcast_mode[uid] = True
        await query.message.reply_text("✉️ ابعت الرسالة الآن")

# --------- استقبال رسالة المشرف ---------
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if broadcast_mode.get(uid):
        msg = update.message.text
        for user in users:
            try:
                await context.bot.send_message(user, msg)
            except:
                pass

        broadcast_mode[uid] = False
        await update.message.reply_text("✅ تم الإرسال")

# --------- الأزرار ---------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    add_points(uid, 1)

    data = query.data

    if data == "quran":
        await query.edit_message_text("📖 اختر سورة:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(str(i), callback_data=f"surah_{i}") for i in range(1, 6)],
            [InlineKeyboardButton("🔙", callback_data="back")]
        ]))

    elif data.startswith("surah_"):
        user_surah[uid] = data.split("_")[1]
        user_page[uid] = 0
        await send_ayat(query, uid)

    elif data == "next":
        user_page[uid] += 1
        await send_ayat(query, uid)

    elif data == "prev":
        user_page[uid] = max(0, user_page[uid]-1)
        await send_ayat(query, uid)

    elif data == "audio":
        await send_audio(query, uid)

    elif data == "reader":
        await query.edit_message_text("اختر القارئ", reply_markup=readers_menu())

    elif data.startswith("reader_"):
        key = data.split("_")[1]
        user_reader[uid] = key
        await query.edit_message_text(f"تم اختيار {READERS[key]}", reply_markup=main_menu())

    elif data == "azkar":
        zekr, markup = azkar_menu(uid)
        await query.edit_message_text(zekr, reply_markup=markup)

    elif data == "tasbeeh":
        user_counter[uid] = user_counter.get(uid, 0)+1
        zekr, markup = azkar_menu(uid)
        await query.edit_message_text(zekr, reply_markup=markup)

    elif data == "points":
        pts = user_points.get(uid, 0)
        await query.edit_message_text(f"🏆 نقاطك: {pts}", reply_markup=main_menu())

    elif data == "back":
        await query.edit_message_text("🏠 الرئيسية", reply_markup=main_menu())

# --------- تشغيل ---------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(CallbackQueryHandler(handle_admin_buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

app.run_polling()
