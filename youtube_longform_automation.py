"""
YouTube Long-Form Video Automation - Bilingual English/Persian Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Persian translations
CATEGORIES_PERSIAN = {
    "Motivation": "انگیزه",
    "Love": "عشق",
    "Success": "موفقیت",
    "Wisdom": "خرد",
    "Happiness": "خوشبختی",
    "Self Improvement": "خودسازی",
    "Gratitude": "قدردانی",
    "Friendship": "دوستی",
    "Hope": "امید",
    "Creativity": "خلاقیت",
    "Inner Peace": "آرامش درون",
    "Confidence": "اعتماد به نفس",
    "Perseverance": "استقامت",
    "Inspiration": "الهام",
    "Positive Life": "زندگی مثبت",
    "Courage": "شجاعت",
    "Kindness": "مهربانی",
    "Patience": "صبر",
    "Forgiveness": "بخشش",
    "Strength": "قدرت",
    "Joy": "شادی",
    "Balance": "تعادل",
    "Growth": "رشد",
    "Purpose": "هدف",
    "Mindfulness": "ذهن آگاهی",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "fa-IR-DilaraNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "persian": phrase["persian"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_persian = CATEGORIES_PERSIAN[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Persian.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - ABSOLUTELY ZERO Persian IN ENGLISH FIELD:
The "english" field must contain ONLY English words. NO Persian words at all.
The "persian" field contains the Persian translation.
The "pronunciation" field is phonetic English spelling approximating Persian sounds.

These are INSPIRATIONAL PHRASES about the topic, NOT language-learning tips.

WRONG (teaching tip with Persian words): {{"english": "Don't say 'chetori,' it means more than 'hello.'", ...}}
WRONG (Persian word in english): {{"english": "Use 'motshakeram' for thank you", ...}}
WRONG (lesson tip): {{"english": "Say 'khodahafez' for goodbye", ...}}
CORRECT (pure english phrase): {{"english": "Knowledge is the key to wisdom.", "persian": "دانش کلید خرد است.", "pronunciation": "da-nesh ke-li-de khe-rad ast"}}
CORRECT: {{"english": "A wise person listens more than they speak.", "persian": "انسان خردمند بیشتر گوش می‌دهد تا اینکه صحبت کند.", "pronunciation": "en-san-e khe-rad-mand bish-tar gush mi-da-had ta in-ke soh-bat ko-nad"}}

The english field MUST be 100% English words only. Absolutely NO Persian words in the english field.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Persian words) with commas for natural pauses
2. Persian translation
3. Pronunciation guide (phonetic English spelling)

Return as JSON array:
[{{"english": "...", "persian": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You create INSPIRATIONAL PHRASES for YouTube language learning videos. CRITICAL: The 'english' field must be PURE ENGLISH with ZERO Persian words - no Persian words at all. These are universal inspirational phrases, NOT language learning tips. Persian goes ONLY in the 'persian' field."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "persian": "به خودت ایمان داشته باش.", "pronunciation": "be kho-det i-man dashteh bash"},
            {"english": "You are capable of amazing things.", "persian": "تو توانایی انجام کارهای شگفت‌انگیز را داری.", "pronunciation": "to ta-va-nai-ye an-jam-e kar-haye she-gift-an-giz ra da-ri"},
            {"english": "Dream big, start small.", "persian": "بزرگ آرزو کن، کوچک شروع کن.", "pronunciation": "bo-zorg ar-zu kon, ku-chak shu-ru kon"},
            {"english": "Your future is created by your actions.", "persian": "آینده تو توسط اعمالت ساخته می‌شود.", "pronunciation": "a-yan-deh to ta-vas-sot-e a-ma-lat sakhteh mi-shav-ad"},
            {"english": "Never give up on your dreams.", "persian": "هرگز از رویاهایت دست نکش.", "pronunciation": "har-gez az ru-ya-ha-yat dast na-kosh"},
            {"english": "Small steps lead to big changes.", "persian": "قدم‌های کوچک به تغییرات بزرگ منجر می‌شوند.", "pronunciation": "gha-dam-haye ku-chak be tagh-iy-rat-e bo-zorg mon-jaer mi-sha-vand"},
            {"english": "You are stronger than you think.", "persian": "تو قوی‌تر از آنی که فکر می‌کنی.", "pronunciation": "to ghavi-tar az a-ni ke fekr mi-ko-ni"},
        ],
        "Love": [
            {"english": "Love yourself first.", "persian": "اول خودت را دوست داشته باش.", "pronunciation": "a-val kho-det ra dust dashteh bash"},
            {"english": "Love makes everything possible.", "persian": "عشق همه چیز را ممکن می‌سازد.", "pronunciation": "eshgh hameh chiz ra momken mi-sa-zad"},
            {"english": "My heart beats for you.", "persian": "قلبم برای تو می‌تپد.", "pronunciation": "ghalbam ba-ray-e to mi-ta-pad"},
            {"english": "You are my everything.", "persian": "تو همه چیز منی.", "pronunciation": "to hameh chiz ma-ni"},
            {"english": "Together forever, hand in hand.", "persian": "تا ابد با هم، دست در دست.", "pronunciation": "ta a-bad ba ham, dast dar dast"},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "persian": "موفقیت از کار سخت به دست می‌آید.", "pronunciation": "mov-fa-ghiy-at az kar-e sakht be dast mi-ayad"},
            {"english": "Keep going, you're getting there.", "persian": "ادامه بده، به آنجا می‌رسی.", "pronunciation": "e-da-meh be-dah, be an-ja mi-rasi"},
            {"english": "Winners never quit.", "persian": "برندگان هرگز تسلیم نمی‌شوند.", "pronunciation": "ba-ran-degan har-gez tas-lim nemi-shav-and"},
            {"english": "Your effort will pay off.", "persian": "تلاشت نتیجه خواهد داد.", "pronunciation": "ta-la-hat na-ti-jeh kha-had dad"},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "persian": "دانش قدرت است.", "pronunciation": "da-nesh ghod-rat ast"},
            {"english": "Learn from yesterday, live for today.", "persian": "از دیروز بیاموز، برای امروز زندگی کن.", "pronunciation": "az di-ruz bi-amuz, ba-ray-e em-ruz zen-de-gi kon"},
            {"english": "Think before you act.", "persian": "قبل از عمل فکر کن.", "pronunciation": "ghabl az amal fekr kon"},
            {"english": "Experience is the best teacher.", "persian": "تجربه بهترین معلم است.", "pronunciation": "taj-robeh beh-tarin mo-allem ast"},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "persian": "خوشبختی یک انتخاب است.", "pronunciation": "khosh-bakh-ti yek en-te-khab ast"},
            {"english": "Find joy in the little things.", "persian": "شادی را در چیزهای کوچک پیدا کن.", "pronunciation": "sha-di ra dar chiz-haye ku-chak pey-da kon"},
            {"english": "Smile, it makes others happy.", "persian": "لبخند بزن، دیگران را شاد می‌کند.", "pronunciation": "lab-khand be-zan, di-ga-ran ra shad mi-ko-nad"},
            {"english": "Today is a gift.", "persian": "امروز یک هدیه است.", "pronunciation": "em-ruz yek he-di-yeh ast"},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "persian": "بهتر از دیروز باش.", "pronunciation": "beh-tar az di-ruz bash"},
            {"english": "Grow through what you go through.", "persian": "از آنچه می‌گذری رشد کن.", "pronunciation": "az an-cheh mi-goza-ri roshd kon"},
            {"english": "Invest in yourself daily.", "persian": "هر روز در خودت سرمایه‌گذاری کن.", "pronunciation": "har ruz dar kho-det sar-ma-yeh-goza-ri kon"},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "persian": "برای همه چیز متشکرم.", "pronunciation": "ba-ray-e hameh chiz mot-shak-eram"},
            {"english": "I appreciate your help.", "persian": "از کمک تو سپاسگزارم.", "pronunciation": "az ko-ma-kat se-pas-go-zaram"},
            {"english": "Grateful for this moment.", "persian": "سپاسگزار این لحظه هستم.", "pronunciation": "se-pas-go-zar-e in lah-zeh has-tam"},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "persian": "دوستان برای همیشه، مهم نیست چه پیش بیاید.", "pronunciation": "du-stan ba-ray-e ha-mi-sheh, mo-hem nist cheh pish bi-ya-yad"},
            {"english": "You are my best friend.", "persian": "تو بهترین دوست منی.", "pronunciation": "to beh-tarin dust ma-ni"},
            {"english": "True friends stick together.", "persian": "دوستان واقعی کنار هم می‌مانند.", "pronunciation": "du-stan-e va-geh-i ke-nar-e ham mi-man-and"},
        ],
        "Hope": [
            {"english": "There is always hope.", "persian": "همیشه امید هست.", "pronunciation": "ha-mi-sheh o-mid hast"},
            {"english": "Better days are coming.", "persian": "روزهای بهتری در راه است.", "pronunciation": "ruz-haye beh-ta-ri dar rah ast"},
            {"english": "Keep faith, keep going.", "persian": "ایمان داشته باش، ادامه بده.", "pronunciation": "i-man dashteh bash, e-da-meh be-dah"},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "persian": "امروز چیزی زیبا خلق کن.", "pronunciation": "em-ruz chi-zi zi-ba khalgh kon"},
            {"english": "Your imagination is unlimited.", "persian": "تخیل تو نامحدود است.", "pronunciation": "ta-kha-yyol to na-mah-dud ast"},
            {"english": "Art comes from the heart.", "persian": "هنر از قلب می‌آید.", "pronunciation": "honar az ghalb mi-ayad"},
            {"english": "Express yourself freely.", "persian": "خودت را آزادانه بیان کن.", "pronunciation": "kho-det ra a-za-deh-neh ba-yan kon"},
            {"english": "Innovation starts with curiosity.", "persian": "نوآوری با کنجکاوی شروع می‌شود.", "pronunciation": "no-a-va-ri ba konj-ka-vi shu-ru mi-shav-ad"},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "persian": "آرامش را در درون خود پیدا کن.", "pronunciation": "a-ra-mesh ra dar da-run-e khod pey-da kon"},
            {"english": "Breathe, relax, let go.", "persian": "نفس بکش، آرام باش، رها کن.", "pronunciation": "na-fas be-kesh, a-ram bash, ra-ha kon"},
            {"english": "Calm mind, happy heart.", "persian": "ذهن آرام، قلب شاد.", "pronunciation": "zehn-e a-ram, ghalb-e shad"},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "persian": "تو کافی هستی، همین‌طور که هستی.", "pronunciation": "to ka-fi has-ti, ham-in-tur ke has-ti"},
            {"english": "Stand tall, speak up.", "persian": "صاف بایست، بلند صحبت کن.", "pronunciation": "saf ba-ist, bo-land soh-bat kon"},
            {"english": "Believe in your abilities.", "persian": "به توانایی‌هایت ایمان داشته باش.", "pronunciation": "be ta-va-nai-ha-yat i-man dashteh bash"},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "persian": "هرگز تسلیم نشو، ادامه بده.", "pronunciation": "har-gez tas-lim na-sho, e-da-meh be-dah"},
            {"english": "Storms make trees take deeper roots.", "persian": "طوفان‌ها ریشه درختان را عمیق‌تر می‌کند.", "pronunciation": "tu-fan-ha ri-sheh-ye di-ra-khtan ra a-migh-tar mi-ko-nad"},
            {"english": "Patience and persistence win.", "persian": "صبر و استقامت پیروز می‌شوند.", "pronunciation": "sabr o es-te-gha-mat pi-ruz mi-sha-vand"},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "persian": "بگذار نورت درخشان بدرخشد.", "pronunciation": "be-gozar nu-rat der-akh-shan be-derakh-shad"},
            {"english": "Inspire others by your actions.", "persian": "با اعمالت به دیگران الهام ببخش.", "pronunciation": "ba a-ma-lat be di-ga-ran el-ham be-bakhsh"},
            {"english": "Be the change you want to see.", "persian": "تغییری باش که می‌خواهی ببینی.", "pronunciation": "tagh-yi-ri bash ke mi-khahi be-bi-ni"},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "persian": "هر روز مثبت‌اندیشی را انتخاب کن.", "pronunciation": "har ruz mos-bat-an-di-shi ra en-te-khab kon"},
            {"english": "Good vibes only.", "persian": "فقط انرژی مثبت.", "pronunciation": "fa-qat en-er-ji-ye mos-bat"},
            {"english": "Life is what you make it.", "persian": "زندگی همانی است که می‌سازی.", "pronunciation": "zen-de-gi ha-man ast ke mi-sa-zi"},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "persian": "شجاع باش، اولین قدم را بردار.", "pronunciation": "sho-ja bash, a-va-lin gha-dam ra bar-dar"},
            {"english": "Courage is not the absence of fear.", "persian": "شجاعت نبود ترس نیست.", "pronunciation": "sho-ja-at na-bud-e tars nist"},
            {"english": "Face your fears head on.", "persian": "مستقیماً با ترس‌هایت روبرو شو.", "pronunciation": "mos-ta-ghi-man ba tars-ha-yat ru-be-ru sho"},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "persian": "با هر کسی که ملاقات می‌کنی مهربان باش.", "pronunciation": "ba har ka-si ke mo-la-ghat mi-ko-ni mehr-ban bash"},
            {"english": "Kindness costs nothing, means everything.", "persian": "مهربانی هزینه‌ای ندارد، اما معنای همه چیز را دارد.", "pronunciation": "mehr-ba-ni ha-zi-neh-i na-darad, a-ma ma-naye hameh chiz ra darad"},
            {"english": "Spread kindness wherever you go.", "persian": "مهربانی را هر جا می‌روی گسترش بده.", "pronunciation": "mehr-ba-ni ra har ja mi-ra-vi gos-taresh be-dah"},
        ],
        "Patience": [
            {"english": "Good things take time.", "persian": "چیزهای خوب زمان می‌برند.", "pronunciation": "chiz-haye khub za-man mi-ba-rad"},
            {"english": "Wait patiently, trust the process.", "persian": "صبورانه منتظر باش، به روند اعتماد کن.", "pronunciation": "sa-bu-ra-neh mon-ta-zer bash, be ra-vand e-te-mad kon"},
            {"english": "Rome wasn't built in a day.", "persian": "روم در یک روز ساخته نشد.", "pronunciation": "Rum dar yek ruz sakh-teh nashod"},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "persian": "ببخش و خودت را آزاد کن.", "pronunciation": "be-bakhsh va kho-det ra a-zad kon"},
            {"english": "Let go of grudges, find peace.", "persian": "کینه‌ها را رها کن، آرامش را پیدا کن.", "pronunciation": "ki-neh-ha ra ra-ha kon, a-ra-mesh ra pey-da kon"},
            {"english": "Forgiveness is a gift to yourself.", "persian": "بخشش هدیه‌ای به خودت است.", "pronunciation": "bakh-shesh he-di-yeh-i be kho-det ast"},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "persian": "تو قوی‌تر از آنی که می‌دانی.", "pronunciation": "to ghavi-tar az a-ni ke mi-da-ni"},
            {"english": "Inner strength comes from within.", "persian": "قدرت درون از درون می‌آید.", "pronunciation": "ghod-rat-e da-run az da-run mi-ayad"},
            {"english": "Challenges make you stronger.", "persian": "چالش‌ها تو را قوی‌تر می‌کنند.", "pronunciation": "cha-lesh-ha to ra ghavi-tar mi-ko-nand"},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "persian": "در هر لحظه شادی را پیدا کن.", "pronunciation": "dar har lah-zeh sha-di ra pey-da kon"},
            {"english": "Joy is contagious, spread it.", "persian": "شادی مسری است، آن را گسترش بده.", "pronunciation": "sha-di mo-sar-ri ast, an ra gos-taresh be-dah"},
            {"english": "Dance like nobody's watching.", "persian": "برقص طوری که انگار کسی نگاه نمی‌کند.", "pronunciation": "be-raqs tu-ri keh en-gar ka-si ne-gah nemi-ko-nad"},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "persian": "در زندگی‌ات تعادل را پیدا کن.", "pronunciation": "dar zen-de-gi-yat ta-a-dol ra pey-da kon"},
            {"english": "Work hard, rest well.", "persian": "سخت کار کن، خوب استراحت کن.", "pronunciation": "sakht kar kon, khub es-te-ra-hat kon"},
            {"english": "Too much of anything is not good.", "persian": "زیاده‌روی در هر چیزی خوب نیست.", "pronunciation": "zi-a-deh-ra-vi dar har chi-zi khub nist"},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "persian": "رشد در خارج از منطقه امن رخ می‌دهد.", "pronunciation": "roshd dar kha-rej az man-ta-geh-ye amn rokh mi-da-had"},
            {"english": "Embrace change, grow stronger.", "persian": "تغییر را بپذیر، قوی‌تر شو.", "pronunciation": "tagh-yir ra ba-pa-zir, ghavi-tar sho"},
            {"english": "Every challenge is a chance to grow.", "persian": "هر چالشی فرصتی برای رشد است.", "pronunciation": "har cha-leshi for-sa-ti ba-ray-e roshd ast"},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "persian": "هدف خود را پیدا کن، دنبالش کن.", "pronunciation": "ha-daf-e khod ra pey-da kon, do-nalesh kon"},
            {"english": "Your life has meaning.", "persian": "زندگی‌ات معنا دارد.", "pronunciation": "zen-de-gi-yat ma-na da-rad"},
            {"english": "Live with intention, not accident.", "persian": "با قصد زندگی کن، نه تصادفی.", "pronunciation": "ba ghasd zen-de-gi kon, na to-sa-do-fi"},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "persian": "در این لحظه حاضر باش.", "pronunciation": "dar in lah-zeh ha-zer bash"},
            {"english": "Breathe deeply, stay grounded.", "persian": "عمیق نفس بکش، متکی بر زمین باش.", "pronunciation": "a-migh na-fas be-kesh, mo-ta-ki bar za-min bash"},
            {"english": "Notice the little things around you.", "persian": "به چیزهای کوچک اطرافت توجه کن.", "pronunciation": "be chiz-haye ku-chak at-ra-fat tavaj-joh kon"},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["persian"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansArabic-Bold.ttf"),
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    persian = phrase_data.get("persian", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(persian, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Persian Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY PERSIAN"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_persian: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansArabic-Bold.ttf"),
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER PERSIAN", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_persian, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 PERSIAN PHRASES"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY PERSIAN", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_persian: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Persian in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_persian})",
        f"60 Persian Phrases for {category_english} | Speak Persian Like a Native! ({category_persian})",
        f"Master Persian {category_english} | 60 Essential Persian Phrases with Pronunciation | Velocity Persian",
        f"Persian Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Persian Fluently | {category_english} Phrases | English + Persian + Pronunciation",
    ]

    description = f"""\U0001F1EE\U0001F1F7 Learn Persian with Velocity Persian! \U0001F1EE\U0001F1F7

