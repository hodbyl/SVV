from core.codes import parse_duration, now_utc
from db import queries_protocol as qp
from db import queries as q
from utils import roles as role_utils


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.2.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Экстренный протокол",
        "1. Объявить экстренный протокол (7+)" if staff_rank >= 7 else "1. Объявить экстренный протокол (7+) ❌",
        "2. Отменить экстренный протокол (8)" if staff_rank >= 8 else "2. Отменить экстренный протокол (8) ❌",
        "3. Статус протокола",
        "4. История протоколов (7+)" if staff_rank >= 7 else "4. История протоколов (7+) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_announce(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.2.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nОбъявление экстренного протокола\n"
        + "Напишите: !экстренный протокол (уровень) (причина) (срок h/d)\n"
        + "Уровни: Жёлтый, Оранжевый, Красный, Чёрный.\n"
        + "Пример: !экстренный протокол Красный Обнаружен враг 12h\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_cancel(message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.2.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nОтмена экстренного протокола\n"
        + "Напишите: !экстренный протокол отмена (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_status(message, acc, staff_rank):
    p = await qp.get_active_protocol()
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.2.1.3]", SEP, MARK, SEP,
             "Система C.B.A.", "Статус протокола"]
    if not p:
        lines.append("Активного протокола нет.")
    else:
        exp = p["expires_at"].strftime("%Y-%m-%d %H:%M UTC") if p["expires_at"] else "—"
        lines += [
            f"Уровень: {p['level']}",
            f"Причина: {p['reason']}",
            f"Кто объявил: {p['actor_callsign']}",
            f"Действует до: {exp}",
        ]
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_history(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    rows = await qp.list_history(15)
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.2.1.4]", SEP, MARK, SEP,
             "Система C.B.A.", "История протоколов"]
    if not rows:
        lines.append("(пусто)")
    else:
        for i, r in enumerate(rows, start=1):
            exp = r["expires_at"].strftime("%Y-%m-%d %H:%M") if r["expires_at"] else "—"
            lines.append(f"{i}. [{r['status']}] {r['level']} — {r['reason']} | до {exp} | от {r['actor_callsign']}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def cmd_announce(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content[len("!экстренный протокол"):].strip().split(maxsplit=2)
    # parts: [уровень, причина, срок]
    if len(parts) < 3:
        await message.channel.send("Формат: `!экстренный протокол (уровень) (причина) (срок h/d)`")
        return
    level = parts[0]
    rest = parts[1] + " " + parts[2] if len(parts) > 2 else ""
    words = rest.rsplit(maxsplit=1)
    if len(words) < 2:
        await message.channel.send("Не указан срок (например 12h, 3d).")
        return
    reason, dur = words[0], words[1]
    expires = parse_duration(dur)
    if not expires:
        await message.channel.send("Неверный срок. Пример: 12h, 3d.")
        return
    valid_levels = ["Жёлтый", "Оранжевый", "Красный", "Чёрный"]
    if level not in valid_levels:
        await message.channel.send(f"Уровень: {', '.join(valid_levels)}")
        return

    existing = await qp.get_active_protocol()
    if existing:
        await message.channel.send("Уже действует активный протокол. Сначала отмените его.")
        return

    p = await qp.insert_protocol(level, reason, expires, acc["callsign"], message.author.id)
    await q.log_action("protocol_announce", message.author.id, level, {"reason": reason})

    # уведомление
    recipients = await role_utils.get_all_server_members(bot)
    sent = 0
    for m in recipients:
        try:
            await m.send(f"⚠ **ЭКСТРЕННЫЙ ПРОТОКОЛ {level}**\nПричина: {reason}\nДо: {expires.strftime('%Y-%m-%d %H:%M UTC')}")
            sent += 1
        except Exception:
            pass

    await message.channel.send(f"Протокол объявлен.\nУровень: {level}\nПричина: {reason}\nРассылка: {sent} чел.")


async def cmd_cancel(bot, message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8.")
        return
    parts = message.content.split(maxsplit=3)
    if len(parts) < 4:
        await message.channel.send("Формат: `!экстренный протокол отмена (причина)`")
        return
    reason = parts[3]
    p = await qp.cancel_active_protocol(reason)
    if not p:
        await message.channel.send("Активного протокола нет.")
        return
    await q.log_action("protocol_cancel", message.author.id, p["level"], {"reason": reason})
    await message.channel.send(f"Протокол отменён. Причина: {reason}")