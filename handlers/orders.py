import discord
from core.codes import parse_duration, now_utc
from core.access import get_staff_rank
from db import queries_orders as qo
from utils import roles as role_utils


async def show_orders_menu(message, acc, staff_rank):
    lines = [
        "-" * 90,
        f"{acc['callsign']} (Ранг {acc['rank']}) [A.1.1.1]",
        "-" * 90,
        "*C.B.A. Team* Не принадлежит распространению",
        "-" * 90,
        "Система C.B.A.",
        "Приказы",
        "1. Выдать приказ (6 ранг и выше)",
        "2. Проверить наличие приказов",
        "3. История приказов (7 ранг и выше)",
        "4. Удалить приказ (6 ранг и выше)",
        "0. Назад",
        "-" * 90,
        "*C.B.A. Team* Не принадлежит распространению",
        "-" * 90,
    ]
    await message.channel.send("\n".join(lines))


async def show_create_order(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send(
            "Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад"
        )
        return
    text = (
        "-" * 90 + "\n"
        + f"{acc['callsign']} (Ранг {acc['rank']}) [A.1.1.2]\n"
        + "-" * 90 + "\n"
        + "*C.B.A. Team* Не принадлежит распространению\n"
        + "-" * 90 + "\n"
        + "Система C.B.A.\n"
        + "Выдача приказов\n"
        + "Напишите команду:\n"
        + "!дать приказ (Отдел/Позывной/Всем отделам/Ранги) (Текст) (срок h/d/m)\n"
        + "0. Назад\n"
        + "-" * 90 + "\n"
        + "*C.B.A. Team* Не принадлежит распространению\n"
        + "-" * 90
    )
    await message.channel.send(text)


async def show_active_orders(message, acc):
    orders = await qo.get_active_orders()
    lines = [
        "-" * 90,
        f"{acc['callsign']} (Ранг {acc['rank']}) [A.1.1.3]",
        "-" * 90,
        "*C.B.A. Team* Не принадлежит распространению",
        "-" * 90,
        "Система C.B.A.",
        "Проверить наличие приказов",
    ]
    if not orders:
        lines.append("(нет активных приказов)")
    else:
        for i, o in enumerate(orders, start=1):
            expires = o["expires_at"].strftime("%Y-%m-%d %H:%M UTC") if o["expires_at"] else "—"
            lines.append(
                f"{i}. [{o['target_type']}: {o['target_value'] or '—'}] "
                f"{o['text']} | до: {expires}"
            )
    lines += [
        "0. Назад",
        "-" * 90,
        "*C.B.A. Team* Не принадлежит распространению",
        "-" * 90,
    ]
    await message.channel.send("\n".join(lines))


async def show_history_orders(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send(
            "Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад"
        )
        return
    orders = await qo.get_history_orders()
    lines = [
        "-" * 90,
        f"{acc['callsign']} (Ранг {acc['rank']}) [A.1.1.4]",
        "-" * 90,
        "*C.B.A. Team* Не принадлежит распространению",
        "-" * 90,
        "Система C.B.A.",
        "История приказов",
    ]
    if not orders:
        lines.append("(история пуста)")
    else:
        for i, o in enumerate(orders, start=1):
            lines.append(
                f"{i}. [{o['status']}] {o['text']} | от: {o['created_by_callsign']}"
            )
    lines += [
        "0. Назад",
        "-" * 90,
        "*C.B.A. Team* Не принадлежит распространению",
        "-" * 90,
    ]
    await message.channel.send("\n".join(lines))


async def show_delete_order(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send(
            "Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад"
        )
        return
    text = (
        "-" * 90 + "\n"
        + f"{acc['callsign']} (Ранг {acc['rank']}) [A.1.1.5]\n"
        + "-" * 90 + "\n"
        + "*C.B.A. Team* Не принадлежит распространению\n"
        + "-" * 90 + "\n"
        + "Система C.B.A.\n"
        + "Удалить приказ\n"
        + "Напишите: !удалить приказ (номер)\n"
        + "0. Назад\n"
        + "-" * 90 + "\n"
        + "*C.B.A. Team* Не принадлежит распространению\n"
        + "-" * 90
    )
    await message.channel.send(text)


async def handle_create_order(bot, message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send(
            "Недостаточный уровень доступа. Требуется ранг 6+."
        )
        return

    content = message.content[len("!дать приказ"):].strip()
    parts = content.split()
    if len(parts) < 4:
        await message.channel.send(
            "Формат: `!дать приказ (Отдел/Позывной/Всем отделам/Ранги) (...кому...) (Текст) (срок h/d/m)`"
        )
        return

    target_type = parts[0]
    valid_types = ["Отдел", "Позывной", "Всем", "Ранг"]
    if target_type not in valid_types:
        await message.channel.send(
            "Тип: `Отдел`, `Позывной`, `Всем`, `Ранг`. Подробнее — в [A.1.1.2]."
        )
        return

    duration = parts[-1]
    expires = parse_duration(duration)
    if not expires:
        await message.channel.send(
            "Последний аргумент должен быть сроком: 60d, 12h, 2m"
        )
        return

    middle = parts[1:-1]

    if target_type == "Всем":
        target_value = None
        text = " ".join(middle)
    elif target_type == "Ранг":
        rank_spec = middle[0] if middle else ""
        target_value = rank_spec
        text = " ".join(middle[1:])
    else:
        target_value = middle[0] if middle else None
        text = " ".join(middle[1:])

    if not text:
        await message.channel.send("Не указан текст приказа.")
        return

    if target_type == "Всем" and staff_rank < 7:
        await message.channel.send(
            "Приказ «Всем отделам» может выдавать только ранг 7+."
        )
        return

    order = await qo.insert_order(
        target_type, target_value, text, duration, expires,
        message.author.id, acc["callsign"]
    )
    await message.channel.send(
        f"Приказ создан. ID: {order['id']}\n"
        f"Тип: {target_type}\n"
        f"Цель: {target_value or 'все'}\n"
        f"Текст: {text}\n"
        f"Действует до: {expires.strftime('%Y-%m-%d %H:%M UTC')}"
    )

    await notify_order(bot, target_type, target_value, acc["callsign"], text)


async def notify_order(bot, target_type, target_value, author_callsign, text):
    recipients = []

    if target_type == "Отдел" and target_value:
        recipients = await role_utils.get_department_members(bot, target_value)
    elif target_type == "Позывной" and target_value:
        guild = bot.get_guild(1462104321461063773)
        if guild:
            for m in guild.members:
                if m.bot:
                    continue
                name = (m.nick or m.name or "").lower()
                if target_value.lower() in name:
                    recipients.append(m)
                    break
    elif target_type == "Всем":
        recipients = await role_utils.get_all_server_members(bot)
    elif target_type == "Ранг" and target_value:
        spec = target_value
        if spec.endswith("+"):
            r = int(spec[:-1])
            recipients = await role_utils.get_members_by_rank_range(bot, r, 8)
        elif spec.endswith("-"):
            r = int(spec[:-1])
            recipients = await role_utils.get_members_by_rank_range(bot, 1, r)
        else:
            r = int(spec)
            recipients = await role_utils.get_members_by_rank(bot, r)

    sent = 0
    for member in recipients:
        try:
            await member.send(
                f"**ПРИКАЗ** от {author_callsign}:\n{text}"
            )
            sent += 1
        except Exception:
            pass

    return sent


async def handle_delete_order(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send(
            "Недостаточный уровень доступа. Требуется ранг 6+."
        )
        return
    parts = message.content.split()
    if len(parts) != 3:
        await message.channel.send("Формат: `!удалить приказ (номер)`")
        return
    try:
        oid = int(parts[2])
    except ValueError:
        await message.channel.send("Номер — число.")
        return
    order = await qo.get_order_by_id(oid)
    if not order:
        await message.channel.send("Приказ не найден.")
        return
    await qo.delete_order(oid)
    await message.channel.send(f"Приказ {oid} удалён.")