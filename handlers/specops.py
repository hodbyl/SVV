from core.codes import parse_duration, now_utc
from db import queries_specops as qs
from db import queries as q
from utils import roles as role_utils


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.5.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Спецоперации",
        "1. Создать (7+)" if staff_rank >= 7 else "1. Создать (7+) ❌",
        "2. Назначить участников (6+)" if staff_rank >= 6 else "2. Назначить участников (6+) ❌",
        "3. Статус операции",
        "4. Отчёт по операции",
        "5. Отменить операцию (8)" if staff_rank >= 8 else "5. Отменить операцию (8) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_create(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.5.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nСоздать спецоперацию\n"
        + "!спецоперация создать (название) (цель) (Отдел) (срок h/d) (уровень 1-8)\n"
        + "Отделы: FUR, DEF, SUW, TOJ, SRT, CHT, KOS, C.B.A.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_assign(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.5.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nНазначить участников\n"
        + "!спецоперация назначить (название) (позывной)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_status(message, acc, staff_rank):
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.5.1.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nСтатус операции\n"
        + "!спецоперация статус (название)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_report(message, acc, staff_rank):
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.5.1.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nОтчёт по операции\n"
        + "!спецоперация отчёт (название) (текст)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_cancel(message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.5.1.5]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nОтменить операцию\n"
        + "!спецоперация отмена (название) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def cmd_create(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content[len("!спецоперация создать"):].strip().split(maxsplit=4)
    if len(parts) < 5:
        await message.channel.send("Формат: `!спецоперация создать (название) (цель) (Отдел) (срок) (уровень)`")
        return
    name, goal, department, dur, lvl_s = parts
    expires = parse_duration(dur)
    if not expires:
        await message.channel.send("Неверный срок. Пример: 12h, 3d.")
        return
    try:
        lvl = int(lvl_s)
    except ValueError:
        await message.channel.send("Уровень — число 1–8.")
        return
    if lvl < 1 or lvl > 8:
        await message.channel.send("Уровень от 1 до 8.")
        return

    existing = await qs.get_specops_by_name(name)
    if existing:
        await message.channel.send("Операция с таким именем уже активна.")
        return

    op = await qs.insert_specops(name, goal, department.upper(), dur, expires,
                                 lvl, acc["callsign"], message.author.id)
    await q.log_action("specops_create", message.author.id, name, {"id": op["id"]})
    await message.channel.send(f"Спецоперация создана.\nID: {op['id']}\nНазвание: {name}\nЦель: {goal}")

    recipients = await role_utils.get_department_members(bot, department.upper())
    for m in recipients:
        try:
            await m.send(f"**Спецоперация «{name}»**\nЦель: {goal}\nОтдел: {department.upper()}\nДо: {expires.strftime('%Y-%m-%d %H:%M UTC')}")
        except Exception:
            pass


async def cmd_assign(bot, message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content[len("!спецоперация назначить"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!спецоперация назначить (название) (позывной)`")
        return
    name, callsign = parts[0], parts[1].strip()
    op = await qs.get_specops_by_name(name)
    if not op:
        await message.channel.send("Активная спецоперация не найдена.")
        return

    member = await role_utils.find_member_by_callsign(bot, callsign)
    discord_id = member.id if member else None

    await qs.add_member(op["id"], callsign, discord_id)
    await q.log_action("specops_assign", message.author.id, name, {"callsign": callsign})
    await message.channel.send(f"{callsign} назначен в операцию «{name}».")

    if member:
        try:
            await member.send(f"Вы назначены в спецоперацию «{name}».\nЦель: {op['goal']}")
        except Exception:
            pass


async def cmd_status(bot, message, acc, staff_rank):
    parts = message.content[len("!спецоперация статус"):].strip().split(maxsplit=1)
    if not parts:
        await message.channel.send("Формат: `!спецоперация статус (название)`")
        return
    name = parts[0]
    op = await qs.get_specops_by_name(name)
    if not op:
        await message.channel.send("Операция не найдена.")
        return
    members = await qs.get_members(op["id"])
    exp = op["expires_at"].strftime("%Y-%m-%d %H:%M UTC") if op["expires_at"] else "—"
    lines = [
        f"Название: {op['name']}",
        f"Цель: {op['goal']}",
        f"Отдел: {op['department']}",
        f"Статус: {op['status']}",
        f"До: {exp}",
        f"Участники ({len(members)}):",
    ]
    for m in members:
        lines.append(f"  - {m['callsign']}")
    await message.channel.send("\n".join(lines))


async def cmd_report(bot, message, acc, staff_rank):
    parts = message.content[len("!спецоперация отчёт"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!спецоперация отчёт (название) (текст)`")
        return
    name, report_text = parts[0], parts[1]
    op = await qs.get_specops_by_name(name)
    if not op:
        await message.channel.send("Операция не найдена.")
        return
    await qs.add_report(op["id"], report_text)
    await q.log_action("specops_report", message.author.id, name, {})
    await message.channel.send(f"Отчёт прикреплён к операции «{name}».")


async def cmd_cancel(bot, message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8.")
        return
    parts = message.content[len("!спецоперация отмена"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!спецоперация отмена (название) (причина)`")
        return
    name, reason = parts[0], parts[1]
    op = await qs.get_specops_by_name(name)
    if not op:
        await message.channel.send("Операция не найдена.")
        return
    await qs.set_status(op["id"], "cancelled", reason)
    await q.log_action("specops_cancel", message.author.id, name, {"reason": reason})
    await message.channel.send(f"Операция «{name}» отменена. Причина: {reason}")