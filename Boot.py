import os
import requests
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

ADMIN_ID = 6310727080
DEV_USERNAME = "@Ahmed_el_mehdi"

# ===== تخزين =====
users = set()
user_points = {}
user_reader = {}
user_page = {}
user_surah = {}
user_counter = {}

user_tasbeeh_index = {}
user_tasbeeh_count = {}

# ===== أسماء السور =====
SURA_NAMES = [
"الفاتحة","البقرة","آل عمران","النساء","المائدة","الأنعام","الأعراف","الأنفال","التوبة","يونس",
"هود","يوسف","الرعد","إبراهيم","الحجر","النحل","الإسراء","الكهف","مريم","طه",
"الأنبياء","الحج","المؤمنون","النور","الفرقان","الشعراء","النمل","القصص","العنكبوت","الروم",
"لقمان","السجدة","الأحزاب","سبأ","فاطر","يس","الصافات","ص","الزمر","غافر",
"فصلت","الشورى","الزخرف","الدخان","الجاثية","الأحقاف","محمد","الفتح","الحجرات","ق",
"الذاريات","الطور","النجم","القمر","الرحمن","الواقعة","الحديد","المجادلة","الحشر","الممتحنة",
"الصف","الجمعة","المنافقون","التغابن","الطلاق","التحريم","الملك","القلم","الحاقة","المعارج",
"نوح","الجن","المزمل","المدثر","القيامة","الإنسان","المرسلات","النبأ","النازعات","عبس",
"التكوير","الانفطار","المطففين","الانشقاق","البروج","الطارق","الأعلى","الغاشية","الفجر","البلد",
"الشمس","الليل","الضحى","الشرح","التين","العلق","القدر","البينة","الزلزلة","العاديات",
"القارعة","التكاثر","العصر","الهمزة","الفيل","قريش","الماعون","الكوثر","الكافرون","النصر",
"المسد","الإخلاص","الفلق","الناس"
]

# ===== القراء =====
READERS = {
    "husary": "husr",
    "abdulbasit": "basit",
    "minshawi": "minsh",
    "dossary": "yasser",
    "qattami": "nasser",
    "qhtani": "qhtani"
}

READERS_NAMES = {
    "husary": "الحصري",
    "abdulbasit": "عبد الباسط",
    "minshawi": "المنشاوي",
    "dossary": "ياسر الدوسري",
    "qattami": "ناصر القطامي",
    "qhtani": "ياسر القحطاني"
}

# ===== أذكار =====
AZKAR = [
"سبحان الله وبحمده سبحان الله العظيم",
"أستغفر الله العظيم وأتوب إليه",
"اللهم صل وسلم على نبينا محمد",
"لا إله إلا أنت سبحانك إني كنت من الظالمين",
"اللهم ارزقني حسن الخاتمة",
"اللهم اجعل القرآن ربيع قلبي"
]

# ===== سبحة =====
TASBEEH_SEQUENCE = [
{"text":"سبحان الله","count":33},
{"text":"الحمد لله","count":33},
{"text":"الله أكبر","count":34}
]

# ===== نقاط =====
def add_points(uid,n=1):
    user_points[uid]=user_points.get(uid,0)+n

# ===== واجهات =====
def main_menu(uid=None):
    reader = READERS_NAMES.get(user_reader.get(uid,"husary"))
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 القرآن",callback_data="quran")],
        [InlineKeyboardButton(f"🎧 القارئ الحالي: {reader}",callback_data="reader")],
        [InlineKeyboardButton("📿 السبحة",callback_data="tasbeeh_menu")],
        [InlineKeyboardButton("🧿 أذكار",callback_data="azkar")],
        [InlineKeyboardButton("🏆 نقاطي",callback_data="points")],
        [InlineKeyboardButton("👑 المطور",url=f"https://t.me/{DEV_USERNAME}")]
    ])

# ===== بدء =====
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    name=update.effective_user.first_name

    users.add(uid)
    add_points(uid)

    await update.message.reply_text(
        f"🤍 أهلاً يا {name}\n\nبوت القرآن الكريم\n\n👑 تطوير:\nأحمد المهدي - قنا الحجيرات",
        reply_markup=main_menu(uid)
    )

