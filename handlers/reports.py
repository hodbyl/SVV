from db import queries_reports as qr
from db import queries as q
from utils import roles as role_utils


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.4.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Донесения",
        "1. Отправить донесение",
        "2. Мои донесения",
        "3. Входящие (5+)" if staff_rank >= 5 else "3. Входящие (5+) ❌",
        "4. Проверить (6+)" if staff_rank >= 6 else "4. Проверить (6+) ❌",
        "5. Архив (7+)" if staff_rank >= 7 else "5. Архив (7+) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_send(message, acc, staff_rank):
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.4.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nОтправить донесение\n"
        + "!донесение (тип) (текст)\n"
        + "Типы: разведка, бой, потери, подозрение, перемещение, связь.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_my(message, acc, staff_rank):
    rows = await qr.get_my_reports(acc["callsign"])
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.4.1.2]", SEP, MARK, SEP,
             "Система C.B.A.", "Мои донесения"]
    if not rows:
        lines.append("(нет)")
    else:
        for i, r in enumerate(rows, start=1):
            lines.append(f"{i}. [ID {r['id']}] [{r['report_type']}] [{r['status']}] {r['text'][:60]}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_incoming(message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+. [A.ERR] 0 Назад")
        return
    rows = await qr.get_incoming_reports()
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.4.1.3]", SEP, MARK, SEP,
             "Система C.B.A.", "Входящие донесения"]
    if not rows:
        lines.append("(нет входящих)")
    else:
        for i, r in enumerate(rows, start=1):
            lines.append(f"{i}. [ID {r['id']}] [{r['report_type']}] от {r['author_callsign']}: {r['text'][:50]}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_review(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.4.1.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nПроверить донесение\n"
        + "!донесение проверить (ID) (принято|отклонено) (комментарий)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_archive(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    rows = await qr.get_archive_reports()
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.4.1.5]", SEP, MARK, SEP,
             "Система C.B.A.", "Архив донесений"]
    if not rows:
        lines.append("(архив пуст)")
    else:
        for i, r in enumerate(rows, start=1):
            lines.append(f"{i}. [ID {r['id']}] [{r['status']}] {r['author_callsign']}: {r['text'][:50]}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def cmd_send(bot, message, acc, staff_rank):
    parts = message.content[len("!донесение"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!донесение (тип) (текст)`")
        return
    rtype = parts[0]
    text = parts[1]
    valid = ["разведка", "бой", "потери", "подозрение", "перемещение", "связь"]
    if rtype not in valid:
        await message.channel.send(f"Типы: {', '.join(valid)}")
        return

    r = await qr.insert_report(acc["callsign"], message.author.id, rtype, text)
    await q.log_action("report_send", message.author.id, str(r["id"]), {"type": rtype})
    await message.channel.send(f"Донесение отправлено. ID: {r['id']}")

    recipients = await role_utils.get_members_by_rank_range(bot, 5, 8)
    for m in recipients:
        if m.id == message.author.id:
            continue
        try:
            await m.send(f"**Входящее донесение (ID {r['id']})** [{rtype}]\nОт: {acc['callsign']}\n{text}")
        except Exception:
            pass


async def cmd_review(bot, message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content[len("!донесение проверить"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!донесение проверить (ID) (принято|отклонено) (комментарий)`")
        return
    try:
        rid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    status_in = parts[1].lower()
    comment = parts[2]

    if status_in not in ("принято", "отклонено"):
        await message.channel.send("Статус: `принято` или `отклонено`.")
        return
    db_status = "accepted" if status_in == "принято" else "rejected"

    r = await qr.get_report_by_id(rid)
    if not r:
        await message.channel.send("Донесение не найдено.")
        return

    await qr.review_report(rid, db_status, comment, acc["callsign"])
    await q.log_action("report_review", message.author.id, str(rid), {"status": db_status})
    await message.channel.send(f"Донесение {rid}: {status_in}.")

    # уведомить автора
    if r["author_discord"]:
        try:
            guild = bot.get_guild(1462104321461063773)
            member = await guild.fetch_member(r["author_discord"]) if guild else None
            if member:
                await member.send(f"Ваше донесение {rid}: **{status_in}**\nКомментарий: {comment}")
        except Exception:
            pass