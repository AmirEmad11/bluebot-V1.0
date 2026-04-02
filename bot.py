# bot.py - كامل ونهائي
# هذا الكود يجمع بين مهام النشر في القناة والترحيب بالأعضاء الجدد.
# Requirements: telethon
# تأكد من وجود الصور: apple1.jpg, apple2.jpg, apple3.jpg في نفس مجلد السكربت.

try:
    import telethonpatch  # اختياري لبعض البيئات
except Exception:
    pass

import os
import json
import asyncio
import logging
import random
import time
import tempfile
import requests
from io import BytesIO
from datetime import datetime
import pytz
from typing import List, Optional, Dict, Union, Any, Tuple
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import HideAllChatJoinRequestsRequest
from telethon.tl.types import UpdatePendingJoinRequests

# ---------------- logging ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("bot")

# ---------------- قراءة الإعدادات من البيئة ----------------
try:
    from config import API_ID, API_HASH, PHONE, PASSWORD, BOT_TOKEN, CHANNEL_IDENTIFIER, ADMIN_ID
except ImportError:
    API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
    API_HASH = os.getenv("TELEGRAM_API_HASH", "")
    PHONE = os.getenv("TELEGRAM_PHONE", "")
    PASSWORD = os.getenv("TELEGRAM_PASSWORD", "")
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    CHANNEL_IDENTIFIER = os.getenv("TELEGRAM_CHANNEL", "")
    ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0")) if os.getenv("TELEGRAM_ADMIN_ID") else 0

TIMEZONE = pytz.timezone('Africa/Cairo')

if not API_ID or not API_HASH:
    log.critical("Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in environment.")
    raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH first.")

if not PHONE:
    log.critical("Missing TELEGRAM_PHONE in environment.")
    raise SystemExit("Set TELEGRAM_PHONE first.")

# ---------------- resources & state ----------------
APPLE_GAME_PHOTOS = ["apple1.jpg", "apple2.jpg", "apple3.jpg"]
PLAN_ONE_IMAGES = ["https://i.ibb.co/rfZ91BK2/6.jpg", "https://i.ibb.co/Ng2CHCgm/7.jpg"]
PLAN_TWO_IMAGES = ["https://i.ibb.co/whfSdLCX/8.jpg", "https://i.ibb.co/wFgCkrxp/9.jpg"]
PLAN_THREE_IMAGE = "https://i.ibb.co/hxDKTCwY/10.jpg"

# ============ إعدادات نظام الفيديوهات الجديد ============
VIDEOS_DIR = "VIDEO"
VIDEO_EVERY_N_SIGNALS = 3  # فيديو كل 3 إشارات
VIDEO_CAPTION = None 

# ربط الأنماط بالفيديوهات (تلقائياً من أسماء الملفات)
def get_pattern_to_video_map() -> Dict[str, str]:
    mapping = {}
    if not os.path.exists(VIDEOS_DIR):
        try:
            os.makedirs(VIDEOS_DIR)
        except:
            return mapping
    for filename in os.listdir(VIDEOS_DIR):
        if filename.endswith(".mp4") and filename.startswith("{") and filename.endswith("}.mp4"):
            # {9-0-8-2-7-1}.mp4 -> 9:0_8:2_7:1
            pattern_str = filename[1:-5] 
            parts = pattern_str.split('-')
            formatted_parts = []
            for i in range(0, len(parts), 2):
                if i+1 < len(parts):
                    formatted_parts.append(f"{parts[i]}:{parts[i+1]}")
            pattern_id = "_".join(formatted_parts)
            mapping[pattern_id] = filename
    return mapping

STATE_FILE = "state.json"
DELAY_BETWEEN_MESSAGES = 3
last_apple_patterns = []
last_used_patterns = []
video_counter = 0
last_apple_info = None

# روابط الأزرار التفاعلية
REGISTRATION_LINK = "https://lb-aff.com/L?tag=d_5431305m_66803c_apk1&site=5431305&ad=66803"
CONTACT_USERNAME = "@Mr_Money223"
TUTORIAL_LINK = "https://t.me/c/3886228588/6"

# ---------------- الرسائل ----------------
WELCOME_MSG = "السلام عليكم 👋\nجاهز تبدأ تشتغل معانا وتعمل فلوس؟ 💰"
SECOND_MSG = (
    "كل يوم بنزل إشارات للعبة 🍎Apple Of Fortune🍎 اللي بتساعد الناس يكسبوا بشكل "
    "ثابت أكتر من 5000 جنيه في اليوم. الموضوع بسيط جدًا: أنا بقولك تراهن فين، "
    "إنت بتكرر، وإنت بتكسب."
)
THIRD_MSG = """بص على نتايج عملائي 👆
الناس دي عمرها ما سمعت عن لعبة 🍎Apple Of Fortune🍎 قبل كده وماكانوش يعرفوا إن ممكن يكسبوا منها.
دلوقتي، بفضل إشاراتي، بيكسبوا 5000 جنيه في اليوم 💸
"""
FOURTH_MSG = """القواعد سهلة ✅

في الأول لازم تسجّل في LineBet بحساب جديد بالبرومو كود او الرمز الترويجي الخاص بينا:   KK100

رابط التسجيل : 🔥🔥 https://lb-aff.com/L?tag=d_5431305m_22611c_site&site=5431305&ad=22611&r=registration

رابط تحميل التطبيق : https://lb-aff.com/L?tag=d_5431305m_66803c_apk1&site=5431305&ad=66803

بعدها بتحط إيداع 275 جنيه او اكتر، وبعدها بتستعمل إشاراتي الـ VIP عشان تكسب!

🚀 تابع قناتي وشوف بنفسك! 👇
https://t.me/+22gwLYrKOBEzNmFk

نصيبي هو 10% من أرباحك في الشهر!
خلينا نكون صريحين مع بعض 🤝😉

اول ما تعمل ارباح صورهالي و ابعتها هنا نشارك بيها الناس مع بعض ❤️
كلمني علي : @Mr_Money223
"""
PLAN_ONE_TEXT = """
✨ مش بس فخور باللي بعمله… كمان سعيد إني بشوف حياة ناس كتير بتتغير بفضل مجهودي 💸
أهم حاجة عندي أشوفك مطمّن، واثق، وعايش أحسن.

فريقي حلّل ألعاب زي التفاحه و الطياره وPenalty.
ومن هنا طلع برنامج قوي بيتوقع بدقة عالية 💻

مش بوعدك تعمل ملايين بين يوم وليلة يا أخويا… لكن لو اتبعت خطوتي، ممكن تكسب بسهولة من ٨٠٠٠ لـ١٠٠٠٠ جنيه يوميًا 🤗

والأحلى: بـ٢٥٠ جنيه بس، ممكن تحولهم لأكتر من ٨٠٠٠ جنيه في ساعتين 🤑

🚀 الفرصة دي مش هترجع… خد خطوة النهاردة وانضم لفريقي.

للتواصل : ⬇️⬇️
👉 @Mr_Money223
👉 @Mr_Money223
👉 @Mr_Money223
"""
PLAN_TWO_TEXT = """
💎 كل يوم بيوصلني رسائل من ناس حياتهم بدأت تتغير بفضل البوت:

💬 "يا أخويا، امبارح سحبت ٨٠٠٠ جنيه من غير أي مجهود. حاجة خيالية!"
💬 "عمري ما كنت أتخيل يكون عندي دخل زيادة كده، دلوقتي بقى عادة كل أسبوع."
💬 "بفضل البوت ما بقيتش معتمد على مرتبي بس، ده مستوى تاني خالص!"

⚡️ ناس عادية زيك بالظبط، لكن عندهم الجرأة ياخدوا خطوة.

❓ عايز قصتك تكون الجاية اللي ننشرها في القناة؟

📩 ابعتلي دلوقتي: @Mr_Money223
"""
PLAN_THREE_TEXT = """
🔥 مش ببيع كورسات ومش بوعِد بمعجزات.

أنا بس بشارك الحاجة اللي فعلاً غيّرت حياتي.
📈 بالبرنامج ده بدأت أكسب بشكل عمري ما كنت متخيّله.

⏳ هتجرّب وتدي لنفسك فرصة؟ ولا هتفضل تتفرّج والناس حواليك بتكسب؟

اكتبلي دلوقتي: 👉💎 @Mr_Money223
"""
GAME_INTRO_TEXT = "🚨🚨 انتظر إشارة جديدة..."
GAME_CONGRATS_TEXT = "🎉 مبروك لكل من شارك وفاز معنا! انتظرونا في الإشارة القادمة..."
FINAL_SUPPORT_MSG = "لو عندك مشكلة او استفسارات تواصل مع : @Mr_Money223"