In this video, you'll learn 60 essential Persian phrases about {category_english} ({category_persian}).
Perfect for beginners and intermediate learners!

\U0001F4DA WHAT YOU'LL LEARN:
\u2022 60 practical {category_english} phrases in Persian
\u2022 Correct pronunciation guide
\u2022 Natural pauses for speaking practice
\u2022 Common expressions used by native speakers

\U0001F551 VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
\U0001F4DD ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Persian: {phrase['persian']}
    Pronunciation: {phrase['pronunciation']}
"""

    description += """
\U0001F3AF PERFECT FOR:
\u2022 Persian beginners wanting to expand vocabulary
\u2022 Intermediate learners practicing pronunciation
\u2022 Anyone interested in Persian language and culture
\u2022 Language enthusiasts and polyglots
\u2022 Students preparing for exams

\U0001F4A1 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

\U0001F514 SUBSCRIBE for more Persian learning content!
\U0001F44D LIKE this video if you found it helpful!
\U0001F4AC COMMENT which phrases you want to learn next!

\U0001F4F1 FOLLOW VELOCITY PERSIAN:
[Add your social media links here]

\U0001F3B5 MUSIC:
[Add music credits if applicable]

\U0001F4D6 RELATED VIDEOS:
\u2022 Persian Motivation Phrases
\u2022 Persian Love Expressions
\u2022 Basic Persian Greetings

#LearnPersian #PersianPhrases #PersianLanguage #{category_english.replace(' ', '')} #VelocityPersian #PersianForBeginners #SpeakPersian #PersianVocabulary #Pronunciation #LanguageLearning #Persian101 #PersianLesson

---
\u00A9 Velocity Persian - Making Persian learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Persian",
            "Persian Phrases",
            "Persian Language",
            category_english,
            "Velocity Persian",
            "Persian for Beginners",
            "Speak Persian",
            "Persian Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Persian 101",
            "Persian Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_persian": category_persian,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_PERSIAN[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['persian']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_ENGLISH[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_ENGLISH[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_PERSIAN[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Persian: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Persian", "Persian Phrases", "Persian", category_english, "Velocity Persian"],
        "category_english": category_english,
        "category_persian": CATEGORIES_PERSIAN[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Persian")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Persian YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY PERSIAN - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_PERSIAN[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)
