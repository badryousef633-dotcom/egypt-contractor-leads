#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Social Media Leads Scraper - Egypt Contractors & Finishing
جميع البوستات الخاصة بالتشطيبات والمقاولات في مصر
يرسل البوست كامل بكل ما فيه إلى تليجرام

المؤلف: AI Assistant
التاريخ: 2026-07-04
"""

import os
import re
import json
import time
import random
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import quote

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# الإعدادات - عدل هذه القيم حسب احتياجاتك
# ============================================================

# تليجرام
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')

# Instagram - هاشتاجات التشطيبات والمقاولات في مصر
INSTAGRAM_HASHTAGS = [
    'تشطيبات_مصر', 'تشطيبات', 'مقاولات', 'ديكور_مصر',
    'تشطيب_شقق', 'تشطيب_فيلا', 'تشطيب_محل', 'تشطيب_كامل',
    'مقاول_تشطيب', 'مقاول_بناء', 'مقاولات_مصر', 'مقاولات_القاهرة',
    'دهانات_شقق', 'سيراميك_مصر', 'بورسلين', 'جبس_بورد',
    'تسليم_مفتاح', 'تشطيبات_داخلية', 'ديكورات_داخلية',
    'تشطيب_الاسكندرية', 'تشطيب_الجيزة', 'تشطيب_6اكتوبر',
    'مقاول_القاهرة', 'مقاول_الاسكندرية', 'تشطيب_المنصورة',
    'شقق_للتشطيب', 'فيلا_للتشطيب', 'محل_للتشطيب',
    'تشطيب_مطاعم', 'تشطيب_مكاتب', 'تشطيب_عيادات',
    'سباكة', 'كهرباء', 'نجارة', 'الوميتال', 'شيش',
    'تشطيب_حديث', 'ديكور_مودرن', 'تصميم_داخلي',
    'مقاول_عام', 'اعمال_تشطيب', 'تشطيب_فاخر',
    'تشطيب_اقتصادي', 'تشطيب_فاخر', 'تشطيب_مميز'
]

# Facebook - صفحات ومجموعات التشطيبات (أسماء الصفحات العامة)
FACEBOOK_PAGES = [
    'تشطيبات_شقق_مصر',
    'مقاولات_ومباني_مصر',
    'ديكورات_داخلية_مصر',
    'تشطيب_شقق_القاهرة',
    'مقاولين_مصر',
]

# كلمات مفتاحية للتأكد من أن البوست للتشطيبات
CONTRACTOR_KEYWORDS = [
    'مقاول', 'تشطيب', 'دهان', 'سيراميك', 'بورسلين', 'جبس',
    'ديكور', 'تسليم_مفتاح', 'تشطيب_شقة', 'تشطيب_فيلا',
    'تشطيب_محل', 'سباكة', 'كهرباء', 'نجارة', 'الوميتال',
    'شيش', 'تصميم_داخلي', 'اعمال_تشطيب', 'تشطيب_كامل',
    'تشطيب_داخلي', 'تشطيب_خارجي', 'تشطيب_حديث',
    'مقاول_عام', 'مقاول_بناء', 'مقاول_تشطيب'
]

# نمط استخراج الأرقام المصرية
PHONE_PATTERNS = [
    re.compile(r'(?:\+?20|0)?(1[0-5]\d{8})'),  # 01012345678
    re.compile(r'(?:\+?20|0)?(1[0-5]\d{3}\s?\d{3}\s?\d{3})'),  # 010 123 456 789
    re.compile(r'(?:\+?20|0)?(1[0-5]\d{2}\s?\d{3}\s?\d{3})'),  # 0101 234 567 89
    re.compile(r'(?:\+?20|0)?(1[0-5]\d{3}-\d{3}-\d{3})'),  # 0101-234-567-89
]

# User Agents للتدوير
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Android 14; Mobile; rv:128.0) Gecko/128.0 Firefox/128.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
]

# ============================================================
# كلاس البيانات
# ============================================================

@dataclass
class Post:
    """تمثيل بوست من السوشيال ميديا"""
    platform: str
    post_id: str
    url: str
    username: str
    display_name: str
    text: str
    date: str
    likes: int
    comments_count: int
    shares: int = 0
    images: List[str] = None
    videos: List[str] = None
    hashtags: List[str] = None
    phones: List[str] = None
    is_contractor: bool = False

    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.videos is None:
            self.videos = []
        if self.hashtags is None:
            self.hashtags = []
        if self.phones is None:
            self.phones = []

# ============================================================
# دوال مساعدة
# ============================================================

def random_delay(min_seconds: float = 3.0, max_seconds: float = 8.0):
    """تأخير عشوائي لتجنب الحظر"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def get_random_headers():
    """إرجاع headers عشوائية"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }

def extract_phones(text: str) -> List[str]:
    """استخراج أرقام الهواتف المصرية من النص"""
    phones = set()

    for pattern in PHONE_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            # تنظيف الرقم
            clean = re.sub(r'[^\d]', '', match)
            if len(clean) == 10 and clean[0] == '1':
                phones.add('0' + clean)
            elif len(clean) == 11 and clean[0] == '0':
                phones.add(clean)

    return sorted(list(phones))

def is_contractor_post(text: str) -> bool:
    """التحقق مما إذا كان البوست يتعلق بالتشطيبات/المقاولات"""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in CONTRACTOR_KEYWORDS)

def clean_text(text: str) -> str:
    """تنظيف النص من الرموز الزائدة"""
    if not text:
        return ""
    # إزالة الروابط
    text = re.sub(r'https?://\S+', '', text)
    # إزالة التاغات الزائدة
    text = re.sub(r'@\w+', '', text)
    # تنظيف المسافات
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def format_phone_for_telegram(phone: str) -> str:
    """تنسيق رقم الهاتف ليكون قابل للنقر في تليجرام"""
    return f'<a href="tel:{phone}">{phone}</a>'

# ============================================================
# تليجرام - إرسال البوستات
# ============================================================

class TelegramSender:
    """إرسال البوستات إلى تليجرام"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def _send_request(self, method: str, data: Dict) -> bool:
        """إرسال طلب إلى API تليجرام"""
        url = f"{self.base_url}/{method}"
        try:
            response = self.session.post(url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return True
                else:
                    logger.error(f"Telegram API error: {result}")
            else:
                logger.error(f"HTTP {response.status_code}: {response.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"Telegram request failed: {e}")
            return False

    def send_post(self, post: Post) -> bool:
        """إرسال بوست كامل إلى تليجرام"""

        # بناء الرسالة
        message = self._build_message(post)

        # إرسال النص أولاً
        if not self._send_text(message):
            return False

        # إرسال الصور
        if post.images:
            for img_url in post.images[:5]:  # أقصى 5 صور
                self._send_photo(img_url, f"📷 صورة من {post.platform}")
                random_delay(1, 2)

        # إرسال الفيديوهات
        if post.videos:
            for video_url in post.videos[:2]:  # أقصى 2 فيديو
                self._send_video(video_url, f"🎥 فيديو من {post.platform}")
                random_delay(1, 2)

        return True

    def _build_message(self, post: Post) -> str:
        """بناء رسالة تليجرام كاملة من البوست"""

        # تحديد الإيموجي حسب المنصة
        platform_emoji = "📸" if post.platform == "Instagram" else "📘"

        # تحديد الإيموجي حسب وجود رقم هاتف
        phone_emoji = "📞" if post.phones else "⚠️"

        # بناء قسم الأرقام
        phones_section = ""
        if post.phones:
            phones_formatted = \"\n".join([
                f"  • {format_phone_for_telegram(phone)}" 
                for phone in post.phones
            ])
            phones_section = f"""
📞 <b>أرقام الهاتف للتواصل:</b>
{phones_formatted}"""
        else:
            phones_section = "\n⚠️ <i>لا يوجد رقم هاتف ظاهر في البوست</i>"

        # بناء قسم الهاشتاجات
        hashtags_section = ""
        if post.hashtags:
            hashtags_text = " ".join([f"#{tag}" for tag in post.hashtags[:10]])
            hashtags_section = f"\n\n🏷 <b>الهاشتاجات:</b>\n{hashtags_text}"

        # بناء قسم الإحصائيات
        stats = f"""
📊 <b>الإحصائيات:</b>
  ❤️ {post.likes:,} إعجاب
  💬 {post.comments_count:,} تعليق
  🔄 {post.shares:,} مشاركة""" if post.shares > 0 else f"""
📊 <b>الإحصائيات:</b>
  ❤️ {post.likes:,} إعجاب
  💬 {post.comments_count:,} تعليق"""

        # بناء الرسالة الكاملة
        message = f"""{platform_emoji} <b>بوست جديد من {post.platform}</b> {phone_emoji}

👤 <b>الحساب:</b> @{post.username}
📝 <b>الاسم:</b> {post.display_name}
📅 <b>التاريخ:</b> {post.date}
🔗 <b>الرابط:</b> <a href="{post.url}">اضغط هنا للمشاهدة</a>

━━━━━━━━━━━━━━━━━━━━
📝 <b>نص البوست:</b>
{post.text[:3000] if len(post.text) > 3000 else post.text}
━━━━━━━━━━━━━━━━━━━━{phones_section}{hashtags_section}
{stats}

🔖 <b>معرف البوست:</b> <code>{post.post_id}</code>
✅ <b>مصنف كـ:</b> {'مقاول/تشطيبات' if post.is_contractor else 'عام'}

#تشطيبات_مصر #مقاولات #ليدز_يومي"""

        return message

    def _send_text(self, text: str) -> bool:
        """إرسال رسالة نصية"""
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False,
            'disable_notification': False
        }
        return self._send_request('sendMessage', data)

    def _send_photo(self, photo_url: str, caption: str = "") -> bool:
        """إرسال صورة"""
        data = {
            'chat_id': self.chat_id,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        return self._send_request('sendPhoto', data)

    def _send_video(self, video_url: str, caption: str = "") -> bool:
        """إرسال فيديو"""
        data = {
            'chat_id': self.chat_id,
            'video': video_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        return self._send_request('sendVideo', data)

    def send_summary(self, total_posts: int, posts_with_phones: int, platform: str) -> bool:
        """إرسال ملخص التشغيل"""
        message = f"""📊 <b>ملخص جمع البوستات - {platform}</b>

✅ تم جمع: {total_posts} بوست
📞 تحتوي على أرقام: {posts_with_phones} بوست
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}

#ملخص_يومي #تشطيبات_مصر"""
        return self._send_text(message)

# ============================================================
# Instagram Scraper
# ============================================================

class InstagramScraper:
    """جمع بوستات Instagram"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(get_random_headers())
        self.base_url = "https://www.instagram.com"
        self.graphql_url = "https://www.instagram.com/graphql/query/"

    def _get_csrf_token(self) -> Optional[str]:
        """الحصول على CSRF token"""
        try:
            response = self.session.get(self.base_url, timeout=15)
            if response.status_code == 200:
                # البحث عن csrf token
                csrf_match = re.search(r'"csrf_token":"([^"]+)"', response.text)
                if csrf_match:
                    return csrf_match.group(1)
        except Exception as e:
            logger.error(f"Failed to get CSRF token: {e}")
        return None

    def search_hashtag(self, hashtag: str, max_posts: int = 20) -> List[Post]:
        """البحث في هاشتاج Instagram"""
        posts = []

        try:
            # تنظيف الهاشتاج
            hashtag = hashtag.strip().replace('#', '').replace(' ', '_')

            logger.info(f"Searching Instagram hashtag: #{hashtag}")

            # استخدام Instagram GraphQL API (Public)
            url = f"{self.base_url}/explore/tags/{hashtag}/"

            random_delay(2, 5)

            response = self.session.get(url, timeout=20)

            if response.status_code != 200:
                logger.warning(f"Instagram returned {response.status_code} for #{hashtag}")
                return posts

            # استخراج البيانات من JSON المضمن في HTML
            shared_data_match = re.search(
                r'<script type="text/javascript">window\._sharedData = (.+?);</script>',
                response.text
            )

            if not shared_data_match:
                # محاولة بديلة
                shared_data_match = re.search(
                    r'<script type="text/javascript">window\.__additionalDataLoaded\(.+?,(.+?)\);</script>',
                    response.text
                )

            if shared_data_match:
                try:
                    data = json.loads(shared_data_match.group(1))

                    # استخراج البوستات من البيانات
                    if 'entry_data' in data and 'TagPage' in data['entry_data']:
                        tag_page = data['entry_data']['TagPage'][0]
                        if 'graphql' in tag_page and 'hashtag' in tag_page['graphql']:
                            hashtag_data = tag_page['graphql']['hashtag']
                            edges = hashtag_data.get('edge_hashtag_to_media', {}).get('edges', [])

                            for edge in edges[:max_posts]:
                                node = edge.get('node', {})
                                if not node:
                                    continue

                                post = self._parse_instagram_node(node, hashtag)
                                if post:
                                    posts.append(post)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Instagram data: {e}")

            # محاولة استخراج من النص المضمن
            if not posts:
                posts = self._extract_from_html(response.text, hashtag)

        except Exception as e:
            logger.error(f"Error searching Instagram hashtag #{hashtag}: {e}")

        logger.info(f"Found {len(posts)} posts from Instagram #{hashtag}")
        return posts

    def _parse_instagram_node(self, node: Dict, hashtag: str) -> Optional[Post]:
        """تحويل node Instagram إلى Post object"""
        try:
            shortcode = node.get('shortcode', '')
            if not shortcode:
                return None

            # الحصول على نص البوست
            caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
            text = caption_edges[0].get('node', {}).get('text', '') if caption_edges else ''

            # استخراج الأرقام
            phones = extract_phones(text)

            # استخراج الهاشتاجات
            hashtags = re.findall(r'#(\w+)', text)

            # التحقق من أنه بوست مقاول/تشطيب
            is_contractor = is_contractor_post(text)

            # إذا لم يكن بوست مقاول ولا يحتوي على أرقام، تخطيه
            if not is_contractor and not phones:
                return None

            # الحصول على الصور
            images = []
            if node.get('display_url'):
                images.append(node['display_url'])

            # التحقق من الفيديو
            videos = []
            if node.get('is_video', False):
                # في الحالة العامة، لا يمكن الحصول على URL الفيديو مباشرة
                pass

            return Post(
                platform='Instagram',
                post_id=shortcode,
                url=f"https://www.instagram.com/p/{shortcode}/",
                username=node.get('owner', {}).get('username', 'unknown'),
                display_name=node.get('owner', {}).get('full_name', ''),
                text=clean_text(text),
                date=datetime.fromtimestamp(node.get('taken_at_timestamp', 0)).strftime('%Y-%m-%d %H:%M'),
                likes=node.get('edge_liked_by', {}).get('count', 0),
                comments_count=node.get('edge_media_to_comment', {}).get('count', 0),
                images=images,
                videos=videos,
                hashtags=hashtags,
                phones=phones,
                is_contractor=is_contractor
            )

        except Exception as e:
            logger.error(f"Error parsing Instagram node: {e}")
            return None

    def _extract_from_html(self, html: str, hashtag: str) -> List[Post]:
        """استخراج البوستات من HTML كبديل"""
        posts = []

        # البحث عن روابط البوستات
        shortcodes = re.findall(r'/p/([A-Za-z0-9_-]+)/', html)
        shortcodes = list(set(shortcodes))[:20]  # إزالة التكرار

        for shortcode in shortcodes:
            # بناء URL
            url = f"https://www.instagram.com/p/{shortcode}/"

            # محاولة الحصول على بيانات البوست
            try:
                random_delay(1, 3)
                response = self.session.get(url, timeout=15)

                if response.status_code == 200:
                    # استخراج البيانات
                    meta_match = re.search(r'<meta property="og:description" content="([^"]+)"', response.text)
                    text = meta_match.group(1) if meta_match else ''

                    phones = extract_phones(text)
                    is_contractor = is_contractor_post(text)

                    if is_contractor or phones:
                        # استخراج الصورة
                        img_match = re.search(r'<meta property="og:image" content="([^"]+)"', response.text)
                        images = [img_match.group(1)] if img_match else []

                        posts.append(Post(
                            platform='Instagram',
                            post_id=shortcode,
                            url=url,
                            username='unknown',
                            display_name='',
                            text=clean_text(text),
                            date=datetime.now().strftime('%Y-%m-%d'),
                            likes=0,
                            comments_count=0,
                            images=images,
                            phones=phones,
                            is_contractor=is_contractor
                        ))

            except Exception as e:
                logger.error(f"Error extracting post {shortcode}: {e}")

        return posts

# ============================================================
# Facebook Scraper (Public Pages Only)
# ============================================================

class FacebookScraper:
    """جمع بوستات Facebook من الصفحات العامة"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(get_random_headers())
        self.base_url = "https://www.facebook.com"
        self.mb_url = "https://mbasic.facebook.com"

    def get_page_posts(self, page_name: str, max_posts: int = 15) -> List[Post]:
        """جمع بوستات من صفحة Facebook عامة"""
        posts = []

        try:
            logger.info(f"Searching Facebook page: {page_name}")

            # استخدام mbasic.facebook.com (نسخة الجوال البسيطة - أسهل في الـ scraping)
            url = f"{self.mb_url}/{page_name}"

            random_delay(2, 5)

            response = self.session.get(url, timeout=20)

            if response.status_code != 200:
                logger.warning(f"Facebook returned {response.status_code} for {page_name}")
                return posts

            # استخراج البوستات من HTML
            posts = self._extract_posts_from_html(response.text, page_name)

        except Exception as e:
            logger.error(f"Error searching Facebook page {page_name}: {e}")

        logger.info(f"Found {len(posts)} posts from Facebook page {page_name}")
        return posts

    def _extract_posts_from_html(self, html: str, page_name: str) -> List[Post]:
        """استخراج البوستات من HTML Facebook"""
        posts = []

        # Facebook mobile basic HTML structure
        # البحث عن قصص/بوستات

        # نمط البوستات في mbasic.facebook.com
        post_patterns = [
            r'<div class="[^"]*story_body_container[^"]*"[^>]*>(.*?)</div>\s*<div class="[^"]*story_footer[^"]*"',
            r'<div[^>]*role="article"[^>]*>(.*?)</article>',
            r'<div class="[^"]*_5rgt[^"]*"[^>]*>(.*?)</div>',
        ]

        # محاولة استخراج النصوص
        text_blocks = re.findall(r'<div[^>]*>([^<]{50,})</div>', html)

        for i, text in enumerate(text_blocks[:20]):
            # تنظيف HTML entities
            text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            text = re.sub(r'<[^>]+>', '', text)

            if len(text) < 50:  # تخطي النصوص القصيرة جداً
                continue

            # استخراج الأرقام
            phones = extract_phones(text)

            # التحقق من أنه بوست مقاول
            is_contractor = is_contractor_post(text)

            # تخطي البوستات غير المرتبطة بالتشطيبات (إلا إذا كان بها رقم)
            if not is_contractor and not phones:
                continue

            # استخراج الرابط
            post_url = f"https://facebook.com/{page_name}"

            posts.append(Post(
                platform='Facebook',
                post_id=f"fb_{page_name}_{i}",
                url=post_url,
                username=page_name,
                display_name=page_name,
                text=clean_text(text),
                date=datetime.now().strftime('%Y-%m-%d'),
                likes=0,
                comments_count=0,
                phones=phones,
                is_contractor=is_contractor
            ))

        return posts

# ============================================================
# مدير التشغيل الرئيسي
# ============================================================

class SocialMediaScraperManager:
    """مدير تشغيل جمع البوستات"""

    def __init__(self):
        self.instagram = InstagramScraper()
        self.facebook = FacebookScraper()
        self.telegram = TelegramSender(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.all_posts: List[Post] = []
        self.sent_posts: set = set()  # لتجنب التكرار
        self.load_sent_posts()

    def load_sent_posts(self):
        """تحميل قائمة البوستات المرسلة سابقاً"""
        try:
            if os.path.exists('sent_posts.json'):
                with open('sent_posts.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sent_posts = set(data.get('sent', []))
        except Exception as e:
            logger.error(f"Error loading sent posts: {e}")

    def save_sent_posts(self):
        """حفظ قائمة البوستات المرسلة"""
        try:
            with open('sent_posts.json', 'w', encoding='utf-8') as f:
                json.dump({'sent': list(self.sent_posts)}, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving sent posts: {e}")

    def scrape_instagram(self, hashtags: List[str] = None, max_per_hashtag: int = 10) -> List[Post]:
        """جمع بوستات Instagram"""
        if hashtags is None:
            hashtags = INSTAGRAM_HASHTAGS

        posts = []

        for hashtag in hashtags[:15]:  # أقصى 15 هاشتاج في التشغيل
            try:
                hashtag_posts = self.instagram.search_hashtag(hashtag, max_per_hashtag)
                posts.extend(hashtag_posts)
                random_delay(5, 10)  # تأخير بين الهاشتاجات
            except Exception as e:
                logger.error(f"Error with Instagram hashtag #{hashtag}: {e}")

        return posts

    def scrape_facebook(self, pages: List[str] = None, max_per_page: int = 10) -> List[Post]:
        """جمع بوستات Facebook"""
        if pages is None:
            pages = FACEBOOK_PAGES

        posts = []

        for page in pages[:5]:  # أقصى 5 صفحات
            try:
                page_posts = self.facebook.get_page_posts(page, max_per_page)
                posts.extend(page_posts)
                random_delay(5, 10)  # تأخير بين الصفحات
            except Exception as e:
                logger.error(f"Error with Facebook page {page}: {e}")

        return posts

    def filter_new_posts(self, posts: List[Post]) -> List[Post]:
        """تصفية البوستات الجديدة (غير مرسلة سابقاً)"""
        new_posts = []
        for post in posts:
            if post.post_id not in self.sent_posts:
                new_posts.append(post)
        return new_posts

    def send_posts_to_telegram(self, posts: List[Post]) -> int:
        """إرسال البوستات إلى تليجرام"""
        sent_count = 0

        for post in posts:
            try:
                if self.telegram.send_post(post):
                    self.sent_posts.add(post.post_id)
                    sent_count += 1
                    logger.info(f"Sent post {post.post_id} to Telegram")
                    random_delay(3, 6)  # تأخير بين البوستات
                else:
                    logger.error(f"Failed to send post {post.post_id}")
            except Exception as e:
                logger.error(f"Error sending post {post.post_id}: {e}")

        self.save_sent_posts()
        return sent_count

    def run(self, instagram: bool = True, facebook: bool = True):
        """التشغيل الرئيسي"""
        logger.info("=" * 60)
        logger.info("Starting Social Media Scraper - Egypt Contractors")
        logger.info("=" * 60)

        all_new_posts = []

        # جمع Instagram
        if instagram:
            logger.info("\n--- Scraping Instagram ---")
            ig_posts = self.scrape_instagram()
            ig_new = self.filter_new_posts(ig_posts)
            logger.info(f"Instagram: {len(ig_posts)} total, {len(ig_new)} new")

            if ig_new:
                self.telegram.send_summary(len(ig_posts), 
                    sum(1 for p in ig_posts if p.phones), "Instagram")
                all_new_posts.extend(ig_new)

            random_delay(10, 15)

        # جمع Facebook
        if facebook:
            logger.info("\n--- Scraping Facebook ---")
            fb_posts = self.scrape_facebook()
            fb_new = self.filter_new_posts(fb_posts)
            logger.info(f"Facebook: {len(fb_posts)} total, {len(fb_new)} new")

            if fb_new:
                self.telegram.send_summary(len(fb_posts), 
                    sum(1 for p in fb_posts if p.phones), "Facebook")
                all_new_posts.extend(fb_new)

        # إرسال البوستات الجديدة
        if all_new_posts:
            logger.info(f"\n--- Sending {len(all_new_posts)} new posts to Telegram ---")
            sent = self.send_posts_to_telegram(all_new_posts)
            logger.info(f"Successfully sent {sent} posts")
        else:
            logger.info("\n--- No new posts to send ---")

        # إرسال ملخص نهائي
        total_with_phones = sum(1 for p in all_new_posts if p.phones)
        if all_new_posts:
            self.telegram.send_summary(len(all_new_posts), total_with_phones, "الإجمالي")

        logger.info("\n" + "=" * 60)
        logger.info("Scraping completed")
        logger.info("=" * 60)

        return all_new_posts

# ============================================================
# تشغيل مباشر
# ============================================================

def main():
    """الدالة الرئيسية"""

    # التحقق من الإعدادات
    if TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE' or TELEGRAM_CHAT_ID == 'YOUR_CHAT_ID_HERE':
        print("""
⚠️ يرجى تعيين متغيرات البيئة أولاً:

export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

أو عدل القيم مباشرة في السكريبت.

للحصول على:
• Bot Token: تواصل مع @BotFather في Telegram
• Chat ID: أرسل رسالة إلى @userinfobot في Telegram
        """)
        return

    # تشغيل المدير
    manager = SocialMediaScraperManager()
    manager.run(instagram=True, facebook=True)

if __name__ == "__main__":
    main()