# رسائل FOMO والمتابعة
FOMO_30MIN_MSG = """⏰ تنبيه مهم!

لاحظت إنك شفت الرسائل لكن لم تسجل بعد.

⚠️ معلومة: الكود الترويجي kk100 متاح لأول 50 شخص فقط كل يوم
📊 اليوم سجل 37 شخص... باقي 13 مكان فقط!

كل دقيقة تتأخر فيها = خسارة فرصة ربح محتملة 💸"""

FOMO_3HOURS_MSG = """🚨 تحذير!

أنت في طريقك لخسارة فرصة العمر...

💰 لو كنت سجلت من 3 ساعات، كنت الآن ربحت من آخر 12 إشارة
📈 الإشارات الأخيرة نجحت بنسبة 100% وكسبت للأعضاء متوسط 3,200 جنيه

⏰ الإشارة القادمة خلال 15 دقيقة
❌ بدون تسجيل = بدون أرباح

هل تريد الانضمام الآن؟"""

FOMO_24HOURS_MSG = """📉 خسرت فعلياً:

بالأمس أرسلنا 96 إشارة رابحة (كل 15 دقيقة):
- متوسط الربح لكل إشارة: +2,500 جنيه
- إجمالي الأرباح المحتملة في 24 ساعة: 240,000 جنيه
- خسارتك الشخصية المحتملة: 12,000+ جنيه

💔 كم يوم آخر ستخسر فيه هذه الفرص؟

⚡ الفرصة الأخيرة - سجل الآن ولا تضيع يوم آخر!"""

GUARANTEE_MSG = """🎁 عرض خاص لك!

أعرف إنك خايف من المخاطرة، عادي جداً.

لذلك أقدملك ضمان شخصي مني:

✅ سجل واشحن الـ 275 جنيه
✅ جرب أول 3 إشارات
✅ لو ما كسبتش في واحدة منهم...
💰 أنا شخصياً أرجعلك الـ 275 جنيه كاملة!

ليه الضمان ده؟ 
لأني واثق 100% من الإشارات 🎯

⏰ العرض ده صالح لـ 24 ساعة فقط
💬 رد بـ "موافق" عشان أبدأ معاك"""

# ---------------- clients and state ----------------
SESSION_USER = "session_user_201153943941"
SESSION_BOT = "session_bot"
user_client = TelegramClient(SESSION_USER, API_ID, API_HASH)
bot_client = TelegramClient(SESSION_BOT, API_ID, API_HASH) if BOT_TOKEN else None
bot_started = False
message_host = None
user_target_channel = None

state = {"users_welcomed": [], "users_sent": [], "users_final_replied": [], "users_join_time": {}, "users_registered": []}
users_welcomed = set()
users_sent = set()
users_final_replied = set()
users_join_time: Dict[int, float] = {}  # وقت انضمام كل عضو
users_registered = set()  # الأعضاء الذين سجلوا
_user_locks: Dict[int, asyncio.Lock] = {}
_dialogs_cache = None
_dialogs_cache_updated_at = 0
_DIALOGS_CACHE_TTL = 3600
_recently_processed_joins: Dict[int, float] = {}
_JOIN_DEDUP_WINDOW = 60
_join_handler_lock = asyncio.Lock()
_is_processing_join_event = False
_broadcast_mode: Dict[int, bool] = {}  # تتبع من في وضع البرودكاست
_follow_up_tasks: Dict[int, asyncio.Task] = {}  # تتبع المهام المجدولة

# ---------------- persistence ----------------
def load_state():
    global state, users_welcomed, users_sent, users_final_replied, users_join_time, users_registered
    global video_counter, last_used_patterns
    try:
        if os.path.isfile(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            users_welcomed = set(state.get("users_welcomed", []))
            users_sent = set(state.get("users_sent", []))
            users_final_replied = set(state.get("users_final_replied", []))
            users_join_time = {int(k): float(v) for k, v in state.get("users_join_time", {}).items()}
            users_registered = set(state.get("users_registered", []))
            video_counter = state.get("video_counter", 0)
            last_used_patterns = state.get("last_used_patterns", [])
            log.info(f"Loaded state: welcomed={len(users_welcomed)}, sent={len(users_sent)}, registered={len(users_registered)}")
        else:
            log.info("No state file found; starting fresh.")
    except Exception as e:
        log.error(f"Failed loading state: {e}")
        state = {"users_welcomed": [], "users_sent": [], "users_final_replied": [], "users_join_time": {}, "users_registered": []}
        users_welcomed = set()
        users_sent = set()
        users_final_replied = set()
        users_join_time = {}
        users_registered = set()

def save_state():
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "users_welcomed": list(users_welcomed), 
                "users_sent": list(users_sent),
                "users_final_replied": list(users_final_replied),
                "users_join_time": {str(k): v for k, v in users_join_time.items()},
                "users_registered": list(users_registered),
                "video_counter": video_counter,
                "last_used_patterns": last_used_patterns
            }, f, ensure_ascii=False, indent=2)
        log.debug("State saved.")
    except Exception as e:
        log.error(f"Failed saving state: {e}")

# ---------------- helpers ----------------
def get_user_lock(user_id: int) -> asyncio.Lock:
    if user_id not in _user_locks:
        _user_locks[user_id] = asyncio.Lock()
    return _user_locks[user_id]

async def safe_sleep(seconds: float):
    try:
        await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        pass

def get_sender_client():
    if bot_client and bot_started:
        return bot_client
    return user_client

