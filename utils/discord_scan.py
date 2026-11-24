import re
from datetime import datetime, timezone
import discord
from config import GUILD_ID


# Простой список "плохих" слов — можешь расширить
SWEAR_WORDS = [
    "бля", "хуй", "пизд", "еба", "сука", "нах", "мраз", "тварь",
    "долбо", "идиот", "дебил", "лох", "гандон", "мудак"
]


async def find_member(bot, query: str):
    """Ищет участника по username, display_name, нику или ID."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return None
    q = query.lower().lstrip("@")

    # Если чистый ID
    if q.isdigit():
        try:
            return await guild.fetch_member(int(q))
        except Exception:
            return None

    # По имени
    for m in guild.members:
        if m.bot:
            continue
        names = [
            m.name.lower(),
            (m.nick or "").lower(),
            m.display_name.lower(),
            f"{m.name}#{m.discriminator}".lower() if m.discriminator != "0" else m.name.lower(),
        ]
        if any(q in n for n in names):
            return m
    return None


async def scan_messages(guild, member, channel_limit=10, msg_per_channel=200):
    """
    Читает последние сообщения участника из доступных текстовых каналов.
    Возвращает список dict'ов с timestamp и content.
    """
    collected = []
    scanned_channels = 0

    for ch in guild.text_channels:
        # Проверяем что у бота есть право читать канал
        perms = ch.permissions_for(guild.me)
        if not perms.read_message_history or not perms.read_messages:
            continue

        if scanned_channels >= channel_limit:
            break

        try:
            count = 0
            async for msg in ch.history(limit=1000):
                if msg.author.id == member.id and not msg.content.startswith("!"):
                    collected.append({
                        "content": msg.content,
                        "created_at": msg.created_at,
                        "channel": ch.name,
                    })
                    count += 1
                    if count >= msg_per_channel:
                        break
            scanned_channels += 1
        except Exception:
            continue

    return collected, scanned_channels


def analyze_behavior(messages):
    """Анализирует список сообщений и выдаёт метрики."""
    if not messages:
        return {
            "message_count": 0,
            "avg_msg_length": 0,
            "caps_ratio": 0,
            "exclaim_count": 0,
            "swear_count": 0,
            "night_activity": 0,
            "day_activity": 0,
        }

    total_len = 0
    caps_chars = 0
    total_chars = 0
    exclaim = 0
    swear = 0
    night = 0
    day = 0

    for m in messages:
        content = m["content"]
        total_len += len(content)

        # Капс
        for c in content:
            if c.isalpha():
                total_chars += 1
                if c.isupper():
                    caps_chars += 1

        # Восклицания
        exclaim += content.count("!")

        # Мат
        low = content.lower()
        for w in SWEAR_WORDS:
            if w in low:
                swear += 1
                break

        # Время (UTC)
        h = m["created_at"].hour
        if 0 <= h < 6 or 22 <= h < 24:
            night += 1
        else:
            day += 1

    n = len(messages)
    return {
        "message_count": n,
        "avg_msg_length": round(total_len / n, 1),
        "caps_ratio": round(caps_chars / total_chars, 2) if total_chars else 0,
        "exclaim_count": exclaim,
        "swear_count": swear,
        "night_activity": night,
        "day_activity": day,
    }


def compute_scores(metrics, member, roles_high=False):
    """Считает агрессию, лояльность, активность, опасность."""
    n = metrics["message_count"] or 1

    # АГРЕССИЯ 0-100
    agg = min(100, int(
        (metrics["swear_count"] / n) * 40
        + (metrics["caps_ratio"]) * 30
        + (metrics["exclaim_count"] / n) * 20
    ))

    # АКТИВНОСТЬ 0-100
    act = min(100, int(n / 2))

    # ЛОЯЛЬНОСТЬ 0-100 — эвристика
    loy = 50
    if roles_high:
        loy += 20
    if metrics["day_activity"] > metrics["night_activity"]:
        loy += 15
    if agg < 20:
        loy += 15
    loy = max(0, min(100, loy))

    # ОПАСНОСТЬ 0-100
    danger = min(100, int(agg * 0.6 + (100 - loy) * 0.4))

    return {
        "aggressive_score": agg,
        "activity_score": act,
        "loyalty_score": loy,
        "danger_level": danger,
    }


def build_report(metrics, scores):
    """Формирует strengths/weaknesses текстом."""
    strengths = []
    weaknesses = []

    if scores["activity_score"] > 60:
        strengths.append("Высокая активность на сервере")
    else:
        weaknesses.append("Низкая активность")

    if scores["aggressive_score"] < 20:
        strengths.append("Спокойное поведение")
    elif scores["aggressive_score"] > 60:
        weaknesses.append("Повышенная агрессия в сообщениях")

    if metrics["night_activity"] > metrics["day_activity"]:
        weaknesses.append("Активность преимущественно ночью")
    else:
        strengths.append("Активность в дневное время")

    if metrics["avg_msg_length"] < 10:
        weaknesses.append("Короткие сообщения (мало информации)")
    elif metrics["avg_msg_length"] > 50:
        strengths.append("Развёрнутые сообщения")

    if not strengths:
        strengths.append("—")
    if not weaknesses:
        weaknesses.append("—")

    return ", ".join(strengths), ", ".join(weaknesses)