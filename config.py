"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY PERSIAN"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "PERSIAN"
HANDLE = "@velocitypersian"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'fa',
 'name': 'Persian',
 'native_name': 'فارسی',
 'history_key': 'persian',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'fa-IR-DilaraNeural',
 'native_fallback_voice': 'fa-IR-FaridNeural',
 'native_engine': 'edge',
 'native_lang_code': 'fa',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'فارسی',
 'translit_label': 'SAY IT LIKE',
 'flag': 'ir',
 'greeting': 'سلام!',
 'encouragement': 'عالی!',
 'rtl': True,
 'char_tiles': False,
 'script_font': 'Script.ttf',
 'glyphs': 'ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'انگیزه',
 'Love': 'عشق',
 'Success': 'موفقیت',
 'Wisdom': 'خرد',
 'Happiness': 'خوشبختی',
 'Self Improvement': 'خودسازی',
 'Gratitude': 'قدردانی',
 'Friendship': 'دوستی',
 'Hope': 'امید',
 'Creativity': 'خلاقیت',
 'Inner Peace': 'آرامش درون',
 'Confidence': 'اعتماد به نفس',
 'Perseverance': 'استقامت',
 'Inspiration': 'الهام',
 'Positive Life': 'زندگی مثبت',
 'Courage': 'شجاعت',
 'Kindness': 'مهربانی',
 'Patience': 'صبر',
 'Forgiveness': 'بخشش',
 'Strength': 'قدرت',
 'Joy': 'شادی',
 'Balance': 'تعادل',
 'Growth': 'رشد',
 'Purpose': 'هدف',
 'Mindfulness': 'ذهن آگاهی',
 'Travel & Airport': 'سفر و فرودگاه',
 'Ordering Food & Dining': 'سفارش غذا و رستوران\u200cداری',
 'Shopping & Prices': 'خرید و قیمت\u200cها',
 'Asking for Directions': 'پرسیدن آدرس',
 'Hotel & Accommodation': 'هتل و اقامتگاه',
 'Daily Routine': 'روال روزانه',
 'Meeting People & Greetings': 'آشنایی با افراد و احوالپرسی',
 'Emergency & Health': 'مواقع اضطراری و سلامتی',
 'Public Transportation': 'حمل و نقل عمومی',
 'Work & Office': 'کار و محیط اداری',
 'Weather & Small Talk': 'هوا و گپ\u200cهای کوتاه',
 'Coffee Shop & Bakery': 'کافی\u200cشاپ و نانوایی',
 'Family & Home': 'خانواده و خانه',
 'Hobbies & Free Time': 'سرگرمی\u200cها و اوقات فراغت',
 'Dating & Romance': 'قرار ملاقات و روابط عاشقانه',
 'Phone Calls & Messages': 'تماس\u200cهای تلفنی و پیام\u200cها',
 'Banking & Money': 'بانکداری و پول',
 'Doctor & Pharmacy': 'دکتر و داروخانه',
 'Sports & Fitness': 'ورزش و تناسب اندام',
 'Celebrations & Parties': 'جشن\u200cها و مهمانی\u200cها',
 'Feelings & Emotions': 'احساسات و عواطف',
 'Agreeing & Disagreeing': 'موافقت و مخالفت',
 'Making Plans': 'برنامه\u200cریزی',
 'Common Native Slang': 'اصطلاحات عامیانه رایج',
 'Cultural Traditions': 'رسوم فرهنگی'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnpersian',
 '#persianlessons',
 '#persianforbeginners',
 '#languagelearning',
 '#persianvocabulary',
 '#velocitypersian',
 '#dailypersian',
 '#persian',
 '#learnlanguages',
 '#speakpersian']
# ==== HASHTAGS END ====