async def safe_get_entity(client, entity_id, retries=3, delay=1.0):
    for i in range(retries):
        try:
            return await client.get_entity(entity_id)
        except Exception as e:
            log.warning(f"Attempt {i+1} to get entity {entity_id} failed: {e}")
            await safe_sleep(delay)
    return None

def create_action_buttons():
    """إنشاء الأزرار التفاعلية الموحدة"""
    return [
        [Button.url("📝 دوس هنا عشان تحمل البرنامج", REGISTRATION_LINK)],
        [Button.url("🎮 شرح طريقة المكسب", TUTORIAL_LINK)],
        [Button.url("💬 التواصل معي", f"https://t.me/{CONTACT_USERNAME.replace('@', '')}")]
    ]

# ---------------- senders ----------------
async def send_text_safe(sender: TelegramClient, peer: Union[int, Any], text: str, parse_mode: Optional[str] = "md") -> bool:
    for attempt in range(4):
        try:
            await sender.send_message(peer, text, parse_mode=parse_mode)
            return True
        except FloodWaitError as fe:
            log.warning(f"FloodWait {fe.seconds}s sending text to {peer}")
            await asyncio.sleep(fe.seconds + 1)
        except Exception as e:
            log.error(f"Attempt {attempt+1} failed sending text to {peer}: {e}")
            await asyncio.sleep(2)
    return False

