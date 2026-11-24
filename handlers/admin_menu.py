from core.codes import parse_duration, now_utc
from db import queries_admin as qa
from db import queries as q
from utils import roles as role_utils


SEP = "-" * 90
MARK = "*C.B.A. Team* Не принадлежит распространению"


async def show_p111(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nЛогирование Нарушений [P.1.1.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Напишите команду:\n"
        + "!лог нарушение (позывной) (тип) (описание) (доказательство)\n"
        + "Типы: устное, предупреждение, выговор, штраф, понижение, перевод, исключение, бан.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p112(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nЛогирование Досье [P.1.1.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Напишите команду:\n"
        + "!лог досье (позывной) (действие) (причина)\n"
        + "Действия: создано, изменено, удалено, просмотрено.\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p113(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nЛогирование Повышений [P.1.1.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Напишите команду:\n"
        + "!повышение (позывной) (с ранга) (на ранг) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p114(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nЛогирование Понижений [P.1.1.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "Напишите команду:\n"
        + "!лог понижение (позывной) (с ранга) (на ранг) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p115(message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
        return
    rows = await qa.list_rank_history(limit=15)
    lines = [SEP, "Глобальное Логирование [P.1.1.5]", SEP, MARK, SEP, "Система C.B.A.",
             "Глобальное Логирование"]
    if not rows:
        lines.append("(записей нет)")
    else:
        for i, r in enumerate(rows, start=1):
            lines.append(f"{i}. {r['target_callsign']} {r['old_rank']}→{r['new_rank']} ({r['reason']}) от {r['actor_callsign']}")
    lines += ["0. Назад", SEP, MARK, SEP]
    await message.channel.send("\n".join(lines))


async def show_p121(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nУстное замечание [P.1.2.1]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "!наказание замечание (позывной) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p122(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nПредупреждение [P.1.2.2]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "!наказание предупреждение (позывной) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p123(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nВыговор [P.1.2.3]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "!наказание выговор (позывной) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p124(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nШтраф [P.1.2.4]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "!наказание штраф (позывной) (сумма) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p125(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nПонижение в ранге [P.1.2.5]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "!наказание понижение (позывной) (на сколько рангов) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p126(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nПеревод в другое подразделение [P.1.2.6]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "!наказание перевод (позывной) (в отдел) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p127(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nИсключение из отдела [P.1.2.7]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "!наказание исключение (позывной) (причина)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def show_p128(message, acc, staff_rank):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
        return
    text = (
        SEP + "\nПерманентный бан [P.1.2.8]\n" + SEP + "\n" + MARK + "\n" + SEP + "\n"
        + "!наказание бан (позывной) (причина) (доказательство)\n"
        + "0. Назад\n" + SEP + "\n" + MARK + "\n" + SEP
    )
    await message.channel.send(text)


async def cmd_log_narushenie(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content.split(maxsplit=4)
    if len(parts) < 4:
        await message.channel.send("Формат: `!лог нарушение (позывной) (тип) (описание) [доказательство]`")
        return
    callsign = parts[2]
    punish_type = parts[3]
    rest = parts[4] if len(parts) > 4 else ""
    description = rest
    evidence = None
    if " http" in rest:
        idx = rest.find(" http")
        description = rest[:idx]
        evidence = rest[idx+1:]

    member = await role_utils.find_member_by_callsign(bot, callsign)
    target_discord = member.id if member else None

    await qa.add_punishment(callsign, target_discord, punish_type,
                            description, message.author.id, acc["callsign"], evidence)
    await q.log_action("log_narushenie", message.author.id, callsign,
                       {"type": punish_type})
    await message.channel.send(f"Нарушение зафиксировано.\nПозывной: {callsign}\nТип: {punish_type}")

    if member:
        try:
            await member.send(f"Вам вынесено: {punish_type}\nПричина: {description}")
        except Exception:
            pass


async def cmd_log_dosie(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content.split(maxsplit=4)
    if len(parts) < 4:
        await message.channel.send("Формат: `!лог досье (позывной) (действие) (причина)`")
        return
    callsign = parts[2]
    action = parts[3]
    reason = parts[4] if len(parts) > 4 else ""
    await q.log_action("log_dosie", message.author.id, callsign,
                       {"action": action, "reason": reason})
    await message.channel.send(f"Действие с досье зафиксировано: {callsign} — {action}")


async def cmd_povyshenie(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content.split(maxsplit=4)
    if len(parts) < 5:
        await message.channel.send("Формат: `!повышение (позывной) (с ранга) (на ранг) (причина)`")
        return
    callsign = parts[1]
    try:
        old_rank = int(parts[2]); new_rank = int(parts[3])
    except ValueError:
        await message.channel.send("Ранги — числа.")
        return
    reason = parts[4]

    if new_rank > staff_rank:
        await message.channel.send("Нельзя повысить выше своего ранга.")
        return
    if new_rank < 1 or new_rank > 8:
        await message.channel.send("Ранг 1–8.")
        return

    target_acc = await qa.get_account_by_callsign(callsign)
    if not target_acc:
        await message.channel.send(f"Аккаунт с позывным «{callsign}» не найден.")
        return

    member = await role_utils.find_member_by_callsign(bot, callsign)
    discord_id = member.id if member else None

    await qa.update_account_rank_by_callsign(callsign, new_rank)

    if member:
        ok, err = await role_utils.set_rank_role(bot, member.id, old_rank, new_rank)
        if not ok:
            await message.channel.send(f"Ранг в БД изменён, но роль Discord не обновлена: {err}")

    await qa.add_rank_history(callsign, discord_id, old_rank, new_rank, reason, acc["callsign"])
    await q.log_action("povyshenie", message.author.id, callsign,
                       {"old": old_rank, "new": new_rank, "reason": reason})
    await message.channel.send(f"Повышение зафиксировано: {callsign} — {old_rank} → {new_rank}")

    if member:
        try:
            await member.send(f"Вас повысили: {old_rank} → {new_rank}\nПричина: {reason}")
        except Exception:
            pass


async def cmd_ponizhenie(bot, message, acc, staff_rank):
    if staff_rank < 7:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+.")
        return
    parts = message.content.split(maxsplit=4)
    if len(parts) < 5:
        await message.channel.send("Формат: `!лог понижение (позывной) (с ранга) (на ранг) (причина)`")
        return
    callsign = parts[2]
    try:
        old_rank = int(parts[3]); new_rank = int(parts[4].split()[0])
    except (ValueError, IndexError):
        await message.channel.send("Ранги — числа.")
        return
    reason = " ".join(parts[4].split()[1:]) if len(parts[4].split()) > 1 else ""

    if new_rank < 1:
        new_rank = 1

    target_acc = await qa.get_account_by_callsign(callsign)
    if not target_acc:
        await message.channel.send(f"Аккаунт с позывным «{callsign}» не найден.")
        return

    member = await role_utils.find_member_by_callsign(bot, callsign)
    discord_id = member.id if member else None

    await qa.update_account_rank_by_callsign(callsign, new_rank)
    if member:
        await role_utils.set_rank_role(bot, member.id, old_rank, new_rank)

    await qa.add_rank_history(callsign, discord_id, old_rank, new_rank, reason, acc["callsign"])
    await q.log_action("ponizhenie", message.author.id, callsign,
                       {"old": old_rank, "new": new_rank, "reason": reason})
    await message.channel.send(f"Понижение зафиксировано: {callsign} — {old_rank} → {new_rank}")


async def _do_punish(bot, message, acc, staff_rank, punish_type):
    if staff_rank < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content.split(maxsplit=4)
    if len(parts) < 4:
        await message.channel.send("Формат: `!наказание (тип) (позывной) (...)`")
        return

    callsign = parts[2]
    reason = parts[3]
    if len(parts) > 4:
        reason = parts[3] + " " + parts[4]

    member = await role_utils.find_member_by_callsign(bot, callsign)
    discord_id = member.id if member else None

    await qa.add_punishment(callsign, discord_id, punish_type, reason,
                            message.author.id, acc["callsign"])
    await q.log_action(f"punish_{punish_type}", message.author.id, callsign, {"reason": reason})
    await message.channel.send(f"Наказание «{punish_type}» выдано: {callsign}")

    if member:
        try:
            await member.send(f"Вам выдано наказание: {punish_type}\nПричина: {reason}")
        except Exception:
            pass

    if punish_type == "предупреждение":
        cnt = await qa.count_active_warnings(callsign)
        if cnt >= 3:
            await qa.add_punishment(callsign, discord_id, "выговор",
                                    "Автоматически: 3 предупреждения",
                                    message.author.id, "СИСТЕМА")
            await message.channel.send(f"⚠ Авто: {callsign} получил выговор за 3 предупреждения.")
    elif punish_type == "выговор":
        cnt = await qa.count_active_rebukes(callsign)
        if cnt >= 3:
            await message.channel.send(f"⚠ У {callsign} 3 выговора. Рекомендуется понижение.")


async def cmd_zamechanie(bot, message, acc, sr):
    await _do_punish(bot, message, acc, sr, "устное")


async def cmd_preduprezhdenie(bot, message, acc, sr):
    await _do_punish(bot, message, acc, sr, "предупреждение")


async def cmd_vygovor(bot, message, acc, sr):
    await _do_punish(bot, message, acc, sr, "выговор")


async def cmd_shtraf(bot, message, acc, sr):
    await _do_punish(bot, message, acc, sr, "штраф")


async def cmd_ponizhenie_nakazanie(bot, message, acc, sr):
    await _do_punish(bot, message, acc, sr, "понижение")


async def cmd_perevod(bot, message, acc, sr):
    await _do_punish(bot, message, acc, sr, "перевод")


async def cmd_isklyuchenie(bot, message, acc, sr):
    await _do_punish(bot, message, acc, sr, "исключение")


async def cmd_ban(bot, message, acc, sr):
    if sr < 6:
        await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+.")
        return
    parts = message.content.split(maxsplit=4)
    if len(parts) < 4:
        await message.channel.send("Формат: `!наказание бан (позывной) (причина) (доказательство)`")
        return
    callsign = parts[2]
    reason = parts[3]
    evidence = parts[4] if len(parts) > 4 else None

    await qa.add_punishment(callsign, None, "бан", reason,
                            message.author.id, acc["callsign"], evidence)
    await qa.block_account_by_callsign(callsign, reason)
    await q.log_action("punish_ban", message.author.id, callsign, {"reason": reason})
    await message.channel.send(f"Аккаунт «{callsign}» забанен. Причина: {reason}")

    member = await role_utils.find_member_by_callsign(bot, callsign)
    if member:
        try:
            await member.send(f"Вы забанены в C.B.A.\nПричина: {reason}")
        except Exception:
            pass