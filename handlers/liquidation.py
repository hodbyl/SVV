from db import queries_liquidation as qliq
from db import queries as q
from utils import roles as role_utils


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.11.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Ликвидация угроз",
        "1. Создать приказ (8)" if staff_rank >= 8 else "1. Создать приказ (8) ❌",
        "2. Подтвердить угрозу (7+)" if staff_rank >= 7 else "2. Подтвердить угрозу (7+) ❌",
        "3. Назначить исполнителя (7+)" if staff_rank >= 7 else "3. Назначить исполнителя (7+) ❌",
        "4. Статус ликвидации",
        "5. Архив ликвидаций (8)" if staff_rank >= 8 else "5. Архив ликвидаций (8) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_create(message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.11.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nСоздать приказ на ликвидацию\n"
        + "!ликвидация создать (позывной/ID) (причина) (доказательство)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_confirm(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.11.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nПодтвердить угрозу\n"
        + "!ликвидация подтвердить (ID)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_assign(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.11.1.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nНазначить исполнителя\n"
        + "!ликвидация назначить (ID) (позывной)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_status(message, acc, staff_rank):
    rows = await qliq.list_active(15)
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.11.1.4]", SEP, MARK, SEP,
             "Система C.B.A.", "Статус ликвидации (активные)"]
    if not rows:
        lines.append("(нет активных)")
    else:
        for r in rows:
            lines.append(
                f"#{r['id']} [{r['status']}] цель: {r['target']} | исполнитель: {r['executor_callsign'] or '—'}"
            )
    lines += ["", "0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_archive(message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8. [A.ERR] 0 Назад")
        return
    rows = await qliq.list_orders(30)
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.11.1.5]", SEP, MARK, SEP,
             "Система C.B.A.", "Архив ликвидаций"]
    if not rows:
        lines.append("(пусто)")
    else:
        for r in rows[:15]:
            lines.append(f"#{r['id']} [{r['status']}] {r['target']} — {r['reason'][:40]}")
    lines += ["", "0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


# ---------- команды ----------
async def cmd_create(bot, message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8.")
        return
    parts = message.content[len("!ликвидация создать"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!ликвидация создать (позывной/ID) (причина) (доказательство)`")
        return
    target = parts[0]
    reason = parts[1]
    evidence = parts[2]

    member = await role_utils.find_member_by_callsign(bot, target)
    target_discord = member.id if member else None

    row = await qliq.insert_order(target, target_discord, reason, evidence,
                                    acc["callsign"], message.author.id)
    await q.log_action("liquid_create", message.author.id, target, {"id": row["id"]})
    await message.channel.send(f"Приказ на ликвидацию создан. ID: {row['id']}\nОжидает подтверждения 7+ ранга.")


async def cmd_confirm(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content[len("!ликвидация подтвердить"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!ликвидация подтвердить (ID)`")
        return
    try:
        oid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    row = await qliq.get_order(oid)
    if not row:
        await message.channel.send("Приказ не найден.")
        return
    if row["status"] != "pending":
        await message.channel.send(f"Статус: {row['status']}. Подтверждение невозможно.")
        return

    await qliq.confirm_order(oid, acc["callsign"])
    await q.log_action("liquid_confirm", message.author.id, str(oid), {})
    await message.channel.send(f"Приказ #{oid} подтверждён.")


async def cmd_assign(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content[len("!ликвидация назначить"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!ликвидация назначить (ID) (позывной)`")
        return
    try:
        oid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    executor = parts[1].strip()

    row = await qliq.get_order(oid)
    if not row:
        await message.channel.send("Приказ не найден.")
        return
    if row["status"] != "confirmed":
        await message.channel.send(f"Статус: {row['status']}. Сначала нужно подтверждение 7+.")
        return

    member = await role_utils.find_member_by_callsign(bot, executor)
    executor_discord = member.id if member else None

    await qliq.assign_executor(oid, executor, executor_discord)
    await q.log_action("liquid_assign", message.author.id, str(oid), {"executor": executor})
    await message.channel.send(f"Исполнитель {executor} назначен на приказ #{oid}.")

    if member:
        try:
            await member.send(
                f"**Вам поручена ликвидация #{oid}**\nЦель: {row['target']}\nПричина: {row['reason']}"
            )
        except Exception:
            pass


async def cmd_done(bot, message, acc, staff_rank):
    # !ликвидация готово (ID) (результат)
    parts = message.content[len("!ликвидация готово"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!ликвидация готово (ID) (результат)`")
        return
    try:
        oid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    result = parts[1]
    row = await qliq.get_order(oid)
    if not row:
        await message.channel.send("Приказ не найден.")
        return

    await qliq.complete_order(oid, result)
    await q.log_action("liquid_done", message.author.id, str(oid), {"result": result})
    await message.channel.send(f"Ликвидация #{oid} завершена.")