def _download_image_sync(url: str) -> Optional[str]:
    """تحميل صورة من URL بشكل متزامن"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        ext = url.split('.')[-1].split('?')[0][:4] or 'jpg'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}')
        temp_file.write(response.content)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        return None

async def download_remote_image(url: str) -> Optional[str]:
    """تحميل صورة من URL وحفظها مؤقتاً (بشكل غير مُعطِّل)"""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _download_image_sync, url)
        if result:
            log.info(f"✅ Downloaded remote image: {url[:50]}...")
        else:
            log.error(f"❌ Failed to download image {url}")
        return result
    except Exception as e:
        log.error(f"❌ Failed to download image {url}: {e}")
        return None

async def upload_photos_with_fallback(sender: TelegramClient, photos_list: List[str]) -> List:
    uploaded = []
    temp_files = []
    for p in photos_list:
        try:
            is_url = p.startswith("http")
            file_path = p
            if is_url:
                downloaded = await download_remote_image(p)
                if not downloaded:
                    log.error(f"Skipping {p} - download failed")
                    continue
                file_path = downloaded
                temp_files.append(downloaded)
            up = await sender.upload_file(file_path, file_name=os.path.basename(file_path))
            uploaded.append(up)
        except FloodWaitError as fe:
            log.warning(f"FloodWait while uploading {p}: wait {fe.seconds}s")
            await safe_sleep(fe.seconds + 1)
        except Exception as e:
            log.error(f"Error uploading {p}: {e}")
    for temp_file in temp_files:
        try:
            os.unlink(temp_file)
        except:
            pass
    return uploaded

async def send_photos_with_caption(sender: TelegramClient, peer: int, images: List[str], caption: str, buttons=None) -> bool:
    try:
        uploaded_files = await upload_photos_with_fallback(sender, images)
        if not uploaded_files:
            log.error(f"Failed to upload any images for sending to {peer}.")
            return False
        await sender.send_file(peer, file=uploaded_files, caption=caption, buttons=buttons)
        log.info(f"Sent album to {peer}")
        return True
    except FloodWaitError as fe:
        log.warning(f"FloodWait sending album: wait {fe.seconds}s")
        await asyncio.sleep(fe.seconds + 1)
        return False
    except Exception as e:
        log.error(f"Error sending album to {peer}: {e}")
        return False

async def send_photo_with_caption(sender: TelegramClient, peer: int, image: str, caption: str) -> bool:
    try:
        uploaded_file = await upload_photos_with_fallback(sender, [image])
        if not uploaded_file:
            log.error(f"Failed to upload image for sending to {peer}.")
            return False
        await sender.send_file(peer, file=uploaded_file[0], caption=caption)
        log.info(f"Sent single photo to {peer}")
        return True
    except FloodWaitError as fe:
        log.warning(f"FloodWait sending photo: wait {fe.seconds}s")
        await asyncio.sleep(fe.seconds + 1)
        return False
    except Exception as e:
        log.error(f"Error sending photo to {peer}: {e}")
        return False

# ---------------- Channel Posting Logic ----------------
def create_pattern_id(pattern: Dict[int, int]) -> str:
    sorted_rows = sorted(pattern.keys(), reverse=True)
    parts = [f"{row}:{pattern[row]}" for row in sorted_rows]
    return "_".join(parts)

def select_smart_pattern() -> Dict[int, int]:
    global last_used_patterns
    # يتم تحديث الخريطة في كل مرة لاكتشاف الملفات الجديدة فوراً
    mapping = get_pattern_to_video_map()
    all_p = []
    for pattern_id in mapping.keys():
        p_dict = {}
        parts = pattern_id.split('_')
        for part in parts:
            row_col = part.split(':')
            if len(row_col) == 2:
                p_dict[int(row_col[0])] = int(row_col[1])
        all_p.append(p_dict)
    
    if not all_p:
        log.warning("⚠️ No patterns with videos found in VIDEO folder! Falling back to random row 9")
        return {9: random.randint(0, 4)}
    
    unused = [p for p in all_p if create_pattern_id(p) not in last_used_patterns[-5:]]
    selected = random.choice(unused if unused else all_p)
    
    pattern_id = create_pattern_id(selected)
    last_used_patterns.append(pattern_id)
    if len(last_used_patterns) > 10:
        last_used_patterns.pop(0)
    
    return selected

async def generate_apple_game_with_video_support() -> Tuple[str, Dict]:
    global last_apple_info
    rows, columns = 10, 5
    base_grid = [["🟫" for _ in range(columns)] for _ in range(rows)]
    
    selected_pattern = select_smart_pattern()
    for row, col in selected_pattern.items():
        base_grid[row][col] = "🍎"
    
    pattern_id = create_pattern_id(selected_pattern)
    last_apple_info = {
        "pattern": selected_pattern,
        "pattern_id": pattern_id
    }
    
    grid_text = "\n".join("".join(row) for row in base_grid)
    game_text = f"✅ اشاره جديده ✅\nالاشاره لمده ٥ دقائق ⏰\n🍏 Apple oF Fortune 🍏\n\n{grid_text}\n\n‼️الاشاره تعمل فقط لمن استعمل الرمز الترويجي KK100 عن التسجيل بحساب جديد\n‼️اقل ايداع عشان الإشارات تشتغل معاك هو  275 جنيه و في حاله الايداع بمبلغ اقل من 275 هتخسر للاسف\nرابط التسجيل : 🔥🔥 {REGISTRATION_LINK}\n\nلو عندك مشكلة او استفسارات تواصل مع : {CONTACT_USERNAME}"
    
    return game_text, last_apple_info

async def send_video_if_needed(apple_info: Dict):
    global video_counter
    video_counter += 1
    save_state()
    
    if video_counter % VIDEO_EVERY_N_SIGNALS == 0:
        # تحديث الخريطة لاكتشاف أي فيديوهات مضافة حديثاً
        mapping = get_pattern_to_video_map()
        pattern_id = apple_info["pattern_id"]
        if pattern_id in mapping:
            video_file = mapping[pattern_id]
            video_path = os.path.join(VIDEOS_DIR, video_file)
            if os.path.exists(video_path):
                log.info(f"📹 Processing video note for pattern: {pattern_id}")
                output_path = f"temp_round_{pattern_id}.mp4"
                try:
                    process = await asyncio.create_subprocess_exec(
                        'ffmpeg', '-y', '-i', video_path,
                        '-vf', "crop='min(iw,ih):min(iw,ih)',scale=400:400",
                        '-an', 
                        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                        output_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                    
                    if os.path.exists(output_path):
                        log.info(f"✅ Video converted and sent: {output_path}")
                        await user_client.send_file(
                            user_target_channel,
                            output_path,
                            video_note=True,
                            caption=None
                        )
                        os.remove(output_path)
                except Exception as e:
                    log.error(f"❌ Error in ffmpeg/sending: {e}")

async def apple_game_loop():
    """دورة لعبة التفاحة المستمرة مع معالجة الأخطاء ونظام الفيديو"""
    retry_delay = 30
    max_retry_delay = 300
    while True:
        try:
            # الخطوة 1: إرسال رسالة "انتظر إشارة جديدة"
            log.info(f"⏱️ [{datetime.now(TIMEZONE)}] إرسال رسالة 'انتظر إشارة جديدة'...")
            success = await send_text_safe(user_client, user_target_channel, GAME_INTRO_TEXT)
            if success:
                log.info(f"✅ [{datetime.now(TIMEZONE)}] رسالة 'انتظر إشارة جديدة' تم إرسالها")
                retry_delay = 30
            else:
                log.warning(f"⚠️ فشل إرسال رسالة الانتظار، إعادة المحاولة بعد {retry_delay}s")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
                continue
            await asyncio.sleep(300)

            # الخطوة 2: إرسال لعبة التفاحة
            log.info(f"🍎 [{datetime.now(TIMEZONE)}] إرسال لعبة التفاحة...")
            game_text, apple_info = await generate_apple_game_with_video_support()
            buttons = create_action_buttons()
            try:
                await user_client.send_message(user_target_channel, game_text, buttons=buttons)
                log.info(f"✅ [{datetime.now(TIMEZONE)}] نموذج لعبة التفاحة تم إرساله")
                retry_delay = 30
            except Exception as e:
                log.error(f"❌ فشل إرسال لعبة التفاحة: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
                continue
            
            # إرسال الفيديو إذا لزم الأمر
            await send_video_if_needed(apple_info)
            await asyncio.sleep(300)

            # الخطوة 3: إرسال رسالة التهنئة
            log.info(f"🎉 [{datetime.now(TIMEZONE)}] إرسال رسالة التهنئة...")
            success = await send_text_safe(user_client, user_target_channel, GAME_CONGRATS_TEXT)
            if success:
                log.info(f"✅ [{datetime.now(TIMEZONE)}] رسالة التهنئة تم إرسالها")
                retry_delay = 30
            else:
                log.warning(f"⚠️ فشل إرسال رسالة التهنئة")
            await asyncio.sleep(300)

        except asyncio.CancelledError:
            log.info("⏹️ Apple game loop cancelled")
            break
        except Exception as e:
            log.error(f"❌ خطأ غير متوقع في دورة لعبة التفاحة: {e}")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)

async def send_apple_game():
    """للاستخدام اليدوي فقط"""
    try:
        game_text, apple_info = await generate_apple_game_with_video_support()
        buttons = create_action_buttons()
        await user_client.send_message(user_target_channel, game_text, buttons=buttons)
        await send_video_if_needed(apple_info)
        log.info(f"✅ [{datetime.now(TIMEZONE)}] نموذج لعبة التفاحة تم إرساله (يدوي)")
    except Exception as e:
        log.error(f"❌ [{datetime.now(TIMEZONE)}] خطأ في إرسال لعبة التفاحة: {e}")

async def send_plan_one():
    try:
        await send_photos_with_caption(user_client, user_target_channel, PLAN_ONE_IMAGES, PLAN_ONE_TEXT)
        log.info(f"📢 [{datetime.now(TIMEZONE)}] Plan One تم الإرسال")
    except Exception as e:
        log.error(f"❌ [{datetime.now(TIMEZONE)}] خطأ في إرسال Plan One: {e}")

async def send_plan_two():
    try:
        await send_photos_with_caption(user_client, user_target_channel, PLAN_TWO_IMAGES, PLAN_TWO_TEXT)
        log.info(f"📢 [{datetime.now(TIMEZONE)}] Plan Two تم الإرسال")
    except Exception as e:
        log.error(f"❌ [{datetime.now(TIMEZONE)}] خطأ في إرسال Plan Two: {e}")

async def send_plan_three():
    try:
        await send_photo_with_caption(user_client, user_target_channel, PLAN_THREE_IMAGE, PLAN_THREE_TEXT)
        log.info(f"📢 [{datetime.now(TIMEZONE)}] Plan Three تم الإرسال")
    except Exception as e:
        log.error(f"❌ [{datetime.now(TIMEZONE)}] خطأ في إرسال Plan Three: {e}")

# ---------------- Smart Follow-up System ----------------
async def restore_pending_followups():
    """استعادة مهام المتابعة للأعضاء الذين لم يسجلوا بعد عند إعادة تشغيل البوت"""
    current_time = time.time()
    restored_count = 0
    for user_id, join_time in users_join_time.items():
        if user_id in users_registered:
            continue
        if user_id in _follow_up_tasks:
            continue
        elapsed = current_time - join_time
        if elapsed < 24 * 60 * 60:
            task = asyncio.create_task(smart_follow_up_system_resume(user_id, elapsed))
            _follow_up_tasks[user_id] = task
            restored_count += 1
    if restored_count > 0:
        log.info(f"🔄 Restored {restored_count} pending follow-up tasks")

async def smart_follow_up_system_resume(user_id: int, elapsed_seconds: float):
    """استكمال نظام المتابعة من حيث توقف"""
    try:
        sender = get_sender_client()
        thirty_min = 30 * 60
        three_hours = 3 * 60 * 60
        twenty_four_hours = 24 * 60 * 60

        if elapsed_seconds < thirty_min:
            wait = thirty_min - elapsed_seconds
            log.info(f"🔄 Resuming 30-min FOMO for {user_id} in {wait/60:.1f} min")
            await asyncio.sleep(wait)
            if user_id not in users_registered:
                await send_text_safe(sender, user_id, FOMO_30MIN_MSG, parse_mode="md")
                await sender.send_message(user_id, "👇 اضغط على الأزرار للبدء:", buttons=create_action_buttons())
                log.info(f"✅ Sent 30-min FOMO to {user_id}")
            elapsed_seconds = thirty_min

        if elapsed_seconds < three_hours:
            wait = three_hours - elapsed_seconds
            log.info(f"🔄 Resuming 3-hour FOMO for {user_id} in {wait/60:.1f} min")
            await asyncio.sleep(wait)
            if user_id not in users_registered:
                await send_text_safe(sender, user_id, FOMO_3HOURS_MSG, parse_mode="md")
                await sender.send_message(user_id, "⚡ لا تفوت الفرصة:", buttons=create_action_buttons())
                log.info(f"✅ Sent 3-hour FOMO to {user_id}")
            elapsed_seconds = three_hours

        if elapsed_seconds < twenty_four_hours:
            wait = twenty_four_hours - elapsed_seconds
            log.info(f"🔄 Resuming 24-hour FOMO for {user_id} in {wait/60:.1f} min")
            await asyncio.sleep(wait)
            if user_id not in users_registered:
                await send_text_safe(sender, user_id, FOMO_24HOURS_MSG, parse_mode="md")
                await asyncio.sleep(5)
                await send_text_safe(sender, user_id, GUARANTEE_MSG, parse_mode="md")
                await sender.send_message(user_id, "🎁 استفد من العرض الخاص:", buttons=create_action_buttons())
                log.info(f"✅ Sent 24-hour FOMO + Guarantee to {user_id}")

    except asyncio.CancelledError:
        log.info(f"⚠️ Resumed follow-up task cancelled for user {user_id}")
    except Exception as e:
        log.error(f"❌ Error in resumed follow-up for {user_id}: {e}")
    finally:
        if user_id in _follow_up_tasks:
            del _follow_up_tasks[user_id]

async def smart_follow_up_system(user_id: int):
    """نظام المتابعة الذكي - يرسل رسائل FOMO حسب وقت انضمام العضو"""
    try:
        log.info(f"🎯 Starting smart follow-up for user {user_id}")

        # انتظار 30 دقيقة - الرسالة الأولى
        await asyncio.sleep(30 * 60)  # 30 minutes
        if user_id not in users_registered:
            sender = get_sender_client()
            await send_text_safe(sender, user_id, FOMO_30MIN_MSG, parse_mode="md")
            await sender.send_message(user_id, "👇 اضغط على الأزرار للبدء:", buttons=create_action_buttons())
            log.info(f"✅ Sent 30-min FOMO to {user_id}")

        # انتظار حتى 3 ساعات - الرسالة الثانية
        await asyncio.sleep(2.5 * 60 * 60)  # 2.5 hours more (total 3 hours)
        if user_id not in users_registered:
            sender = get_sender_client()
            await send_text_safe(sender, user_id, FOMO_3HOURS_MSG, parse_mode="md")
            await sender.send_message(user_id, "⚡ لا تفوت الفرصة:", buttons=create_action_buttons())
            log.info(f"✅ Sent 3-hour FOMO to {user_id}")

        # انتظار حتى 24 ساعة - رسالة الضمان
        await asyncio.sleep(21 * 60 * 60)  # 21 hours more (total 24 hours)
        if user_id not in users_registered:
            sender = get_sender_client()
            await send_text_safe(sender, user_id, FOMO_24HOURS_MSG, parse_mode="md")
            await asyncio.sleep(5)
            await send_text_safe(sender, user_id, GUARANTEE_MSG, parse_mode="md")
            await sender.send_message(user_id, "🎁 استفد من العرض الخاص:", buttons=create_action_buttons())
            log.info(f"✅ Sent 24-hour FOMO + Guarantee to {user_id}")

    except asyncio.CancelledError:
        log.info(f"⚠️ Follow-up task cancelled for user {user_id}")
    except Exception as e:
        log.error(f"❌ Error in smart follow-up for {user_id}: {e}")
    finally:
        # تنظيف المهمة من الذاكرة عند الانتهاء لتجنب memory leak
        if user_id in _follow_up_tasks:
            del _follow_up_tasks[user_id]
            log.debug(f"🧹 Cleaned up follow-up task for user {user_id}")

# ---------------- Welcome Bot Logic ----------------
async def send_followup_messages(user_id: int):
    lock = get_user_lock(user_id)
    if lock.locked():
        log.info(f"User {user_id} already being processed — skipping duplicate.")
        return False
    async with lock:
        sender = get_sender_client()
        try:
            await safe_sleep(DELAY_BETWEEN_MESSAGES)
            await sender.send_message(user_id, SECOND_MSG, parse_mode="md", buttons=create_action_buttons())

            await safe_sleep(DELAY_BETWEEN_MESSAGES)
            await send_photos_with_caption(sender, user_id, APPLE_GAME_PHOTOS, THIRD_MSG, buttons=create_action_buttons())

            await safe_sleep(DELAY_BETWEEN_MESSAGES)
            await sender.send_message(user_id, FOURTH_MSG, parse_mode="md", buttons=create_action_buttons())

            # إضافة رسالة الدعم في النهاية كآخر رسالة
            await safe_sleep(DELAY_BETWEEN_MESSAGES)
            await sender.send_message(user_id, FINAL_SUPPORT_MSG, parse_mode="md", buttons=create_action_buttons())

            users_sent.add(user_id)
            users_final_replied.add(user_id)  # إضافة العضو لقائمة من تلقى الرد النهائي
            save_state()
            log.info(f"✅ Completed followups and final support message for {user_id}")
        except Exception as e:
            log.error(f"❌ Error sending followup messages to {user_id}: {e}")

async def send_welcome_to_user(user_id: int, user_name: str = "عضو جديد"):
    """إرسال رسالة ترحيب للعضو الجديد باستخدام user_id مباشرة"""
    log.info(f"🎯 Welcoming user {user_id} ({user_name})")

    sender = get_sender_client()
    lock = get_user_lock(user_id)
    if lock.locked():
        log.info(f"User {user_id} already being processed — skipping welcome.")
        return False

    async with lock:
        try:
            # محاولة إرسال الرسالة مباشرة باستخدام user_id مع الأزرار
            await sender.send_message(user_id, WELCOME_MSG, parse_mode="md", buttons=create_action_buttons())

            users_welcomed.add(user_id)
            users_join_time[user_id] = time.time()  # حفظ وقت الانضمام
            save_state()
            log.info(f"✅ Sent initial welcome to {user_id} ({user_name})")

            # بدء إرسال باقي الرسائل بعد 5 ثواني
            await asyncio.sleep(5)
            asyncio.create_task(send_followup_messages(user_id))

            # بدء نظام المتابعة الذكي
            task = asyncio.create_task(smart_follow_up_system(user_id))
            _follow_up_tasks[user_id] = task
            log.info(f"🎯 Started smart follow-up system for {user_id}")

            return True
        except Exception as e:
            log.error(f"❌ Failed to send initial welcome to {user_id}: {e}")
            return False

# ---------------- Daily Scheduler ----------------
async def daily_scheduler():
    sent_today = {"plan1": False, "plan2": False, "plan3": False}
    log.info("📅 Daily scheduler started.")
    while True:
        now = datetime.now(TIMEZONE)

        # Reset at midnight (00:00)
        if now.hour == 0 and now.minute == 0 and now.second < 10:
            sent_today = {"plan1": False, "plan2": False, "plan3": False}
            log.info("🔄 Reset daily sent flags")

        # Send plans at specific times
        if now.hour == 20 and now.minute == 0 and not sent_today["plan1"]:
            await send_plan_one()
            sent_today["plan1"] = True
        if now.hour == 22 and now.minute == 0 and not sent_today["plan2"]:
            await send_plan_two()
            sent_today["plan2"] = True
        if now.hour == 0 and now.minute == 0 and not sent_today["plan3"]:
            await send_plan_three()
            sent_today["plan3"] = True

        await asyncio.sleep(60)

# ---------------- Bot Status Check ----------------
async def check_bot_status():
    if bot_client and bot_started:
        try:
            me = await bot_client.get_me()
            log.info(f"✅ البوت يعمل كـ: @{me.username} (ID: {me.id})")
            return True
        except Exception as e:
            log.error(f"❌ البوت غير متصل: {e}")
            return False
    else:
        log.warning("⚠️ البوت غير مفعل (BOT_TOKEN غير مستخدم)")
        return False

# ---------------- Bot Handlers Setup ----------------
def setup_bot_handlers():
    """إعداد handlers البوت بعد التأكد من اتصاله"""
    if bot_client and bot_started:

        @bot_client.on(events.NewMessage(pattern="/start"))
        async def start_handler(event):
            log.info(f"🎯 START HANDLER TRIGGERED - User: {event.sender_id}")
            try:
                user_id = event.sender_id
                await bot_client.send_message(user_id, WELCOME_MSG, parse_mode="md", buttons=create_action_buttons())

                users_welcomed.add(user_id)
                users_join_time[user_id] = time.time()  # حفظ وقت الانضمام
                save_state()
                log.info(f"✅ Sent /start welcome to {user_id}")

                await asyncio.sleep(5)
                asyncio.create_task(send_followup_messages(user_id))

                # بدء نظام المتابعة الذكي
                task = asyncio.create_task(smart_follow_up_system(user_id))
                _follow_up_tasks[user_id] = task
                log.info(f"🎯 Started smart follow-up system for {user_id}")
            except Exception as e:
                log.error(f"❌ Error in start_handler: {e}")

        @bot_client.on(events.NewMessage(pattern="/admin"))
        async def admin_handler(event):
            if event.sender_id != ADMIN_ID:
                await event.respond("⛔ غير مصرح لك باستخدام هذا الأمر")
                return

            admin_menu = """🎛️ **لوحة تحكم Admin**

