from core.codes import parse_duration, now_utc
from db import queries_codenames as qc
from db import queries as q

SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"

async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.14.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Кодовые имена",
        "1. Создать кодовое имя (6+)" if staff_rank >= 6 else "1. Создать кодовое имя (6+) ❌",
        "2. Изменить кодовое имя (6+)" if staff_rank >= 6 else "2. Изменить кодовое имя (6+) ❌",
        "3. Список кодовых имён (5+)" if staff_rank >= 5 else "3. Список кодовых имён (5+) ❌",
        "4. Удалить кодовое имя (8)" if staff_rank >= 8 else "4. Удалить кодовое имя (8) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_create(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.14.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nСоздать кодовое имя\n"
        + "!кодовоеимя создать (позывной) (кодовое) (срок h/d)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_change(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.14.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nИзменить кодовое имя\n"
        + "!кодовоеимя изменить (позывной) (новое кодовое)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_list(message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+. [A.ERR] 0 Назад")
        return
    rows = await qc.list_codenames()
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.14.1.3]", SEP, MARK, SEP,
             "Система C.B.A.", "Список кодовых имён"]
    if not rows:
        lines.append("(пусто)")
    else:
        for r in rows:
            exp = r["expires_at"].strftime("%Y-%m-%d") if r["expires_at"] else "—"
            lines.append(f"• {r['target_callsign']} — «{r['codename']}» (до {exp})")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_delete(message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.14.1.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nУдалить кодовое имя\n"
        + "!кодовоеимя удалить (кодовое)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def cmd_create(bot, message, acc, staff_rank):
    print(f"DEBUG: Функция cmd_create ВЫЗВАНА! Текст: {message.content}")  # <-- ДОБАВЬ ЭТО
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content[len("!кодовоеимя создать"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!кодовоеимя создать (позывной) (кодовое) (срок h/d)`")
        return
    callsign, codename, dur = parts
    expires = parse_duration(dur)
    if not expires:
        await message.channel.send("Неверный срок. Пример: 30d.")
        return

    try:
        r = await qc.insert_codename(callsign, codename, expires, acc["callsign"])
        await q.log_action("codename_create", message.author.id, callsign, {"codename": codename})
        await message.channel.send(f"✅ Кодовое имя «{codename}» закреплено за {callsign} до {expires.strftime('%Y-%m-%d')}.")
    except Exception as e:
        await message.channel.send(f"❌ Ошибка базы данных: `{e}`")


async def cmd_change(bot, message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content[len("!кодовоеимя изменить"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!кодовоеимя изменить (позывной) (новое)`")
        return
    callsign, new_name = parts
    r = await qc.update_codename(callsign, new_name)
    if not r:
        await message.channel.send("Кодовое имя для этого игрока не найдено. Сначала создайте.")
        return
    await message.channel.send(f"✅ Кодовое имя для {callsign} изменено на «{new_name}».")


async def cmd_delete(bot, message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8.")
        return
    parts = message.content[len("!кодовоеимя удалить"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!кодовоеимя удалить (кодовое)`")
        return
    codename = parts[0]
    r = await qc.delete_codename(codename)
    if not r:
        await message.channel.send("Такое кодовое имя не найдено.")
        return
    await message.channel.send(f"✅ Кодовое имя «{codename}» удалено.")