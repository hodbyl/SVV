from core.codes import parse_duration, now_utc
from db import queries_tasks as qt
from db import queries as q
from utils import roles as role_utils


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.3.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Задачи",
        "1. Создать задачу (4+)" if staff_rank >= 4 else "1. Создать задачу (4+) ❌",
        "2. Мои задачи",
        "3. Выдать задачу отделу (6+)" if staff_rank >= 6 else "3. Выдать задачу отделу (6+) ❌",
        "4. Закрыть задачу",
        "5. Просроченные задачи (5+)" if staff_rank >= 5 else "5. Просроченные задачи (5+) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_create(message, acc, staff_rank):
    if staff_rank < 4:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 4+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.3.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nСоздать задачу\n"
        + "!задача создать (позывной) (текст) (срок h/d/m) (приоритет)\n"
        + "Приоритеты: низкий, обычный, высокий, критический.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_my(message, acc, staff_rank):
    tasks = await qt.get_my_tasks(acc["callsign"])
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.3.1.2]", SEP, MARK, SEP,
             "Система C.B.A.", "Мои задачи"]
    if not tasks:
        lines.append("(нет активных задач)")
    else:
        for i, t in enumerate(tasks, start=1):
            exp = t["expires_at"].strftime("%Y-%m-%d %H:%M UTC") if t["expires_at"] else "—"
            lines.append(f"{i}. [ID {t['id']}] [{t['priority']}] {t['text']} | до {exp} | от {t['created_by_callsign']}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_issue_dept(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.3.1.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nВыдать задачу отделу\n"
        + "!задача отдел (Отдел) (текст) (срок h/d/m) (приоритет)\n"
        + "Отделы: FUR, DEF, SUW, TOJ, SRT, CHT, KOS, C.B.A.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_close(message, acc, staff_rank):
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.3.1.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nЗакрыть задачу\n"
        + "!задача закрыть (ID) (отчёт)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_overdue(message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+. [A.ERR] 0 Назад")
        return
    await qt.mark_expired_tasks()
    rows = await qt.get_overdue_tasks()
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.3.1.5]", SEP, MARK, SEP,
             "Система C.B.A.", "Просроченные задачи"]
    if not rows:
        lines.append("(нет просроченных)")
    else:
        for i, t in enumerate(rows, start=1):
            exp = t["expires_at"].strftime("%Y-%m-%d %H:%M") if t["expires_at"] else "—"
            who = t["target_callsign"] or t["department"] or "—"
            lines.append(f"{i}. [ID {t['id']}] {who} — {t['text']} | до {exp}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def cmd_create(bot, message, acc, staff_rank):
    if staff_rank < 4:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 4+.")
        return
    parts = message.content[len("!задача создать"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!задача создать (позывной) (текст) (срок) (приоритет)`")
        return
    callsign = parts[0]
    rest = parts[1] + " " + parts[2]
    tokens = rest.rsplit(maxsplit=2)
    # [текст..., срок, приоритет]
    if len(tokens) < 3:
        await message.channel.send("Не хватает аргументов: текст, срок, приоритет.")
        return
    text, dur, priority = tokens[0], tokens[1], tokens[2]
    expires = parse_duration(dur)
    if not expires:
        await message.channel.send("Неверный срок. Пример: 12h, 3d.")
        return

    member = await role_utils.find_member_by_callsign(bot, callsign)
    discord_id = member.id if member else None

    t = await qt.insert_task(callsign, discord_id, None, text, dur,
                             expires, priority, acc["callsign"], message.author.id)
    await q.log_action("task_create", message.author.id, callsign, {"id": t["id"]})
    await message.channel.send(f"Задача создана. ID: {t['id']}\nКому: {callsign}\nТекст: {text}")

    if member:
        try:
            await member.send(f"**Задача (ID {t['id']})** от {acc['callsign']}\n{text}\nДо: {expires.strftime('%Y-%m-%d %H:%M UTC')}\nПриоритет: {priority}")
        except Exception:
            pass


async def cmd_dept(bot, message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content[len("!задача отдел"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!задача отдел (Отдел) (текст) (срок) (приоритет)`")
        return
    dept = parts[0].upper()
    rest = parts[1] + " " + parts[2]
    tokens = rest.rsplit(maxsplit=2)
    if len(tokens) < 3:
        await message.channel.send("Не хватает аргументов.")
        return
    text, dur, priority = tokens[0], tokens[1], tokens[2]
    expires = parse_duration(dur)
    if not expires:
        await message.channel.send("Неверный срок.")
        return

    t = await qt.insert_task(None, None, dept, text, dur,
                             expires, priority, acc["callsign"], message.author.id)
    await q.log_action("task_dept", message.author.id, dept, {"id": t["id"]})
    await message.channel.send(f"Задача отделу {dept} создана. ID: {t['id']}")

    recipients = await role_utils.get_department_members(bot, dept)
    sent = 0
    for m in recipients:
        try:
            await m.send(f"**Задача отдела {dept} (ID {t['id']})**\n{text}\nДо: {expires.strftime('%Y-%m-%d %H:%M UTC')}")
            sent += 1
        except Exception:
            pass
    await message.channel.send(f"Рассылка: {sent} чел.")


async def cmd_close(bot, message, acc, staff_rank):
    parts = message.content[len("!задача закрыть"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!задача закрыть (ID) (отчёт)`")
        return
    try:
        tid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    report = parts[1]
    t = await qt.get_task_by_id(tid)
    if not t:
        await message.channel.send("Задача не найдена.")
        return
    await qt.close_task(tid, report)
    await q.log_action("task_close", message.author.id, str(tid), {"report": report})
    await message.channel.send(f"Задача {tid} закрыта.")

    # уведомить постановщика
    if t["created_by_discord"]:
        try:
            guild = bot.get_guild(1462104321461063773)
            member = await guild.fetch_member(t["created_by_discord"]) if guild else None
            if member:
                await member.send(f"Задача {tid} закрыта.\nОтчёт: {report}")
        except Exception:
            pass