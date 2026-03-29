import os
import requests
import json
import random
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
DATA_FILE = "users.json"

# ================= STORAGE =================
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

users = load_users()

# ================= CONFIG =================
RECITERS = {
    "عبد الباسط": "afs",
    "الحصري": "husr",
    "المنشاوي": "minsh",
    "مشاري العفاسي": "mshari",
    "ماهر المعيقلي": "maher",
    "ياسر الدوسري": "yasser",
    "ناصر القطامي": "nasser",
    "أحمد العجمي": "ahmad",
    "السديس": "sudais"
}

AZKAR = [
"سبحان الله وبحمده سبحان الله العظيم",
"اللهم صل وسلم على نبينا محمد",
"أستغفر الله العظيم وأتوب إليه",
"لا إله إلا الله وحده لا شريك له له الملك وله الحمد وهو على كل شيء قدير",
"لا حول ولا قوة إلا بالله",
"حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم"
]

# ================= MENU =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 قراءة القرآن", callback_data="read")],
        [InlineKeyboardButton("🌅 أذكار", callback_data="azkar")],
        [InlineKeyboardButton("🎧 اختيار القارئ", callback_data="reciter")],
        [InlineKeyboardButton("📿 سبحة", callback_data="tasbeeh_0_0")],
        [InlineKeyboardButton("📊 لوحتي", callback_data="dashboard")],
        [InlineKeyboardButton("🎯 التحدي اليومي", callback_data="challenge")]
    ])

def back_btn():
    return [[InlineKeyboardButton("⬅️ رجوع", callback_data="back")]]

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in users:
        users[uid] = {
            "reciter": "afs",
            "points": 0,
            "level": 1,
            "read": 0,
            "listen": 0,
            "tasbeeh": 0,
            "last_day": "",
            "challenge": {}
        }
        save_users(users)

    text = """🌙 أهلاً بك

📖 تم تطوير البوت بواسطة:
أحمد جاب الله - الحجيرات (قنا)

🤍 صدقة جارية

اختر من القائمة 👇"""

    await update.message.reply_text(text, reply_markup=main_menu())

# ================= LEVEL =================
def update_level(u):
    u["level"] = u["points"] // 10 + 1

# ================= CHALLENGE =================
def reset_challenge(uid):
    users[uid]["challenge"] = {
        "read": 0,
        "listen": False,
        "tasbeeh": 0,
        "goal_read": 3,
        "goal_tasbeeh": 20,
        "done": False
    }

def check_new_day(uid):
    today = datetime.now().strftime("%Y-%m-%d")
    if users[uid]["last_day"] != today:
        users[uid]["last_day"] = today
        reset_challenge(uid)

def check_challenge(uid):
    ch = users[uid]["challenge"]

    if (
        ch["read"] >= ch["goal_read"]
        and ch["listen"]
        and ch["tasbeeh"] >= ch["goal_tasbeeh"]
        and not ch["done"]
    ):
        users[uid]["points"] += 10
        ch["done"] = True
        return True
    return False

# ================= BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    check_new_day(uid)

    data = query.data

    if data == "back":
        await query.message.edit_text("🏠 الرئيسية", reply_markup=main_menu())
        return

    if data == "read":
        buttons = [[InlineKeyboardButton(f"{i}", callback_data=f"sura_{i}")] for i in range(1, 115)]
        buttons += back_btn()
        await query.message.edit_text("📖 اختر سورة", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("sura_"):
        sura = int(data.split("_")[1])

        await query.message.edit_text("⏳ جاري التحميل...")

        try:
            res = requests.get(f"https://api.alquran.cloud/v1/surah/{sura}")
            data_json = res.json()

            name = data_json["data"]["name"]
            ayat = data_json["data"]["ayahs"]

            text = f"📖 سورة {name}\n\n"
            for a in ayat[:5]:
                text += a["text"] + "\n"

            await query.message.edit_text(text, reply_markup=main_menu())

            rec = users[uid]["reciter"]
            audio = f"https://server8.mp3quran.net/{rec}/{sura:03}.mp3"
            await query.message.reply_audio(audio=audio)

            users[uid]["read"] += 1
            users[uid]["listen"] += 1
            users[uid]["points"] += 4
            users[uid]["challenge"]["read"] += 1
            users[uid]["challenge"]["listen"] = True

            if check_challenge(uid):
                await query.message.reply_text("🎉 أنهيت التحدي +10 نقاط")

            update_level(users[uid])
            save_users(users)

        except:
            await query.message.edit_text("❌ خطأ")
        return

    if data == "azkar":
        zikr = random.sample(AZKAR, k=3)
        await query.message.edit_text("\n\n".join(zikr), reply_markup=main_menu())
        return

    if data == "reciter":
        buttons = [[InlineKeyboardButton(k, callback_data=f"rec_{k}")] for k in RECITERS]
        buttons += back_btn()
        await query.message.edit_text("🎧 اختر قارئ", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("rec_"):
        name = data.replace("rec_", "")
        users[uid]["reciter"] = RECITERS[name]
        save_users(users)
        await query.answer("✅ تم")
        return

    if data.startswith("tasbeeh"):
        parts = data.split("_")
        count = int(parts[1])
        index = int(parts[2])

        Z = ["الحمد لله", "سبحان الله", "الله أكبر"]

        count += 1

        if count >= 33:
            count = 0
            index = (index + 1) % 3

        users[uid]["tasbeeh"] += 1
        users[uid]["points"] += 1
        users[uid]["challenge"]["tasbeeh"] += 1

        if check_challenge(uid):
            await query.answer("🎉 خلصت التحدي!")

        update_level(users[uid])
        save_users(users)

        kb = [
            [InlineKeyboardButton(f"{Z[index]}", callback_data=f"tasbeeh_{count}_{index}")],
            [InlineKeyboardButton(f"🔢 {count}", callback_data="ignore")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data="back")]
        ]

        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "ignore":
        return

    if data == "dashboard":
        u = users[uid]
        text = f"""
📊 بياناتك

📖 {u['read']}
🎧 {u['listen']}
📿 {u['tasbeeh']}

⭐ {u['points']}
🏆 {u['level']}
"""
        await query.message.edit_text(text, reply_markup=main_menu())
        return

    if data == "challenge":
        ch = users[uid]["challenge"]
        text = f"""
🎯 التحدي اليومي

📖 {ch['read']}/{ch['goal_read']}
🎧 {'✅' if ch['listen'] else '❌'}
📿 {ch['tasbeeh']}/{ch['goal_tasbeeh']}
"""
        await query.message.edit_text(text, reply_markup=main_menu())
        return

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))

app.run_polling()
