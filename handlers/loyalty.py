import json
from db import queries_loyalty as ql
from db import queries as q
from db import queries_stats as qst
from utils import roles as role_utils


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


# Вопросы по уровням
QUESTIONS_BY_LEVEL = {
    1: [
        "Как вы попали в C.B.A.?",
        "Знаете ли вы свой отдел и ранг?",
    ],
    2: [
        "Как вы попали в C.B.A.?",
        "Назовите вашего лидера и заместителя.",
        "Что вы знаете о целях организации?",
    ],
    3: [
        "Как вы попали в C.B.A.?",
        "Назовите вашего лидера и заместителя.",
        "Что вы знаете о целях организации?",
        "Готовы ли вы выполнить приказ, даже если он противоречит вашему мнению?",
        "Есть ли у вас связи с враждебными структурами?",
    ],
}


def _score_answers(answers):
    """Считает баллы лояльности. Пока простая эвристика по длине."""
    score = 0
    for a in answers:
        if not a or len(a.strip()) < 5:
            score += 0
        elif len(a.strip()) < 20:
            score += 10
        elif len(a.strip()) < 60:
            score += 15
        else:
            score += 20
    # Нормализуем к 0-100
    max_score = len(answers) * 20
    if max_score == 0:
        return 0
    return int(score / max_score * 100)


