import json
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8440647341:AAG9um7lK7v5c88_rOF2_Uv8MvujmRstezo"

# ================= STORAGE =================
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f)

users = load_users()

# ================= RECITERS =================
RECITERS = {
    "الحصري": "husr",
    "عبد الباسط": "basit",
    "المنشاوي": "minsh",
    "ماهر المعيقلي": "maher",
    "سعد الغامدي": "s_gmd",
    "ياسر الدوسري": "yasser",
    "ناصر القطامي": "nasser"
}

# ================= MENU =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 القرآن", callback_data="quran")],
        [InlineKeyboardButton("📖 ختمتي", callback_data="khatma")],
        [InlineKeyboardButton("🎧 اختيار القارئ", callback_data="reciter")],
        [InlineKeyboardButton("📊 حسابي", callback_data="dashboard")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name or "صديقي"

    if uid not in users:
        users[uid] = {
            "reciter": "الحصري",
            "khatma": {"sura": 1, "ayah": 0}
        }
        save_users(users)

    text = f"""
🤍 أهلاً بيك يا {name}

📖 اقرأ القرآن بسهولة
🎧 اسمع بأجمل الأصوات

━━━━━━━━━━━━━━━
👨‍💻 تطوير:
أحمد المهدي  
📍 قنا - الحجيرات  

📲 https://t.me/@Ahmed_el_mehdi
━━━━━━━━━━━━━━━
"""

    await update.message.reply_text(text, reply_markup=main_menu())

# ================= BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    user = users[uid]

    # ===== قائمة السور =====
    if query.data == "quran":
        kb = [[InlineKeyboardButton(f"سورة {i}", callback_data=f"sura_{i}_0")] for i in range(1,115)]
        await query.edit_message_text("📖 اختر سورة", reply_markup=InlineKeyboardMarkup(kb))

    # ===== عرض سورة =====
    elif query.data.startswith("sura_"):
        parts = query.data.split("_")
        sura = int(parts[1])
        start = int(parts[2])

        res = requests.get(f"https://api.alquran.cloud/v1/surah/{sura}")
        data = res.json()["data"]
        ayat = data["ayahs"]

        chunk = ayat[start:start+10]

        text = f"📖 سورة {data['name']}\n\n"
        for a in chunk:
            text += f"﴿{a['numberInSurah']}﴾ {a['text']}\n\n"

        # حفظ للختمة
        user["khatma"]["sura"] = sura
        user["khatma"]["ayah"] = start
        save_users(users)

        buttons_list = []

        if start > 0:
            buttons_list.append(
                InlineKeyboardButton("⬅️ السابق", callback_data=f"sura_{sura}_{start-10}")
            )

        if start + 10 < len(ayat):
            buttons_list.append(
                InlineKeyboardButton("➡️ التالي", callback_data=f"sura_{sura}_{start+10}")
            )

        nav = [buttons_list] if buttons_list else []
        nav.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="home")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(nav))

        # صوت مرة واحدة
        if start == 0:
            rec = RECITERS[user["reciter"]]
            audio = f"https://server8.mp3quran.net/{rec}/{sura:03}.mp3"
            await query.message.reply_audio(audio=audio)

    # ===== ختمة =====
    elif query.data == "khatma":
        sura = user["khatma"]["sura"]
        ayah = user["khatma"]["ayah"]

        await query.edit_message_text(
            f"📖 آخر مكان ليك:\nسورة {sura}\nآية رقم {ayah+1}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 كمل القراءة", callback_data=f"sura_{sura}_{ayah}")],
                [InlineKeyboardButton("🏠 رجوع", callback_data="home")]
            ])
        )

    # ===== قارئ =====
    elif query.data == "reciter":
        kb = [[InlineKeyboardButton(k, callback_data=f"rec_{k}")] for k in RECITERS]
        kb.append([InlineKeyboardButton("🏠 رجوع", callback_data="home")])
        await query.edit_message_text("🎧 اختر قارئ", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("rec_"):
        name = query.data.replace("rec_", "")
        user["reciter"] = name
        save_users(users)
        await query.edit_message_text(f"✅ تم اختيار: {name}", reply_markup=main_menu())

    # ===== حساب =====
    elif query.data == "dashboard":
        await query.edit_message_text(
            f"🎧 القارئ: {user['reciter']}\n📖 ختمتك عند سورة {user['khatma']['sura']}",
            reply_markup=main_menu()
        )

    elif query.data == "home":
        await query.edit_message_text("🏠 القائمة الرئيسية", reply_markup=main_menu())


# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))

app.run_polling()