📊 الأوامر المتاحة:

/stats - عرض الإحصائيات ومعدل التحويل
/status - حالة البوت
/broadcast - إرسال رسالة جماعية
/send_signal - إرسال إشارة جديدة الآن
/listchannels - عرض قائمة القنوات المتاحة
/setchannel [ID] - تحديد القناة المستهدفة
/mark_registered [user_id] - تسجيل عضو كمسجل (إيقاف FOMO)
/admin - عرض هذه القائمة

━━━━━━━━━━━━━━━━━
✅ البوت يعمل بنجاح!
🎯 نظام FOMO النشط!"""

            await event.respond(admin_menu)
            log.info(f"✅ Admin menu sent to {event.sender_id}")

        @bot_client.on(events.NewMessage(pattern="/stats"))
        async def stats_handler(event):
            if event.sender_id != ADMIN_ID:
                await event.respond("⛔ غير مصرح لك باستخدام هذا الأمر")
                return

            total_welcomed = len(users_welcomed)
            total_sent = len(users_sent)
            total_final = len(users_final_replied)
            total_registered = len(users_registered)

            # حساب معدل التحويل
            conversion_rate = (total_registered / total_welcomed * 100) if total_welcomed > 0 else 0

            stats_msg = f"""📊 **إحصائيات البوت**