# ===== عرض الآيات =====
async def send_ayat(query,uid):
    sura=user_surah.get(uid,1)
    page=user_page.get(uid,0)

    res=requests.get(f"https://api.alquran.cloud/v1/surah/{sura}")
    data=res.json()["data"]["ayahs"]

    chunk=data[page*10:(page*10)+10]

    text=f"📖 سورة {SURA_NAMES[sura-1]}\n\n"
    for a in chunk:
        text+=f"﴿{a['numberInSurah']}﴾ {a['text']}\n\n"

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️",callback_data="prev"),
             InlineKeyboardButton("➡️",callback_data="next")],
            [InlineKeyboardButton("🔊 تشغيل الصوت",callback_data="audio")],
            [InlineKeyboardButton("🔙",callback_data="back")]
        ])
    )

# ===== الصوت =====
async def send_audio(query,uid):
    sura=user_surah.get(uid,1)
    reader_key=user_reader.get(uid,"husary")
    reciter=READERS.get(reader_key,"husr")

    url=f"https://server8.mp3quran.net/{reciter}/{int(sura):03}.mp3"

    loading=await query.message.reply_text("⏳ جاري تحميل الصوت...")

    try:
        await query.message.reply_audio(audio=url)
        await loading.delete()
    except:
        fallback=f"https://server8.mp3quran.net/husr/{int(sura):03}.mp3"
        await query.message.reply_audio(audio=fallback)
        await loading.delete()

# ===== الأزرار =====
async def buttons(update:Update,context:ContextTypes.DEFAULT_TYPE):
    query=update.callback_query
    uid=query.from_user.id
    await query.answer()

    add_points(uid)

    if query.data=="quran":
        kb=[[InlineKeyboardButton(SURA_NAMES[i],callback_data=f"sura_{i+1}")]
             for i in range(114)]
        await query.edit_message_text("اختر السورة",reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("sura_"):
        user_surah[uid]=int(query.data.split("_")[1])
        user_page[uid]=0
        await send_ayat(query,uid)

    elif query.data=="next":
        user_page[uid]+=1
        await send_ayat(query,uid)

    elif query.data=="prev":
        user_page[uid]=max(0,user_page[uid]-1)
        await send_ayat(query,uid)

    elif query.data=="audio":
        await send_audio(query,uid)

    elif query.data=="reader":
        kb=[[InlineKeyboardButton(v,callback_data=f"r_{k}")]
            for k,v in READERS_NAMES.items()]
        kb.append([InlineKeyboardButton("🔙",callback_data="back")])
        await query.edit_message_text("اختر القارئ",reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("r_"):
        r=query.data.split("_")[1]
        user_reader[uid]=r
        await query.edit_message_text(
            f"✅ تم اختيار {READERS_NAMES[r]}",
            reply_markup=main_menu(uid)
        )

    elif query.data=="azkar":
        z=random.choice(AZKAR)
        await query.edit_message_text(z,reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄",callback_data="azkar")],
            [InlineKeyboardButton("🔙",callback_data="back")]
        ]))

    elif query.data=="tasbeeh_menu":
        user_tasbeeh_index[uid]=0
        user_tasbeeh_count[uid]=0

        cur=TASBEEH_SEQUENCE[0]

        await query.edit_message_text(
            f"{cur['text']}\n\n0 / {cur['count']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📿",callback_data="tasbeeh_click")],
                [InlineKeyboardButton("🔙",callback_data="back")]
            ])
        )

    elif query.data=="tasbeeh_click":
        i=user_tasbeeh_index.get(uid,0)
        c=user_tasbeeh_count.get(uid,0)

        cur=TASBEEH_SEQUENCE[i]
        c+=1

        if c>=cur["count"]:
            i+=1
            c=0
            if i>=len(TASBEEH_SEQUENCE):
                i=0

        user_tasbeeh_index[uid]=i
        user_tasbeeh_count[uid]=c

        cur=TASBEEH_SEQUENCE[i]

        await query.edit_message_text(
            f"{cur['text']}\n\n{c} / {cur['count']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📿",callback_data="tasbeeh_click")],
                [InlineKeyboardButton("🔙",callback_data="back")]
            ])
        )

    elif query.data=="points":
        await query.edit_message_text(
            f"🏆 نقاطك: {user_points.get(uid,0)}",
            reply_markup=main_menu(uid)
        )

    elif query.data=="back":
        await query.edit_message_text("🏠 الرئيسية",reply_markup=main_menu(uid))

# ===== تشغيل =====
app=ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CallbackQueryHandler(buttons))

app.run_polling()
