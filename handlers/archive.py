from db import queries_archive as qar
from db import queries as q


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.13.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Архив",
        "1. Поиск по архиву (3+)" if staff_rank >= 3 else "1. Поиск по архиву (3+) ❌",
        "2. Добавить в архив (6+)" if staff_rank >= 6 else "2. Добавить в архив (6+) ❌",
        "3. Извлечь из архива (7+)" if staff_rank >= 7 else "3. Извлечь из архива (7+) ❌",
        "4. Удалить из архива (8)" if staff_rank >= 8 else "4. Удалить из архива (8) ❌",
        "5. Список архивов",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_search(message, acc, staff_rank):
    if staff_rank < 3:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 3+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.13.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nПоиск по архиву\n"
        + "!архив поиск (запрос)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_add(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.13.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nДобавить в архив\n"
        + "!архив добавить (тип) (заголовок) (текст)\n"
        + "Типы: отчёт, донесение, приказ, спецоперация, прочее.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_extract(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.13.1.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nИзвлечь из архива\n"
        + "!архив извлечь (ID)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_delete(message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.13.1.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nУдалить из архива\n"
        + "!архив удалить (ID)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_list(message, acc, staff_rank):
    rows = await qar.get_archive(30)
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.13.1.5]", SEP, MARK, SEP,
             "Система C.B.A.", "Список архивов"]
    if not rows:
        lines.append("(архив пуст)")
    else:
        for r in rows:
            lines.append(f"#{r['id']} [{r['doc_type']}] {r['title'][:40]} — {r['author_callsign']}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def cmd_search(bot, message, acc, staff_rank):
    if staff_rank < 3:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 3+.")
        return
    parts = message.content[len("!архив поиск"):].strip().split(maxsplit=1)
    if not parts:
        await message.channel.send("Формат: `!архив поиск (запрос)`")
        return
    query = parts[0]

    rows = await qar.search_archive(query)
    if not rows:
        await message.channel.send(f"По запросу «{query}» ничего не найдено.")
        return

    lines = [f"Результаты поиска «{query}»:", "-" * 40]
    for r in rows:
        lines.append(f"#{r['id']} [{r['doc_type']}] {r['title']} — {r['author_callsign']}")
    await message.channel.send("\n".join(lines))


async def cmd_add(bot, message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content[len("!архив добавить"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!архив добавить (тип) (заголовок) (текст)`")
        return
    doc_type, title, content = parts

    r = await qar.insert_archive(doc_type, title, content, acc["callsign"], message.author.id)
    await q.log_action("archive_add", message.author.id, str(r["id"]), {"type": doc_type})
    await message.channel.send(f"✅ Документ добавлен в архив. ID: {r['id']}")


async def cmd_extract(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content[len("!архив извлечь"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!архив извлечь (ID)`")
        return
    try:
        aid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return

    row = await qar.get_archive(1)
    # Ищем по ID
    from db.connection import pool
    row = await pool().fetchrow("SELECT * FROM archive WHERE id=$1", aid)
    if not row:
        await message.channel.send("Документ не найден.")
        return

    lines = [SEP, f"ДОКУМЕНТ #{row['id']}", SEP, MARK, SEP,
             f"Тип: {row['doc_type']}",
             f"Заголовок: {row['title']}",
             f"Автор: {row['author_callsign']}",
             f"Дата: {row['created_at'].strftime('%Y-%m-%d %H:%M')}",
             SEP, row['content'], SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def cmd_delete(bot, message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8.")
        return
    parts = message.content[len("!архив удалить"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!архив удалить (ID)`")
        return
    try:
        aid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return

    row = await qar.delete_archive(aid)
    if not row:
        await message.channel.send("Документ не найден.")
        return
    await q.log_action("archive_delete", message.author.id, str(aid), {})
    await message.channel.send(f"✅ Документ #{aid} удалён из архива.")