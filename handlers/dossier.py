from db import queries_dossier as qd
from db import queries as q


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.7.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Создание Досье",
        "1. Создать досье (3+)" if staff_rank >= 3 else "1. Создать досье (3+) ❌",
        "2. Редактировать (5+)" if staff_rank >= 5 else "2. Редактировать (5+) ❌",
        "3. Просмотреть (2+)" if staff_rank >= 2 else "3. Просмотреть (2+) ❌",
        "4. Удалить (7+)" if staff_rank >= 7 else "4. Удалить (7+) ❌",
        "5. Поиск",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_create(message, acc, staff_rank):
    if staff_rank < 3:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 3+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.7.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nСоздать досье\n"
        + "!досье создать (позывной) (отдел) (ранг) (примечание)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_edit(message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.7.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nРедактировать досье\n"
        + "!досье edit (позывной) (поле) (значение)\n"
        + "Поля: rank, department, status, violations, awards, connections, notes\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_view(message, acc, staff_rank):
    if staff_rank < 2:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 2+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.7.1.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nПросмотреть досье\n"
        + "!досье view (позывной)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_delete(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.7.1.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nУдалить досье\n"
        + "!досье удалить (позывной)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_search(message, acc, staff_rank):
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.7.1.5]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nПоиск досье\n"
        + "!досье поиск (запрос)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def cmd_create(bot, message, acc, staff_rank):
    if staff_rank < 3:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 3+.")
        return
    parts = message.content[len("!досье создать"):].strip().split(maxsplit=3)
    if len(parts) < 4:
        await message.channel.send("Формат: `!досье создать (позывной) (отдел) (ранг) (примечание)`")
        return
    callsign, dept, rank_s, notes = parts
    try:
        rank = int(rank_s)
    except ValueError:
        await message.channel.send("Ранг — число.")
        return
    existing = await qd.get_dossier(callsign)
    if existing:
        await message.channel.send("Досье уже существует. Используйте `!досье edit`.")
        return
    d = await qd.insert_dossier(callsign, rank, dept.upper(), notes, acc["callsign"])
    await q.log_action("dossier_create", message.author.id, callsign, {})
    await message.channel.send(f"Досье создано: {callsign}")


async def cmd_edit(bot, message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+.")
        return
    parts = message.content[len("!досье edit"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!досье edit (позывной) (поле) (значение)`")
        return
    callsign, field, value = parts
    d = await qd.get_dossier(callsign)
    if not d:
        await message.channel.send("Досье не найдено.")
        return
    if field == "rank":
        try:
            value = int(value)
        except ValueError:
            await message.channel.send("rank — число.")
            return
    updated = await qd.update_field(callsign, field, value, acc["callsign"])
    if not updated:
        await message.channel.send("Поле не разрешено.")
        return
    await q.log_action("dossier_edit", message.author.id, callsign, {"field": field})
    await message.channel.send(f"Досье {callsign}: поле {field} обновлено.")


async def cmd_view(bot, message, acc, staff_rank):
    if staff_rank < 2:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 2+.")
        return
    parts = message.content[len("!досье view"):].strip().split(maxsplit=1)
    if not parts:
        await message.channel.send("Формат: `!досье view (позывной)`")
        return
    callsign = parts[0]
    d = await qd.get_dossier(callsign)
    if not d:
        await message.channel.send("Досье не найдено.")
        return
    lines = [
        SEP, f"ДОСЬЕ: {d['callsign']}", SEP, MARK, SEP,
        f"Ранг: {d['rank']}",
        f"Отдел: {d['department'] or '—'}",
        f"Статус: {d['status']}",
        f"Нарушения: {d['violations'] or '—'}",
        f"Награды: {d['awards'] or '—'}",
        f"Связи: {d['connections'] or '—'}",
        f"Примечания: {d['notes'] or '—'}",
        f"Создано: {d['created_by']}",
        f"Обновлено: {d['updated_by'] or '—'}",
        SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def cmd_delete(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content[len("!досье удалить"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!досье удалить (позывной)`")
        return
    callsign = parts[0]
    d = await qd.delete_dossier(callsign)
    if not d:
        await message.channel.send("Досье не найдено.")
        return
    await q.log_action("dossier_delete", message.author.id, callsign, {})
    await message.channel.send(f"Досье {callsign} удалено.")


async def cmd_search(bot, message, acc, staff_rank):
    parts = message.content[len("!досье поиск"):].strip().split(maxsplit=1)
    if not parts:
        await message.channel.send("Формат: `!досье поиск (запрос)`")
        return
    query = parts[0]
    rows = await qd.search_dossiers(query)
    if not rows:
        await message.channel.send("Ничего не найдено.")
        return
    lines = [SEP, "Результаты поиска:", SEP]
    for r in rows:
        lines.append(f"• {r['callsign']} (ранг {r['rank']}, {r['department'] or '—'})")
    lines += [SEP]
    await message.channel.send("\n".join(lines))