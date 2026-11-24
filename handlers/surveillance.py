from core.codes import parse_duration, now_utc
from db import queries_surveillance as qsv
from db import queries as q
from utils import roles as role_utils


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.6.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Слежка",
        "1. Начать слежку (5+)" if staff_rank >= 5 else "1. Начать слежку (5+) ❌",
        "2. Отчёт слежки",
        "3. Прекратить слежку",
        "4. Активные слежки (6+)" if staff_rank >= 6 else "4. Активные слежки (6+) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_start(message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.6.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nНачать слежку\n"
        + "!слежка начать (ID или позывной) (причина) (срок h/d)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_report(message, acc, staff_rank):
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.6.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nОтчёт слежки\n"
        + "!слежка отчёт (ID слежки) (текст)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_stop(message, acc, staff_rank):
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.6.1.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nПрекратить слежку\n"
        + "!слежка стоп (ID слежки)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_active(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    rows = await qsv.get_active_surveillance()
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.6.1.4]", SEP, MARK, SEP,
             "Система C.B.A.", "Активные слежки"]
    if not rows:
        lines.append("(нет активных)")
    else:
        for r in rows:
            exp = r["expires_at"].strftime("%Y-%m-%d %H:%M UTC") if r["expires_at"] else "—"
            lines.append(f"[ID {r['id']}] {r['target_name'] or r['target_id']} | {r['reason']} | до {exp}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def cmd_start(bot, message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+.")
        return
    parts = message.content[len("!слежка начать"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!слежка начать (ID/позывной) (причина) (срок h/d)`")
        return
    target = parts[0]
    rest = parts[1] + " " + parts[2]
    words = rest.rsplit(maxsplit=1)
    if len(words) < 2:
        await message.channel.send("Не хватает аргументов.")
        return
    reason, dur = words[0], words[1]
    expires = parse_duration(dur)
    if not expires:
        await message.channel.send("Неверный срок.")
        return

    target_name = target
    member = await role_utils.find_member_by_callsign(bot, target)
    if member:
        target_name = member.display_name

    s = await qsv.insert_surveillance(target, target_name, reason, dur, expires,
                                       acc["callsign"], message.author.id)
    await q.log_action("surveillance_start", message.author.id, target, {"id": s["id"]})
    await message.channel.send(f"Слежка начата. ID: {s['id']}\nЦель: {target_name}\nДо: {expires.strftime('%Y-%m-%d %H:%M UTC')}")


async def cmd_report(bot, message, acc, staff_rank):
    parts = message.content[len("!слежка отчёт"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!слежка отчёт (ID) (текст)`")
        return
    try:
        sid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    text = parts[1]
    s = await qsv.get_surveillance_by_id(sid)
    if not s:
        await message.channel.send("Слежка не найдена.")
        return
    await qsv.add_surv_report(sid, text, acc["callsign"])
    await q.log_action("surveillance_report", message.author.id, str(sid), {})
    await message.channel.send(f"Отчёт по слежке {sid} добавлен.")


async def cmd_stop(bot, message, acc, staff_rank):
    parts = message.content[len("!слежка стоп"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!слежка стоп (ID)`")
        return
    try:
        sid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    s = await qsv.get_surveillance_by_id(sid)
    if not s:
        await message.channel.send("Слежка не найдена.")
        return
    await qsv.stop_surveillance(sid)
    await q.log_action("surveillance_stop", message.author.id, str(sid), {})
    await message.channel.send(f"Слежка {sid} прекращена.")