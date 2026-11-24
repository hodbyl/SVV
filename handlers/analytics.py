from db import queries_analytics as qa
from db import queries_stats as qst
from db import queries as q
from utils import roles as role_utils


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


def _risk_score(stats):
    p = stats["punish"]
    warnings = p.get("предупреждение", 0)
    rebukes = p.get("выговор", 0)
    fines = p.get("штраф", 0)
    demotions = p.get("понижение", 0)
    bans = p.get("бан", 0)
    overdue = stats["tasks_overdue"]
    rejected = stats["reports_no"]
    promote = stats["promote"]

    score = (warnings * 5 + rebukes * 15 + fines * 3 + demotions * 20
             + bans * 50 + overdue * 10 + rejected * 5 - promote * 3)
    return max(0, min(100, int(score)))


def _risk_label(score):
    if score < 10: return "🟢 Низкий"
    if score < 30: return "🟡 Умеренный"
    if score < 60: return "🟠 Повышенный"
    if score < 85: return "🔴 Высокий"
    return "⛔ Критический"


def _behavior_report(stats):
    lines = []
    p = stats["punish"]
    if p:
        lines.append("Наказания:")
        for k, v in p.items():
            lines.append(f"  • {k}: {v}")
    else:
        lines.append("Наказания: нет")

    if stats["tasks_done"] or stats["tasks_overdue"]:
        lines.append(f"Задачи: выполнено {stats['tasks_done']}, просрочено {stats['tasks_overdue']}")
    if stats["reports_sent"]:
        lines.append(f"Донесения: {stats['reports_sent']} (принято {stats['reports_ok']}, отклонено {stats['reports_no']})")
    if stats["promote"] or stats["demote"]:
        lines.append(f"Изменения ранга: +{stats['promote']} / -{stats['demote']}")
    return "\n".join(lines)


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.8.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Аналитика",
        "1. Запросить анализ игрока (4+)",
        "2. Активность отделов (5+)" if staff_rank >= 5 else "2. Активность отделов (5+) ❌",
        "3. Подозрительные действия (6+)" if staff_rank >= 6 else "3. Подозрительные действия (6+) ❌",
        "4. Общий отчёт системы",
        "5. Глобальное досье Discord (5+)",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_request(message, acc, staff_rank):
    if staff_rank < 4:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 4+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.8.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nАвтоматический анализ игрока\n"
        + "!аналитика игрок (позывной)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_activity(message, acc, staff_rank, bot=None):
    if staff_rank < 5:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 5+. [A.ERR] 0 Назад")
        return

    depts = ["FUR", "DEF", "SUW", "TOJ", "SRT", "CHT", "KOS"]
    lines = [
        SEP,
        f"{acc['callsign']} (Ранг {acc['rank']}) [A.8.1.2]",
        SEP, MARK, SEP,
        "Система C.B.A.",
        "Активность отделов (Discord-роли)",
        "",
    ]

    total_all = 0
    for d in depts:
        ds = await role_utils.get_department_stats_from_discord(bot, d)
        db_stats = await qst.get_department_stats(d)
        total_all += ds["members"]
        lines.append(
            f"• {d}: всего {ds['members']} | "
            f"лидер {ds['leaders']} / high {ds['high']} / состав {ds['regular']} | "
            f"наказаний {db_stats['punish_total']} | задач {db_stats['active_tasks']}"
        )

    lines.append("")
    lines.append(f"Всего по всем отделам: {total_all} чел.")
    lines += ["", "0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_suspicious(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    from db.connection import pool
    dossiers = await pool().fetch("SELECT callsign FROM dossiers")
    if not dossiers:
        await message.channel.send("Досье пусты — нечего анализировать.")
        return

    risky = []
    for d in dossiers:
        st = await qst.get_player_stats(d["callsign"])
        if not st: continue
        score = _risk_score(st)
        if score >= 30:
            risky.append((d["callsign"], score, st))

    risky.sort(key=lambda x: -x[1])
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.8.1.3]", SEP, MARK, SEP,
             "Система C.B.A.", "Подозрительные действия (автоматически)", ""]
    if not risky:
        lines.append("Подозрительных игроков не обнаружено.")
    else:
        for cs, sc, st in risky[:10]:
            lines.append(f"• {cs} — риск {sc}/100 ({_risk_label(sc)})")

    lines += ["", "0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_report(message, acc, staff_rank):
    s = await qst.get_overall_stats()
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.8.1.4]", SEP, MARK, SEP,
        "Система C.B.A.", "Общий отчёт системы", "",
        f"Всего аккаунтов: {s['accounts']}",
        f"Заблокировано: {s['blocked']}",
        f"Активных приказов: {s['orders_active']}",
        f"Активных задач: {s['tasks_active']}",
        f"Активных наказаний: {s['punish_active']}",
        f"Досье в базе: {s['dossiers']}",
        "",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def cmd_request(bot, message, acc, staff_rank):
    if staff_rank < 4:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 4+.")
        return
    parts = message.content[len("!аналитика игрок"):].strip().split(maxsplit=1)
    if not parts:
        await message.channel.send("Формат: `!аналитика игрок (позывной)`")
        return
    callsign = parts[0]
    st = await qst.get_player_stats(callsign)
    if not st:
        await message.channel.send("Игрок не найден.")
        return

    score = _risk_score(st)
    lines = [
        SEP, f"АНАЛИТИКА ПО ИГРОКУ: {callsign}", SEP, MARK, SEP,
        f"Ранг: {st['account']['rank']}",
        f"Статус: {'🚫 ЗАБЛОКИРОВАН' if st['account']['is_blocked'] else '✅ Активен'}",
        "",
        _behavior_report(st),
        "",
        f"Оценка риска: {score}/100 — {_risk_label(score)}",
        SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))
    await q.log_action("analytics_player", message.author.id, callsign, {"score": score})