async def show_menu(message, acc, staff_rank):
    lines = [
        SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.10.1]", SEP, MARK, SEP,
        "Система C.B.A.", "Проверка лояльности",
        "1. Начать проверку (6+)" if staff_rank >= 6 else "1. Начать проверку (6+) ❌",
        "2. Вопросы проверки",
        "3. Результат проверки",
        "4. Оспорить результат (7+)" if staff_rank >= 7 else "4. Оспорить результат (7+) ❌",
        "5. Журнал проверок (8)" if staff_rank >= 8 else "5. Журнал проверок (8) ❌",
        "0. Назад", SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def show_start(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.10.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nНачать проверку\n"
        + "!лояльность начать (позывной) (уровень 1-3)\n"
        + "Уровни: 1 — быстрая, 2 — стандартная, 3 — глубокая.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_questions(message, acc, staff_rank):
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.10.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nВопросы проверки\n"
        + "!лояльность вопросы (ID проверки)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_result(message, acc, staff_rank):
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.10.1.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nРезультат проверки\n"
        + "!лояльность результат (ID)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_dispute(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + f"\n{acc['callsign']} (Ранг {acc['rank']}) [A.10.1.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Система C.B.A.\nОспорить результат\n"
        + "!лояльность оспорить (ID) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_journal(message, acc, staff_rank):
    if staff_rank < 8:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 8. [A.ERR] 0 Назад")
        return
    rows = await ql.list_checks(20)
    lines = [SEP, f"{acc['callsign']} (Ранг {acc['rank']}) [A.10.1.5]", SEP, MARK, SEP,
             "Система C.B.A.", "Журнал проверок"]
    if not rows:
        lines.append("(пусто)")
    else:
        for r in rows:
            sc = r["score"] if r["score"] is not None else "—"
            lines.append(
                f"#{r['id']} {r['target_callsign']} — {r['status']} | балл {sc} | {r['verdict'] or '—'}"
            )
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


# ---------- команды ----------
async def cmd_start(bot, message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content[len("!лояльность начать"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!лояльность начать (позывной) (1-3)`")
        return
    callsign = parts[0]
    try:
        level = int(parts[1])
    except ValueError:
        await message.channel.send("Уровень — число 1, 2 или 3.")
        return
    if level not in (1, 2, 3):
        await message.channel.send("Уровень: 1, 2 или 3.")
        return

    target = await qst.get_player_stats(callsign)
    if not target:
        await message.channel.send(f"Аккаунт «{callsign}» не найден.")
        return

    member = await role_utils.find_member_by_callsign(bot, callsign)
    target_discord = member.id if member else None

    questions = QUESTIONS_BY_LEVEL[level]
    check = await ql.insert_check(callsign, target_discord, level,
                                   questions, acc["callsign"], message.author.id)
    await q.log_action("loyalty_start", message.author.id, callsign, {"id": check["id"]})
    await message.channel.send(
        f"Проверка начата. ID: {check['id']}\nЦель: {callsign}\nУровень: {level}\nВопросов: {len(questions)}"
    )

    if member:
        q_text = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
        try:
            await member.send(
                f"**ПРОВЕРКА ЛОЯЛЬНОСТИ (ID {check['id']})**\n"
                f"Отвечайте по порядку через команду:\n"
                f"`!ответ {check['id']} (номер) (текст)`\n\n{q_text}"
            )
        except Exception:
            pass


async def cmd_questions(bot, message, acc, staff_rank):
    parts = message.content[len("!лояльность вопросы"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!лояльность вопросы (ID)`")
        return
    try:
        cid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    row = await ql.get_check(cid)
    if not row:
        await message.channel.send("Проверка не найдена.")
        return
    qs = json.loads(row["questions"]) if row["questions"] else []
    lines = [f"ПРОВЕРКА #{cid} — {row['target_callsign']}", ""]
    for i, qq in enumerate(qs, start=1):
        lines.append(f"{i}. {qq}")
    await message.channel.send("\n".join(lines))


async def cmd_answer(bot, message, acc, staff_rank):
    # !ответ (ID) (номер) (текст)
    parts = message.content[len("!ответ"):].strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.channel.send("Формат: `!ответ (ID) (номер) (текст)`")
        return
    try:
        cid = int(parts[0]); num = int(parts[1])
    except ValueError:
        await message.channel.send("ID и номер — числа.")
        return
    text = parts[2]

    row = await ql.get_check(cid)
    if not row:
        await message.channel.send("Проверка не найдена.")
        return
    if row["status"] == "finished":
        await message.channel.send("Проверка уже завершена.")
        return

    qs = json.loads(row["questions"]) if row["questions"] else []
    if num < 1 or num > len(qs):
        await message.channel.send(f"Номер вопроса от 1 до {len(qs)}.")
        return

    answers = json.loads(row["answers"]) if row["answers"] else []
    while len(answers) < len(qs):
        answers.append("")
    answers[num-1] = text

    filled = sum(1 for a in answers if a)
    if filled < len(qs):
        # обновим частично
        from db.connection import pool
        await pool().execute(
            "UPDATE loyalty_checks SET answers=$1 WHERE id=$2",
            json.dumps(answers), cid
        )
        await message.channel.send(
            f"Ответ на вопрос {num} сохранён. Отвечено: {filled}/{len(qs)}. Продолжайте."
        )
        return

    # Все ответы — считаем результат
    score = _score_answers(answers)
    if score >= 70:
        verdict = "Лоялен"
    elif score >= 40:
        verdict = "Условно лоялен"
    else:
        verdict = "Подозрительно"
    await ql.save_answers(cid, answers, score, verdict)
    await q.log_action("loyalty_finish", message.author.id, str(cid), {"score": score})

    await message.channel.send(
        f"✅ Проверка #{cid} завершена.\nБалл лояльности: {score}/100\nВердикт: {verdict}"
    )

    # уведомить инициатора
    if row["actor_discord"]:
        try:
            guild = bot.get_guild(1462104321461063773)
            m = await guild.fetch_member(row["actor_discord"]) if guild else None
            if m:
                await m.send(f"Проверка #{cid} ({row['target_callsign']}) завершена.\nБалл: {score}/100 | {verdict}")
        except Exception:
            pass


async def cmd_result(bot, message, acc, staff_rank):
    parts = message.content[len("!лояльность результат"):].strip().split()
    if not parts:
        await message.channel.send("Формат: `!лояльность результат (ID)`")
        return
    try:
        cid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    row = await ql.get_check(cid)
    if not row:
        await message.channel.send("Проверка не найдена.")
        return

    answers = json.loads(row["answers"]) if row["answers"] else []
    qs = json.loads(row["questions"]) if row["questions"] else []

    lines = [SEP, f"ПРОВЕРКА #{cid} — {row['target_callsign']}", SEP, MARK, SEP,
             f"Статус: {row['status']}",
             f"Уровень: {row['level']}",
             f"Инициатор: {row['actor_callsign']}",
             ""]
    for i, qq in enumerate(qs):
        a = answers[i] if i < len(answers) else "—"
        lines.append(f"{i+1}. {qq}")
        lines.append(f"   → {a or '—'}")
    lines += [
        "",
        f"Балл: {row['score'] if row['score'] is not None else '—'}/100",
        f"Вердикт: {row['verdict'] or '—'}",
        SEP, MARK, SEP,
    ]
    await message.channel.send("\n".join(lines))


async def cmd_dispute(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content[len("!лояльность оспорить"):].strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.channel.send("Формат: `!лояльность оспорить (ID) (причина)`")
        return
    try:
        cid = int(parts[0])
    except ValueError:
        await message.channel.send("ID — число.")
        return
    reason = parts[1]
    row = await ql.dispute_check(cid, reason)
    if not row:
        await message.channel.send("Проверка не найдена.")
        return
    await q.log_action("loyalty_dispute", message.author.id, str(cid), {"reason": reason})
    await message.channel.send(f"Результат проверки #{cid} оспорен. Причина: {reason}")