from db import queries_global as qg
from db import queries as q
from utils import discord_scan as scanner


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.8.1.5]", SEP, MARK, SEP,
        "Система C.B.A.", "Глобальное досье (Discord-сканирование)",
        "1. Сканировать игрока (5+)" if staff_rank >= 5 else "1. Сканировать игрока (5+) ❌",
        "2. Список опасных (6+)" if staff_rank >= 6 else "2. Список опасных (6+) ❌",
        "3. Открыть досье по Discord ID",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_scan(message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.8.1.5.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nСканировать игрока Discord\n"
        + "!скан (username или @ник или ID)\n"
        + "Пример: !скан romaksentigmr\n"
        + "Бот просканирует сообщения, роли, активность.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_dangerous(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    rows = await qg.list_global_dossiers(30)
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.8.1.5.2]", SEP, MARK, SEP,
             "Система C.B.A.", "Глобальный список (по уровню опасности)", ""]
    if not rows:
        lines.append("(пусто)")
    else:
        for i, r in enumerate(rows[:15], start=1):
            lines.append(
                f"{i}. {r['username']} — опасность {r['danger_level']}/100, "
                f"агрессия {r['aggressive_score']}, лояльность {r['loyalty_score']}"
            )
    lines += ["", "0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_by_id(message, acc, staff_rank):
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.8.1.5.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nОткрыть глобальное досье\n"
        + "!гдосье (Discord ID или username)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def cmd_scan(bot, message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+.")
        return

    parts = message.content[len("!скан"):].strip().split(maxsplit=1)
    if not parts:
        await message.channel.send("Формат: `!скан (username)`")
        return
    query = parts[0]

    guild = bot.get_guild(1462104321461063773)
    if not guild:
        await message.channel.send("Бот не на целевом сервере.")
        return

    member = await scanner.find_member(bot, query)
    if not member:
        await message.channel.send(f"Игрок «{query}» не найден на сервере.")
        return

    await message.channel.send(f"🔍 Сканирую {member.display_name}... Это может занять до 30 секунд.")

    # Собираем сообщения
    messages, channels_scanned = await scanner.scan_messages(guild, member,
                                                             channel_limit=10,
                                                             msg_per_channel=200)

    # Анализ
    metrics = scanner.analyze_behavior(messages)

    # Проверяем высокие роли (Staff или лидер отдела)
    high_roles = False
    for r in member.roles:
        name = r.name.lower()
        if any(x in name for x in ["leader", "директор", "заместитель",
                                     "high", "следящий", "старший"]):
            high_roles = True
            break

    scores = scanner.compute_scores(metrics, member, high_roles)
    strengths, weaknesses = scanner.build_report(metrics, scores)

    # Сохраняем в БД
    await qg.upsert_global_dossier({
        "discord_id": member.id,
        "username": member.name,
        "display_name": member.display_name,
        "joined_at": member.joined_at,
        "account_created": member.created_at,
        "roles": ", ".join(r.name for r in member.roles if r.name != "@everyone"),
        "message_count": metrics["message_count"],
        "channels_scanned": channels_scanned,
        "avg_msg_length": metrics["avg_msg_length"],
        "caps_ratio": metrics["caps_ratio"],
        "exclaim_count": metrics["exclaim_count"],
        "swear_count": metrics["swear_count"],
        "night_activity": metrics["night_activity"],
        "day_activity": metrics["day_activity"],
        "aggressive_score": scores["aggressive_score"],
        "loyalty_score": scores["loyalty_score"],
        "activity_score": scores["activity_score"],
        "danger_level": scores["danger_level"],
        "strengths": strengths,
        "weaknesses": weaknesses,
        "notes": None,
        "scanned_by": acc["callsign"],
    })

    await q.log_action("global_scan", message.author.id, member.name,
                       {"danger": scores["danger_level"]})

    # Формируем отчёт
    lines = [
        SEP, f"ДОСЬЕ: {member.display_name}", SEP, MARK, SEP,
        f"Username: {member.name}",
        f"ID: {member.id}",
        f"Аккаунт создан: {member.created_at.strftime('%Y-%m-%d')}",
        f"Вход на сервер: {member.joined_at.strftime('%Y-%m-%d') if member.joined_at else '—'}",
        f"Роли: {', '.join(r.name for r in member.roles if r.name != '@everyone') or '—'}",
        "",
        "=== АКТИВНОСТЬ ===",
        f"Сообщений просканировано: {metrics['message_count']}",
        f"Каналов: {channels_scanned}",
        f"Средняя длина: {metrics['avg_msg_length']} симв.",
        f"Активность днём: {metrics['day_activity']} | Ночью: {metrics['night_activity']}",
        f"Мат: {metrics['swear_count']} | Капс: {int(metrics['caps_ratio']*100)}% | Восклицания: {metrics['exclaim_count']}",
        "",
        "=== ОЦЕНКИ (0-100) ===",
        f"⚠ Агрессия:     {scores['aggressive_score']}",
        f"✅ Лояльность:  {scores['loyalty_score']}",
        f"📊 Активность:  {scores['activity_score']}",
        f"🚨 Опасность:   {scores['danger_level']}",
        "",
        "=== СИЛЬНЫЕ СТОРОНЫ ===",
        strengths,
        "",
        "=== СЛАБЫЕ СТОРОНЫ ===",
        weaknesses,
        SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def cmd_view(bot, message, acc, staff_rank):
    parts = message.content[len("!гдосье"):].strip().split(maxsplit=1)
    if not parts:
        await message.channel.send("Формат: `!гдосье (username или ID)`")
        return
    query = parts[0]

    if query.isdigit():
        row = await qg.get_global_dossier(int(query))
    else:
        member = await scanner.find_member(bot, query)
        if not member:
            await message.channel.send("Игрок не найден.")
            return
        row = await qg.get_global_dossier(member.id)

    if not row:
        await message.channel.send("Досье не найдено. Сначала просканируйте: `!скан (username)`")
        return

    lines = [
        SEP, f"ДОСЬЕ (сохранённое): {row['display_name']}", SEP, MARK, SEP,
        f"Username: {row['username']}",
        f"ID: {row['discord_id']}",
        f"Роли: {row['roles'] or '—'}",
        f"Сканирован: {row['scanned_at'].strftime('%Y-%m-%d %H:%M')} (от {row['scanned_by']})",
        "",
        f"Сообщений: {row['message_count']}",
        f"Активность днём/ночью: {row['day_activity']} / {row['night_activity']}",
        f"Мат: {row['swear_count']} | Капс: {int(row['caps_ratio']*100)}%",
        "",
        f"⚠ Агрессия:     {row['aggressive_score']}",
        f"✅ Лояльность:  {row['loyalty_score']}",
        f"📊 Активность:  {row['activity_score']}",
        f"🚨 Опасность:   {row['danger_level']}",
        "",
        f"Сильные: {row['strengths']}",
        f"Слабые: {row['weaknesses']}",
        SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))