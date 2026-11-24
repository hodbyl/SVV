import base64
from db import queries_ciphers as qci
from db import queries as q
from db.connection import pool

SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


# --- АЛГОРИТМЫ ШИФРОВАНИЯ ---
def caesar_encrypt(text, shift):
    res = ""
    for c in text:
        if 'A' <= c <= 'Z':
            res += chr((ord(c) - ord('A') + shift) % 26 + ord('A'))
        elif 'a' <= c <= 'z':
            res += chr((ord(c) - ord('a') + shift) % 26 + ord('a'))
        elif 'А' <= c <= 'Я':
            res += chr((ord(c) - ord('А') + shift) % 32 + ord('А'))
        elif 'а' <= c <= 'я':
            res += chr((ord(c) - ord('а') + shift) % 32 + ord('а'))
        else:
            res += c
    return res


def cba_encrypt(text, key="CBA"):
    """Уникальный шифр C.B.A. (XOR + Hex)"""
    if not key: key = "CBA"
    result = []
    for i, char in enumerate(text):
        k = ord(key[i % len(key)])
        result.append(format(ord(char) ^ k, '02x'))
    return "".join(result)


def cba_decrypt(hex_str, key="CBA"):
    if not key: key = "CBA"
    if len(hex_str) % 2 != 0: return "Ошибка длины"
    result = []
    try:
        for i in range(0, len(hex_str), 2):
            hex_char = hex_str[i:i+2]
            k = ord(key[(i//2) % len(key)])
            result.append(chr(int(hex_char, 16) ^ k))
        return "".join(result)
    except Exception:
        return "Ошибка расшифровки"


# --- ОКНА МЕНЮ ---
async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.15.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Шифры",
        "1. Создать шифр (6+)" if staff_rank >= 6 else "1. Создать шифр (6+) ❌",
        "2. Расшифровать (5+)" if staff_rank >= 5 else "2. Расшифровать (5+) ❌",
        "3. Список шифров (6+)" if staff_rank >= 6 else "3. Список шифров (6+) ❌",
        "4. Удалить шифр (8)" if staff_rank >= 8 else "4. Удалить шифр (8) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_create(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.15.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nСоздать шифр\n"
        + "!шифр создать (тип) (текст) (ключ)\n"
        + "Типы: цба, base64, цезарь, бинарный.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_decrypt(message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.15.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nРасшифровать\n"
        + "!шифр расшифровать (ID)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_list(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    rows = await qci.list_ciphers()
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.15.1.3]", SEP, MARK, SEP,
             "Система C.B.A.", "Список шифров"]
    if not rows:
        lines.append("(пусто)")
    else:
        for r in rows:
            lines.append(f"#{r['id']} [{r['cipher_type']}] {r['original_text'][:30]} — {r['author_callsign']}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_delete(message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.15.1.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nУдалить шифр\n"
        + "!шифр удалить (ID)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


# --- КОМАНДЫ ---
async def cmd_create(bot, message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content[len("!шифр создать"):].strip().split(maxsplit=2)
    if len(parts) < 2:
        await message.channel.send("Формат: `!шифр создать (тип) (текст) (ключ)`")
        return

    ctype = parts[0].lower()
    text = parts[1]
    key = parts[2] if len(parts) > 2 else ""

    try:
        if ctype in ["цба", "cba"]:
            enc = cba_encrypt(text, key)
        elif ctype == "base64":
            enc = base64.b64encode(text.encode()).decode()
        elif ctype in ["цезарь", "цезаря"]:
            shift = int(key) if key else 3
            enc = caesar_encrypt(text, shift)
        elif ctype == "бинарный":
            enc = " ".join(format(ord(c), '08b') for c in text)
        else:
            await message.channel.send("Типы: `цба`, `base64`, `цезарь`, `бинарный`.")
            return

        r = await qci.insert_cipher(ctype, text, enc, key, acc["callsign"])
        await q.log_action("cipher_create", message.author.id, str(r["id"]), {"type": ctype})
        
        # Красиво оформляем вывод для секретного шифра
        if ctype in ["цба", "cba"]:
            await message.channel.send(f"🕵️ **СЕКРЕТНЫЙ ШИФР Ц.Б.А.**\nID: {r['id']}\nКлюч: `{key or 'CBA'}`\nКод:\n`{enc}`")
        else:
            await message.channel.send(f"✅ Шифр создан. ID: {r['id']}\nРезультат:\n`{enc}`")
            
    except Exception as e:
        await message.channel.send(f"Ошибка при шифровании: {e}")


async def cmd_decrypt(bot, message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+.")
        return
    parts = message.content[len("!шифр расшифровать"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!шифр расшифровать (ID)`")
        return
    try:
        cid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return

    row = await pool().fetchrow("SELECT * FROM ciphers WHERE id=$1", cid)
    if not row:
        await message.channel.send("Шифр не найден.")
        return

    ctype = row['cipher_type']
    enc = row['encrypted_text']
    key = row['cipher_key'] or ""

    try:
        if ctype in ["цба", "cba"]:
            dec = cba_decrypt(enc, key)
        elif ctype == "base64":
            dec = base64.b64decode(enc.encode()).decode()
        elif ctype in ["цезарь", "цезаря"]:
            shift = -int(key) if key else -3
            dec = caesar_encrypt(enc, shift)
        elif ctype == "бинарный":
            dec = "".join(chr(int(b, 2)) for b in enc.split(" "))
        else:
            dec = "Неизвестный тип"

        await message.channel.send(f"🔓 **Расшифровка #{cid}**\nТип: {ctype}\nТекст: `{dec}`")
    except Exception as e:
        await message.channel.send(f"❌ Ошибка расшифровки: возможно, неверный ключ.")


async def cmd_delete(bot, message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8.")
        return
    parts = message.content[len("!шифр удалить"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!шифр удалить (ID)`")
        return
    try:
        cid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    row = await qci.delete_cipher(cid)
    if not row:
        await message.channel.send("Шифр не найден.")
        return
    await message.channel.send(f"✅ Шифр #{cid} удален.")