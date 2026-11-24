from db import queries as q
from db.connection import pool


async def cmd_deactivate(bot, message, acc, staff_rank):
    """7+ ранг деактивирует аккаунт по позывному."""
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return

    parts = message.content[len("!деактивировать"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!деактивировать (позывной) (причина)`")
        return

    callsign = parts[0]
    reason = parts[1]

    target = await q.get_account_by_callsign(callsign)
    if not target:
        await message.channel.send(f"Аккаунт «{callsign}» не найден.")
        return

    if target["is_deactivated"]:
        await message.channel.send(f"Аккаунт «{callsign}» уже деактивирован.")
        return

    # Защита от деактивации самого себя
    if target["callsign"] == acc["callsign"]:
        await message.channel.send("Нельзя деактивировать собственный аккаунт.")
        return

    await q.deactivate_account(callsign, reason, acc["callsign"])
    await q.log_action("deactivate_account", message.author.id, callsign, {"reason": reason})

    # Разлогинить все активные сессии этого аккаунта
    sessions = await pool().fetch(
        "SELECT discord_id FROM sessions WHERE account_id=$1", target["id"]
    )
    for s in sessions:
        await q.upsert_session(s["discord_id"], account_id=None)
        await q.set_session_window(s["discord_id"], "A.1.1", None)
        try:
            guild = bot.get_guild(1462104321461063773)
            member = await guild.fetch_member(s["discord_id"]) if guild else None
            if member:
                await member.send(f"🚫 **Ваш аккаунт C.B.A. деактивирован.**\nПричина: {reason}")
        except Exception:
            pass

    await message.channel.send(f"✅ Аккаунт «{callsign}» деактивирован.\nПричина: {reason}")


async def cmd_activate(bot, message, acc, staff_rank):
    """7+ ранг восстанавливает аккаунт."""
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return

    parts = message.content[len("!активировать"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!активировать (позывной)`")
        return

    callsign = parts[0]
    target = await q.get_account_by_callsign(callsign)
    if not target:
        await message.channel.send(f"Аккаунт «{callsign}» не найден.")
        return

    if not target["is_deactivated"]:
        await message.channel.send(f"Аккаунт «{callsign}» и так активен.")
        return

    await q.activate_account(callsign)
    await q.log_action("activate_account", message.author.id, callsign, {})
    await message.channel.send(f"✅ Аккаунт «{callsign}» восстановлен. Игрок может войти снова.")


async def cmd_list_deactivated(bot, message, acc, staff_rank):
    """7+ ранг смотрит список деактивированных аккаунтов."""
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return

    rows = await q.list_deactivated(30)
    lines = ["Деактивированные аккаунты:", "-" * 40]
    if not rows:
        lines.append("(пусто)")
    else:
        for i, r in enumerate(rows, start=1):
            when = r["deactivated_at"].strftime("%Y-%m-%d %H:%M") if r["deactivated_at"] else "—"
            lines.append(
                f"{i}. {r['callsign']} (ранг {r['rank']}) — {r['deactivated_reason'] or '—'} | {when}"
            )
    
    await message.channel.send("\n".join(lines))

async def cmd_restore(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return

    parts = message.content[len("!восстановить"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!восстановить (позывной)`")
        return

    callsign = parts[0]
    target = await q.get_account_by_callsign(callsign)
    if not target:
        await message.channel.send(f"Аккаунт «{callsign}» не найден.")
        return

    was_blocked = target["is_blocked"]
    was_deactivated = target["is_deactivated"]

    if not was_blocked and not was_deactivated:
        await message.channel.send(f"Аккаунт «{callsign}» и так активен.")
        return

    await q.full_restore_account(callsign)
    await q.log_action("restore_account", message.author.id, callsign,
                       {"was_blocked": was_blocked, "was_deactivated": was_deactivated})

    msg = f"✅ Аккаунт «{callsign}» восстановлен.\n"
    if was_blocked:
        msg += "• Снята блокировка (бан)\n"
    if was_deactivated:
        msg += "• Снята деактивация\n"
    msg += "Игрок может войти снова: `!start`"
    await message.channel.send(msg)