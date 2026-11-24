from db import queries_forecasts as qf
from db import queries_stats as qst
from db import queries as q


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


def _predict(stats):
    p = stats["punish"]
    warnings = p.get("предупреждение", 0)
    rebukes = p.get("выговор", 0)
    demotions = p.get("понижение", 0)
    overdue = stats["tasks_overdue"]
    rejected = stats["reports_no"]
    promote = stats["promote"]
    done = stats["tasks_done"]

    demote_risk = min(100, warnings * 8 + rebukes * 20 + overdue * 15 + demotions * 10)
    promote_chance = max(0, min(100, done * 15 + promote * 10 + stats["reports_ok"] * 5
                                 - warnings * 5 - rebukes * 15 - overdue * 10))
    kick_risk = min(100, rebukes * 25 + demotions * 15 + rejected * 10)
    return demote_risk, promote_chance, kick_risk


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.9.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Прогнозы",
        "1. Прогноз на игрока (6+)" if staff_rank >= 6 else "1. Прогноз на игрока (6+) ❌",
        "2. Прогноз по отделу (5+)" if staff_rank >= 5 else "2. Прогноз по отделу (5+) ❌",
        "3. Прогноз угроз (7+)" if staff_rank >= 7 else "3. Прогноз угроз (7+) ❌",
        "4. Архив прогнозов (7+)" if staff_rank >= 7 else "4. Архив прогнозов (7+) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_create(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.9.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nАвтоматический прогноз на игрока\n"
        + "!прогноз игрок (позывной)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_dept(message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.9.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nПрогноз по отделу\n"
        + "!прогноз отдел (Отдел)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_threat(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.9.1.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nПрогноз угроз\n"
        + "!прогноз угрозы (уровень) (текст)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_archive(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    rows = await qf.list_forecasts(20)
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.9.1.4]", SEP, MARK, SEP,
             "Система C.B.A.", "Архив прогнозов"]
    if not rows:
        lines.append("(нет сохранённых прогнозов)")
    else:
        for i, r in enumerate(rows, start=1):
            tgt = r["target"] or "—"
            prob = f"{r['probability']}%" if r["probability"] is not None else "—"
            lines.append(f"{i}. [{r['forecast_type']}] {tgt} — {r['scenario'][:50]} ({prob})")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def cmd_player(bot, message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content[len("!прогноз игрок"):].strip().split(maxsplit=1)
    if not parts:
        await message.channel.send("Формат: `!прогноз игрок (позывной)`")
        return
    callsign = parts[0]
    st = await qst.get_player_stats(callsign)
    if not st:
        await message.channel.send("Игрок не найден.")
        return

    demote, promote, kick = _predict(st)
    lines = [
        SEP, f"ПРОГНОЗ НА ИГРОКА: {callsign}", SEP, MARK, SEP,
        f"Текущий ранг: {st['account']['rank']}",
        "",
        f"📉 Вероятность понижения:  {demote}%",
        f"📈 Вероятность повышения: {promote}%",
        f"🚪 Вероятность исключения: {kick}%",
        "",
        "Прогноз рассчитан автоматически по:",
        "— наказаниям (варны, выговоры, штрафы)",
        "— просроченным задачам",
        "— отклонённым донесениям",
        "— истории повышений",
        SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))
    await q.log_action("forecast_player", message.author.id, callsign,
                       {"demote": demote, "promote": promote, "kick": kick})


async def cmd_dept(bot, message, acc, staff_rank):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+.")
        return
    parts = message.content[len("!прогноз отдел"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!прогноз отдел (Отдел)`")
        return
    dept = parts[0].upper()
    s = await qst.get_department_stats(dept)

    risk = min(100, s["punish_total"] * 5)
    activity = min(100, (s["active_orders"] + s["active_tasks"]) * 10)
    stability = max(0, 100 - risk)

    lines = [
        SEP, f"ПРОГНОЗ ПО ОТДЕЛУ: {dept}", SEP, MARK, SEP,
        f"Участников: {s['members']}",
        f"Средний ранг: {s['avg_rank']}",
        f"Наказаний: {s['punish_total']}",
        f"Активных приказов: {s['active_orders']}",
        f"Активных задач: {s['active_tasks']}",
        "",
        f"📊 Активность: {activity}/100",
        f"⚠ Риск: {risk}/100",
        f"🛡 Стабильность: {stability}/100",
        SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def cmd_threat(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content[len("!прогноз угрозы"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!прогноз угрозы (уровень) (текст)`")
        return
    level, text = parts
    f = await qf.insert_forecast("threat", level, text, None, None, None,
                                 acc["callsign"], message.author.id)
    await q.log_action("forecast_threat", message.author.id, level, {"id": f["id"]})
    await message.channel.send(f"Прогноз угроз создан. ID: {f['id']}\nУровень: {level}")