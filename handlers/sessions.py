from db.connection import pool
from db import queries as q


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def cmd_logout(bot, message, acc, staff_rank):
    """Игрок сам выходит из своего аккаунта."""
    uid = message.author.id
    await q.upsert_session(uid, account_id=None)
    await q.set_session_window(uid, "A.1.1", None)
    await message.channel.send(
        "Вы вышли из аккаунта.\n\n"
        "Чтобы войти снова: `!start`"
    )
    await q.log_action("logout", uid, acc["callsign"] if acc else None, {})


async def cmd_kick(bot, message, acc, staff_rank):
    """7+ ранг принудительно разлогинивает игрока по позывному или Discord ID."""
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return

    parts = message.content[len("!выгнать"):].strip().split(maxsplit=1)
    if not parts:
        await message.channel.send("Формат: `!выгнать (позывной или Discord ID)`")
        return

    query = parts[0].strip()

    # Ищем аккаунт по позывному
    target_acc = await pool().fetchrow(
        "SELECT * FROM accounts WHERE callsign=$1", query
    )
    if not target_acc:
        await message.channel.send(f"Аккаунт «{query}» не найден.")
        return

    # Ищем активные сессии этого аккаунта
    sessions = await pool().fetch(
        "SELECT discord_id FROM sessions WHERE account_id=$1",
        target_acc["id"]
    )

    if not sessions:
        await message.channel.send(
            f"У аккаунта «{query}» нет активных сессий."
        )
        return

    # Разлогиниваем все сессии
    for s in sessions:
        await q.upsert_session(s["discord_id"], account_id=None)
        await q.set_session_window(s["discord_id"], "A.1.1", None)
        # пробуем уведомить игрока
        try:
            guild = bot.get_guild(1462104321461063773)
            member = await guild.fetch_member(s["discord_id"]) if guild else None
            if member:
                await member.send(
                    f"Ваша сессия C.B.A. завершена администратором.\n"
                    f"Причина: принудительный выход.\n"
                    f"Для входа заново: `!start`"
                )
        except Exception:
            pass

    await q.log_action("kick_player", message.author.id, query,
                       {"sessions": len(sessions)})
    await message.channel.send(
        f"Игрок «{query}» принудительно выгнан.\n"
        f"Завершено сессий: {len(sessions)}"
    )


async def cmd_kick_all(bot, message, acc, staff_rank):
    """8 ранг — разлогинивает всех игроков системы."""
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8.")
        return

    # Все активные сессии
    sessions = await pool().fetch(
        "SELECT discord_id, account_id FROM sessions WHERE account_id IS NOT NULL"
    )

    if not sessions:
        await message.channel.send("Нет активных сессий.")
        return

    count = 0
    for s in sessions:
        await q.upsert_session(s["discord_id"], account_id=None)
        await q.set_session_window(s["discord_id"], "A.1.1", None)
        try:
            guild = bot.get_guild(1462104321461063773)
            member = await guild.fetch_member(s["discord_id"]) if guild else None
            if member:
                await member.send(
                    f"⚠ Глобальный сброс сессий C.B.A.\n"
                    f"Все игроки выведены из системы.\n"
                    f"Для входа заново: `!start`"
                )
        except Exception:
            pass
        count += 1

    await q.log_action("kick_all", message.author.id, "all",
                       {"count": count})
    await message.channel.send(
        f"✅ Все сессии сброшены.\n"
        f"Разлогинено: {count}"
    )


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.SES]", SEP, MARK, SEP,
        "Система C.B.A.", "Управление сессиями",
        "1. Выйти из аккаунта (!logout)",
        "2. Принудительно выгнать игрока (7+) !выгнать (позывной)",
        "3. Сбросить все сессии (8) !выгнать всех",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))