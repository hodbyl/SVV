from db import queries_reports_out as qro
from db import queries as q
from utils import roles as role_utils


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.12.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Отчёты",
        "1. Создать отчёт (2+)" if staff_rank >= 2 else "1. Создать отчёт (2+) ❌",
        "2. Отправить отчёт (2+)" if staff_rank >= 2 else "2. Отправить отчёт (2+) ❌",
        "3. Мои отчёты",
        "4. Проверить отчёты (5+)" if staff_rank >= 5 else "4. Проверить отчёты (5+) ❌",
        "5. Архив отчётов (6+)" if staff_rank >= 6 else "5. Архив отчётов (6+) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_create(message, acc, staff_rank):
    if staff_rank < 2:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 2+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.12.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nСоздать отчёт\n"
        + "!отчёт создать (тип) (период) (текст)\n"
        + "Типы: оперативный, разведывательный, боевой, дисциплинарный, финансовый.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_send(message, acc, staff_rank):
    if staff_rank < 2:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 2+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.12.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nОтправить отчёт на проверку\n"
        + "!отчёт отправить (ID)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_my(message, acc, staff_rank):
    rows = await qro.get_my_reports(acc["callsign"])
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.12.1.3]", SEP, MARK, SEP,
             "Система C.B.A.", "Мои отчёты"]
    if not rows:
        lines.append("(нет отчётов)")
    else:
        for r in rows:
            status_map = {"draft": "черновик", "sent": "на проверке", "accepted": "принят", "rejected": "отклонён"}
            lines.append(f"#{r['id']} [{status_map.get(r['status'], r['status'])}] {r['report_type']}: {r['text'][:40]}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_review(message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.12.1.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nПроверить отчёты\n"
        + "!отчёт проверить (ID) (принят/отклонён) (комментарий)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_archive(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    rows = await qro.get_archive_reports()
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.12.1.5]", SEP, MARK, SEP,
             "Система C.B.A.", "Архив отчётов"]
    if not rows:
        lines.append("(архив пуст)")
    else:
        for r in rows:
            lines.append(f"#{r['id']} [{r['status']}] {r['author_callsign']} — {r['text'][:40]}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def cmd_create(bot, message, acc, staff_rank):
    if staff_rank < 2:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 2+.")
        return
    parts = message.content[len("!отчёт создать"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!отчёт создать (тип) (период) (текст)`")
        return
    rtype, period, text = parts
    valid = ["оперативный", "разведывательный", "боевой", "дисциплинарный", "финансовый"]
    if rtype not in valid:
        await message.channel.send(f"Типы: {', '.join(valid)}")
        return

    r = await qro.insert_report(acc["callsign"], message.author.id, rtype, text, period)
    await q.log_action("report_out_create", message.author.id, str(r["id"]), {"type": rtype})
    await message.channel.send(f"✅ Отчёт создан как черновик. ID: {r['id']}")


async def cmd_send(bot, message, acc, staff_rank):
    parts = message.content[len("!отчёт отправить"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!отчёт отправить (ID)`")
        return
    try:
        rid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    r = await qro.get_report(rid)
    if not r:
        await message.channel.send("Отчёт не найден.")
        return
    if r["author_callsign"] != acc["callsign"]:
        await message.channel.send("Это не ваш отчёт.")
        return
    if r["status"] != "draft":
        await message.channel.send(f"Статус отчёта: {r['status']}. Отправить можно только черновик.")
        return

    await qro.update_status(rid, "sent", None)
    await message.channel.send(f"✅ Отчёт #{rid} отправлен на проверку 5+ рангу.")

    # Уведомление проверяющим
    recipients = await role_utils.get_members_by_rank_range(bot, 5, 8)
    for m in recipients:
        try:
            await m.send(f"**На проверку поступил отчёт #{rid}**\nОт: {acc['callsign']}\nТип: {r['report_type']}")
        except Exception:
            pass


async def cmd_review(bot, message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+.")
        return
    parts = message.content[len("!отчёт проверить"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!отчёт проверить (ID) (принят/отклонён) (комментарий)`")
        return
    try:
        rid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    status = parts[1].lower()
    if status not in ("принят", "отклонён"):
        await message.channel.send("Статус: `принят` или `отклонён`.")
        return
    db_status = "accepted" if status == "принят" else "rejected"
    comment = parts[2]

    r = await qro.get_report(rid)
    if not r:
        await message.channel.send("Отчёт не найден.")
        return
    if r["status"] != "sent":
        await message.channel.send(f"Статус отчёта: {r['status']}. Проверить можно только отправленный.")
        return

    await qro.update_status(rid, db_status, acc["callsign"], comment)
    await q.log_action("report_out_review", message.author.id, str(rid), {"status": db_status})
    await message.channel.send(f"✅ Отчёт #{rid}: {status}.")

    # Уведомление автору
    if r["author_discord"]:
        try:
            guild = bot.get_guild(1462104321461063773)
            m = await guild.fetch_member(r["author_discord"]) if guild else None
            if m:
                await m.send(f"**Ваш отчёт #{rid}: {status}**\nКомментарий: {comment}")
        except Exception:
            pass