👥 إجمالي الأعضاء الجدد: {total_welcomed}
📨 رسائل المتابعة المرسلة: {total_sent}
✅ أعضاء استلموا جميع الرسائل: {total_final}
🎯 أعضاء مسجلين: {total_registered}
📈 معدل التحويل: {conversion_rate:.1f}%

📅 التاريخ: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}
🕐 المنطقة الزمنية: Africa/Cairo

💡 استخدم /mark_registered [user_id] لتسجيل عضو كمسجل"""

            await event.respond(stats_msg)
            log.info(f"✅ Stats sent to {event.sender_id}")

        @bot_client.on(events.NewMessage(pattern="/status"))
        async def status_handler(event):
            if event.sender_id != ADMIN_ID:
                await event.respond("⛔ غير مصرح لك باستخدام هذا الأمر")
                return

            bot_status = "🟢 نشط" if bot_started else "🔴 غير نشط"
            channel_name = getattr(user_target_channel, 'title', 'Unknown')

            status_msg = f"""⚡ **حالة البوت**

🤖 حالة البوت: {bot_status}
📢 القناة المستهدفة: {channel_name}
🆔 ID القناة: {CHANNEL_IDENTIFIER}
👥 عدد الأعضاء: {len(users_welcomed)}

⏰ الوقت الحالي: {datetime.now(TIMEZONE).strftime('%H:%M:%S')}
📅 التاريخ: {datetime.now(TIMEZONE).strftime('%Y-%m-%d')}"""

            await event.respond(status_msg)
            log.info(f"✅ Status sent to {event.sender_id}")

        @bot_client.on(events.NewMessage(pattern="/broadcast"))
        async def broadcast_handler(event):
            if event.sender_id != ADMIN_ID:
                await event.respond("⛔ غير مصرح لك باستخدام هذا الأمر")
                return

            _broadcast_mode[event.sender_id] = True
            await event.respond("📢 **إرسال رسالة جماعية**\n\nأرسل الرسالة التي تريد إرسالها لجميع الأعضاء:\n\n(أو أرسل /cancel للإلغاء)")
            log.info(f"📢 Broadcast mode activated by {event.sender_id}")

        @bot_client.on(events.NewMessage(pattern="/send_signal"))
        async def send_signal_handler(event):
            if event.sender_id != ADMIN_ID:
                await event.respond("⛔ غير مصرح لك باستخدام هذا الأمر")
                return

            await event.respond("🎮 جاري إرسال إشارة جديدة...")
            asyncio.create_task(send_apple_game())
            await event.respond("✅ تم إرسال الإشارة بنجاح!")
            log.info(f"🎮 Manual signal sent by admin {event.sender_id}")

        @bot_client.on(events.NewMessage(pattern="/listchannels"))
        async def listchannels_handler(event):
            if event.sender_id != ADMIN_ID:
                await event.respond("⛔ غير مصرح لك باستخدام هذا الأمر")
                return

            await event.respond("🔍 جاري البحث عن القنوات...")
            channels_list = []
            try:
                async for dialog in user_client.iter_dialogs():
                    if dialog.is_channel:
                        channels_list.append(f"📢 {dialog.title}\n🆔 ID: `{dialog.id}`")

                if channels_list:
                    response = "📋 **القنوات المتاحة:**\n\n" + "\n\n".join(channels_list[:10])
                    if len(channels_list) > 10:
                        response += f"\n\n... و {len(channels_list) - 10} قناة أخرى"
                    response += "\n\n💡 استخدم /setchannel [ID] لتحديد القناة"
                else:
                    response = "⚠️ لم يتم العثور على أي قنوات"

                await event.respond(response)
                log.info(f"✅ Channels list sent to {event.sender_id}")
            except Exception as e:
                await event.respond(f"❌ حدث خطأ: {e}")
                log.error(f"Error listing channels: {e}")

        @bot_client.on(events.NewMessage(pattern=r"/mark_registered\s+(.+)"))
        async def mark_registered_handler(event):
            if event.sender_id != ADMIN_ID:
                await event.respond("⛔ غير مصرح لك باستخدام هذا الأمر")
                return

            try:
                user_id_str = event.pattern_match.group(1).strip()
                user_id = int(user_id_str)

                users_registered.add(user_id)
                save_state()

                # إلغاء مهمة المتابعة إذا كانت موجودة
                if user_id in _follow_up_tasks:
                    _follow_up_tasks[user_id].cancel()
                    del _follow_up_tasks[user_id]
                    log.info(f"🚫 Cancelled follow-up task for user {user_id}")

                await event.respond(f"✅ تم تسجيل العضو {user_id} كعضو مسجل!\n\n🛑 تم إيقاف رسائل المتابعة التلقائية له.")
                log.info(f"✅ User {user_id} marked as registered by admin")
            except ValueError:
                await event.respond("❌ خطأ: يجب إدخال رقم صحيح\n\nمثال: /mark_registered 123456789")
            except Exception as e:
                await event.respond(f"❌ حدث خطأ: {e}")
                log.error(f"Error marking user as registered: {e}")

        @bot_client.on(events.NewMessage(pattern=r"/setchannel\s+(.+)"))
        async def setchannel_handler(event):
            global user_target_channel, CHANNEL_IDENTIFIER
            if event.sender_id != ADMIN_ID:
                await event.respond("⛔ غير مصرح لك باستخدام هذا الأمر")
                return

            channel_id = event.pattern_match.group(1).strip()
            await event.respond(f"🔍 جاري البحث عن القناة: {channel_id}...")

            try:
                # محاولة الحصول على القناة
                if channel_id.isdigit() or channel_id.startswith('-'):
                    new_channel = await user_client.get_entity(int(channel_id))
                else:
                    new_channel = await find_channel_by_name(channel_id)

                if new_channel:
                    user_target_channel = new_channel
                    CHANNEL_IDENTIFIER = getattr(new_channel, 'id', channel_id)
                    channel_name = getattr(new_channel, 'title', 'Unknown')
                    await event.respond(f"✅ تم تحديد القناة بنجاح!\n\n📢 {channel_name}\n🆔 ID: {CHANNEL_IDENTIFIER}")
                    log.info(f"✅ Channel set to: {channel_name} (ID: {CHANNEL_IDENTIFIER})")
                else:
                    await event.respond("❌ لم يتم العثور على القناة")
            except Exception as e:
                await event.respond(f"❌ حدث خطأ: {e}")
                log.error(f"Error setting channel: {e}")

        @bot_client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def pm_handler(event):
            if event.raw_text and event.raw_text.strip() != "/start":
                log.info(f"💬 PM HANDLER TRIGGERED - User: {event.sender_id}, Text: {event.raw_text}")
                try:
                    user_id = event.sender_id

                    # معالجة البرودكاست للأدمن
                    if user_id == ADMIN_ID and _broadcast_mode.get(user_id, False):
                        if event.raw_text.strip() == "/cancel":
                            _broadcast_mode[user_id] = False
                            await event.respond("✅ تم إلغاء البرودكاست")
                            log.info(f"📢 Broadcast cancelled by admin")
                            return

                        # إرسال الرسالة لكل الأعضاء
                        _broadcast_mode[user_id] = False
                        await event.respond(f"📢 جاري إرسال الرسالة لـ {len(users_welcomed)} عضو...")

                        # تحميل الميديا مرة واحدة إذا كانت موجودة
                        media_file = None
                        if event.message.media:
                            try:
                                media_file = await event.message.download_media(file=bytes)
                            except Exception as e:
                                log.error(f"Failed to download media: {e}")

                        sent_count = 0
                        failed_count = 0
                        for uid in users_welcomed:
                            try:
                                # إرسال الرسالة مباشرة بدون forward
                                if media_file:
                                    # إذا كانت الرسالة تحتوي على ميديا (صور، فيديو، ملفات)
                                    await bot_client.send_file(
                                        uid, 
                                        media_file,
                                        caption=event.message.text or ""
                                    )
                                else:
                                    # إذا كانت رسالة نصية فقط
                                    await bot_client.send_message(uid, event.message.text)
                                sent_count += 1
                                await asyncio.sleep(0.1)  # تأخير بسيط لتجنب FloodWait
                            except Exception as e:
                                failed_count += 1
                                log.error(f"Failed to send broadcast to {uid}: {e}")

                        await event.respond(f"✅ تم إرسال البرودكاست!\n\n✅ نجح: {sent_count}\n❌ فشل: {failed_count}")
                        log.info(f"📢 Broadcast sent: {sent_count} success, {failed_count} failed")
                        return

                    # إذا العضو لم يستلم كل الرسائل بعد، أرسلها له
                    if user_id not in users_sent:
                        asyncio.create_task(send_followup_messages(user_id))
                    # إذا تلقى كل شيء، لا ترد على أي رسائل أخرى
                    else:
                        log.info(f"⚠️ Ignoring message from {user_id} - already received all messages")

                except Exception as e:
                    log.error(f"❌ Error in pm_handler: {e}")

        log.info("✅ Bot handlers registered successfully")

# ---------------- Events Handlers ----------------
@user_client.on(events.Raw(types=[UpdatePendingJoinRequests]))
async def handle_join_requests(event):
    global _is_processing_join_event

    try:
        if not user_target_channel:
            log.warning("No target channel set - skipping auto-approve.")
            return

        # ✅ التحقق من أن الحدث خاص بالقناة المستهدفة فقط
        event_peer_id = getattr(event.peer, 'channel_id', None)
        target_channel_id = getattr(user_target_channel, 'id', None)

        if event_peer_id != target_channel_id:
            log.info(f"⏭️ Ignoring join request event for different channel (event: {event_peer_id}, target: {target_channel_id})")
            return

        # ✅ حماية من التنفيذ المتزامن - تجاهل الحدث إذا كان handler شغال
        if _join_handler_lock.locked():
            log.info(f"⏭️ Handler already processing join event - skipping duplicate")
            return

        async with _join_handler_lock:
            log.info(f"👥 Detected pending join requests event for our channel ({target_channel_id}).")

            try:
                # استخدام event.peer بدلاً من user_target_channel للتأكد من الموافقة على القناة الصحيحة
                await user_client(HideAllChatJoinRequestsRequest(peer=event.peer, approved=True, link=None))
                log.info("✅ Approved pending join requests.")
            except FloodWaitError as fe:
                log.warning(f"FloodWait during approve: wait {fe.seconds}s")
                await safe_sleep(fe.seconds + 1)
            except Exception as e:
                log.error(f"❌ Error approving requests: {e}")

            if hasattr(event, "recent_requesters") and event.recent_requesters:
                log.info(f"👤 Recent requesters: {len(event.recent_requesters)}")

                # تنظيف المدخلات القديمة من قائمة المعالجة
                current_time = time.time()
                expired_users = [u for u, t in _recently_processed_joins.items() if current_time - t > _JOIN_DEDUP_WINDOW]
                for u in expired_users:
                    del _recently_processed_joins[u]

                for uid in event.recent_requesters:
                    try:
                        # ✅ حماية من التكرار: تحقق إذا تم معالجة هذا العضو مؤخراً
                        if uid in _recently_processed_joins:
                            log.info(f"⏭️ Skipping uid {uid} - already processed recently")
                            continue

                        # تسجيل أن العضو تم معالجته
                        _recently_processed_joins[uid] = current_time

                        # محاولة الحصول على بيانات العضو (اختياري)
                        user_name = "عضو جديد"
                        try:
                            ent = await safe_get_entity(user_client, uid)
                            if ent:
                                user_name = getattr(ent, "first_name", "عضو جديد")
                        except:
                            pass  # لا بأس إذا فشل في الحصول على اسم العضو

                        # إرسال الترحيب باستخدام user_id مباشرة
                        await send_welcome_to_user(uid, user_name)
                        await safe_sleep(1.5)
                    except Exception as e:
                        log.error(f"❌ Error welcoming uid {uid}: {e}")
    except Exception as e:
        log.error(f"❌ Error in handle_join_requests: {e}")

# تم تعطيل ChatAction handler لمنع التكرار - نعتمد فقط على handle_join_requests
# @user_client.on(events.ChatAction())
# async def handle_chat_action(event):
#     try:
#         if not user_target_channel:
#             return
#         chat_id = getattr(event.chat, "id", getattr(event, "chat_id", None))
#         target_id = getattr(user_target_channel, "id", getattr(user_target_channel, "channel_id", None))
#         if chat_id == target_id:
#             if getattr(event, "user_joined", False) or getattr(event, "user_added", False):
#                 user_name = "عضو جديد"
#                 try:
#                     user = await safe_get_entity(user_client, event.user_id)
#                     if user:
#                         user_name = getattr(user, "first_name", "عضو جديد")
#                 except:
#                     pass
#                 
#                 log.info(f"👤 User joined via ChatAction: {event.user_id} / {user_name}")
#                 await send_welcome_to_user(event.user_id, user_name)
#     except Exception as e:
#         log.error(f"❌ Error in handle_chat_action: {e}")

# ---------------- helper: find target channel once ----------------
async def find_channel_by_name(channel_name: str) -> Optional[object]:
    """البحث عن القناة بالاسم في القنوات التي ينتمي لها الحساب"""
    try:
        async for dialog in user_client.iter_dialogs():
            if dialog.is_channel:
                # البحث بالعنوان
                if dialog.title and channel_name.lower() in dialog.title.lower():
                    log.info(f"✅ Found channel: {dialog.title} (ID: {dialog.id})")
                    return dialog.entity
        log.warning(f"⚠️ Channel '{channel_name}' not found")
        return None
    except Exception as e:
        log.error(f"❌ Error searching for channel by name: {e}")
        return None

async def find_target_channel_once() -> Optional[object]:
    """البحث عن القناة المستهدفة بالمعرف أو الاسم"""
    if not CHANNEL_IDENTIFIER:
        log.warning("⚠️ No CHANNEL_IDENTIFIER set, will need manual setup")
        return None

    try:
        # محاولة استخدام المعرف مباشرة
        if str(CHANNEL_IDENTIFIER).isdigit() or str(CHANNEL_IDENTIFIER).startswith('-'):
            return await user_client.get_entity(int(CHANNEL_IDENTIFIER))
        else:
            # البحث بالاسم
            return await find_channel_by_name(CHANNEL_IDENTIFIER)
    except Exception as e:
        log.warning(f"⚠️ Could not find channel by ID, trying by name: {e}")
        # محاولة البحث بالاسم
        return await find_channel_by_name(str(CHANNEL_IDENTIFIER))

# ---------------- main ----------------
async def main():
    global message_host, user_target_channel, bot_started
    load_state()

    # start user client
    try:
        await user_client.start(phone=PHONE, password=PASSWORD)
        me = await user_client.get_me()
        log.info(f"✅ User client started as @{getattr(me,'username','unknown')}")
    except Exception as e:
        log.critical(f"❌ Failed to start user client: {e}")
        return

    # start bot client if provided
    if bot_client and BOT_TOKEN:
        try:
            await bot_client.start(bot_token=BOT_TOKEN)
            binfo = await bot_client.get_me()
            bot_started = True
            log.info(f"✅ Bot client started as @{getattr(binfo,'username','unknown')}")

            # التحقق من حالة البوت وتسجيل الـ handlers
            bot_status = await check_bot_status()
            if bot_status:
                setup_bot_handlers()
            else:
                log.warning("⚠️ Bot handlers not registered due to connection issues")

        except Exception as e:
            log.error(f"❌ Failed to start bot client: {e}")
            bot_started = False

    # find target channel
    log.info("🔍 Searching for target channel...")
    user_target_channel = await find_target_channel_once()
    if not user_target_channel:
        log.critical(f"❌ Could not find target channel '{CHANNEL_IDENTIFIER}'. Please set TELEGRAM_CHANNEL correctly and ensure the account has access.")
        try:
            if user_client.is_connected(): 
                await user_client.disconnect()
            if bot_client and bot_started and bot_client.is_connected(): 
                await bot_client.disconnect()
        except Exception:
            pass
        return

    log.info(f"🎯 Target channel set: {getattr(user_target_channel,'title', str(user_target_channel))}")

    # اختيار host الرسائل
    message_host = bot_client if (bot_client and bot_started) else user_client

    if message_host == user_client:
        log.info("📞 Listening for PMs on the user account.")
    else:
        log.info("🤖 Listening for PMs on the bot account.")

    log.info("🚀 Ready — listening for events.")

    # استعادة مهام المتابعة للأعضاء الذين لم يسجلوا بعد
    await restore_pending_followups()

    # تشغيل جميع المهام
    try:
        await asyncio.gather(
            daily_scheduler(),
            apple_game_loop(),
            user_client.run_until_disconnected(),
            bot_client.run_until_disconnected() if bot_client and bot_started else asyncio.sleep(999999)
        )
    except Exception as e:
        log.error(f"❌ Error in main loop: {e}")
    finally:
        try:
            if user_client.is_connected(): 
                await user_client.disconnect()
            if bot_client and getattr(bot_client, "is_connected", lambda: False)(): 
                await bot_client.disconnect()
        except Exception:
            pass
        log.info("🛑 Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("⏹️ Interrupted by user.")
    except Exception as e:
        log.error(f"💥 Error in main run: {e}")
