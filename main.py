import asyncio
import discord
from discord.ext import commands
bot.run('YOUR_TOKEN')

from config import (
    TOKEN, MIN_RANK_CREATE_ACCOUNT, MIN_RANK_CREATE_UNBAN,
    MAX_WRONG_ATTEMPTS, MIN_RANK_ADMIN_MENU
)
from db.connection import init_pool, close_pool
from db import queries as q
from db import queries_protocol as qp
from core.access import get_staff_rank, fetch_guild_member
from core.codes import (
    is_valid_account_code, is_valid_unban_code,
    parse_duration, now_utc
)
from utils import render
from handlers import reports_out as reports_out_handler
from handlers import orders as orders_handler
from handlers import admin_menu as admin
from handlers import protocol as protocol_handler
from handlers import tasks as tasks_handler
from handlers import reports as reports_handler
from handlers import specops as specops_handler
from handlers import surveillance as surv_handler
from handlers import dossier as dossier_handler
from handlers import analytics as analytics_handler
from handlers import forecasts as forecasts_handler
from handlers import global_dossier as gdossier_handler
from handlers import loyalty as loyalty_handler
from handlers import liquidation as liquidation_handler
from handlers import sessions as sessions_handler
from handlers import deactivation as deact_handler
from handlers import archive as archive_handler
from handlers import codenames as codenames_handler
from handlers import ciphers as ciphers_handler
from handlers import locus as locus_ui
from db import queries_locus as ql
import json

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    await init_pool()
    print(f"Бот запущен: {bot.user} ({bot.user.id})")


async def _ctx(uid):
    sess = await q.get_session(uid)
    acc = None
    if sess and sess["account_id"]:
        acc = await q.get_account_by_id(sess["account_id"])
    member = await fetch_guild_member(bot, uid)
    sr = get_staff_rank(member)
    return sess, acc, sr


async def _send_main_menu(message, acc, staff_rank):
    p = await qp.get_active_protocol()
    await message.channel.send(render.window_a12(acc, staff_rank, p))


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if not isinstance(message.channel, discord.DMChannel):
        return

    text = message.content.strip()
    uid = message.author.id

    if text.lower() == "!kosmenu":
        await ql.create_locus_session(uid)
        await ql.set_locus_window(uid, "RZ.1.1", {})
        await message.channel.send(locus_ui.rz_11())
        return

    if text.lower() == "!start":
        await q.upsert_session(uid)
        # ... дальше твой код ...
    # === БАЗОВЫЕ КОМАНДЫ ===
    if text.lower() == "!start":
        await q.upsert_session(uid)
        await q.set_session_window(uid, "A.1.1", None)
        await message.channel.send(render.window_a11())
        return

    if text.startswith("!k КодАккаунт"):
        await handle_create_account_code(message)
        return

    if text.startswith("!K разбанкод"):
        await handle_create_unban_code(message)
        return

    # === ПРИКАЗЫ ===
    if text.startswith("!дать приказ"):
        sess, acc, sr = await _ctx(uid)
        if not acc:
            await message.channel.send("Сначала войдите: `!start`")
            return
        await orders_handler.handle_create_order(bot, message, acc, sr)
        return

    if text.startswith("!удалить приказ"):
        sess, acc, sr = await _ctx(uid)
        if not acc:
            await message.channel.send("Сначала войдите: `!start`")
            return
        await orders_handler.handle_delete_order(message, acc, sr)
        return

    # === ADMIN: ЛОГИ ===
    if text.startswith("!лог нарушение"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_log_narushenie(bot, message, acc, sr)
        return

    if text.startswith("!лог досье"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_log_dosie(bot, message, acc, sr)
        return

    if text.startswith("!повышение"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_povyshenie(bot, message, acc, sr)
        return

    if text.startswith("!лог понижение"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_ponizhenie(bot, message, acc, sr)
        return

    # === ADMIN: НАКАЗАНИЯ ===
    if text.startswith("!наказание замечание"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_zamechanie(bot, message, acc, sr)
        return

    if text.startswith("!наказание предупреждение"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_preduprezhdenie(bot, message, acc, sr)
        return

    if text.startswith("!наказание выговор"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_vygovor(bot, message, acc, sr)
        return

    if text.startswith("!наказание штраф"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_shtraf(bot, message, acc, sr)
        return

    if text.startswith("!наказание понижение"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_ponizhenie_nakazanie(bot, message, acc, sr)
        return

    if text.startswith("!наказание перевод"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_perevod(bot, message, acc, sr)
        return

    if text.startswith("!наказание исключение"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_isklyuchenie(bot, message, acc, sr)
        return

    if text.startswith("!наказание бан"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await admin.cmd_ban(bot, message, acc, sr)
        return

    # === ПРОТОКОЛ ===
    if text.startswith("!экстренный протокол отмена"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await protocol_handler.cmd_cancel(bot, message, acc, sr)
        return

    if text.startswith("!экстренный протокол"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await protocol_handler.cmd_announce(bot, message, acc, sr)
        return

    # === ЗАДАЧИ ===
    if text.startswith("!задача создать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await tasks_handler.cmd_create(bot, message, acc, sr)
        return

    if text.startswith("!задача отдел"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await tasks_handler.cmd_dept(bot, message, acc, sr)
        return

    if text.startswith("!задача закрыть"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await tasks_handler.cmd_close(bot, message, acc, sr)
        return

    # === ДОНЕСЕНИЯ ===
    if text.startswith("!донесение проверить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await reports_handler.cmd_review(bot, message, acc, sr)
        return

    if text.startswith("!донесение"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await reports_handler.cmd_send(bot, message, acc, sr)
        return

    # === СПЕЦОПЕРАЦИИ ===
    if text.startswith("!спецоперация создать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await specops_handler.cmd_create(bot, message, acc, sr)
        return

    if text.startswith("!спецоперация назначить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await specops_handler.cmd_assign(bot, message, acc, sr)
        return

    if text.startswith("!спецоперация статус"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await specops_handler.cmd_status(bot, message, acc, sr)
        return

    if text.startswith("!спецоперация отчёт"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await specops_handler.cmd_report(bot, message, acc, sr)
        return

    if text.startswith("!спецоперация отмена"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await specops_handler.cmd_cancel(bot, message, acc, sr)
        return

    # === СЛЕЖКА ===
    if text.startswith("!слежка начать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await surv_handler.cmd_start(bot, message, acc, sr)
        return

    if text.startswith("!слежка отчёт"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await surv_handler.cmd_report(bot, message, acc, sr)
        return

    if text.startswith("!слежка стоп"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await surv_handler.cmd_stop(bot, message, acc, sr)
        return

    # === ДОСЬЕ ===
    if text.startswith("!досье создать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await dossier_handler.cmd_create(bot, message, acc, sr)
        return

    if text.startswith("!досье edit"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await dossier_handler.cmd_edit(bot, message, acc, sr)
        return

    if text.startswith("!досье view"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await dossier_handler.cmd_view(bot, message, acc, sr)
        return

    if text.startswith("!досье удалить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await dossier_handler.cmd_delete(bot, message, acc, sr)
        return

    if text.startswith("!досье поиск"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await dossier_handler.cmd_search(bot, message, acc, sr)
        return


    # === АНАЛИТИКА ===
    if text.startswith("!аналитика игрок"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await analytics_handler.cmd_request(bot, message, acc, sr)
        return

    if text.startswith("!аналитика отделы"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await analytics_handler.show_activity(message, acc, sr)
        return

    if text.startswith("!аналитика подозрения"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await analytics_handler.show_suspicious(message, acc, sr)
        return

    # === ПРОГНОЗЫ ===
    if text.startswith("!прогноз игрок"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await forecasts_handler.cmd_player(bot, message, acc, sr)
        return

    if text.startswith("!прогноз отдел"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await forecasts_handler.cmd_dept(bot, message, acc, sr)
        return

    if text.startswith("!прогноз угрозы"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await forecasts_handler.cmd_threat(bot, message, acc, sr)
        return

            # === ГЛОБАЛЬНОЕ ДОСЬЕ ===
    if text.startswith("!скан"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await gdossier_handler.cmd_scan(bot, message, acc, sr)
        return

    if text.startswith("!гдосье"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await gdossier_handler.cmd_view(bot, message, acc, sr)
        return

    # === ОТЧЁТЫ ===
    if text.startswith("!отчёт создать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await reports_out_handler.cmd_create(bot, message, acc, sr)
        return

    if text.startswith("!отчёт отправить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await reports_out_handler.cmd_send(bot, message, acc, sr)
        return

    if text.startswith("!отчёт проверить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await reports_out_handler.cmd_review(bot, message, acc, sr)
        return

    # === АРХИВ ===
    if text.startswith("!архив поиск"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await archive_handler.cmd_search(bot, message, acc, sr)
        return

    if text.startswith("!архив добавить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await archive_handler.cmd_add(bot, message, acc, sr)
        return

    if text.startswith("!архив извлечь"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await archive_handler.cmd_extract(bot, message, acc, sr)
        return

    if text.startswith("!архив удалить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await archive_handler.cmd_delete(bot, message, acc, sr)
        return


    # === ДЕАКТИВАЦИЯ ===
    if text.startswith("!деактивировать"):
        print(f"DEBUG: Бот поймал команду от {message.author}")  # <--- ДОБАВЬ ЭТУ СТРОКУ
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await deact_handler.cmd_deactivate(bot, message, acc, sr)
        return

    if text.startswith("!деактивировать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await deact_handler.cmd_deactivate(bot, message, acc, sr)
        return

    if text.startswith("!активировать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await deact_handler.cmd_activate(bot, message, acc, sr)
        return

    if text.startswith("!восстановить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await deact_handler.cmd_restore(bot, message, acc, sr)
        return

    # === КОДОВЫЕ ИМЕНА ===
    if text.startswith("!кодовоеимя создать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await codenames_handler.cmd_create(bot, message, acc, sr)
        return

    if text.startswith("!кодовоеимя изменить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await codenames_handler.cmd_change(bot, message, acc, sr)
        return

    if text.startswith("!кодовоеимя удалить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await codenames_handler.cmd_delete(bot, message, acc, sr)
        return

    # === ШИФРЫ ===
    if text.startswith("!шифр создать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await ciphers_handler.cmd_create(bot, message, acc, sr)
        return

    if text.startswith("!шифр расшифровать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await ciphers_handler.cmd_decrypt(bot, message, acc, sr)
        return

    if text.startswith("!шифр удалить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await ciphers_handler.cmd_delete(bot, message, acc, sr)
        return

    # === НАВИГАЦИЯ ЦИФРАМИ ===
    # === L.O.C.U.S. СИСТЕМА (ГЛАВНЫЙ ПРИОРИТЕТ) ===
    locus_sess = await ql.get_locus_session(uid)
    if locus_sess:
        win = locus_sess['current_window']
                if win == "LOGOUT":
            await message.channel.send("Вы уже вышли из системы L.O.C.U.S. Напишите `!Kosmenu` для входа.")
            return
        if win == "RZ.1.1":
            if text == "1":
                await ql.set_locus_window(uid, "RZ.1.2.1", {})
                await message.channel.send(locus_ui.rz_121({}))
                return
            elif text == "2":
                await ql.set_locus_window(uid, "RZ.1.3", {})
                await message.channel.send(locus_ui.rz_13())
                return
            elif text == "3":
                await message.channel.send("Тех. поддержка: Discord -> nob_fa")
                return
            elif text == "4":
                await message.channel.send("Спец-код пока в разработке.")
                return
            elif text == "0":
                await ql.set_locus_window(uid, "A.1.1", {})
                await message.channel.send("Вы вышли из системы L.O.C.U.S.")
                return
                
        if win.startswith("RZ.1.2."):
            await locus_ui.handle_registration(message, locus_sess, text)
            return
            
        if win.startswith("RZ.1.3"):
            await locus_ui.handle_login(message, locus_sess, text)
            return

        if win == "RZ.1.6":
            user = await ql.get_locus_user_by_id(uid)
            if text == "0":
                await ql.set_locus_window(uid, "A.1.1", {})
                await message.channel.send("Вы вышли из системы L.O.C.U.S.")
                return
            elif text == "1":
                await ql.set_locus_window(uid, "RZ.2.1", {})
                await message.channel.send(locus_ui.rz_21(user))
                return
            else:
                await message.channel.send("Этот раздел пока в разработке.")
                return

        if win.startswith("RZ.2.1"):
            await locus_ui.handle_economy(message, locus_sess, text)
            return

    # === C.B.A. СИСТЕМА (ЦИФРЫ) ===
    if text.isdigit():
        await handle_navigation(message, int(text))
        return

    # === ЛОЯЛЬНОСТЬ ===
    if text.startswith("!лояльность начать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await loyalty_handler.cmd_start(bot, message, acc, sr)
        return

    if text.startswith("!лояльность вопросы"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await loyalty_handler.cmd_questions(bot, message, acc, sr)
        return

    if text.startswith("!лояльность результат"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await loyalty_handler.cmd_result(bot, message, acc, sr)
        return

    if text.startswith("!лояльность оспорить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await loyalty_handler.cmd_dispute(bot, message, acc, sr)
        return

    if text.startswith("!ответ"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await loyalty_handler.cmd_answer(bot, message, acc, sr)
        return

    # === ЛИКВИДАЦИЯ ===
    if text.startswith("!ликвидация создать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await liquidation_handler.cmd_create(bot, message, acc, sr)
        return

    if text.startswith("!ликвидация подтвердить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await liquidation_handler.cmd_confirm(bot, message, acc, sr)
        return

    if text.startswith("!ликвидация назначить"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await liquidation_handler.cmd_assign(bot, message, acc, sr)
        return

    if text.startswith("!ликвидация готово"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await liquidation_handler.cmd_done(bot, message, acc, sr)
        return

    # === СЕССИИ ===
    if text.startswith("!logout"):
        sess, acc, sr = await _ctx(uid)
        await sessions_handler.cmd_logout(bot, message, acc, sr)
        return

    if text.startswith("!выгнать всех"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await sessions_handler.cmd_kick_all(bot, message, acc, sr)
        return

    if text.startswith("!выгнать"):
        sess, acc, sr = await _ctx(uid)
        if not acc: return
        await sessions_handler.cmd_kick(bot, message, acc, sr)
        return
    # === НАВИГАЦИЯ ЦИФРАМИ ===

        # === МАШИНА СОСТОЯНИЙ L.O.C.U.S ===
    locus_sess = await ql.get_locus_session(uid)
    if locus_sess:
        win = locus_sess['current_window']
        
        # Если мы в процессе регистрации (окна от RZ.1.2.1 до RZ.1.2.9)
        if win.startswith("RZ.1.2."):
            await locus_ui.handle_registration(message, locus_sess, text)
            return
            
        # Переход из стартового меню в регистрацию
        if win == "RZ.1.1" and text == "1":
            await ql.set_locus_window(uid, "RZ.1.2.1", {})
            await message.channel.send(locus_ui.rz_121({}))
            return

    # === L.O.C.U.S. СИСТЕМА (ВЫШЕ ЦИФР) ===
    locus_sess = await ql.get_locus_session(uid)
    if locus_sess:
        win = locus_sess['current_window']
        
        # Стартовое меню
        if win == "RZ.1.1":
            if text == "1":
                await ql.set_locus_window(uid, "RZ.1.2.1", {})
                await message.channel.send(locus_ui.rz_121({}))
                return
            elif text == "2":
                await ql.set_locus_window(uid, "RZ.1.3", {})
                await message.channel.send(locus_ui.rz_13())
                return
            elif text == "3":
                await message.channel.send("Тех. поддержка: Discord -> nob_fa")
                return
            elif text == "4":
                await message.channel.send("Спец-код пока в разработке.")
                return
            elif text == "0":
                await ql.set_locus_window(uid, "LOGOUT", {})
                await message.channel.send("Вы вышли из системы L.O.C.U.S.")
                return
                
        # Регистрация
        if win.startswith("RZ.1.2."):
            await locus_ui.handle_registration(message, locus_sess, text)
            return
            
        # Вход в аккаунт
        if win.startswith("RZ.1.3"):
            await locus_ui.handle_login(message, locus_sess, text)
            return

        # Главное меню
        if win == "RZ.1.6":
            user = await ql.get_locus_user_by_id(uid)
            if text == "0":
                await ql.set_locus_window(uid, "A.1.1", {})
                await message.channel.send("Вы вышли из системы L.O.C.U.S.")
                return
            elif text == "1":
                await ql.set_locus_window(uid, "RZ.2.1", {})
                await message.channel.send(locus_ui.rz_21(user))
                return
            else:
                await message.channel.send("Этот раздел пока в разработке.")
                return

        # Экономика
        if win.startswith("RZ.2.1"):
            await locus_ui.handle_economy(message, locus_sess, text)
            return

    # === ВВОД КОДА ===
    sess = await q.get_session(uid)
    if not sess:
        await message.channel.send("Напишите `!start` для начала.")
        return
    if sess["current_window"] in ("A.1.1", "X.1.1"):
        await handle_code_input(message, sess)
        return


async def handle_create_account_code(message):
    parts = message.content.split()
    if len(parts) != 6:
        await message.channel.send("Формат: `!k КодАккаунт AAAA_BBBB_HHHH_XXXX Тайга 60d 1`")
        return
    _, _, code, callsign, dur, rank_s = parts
    uid = message.author.id
    member = await fetch_guild_member(bot, uid)
    staff_rank = get_staff_rank(member)
    if staff_rank < MIN_RANK_CREATE_ACCOUNT:
        await message.channel.send(f"Недостаточный уровень доступа. Требуется ранг {MIN_RANK_CREATE_ACCOUNT}+.")
        return
    if not is_valid_account_code(code):
        await message.channel.send("Неправильный формат кода. Правильный: AAAA_BBBB_HHHH_XXXX")
        return
    expiry = parse_duration(dur)
    if not expiry:
        await message.channel.send("Неверный срок. Пример: 60d, 12h, 2m")
        return
    try:
        rank = int(rank_s)
    except ValueError:
        await message.channel.send("Ранг — число от 1 до 8.")
        return
    if rank < 1 or rank > 8:
        await message.channel.send("Ранг от 1 до 8.")
        return
    if rank > staff_rank:
        await message.channel.send("Нельзя выдать ранг выше своего.")
        return
    if await q.get_code(code):
        await message.channel.send("Такой код уже существует.")
        return
    await q.insert_account_code(code, callsign, rank, expiry, uid)
    await q.log_action("create_account_code", uid, code, {"callsign": callsign, "rank": rank})
    await message.channel.send(
        f"Код аккаунта создан.\nКод: `{code}`\nПозывной: {callsign}\nРанг: {rank}\n"
        f"Действует до: {expiry.strftime('%Y-%m-%d %H:%M UTC')}"
    )


async def handle_create_unban_code(message):
    parts = message.content.split()
    if len(parts) != 3:
        await message.channel.send("Формат: `!K разбанкод AAAA_ZZZZ_HHHH_XXXX`")
        return
    _, _, code = parts
    uid = message.author.id
    member = await fetch_guild_member(bot, uid)
    staff_rank = get_staff_rank(member)
    if staff_rank < MIN_RANK_CREATE_UNBAN:
        await message.channel.send(f"Недостаточный уровень доступа. Требуется ранг {MIN_RANK_CREATE_UNBAN}+.")
        return
    if not is_valid_unban_code(code):
        await message.channel.send("Неправильный формат. Правильный: AAAA_ZZZZ_HHHH_XXXX")
        return
    if await q.get_code(code):
        await message.channel.send("Такой код уже существует.")
        return
    expiry = parse_duration("3d")
    await q.insert_unban_code(code, expiry, uid)
    await q.log_action("create_unban_code", uid, code, {})
    await message.channel.send(f"Разбан-код создан.\nКод: `{code}`\nДействует до: {expiry.strftime('%Y-%m-%d %H:%M UTC')}")


async def handle_code_input(message, sess):
    uid = message.author.id
    code = message.content.strip()
    acc = await q.get_account_by_code(code)
    if acc:
        if acc["is_blocked"]:
            await q.set_session_window(uid, "X.1.1", None)
            await message.channel.send(render.window_x11())
            return
        if acc["is_deactivated"]:
            await message.channel.send("🚫 Ваш аккаунт деактивирован. Обратитесь к администрации C.B.A.")
            return

    if sess["current_window"] == "X.1.1":
        cd = await q.get_code(code)
        if not cd or cd["code_type"] != "unban" or cd["activated_at"] is not None:
            await message.channel.send("Неверный или использованный разбан-код.")
            return
        if cd["expiry"] and cd["expiry"] < now_utc():
            await message.channel.send("Разбан-код истёк.")
            return
        if sess["account_id"]:
            await q.unblock_account(sess["account_id"])
        await q.mark_code_activated(code)
        await q.set_session_window(uid, "A.1.1", None)
        await q.log_action("unban_used", uid, code, {})
        await message.channel.send("Разблокировка выполнена.")
        await message.channel.send(render.window_a11())
        return

    acc = await q.get_account_by_code(code)
    if acc:
        if acc["is_blocked"]:
            await q.set_session_window(uid, "X.1.1", None)
            await message.channel.send(render.window_x11())
            return
        await q.upsert_session(uid, account_id=acc["id"], wrong_attempts=0)
        await q.set_session_window(uid, "A.1.2", None)
        member = await fetch_guild_member(bot, uid)
        sr = get_staff_rank(member)
        await _send_main_menu(message, acc, sr)
        await q.log_action("login", uid, acc["callsign"], {})
        return

    cd = await q.get_code(code)
    if not cd or cd["code_type"] != "account":
        n = await q.inc_wrong_attempts(uid)
        if n >= MAX_WRONG_ATTEMPTS:
            await message.channel.send("5 неверных попыток. Обратитесь к Staff 7+.")
            return
        if n == 3:
            await message.channel.send("Неверный код. Блокировка на 30 секунд.")
            await asyncio.sleep(30)
            return
        if n == 4:
            await message.channel.send("Неверный код. При попытке взлома вы будете заблокированы.")
            return
        await message.channel.send("Неверный код.")
        return

    if cd["activated_at"] is not None:
        await message.channel.send("Код уже активирован.")
        return
    if cd["expiry"] and cd["expiry"] < now_utc():
        await message.channel.send("Срок действия кода истёк.")
        return

    new_acc = await q.create_account(cd["callsign"], cd["rank"], code, cd["created_by"])
    await q.mark_code_activated(code)
    await q.upsert_session(uid, account_id=new_acc["id"], wrong_attempts=0)
    await q.set_session_window(uid, "A.1.2", None)
    member = await fetch_guild_member(bot, uid)
    sr = get_staff_rank(member)
    await _send_main_menu(message, new_acc, sr)
    await q.log_action("account_activated", uid, cd["callsign"], {"rank": cd["rank"]})


async def handle_navigation(message, digit: int):
    uid = message.author.id
    sess, acc, staff_rank = await _ctx(uid)
    if not sess:
        await message.channel.send("Напишите `!start`.")
        return

    win = sess["current_window"]

    if win.startswith("RZ."):
        return
    # ========== [A.1.2] ГЛАВНОЕ МЕНЮ ==========
    if win == "A.1.2":
        if not acc:
            await message.channel.send("Ошибка сессии.")
            return
        if digit in (0, 24):
            await q.upsert_session(uid, account_id=None)
            await q.set_session_window(uid, "A.1.1", None)
            await message.channel.send(render.window_a11())
            return
        if digit == 25:
            if staff_rank < MIN_RANK_ADMIN_MENU:
                await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
                return
            await q.set_session_window(uid, "P.1", None)
            await message.channel.send(render.window_p1(staff_rank))
            return
        if digit == 1:
            await q.set_session_window(uid, "A.1.1.1", None)
            await orders_handler.show_orders_menu(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.2.1", None)
            await protocol_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.3.1", None)
            await tasks_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.4.1", None)
            await reports_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "A.5.1", None)
            await specops_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 6:
            await q.set_session_window(uid, "A.6.1", None)
            await surv_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 7:
            await q.set_session_window(uid, "A.7.1", None)
            await dossier_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 8:
            await q.set_session_window(uid, "A.8.1", None)
            await analytics_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 9:
            await q.set_session_window(uid, "A.9.1", None)
            await forecasts_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 10:
            await q.set_session_window(uid, "A.10.1", None)
            await loyalty_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 11:
            await q.set_session_window(uid, "A.11.1", None)
            await liquidation_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 12:
            await q.set_session_window(uid, "A.12.1", None)
            await reports_out_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 13:
            await q.set_session_window(uid, "A.13.1", None)
            await archive_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 14:
            await q.set_session_window(uid, "A.14.1", None)
            await codenames_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 15:
            await q.set_session_window(uid, "A.15.1", None)
            await ciphers_handler.show_menu(message, acc, staff_rank)
            return
        if 16 <= digit <= 23:
            await message.channel.send(render.window_placeholder(f"Раздел {digit}", f"[A.{digit}.1]"))
            return

    # ========== [P.1] АДМИН-МЕНЮ ==========
    if win == "P.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            if staff_rank < 7:
                await message.channel.send("Недостаточный уровень доступа. Требуется ранг 7+. [A.ERR] 0 Назад")
                return
            await q.set_session_window(uid, "P.1.1", None)
            await message.channel.send(render.window_p11())
            return
        if digit == 2:
            if staff_rank < 6:
                await message.channel.send("Недостаточный уровень доступа. Требуется ранг 6+. [A.ERR] 0 Назад")
                return
            await q.set_session_window(uid, "P.1.2", None)
            await message.channel.send(render.window_p12())
            return

    # ========== [P.1.1] ==========
    if win == "P.1.1":
        if digit == 0:
            await q.set_session_window(uid, "P.1", None)
            await message.channel.send(render.window_p1(staff_rank))
            return
        if digit == 1:
            await q.set_session_window(uid, "P.1.1.1", None)
            await admin.show_p111(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "P.1.1.2", None)
            await admin.show_p112(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "P.1.1.3", None)
            await admin.show_p113(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "P.1.1.4", None)
            await admin.show_p114(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "P.1.1.5", None)
            await admin.show_p115(message, acc, staff_rank)
            return
        return

    # ========== [P.1.2] ==========
    if win == "P.1.2":
        if digit == 0:
            await q.set_session_window(uid, "P.1", None)
            await message.channel.send(render.window_p1(staff_rank))
            return
        if digit == 1:
            await q.set_session_window(uid, "P.1.2.1", None)
            await admin.show_p121(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "P.1.2.2", None)
            await admin.show_p122(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "P.1.2.3", None)
            await admin.show_p123(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "P.1.2.4", None)
            await admin.show_p124(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "P.1.2.5", None)
            await admin.show_p125(message, acc, staff_rank)
            return
        if digit == 6:
            await q.set_session_window(uid, "P.1.2.6", None)
            await admin.show_p126(message, acc, staff_rank)
            return
        if digit == 7:
            await q.set_session_window(uid, "P.1.2.7", None)
            await admin.show_p127(message, acc, staff_rank)
            return
        if digit == 8:
            await q.set_session_window(uid, "P.1.2.8", None)
            await admin.show_p128(message, acc, staff_rank)
            return
        return

    if win.startswith("P.1.1."):
        if digit == 0:
            await q.set_session_window(uid, "P.1.1", None)
            await message.channel.send(render.window_p11())
            return
        return

    if win.startswith("P.1.2."):
        if digit == 0:
            await q.set_session_window(uid, "P.1.2", None)
            await message.channel.send(render.window_p12())
            return
        return

    # ========== [A.1.1.x] ПРИКАЗЫ ==========
    if win == "A.1.1.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.1.1.2", None)
            await orders_handler.show_create_order(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.1.1.3", None)
            await orders_handler.show_active_orders(message, acc)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.1.1.4", None)
            await orders_handler.show_history_orders(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.1.1.5", None)
            await orders_handler.show_delete_order(message, acc, staff_rank)
            return
        return

    if win in ("A.1.1.2", "A.1.1.3", "A.1.1.4", "A.1.1.5"):
        if digit == 0:
            await q.set_session_window(uid, "A.1.1.1", None)
            await orders_handler.show_orders_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.2.1] ПРОТОКОЛ ==========
    if win == "A.2.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.2.1.1", None)
            await protocol_handler.show_announce(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.2.1.2", None)
            await protocol_handler.show_cancel(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.2.1.3", None)
            await protocol_handler.show_status(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.2.1.4", None)
            await protocol_handler.show_history(message, acc, staff_rank)
            return
        return

    if win in ("A.2.1.1", "A.2.1.2", "A.2.1.3", "A.2.1.4"):
        if digit == 0:
            await q.set_session_window(uid, "A.2.1", None)
            await protocol_handler.show_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.3.1] ЗАДАЧИ ==========
    if win == "A.3.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.3.1.1", None)
            await tasks_handler.show_create(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.3.1.2", None)
            await tasks_handler.show_my(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.3.1.3", None)
            await tasks_handler.show_issue_dept(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.3.1.4", None)
            await tasks_handler.show_close(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "A.3.1.5", None)
            await tasks_handler.show_overdue(message, acc, staff_rank)
            return
        return

    if win in ("A.3.1.1", "A.3.1.2", "A.3.1.3", "A.3.1.4", "A.3.1.5"):
        if digit == 0:
            await q.set_session_window(uid, "A.3.1", None)
            await tasks_handler.show_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.4.1] ДОНЕСЕНИЯ ==========
    if win == "A.4.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.4.1.1", None)
            await reports_handler.show_send(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.4.1.2", None)
            await reports_handler.show_my(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.4.1.3", None)
            await reports_handler.show_incoming(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.4.1.4", None)
            await reports_handler.show_review(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "A.4.1.5", None)
            await reports_handler.show_archive(message, acc, staff_rank)
            return
        return

    if win in ("A.4.1.1", "A.4.1.2", "A.4.1.3", "A.4.1.4", "A.4.1.5"):
        if digit == 0:
            await q.set_session_window(uid, "A.4.1", None)
            await reports_handler.show_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.5.1] СПЕЦОПЕРАЦИИ ==========
    if win == "A.5.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.5.1.1", None)
            await specops_handler.show_create(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.5.1.2", None)
            await specops_handler.show_assign(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.5.1.3", None)
            await specops_handler.show_status(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.5.1.4", None)
            await specops_handler.show_report(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "A.5.1.5", None)
            await specops_handler.show_cancel(message, acc, staff_rank)
            return
        return

    if win in ("A.5.1.1", "A.5.1.2", "A.5.1.3", "A.5.1.4", "A.5.1.5"):
        if digit == 0:
            await q.set_session_window(uid, "A.5.1", None)
            await specops_handler.show_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.6.1] СЛЕЖКА ==========
    if win == "A.6.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.6.1.1", None)
            await surv_handler.show_start(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.6.1.2", None)
            await surv_handler.show_report(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.6.1.3", None)
            await surv_handler.show_stop(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.6.1.4", None)
            await surv_handler.show_active(message, acc, staff_rank)
            return
        return

    if win in ("A.6.1.1", "A.6.1.2", "A.6.1.3", "A.6.1.4"):
        if digit == 0:
            await q.set_session_window(uid, "A.6.1", None)
            await surv_handler.show_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.7.1] ДОСЬЕ ==========
    if win == "A.7.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.7.1.1", None)
            await dossier_handler.show_create(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.7.1.2", None)
            await dossier_handler.show_edit(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.7.1.3", None)
            await dossier_handler.show_view(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.7.1.4", None)
            await dossier_handler.show_delete(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "A.7.1.5", None)
            await dossier_handler.show_search(message, acc, staff_rank)
            return
        return

    if win in ("A.7.1.1", "A.7.1.2", "A.7.1.3", "A.7.1.4", "A.7.1.5"):
        if digit == 0:
            await q.set_session_window(uid, "A.7.1", None)
            await dossier_handler.show_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.8.1] АНАЛИТИКА ==========
    if win == "A.8.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.8.1.1", None)
            await analytics_handler.show_request(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.8.1.2", None)
            await analytics_handler.show_activity(message, acc, staff_rank, bot)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.8.1.3", None)
            await analytics_handler.show_suspicious(message, acc, staff_rank)
            return
            if digit == 4:
                await q.set_session_window(uid, "A.8.1.4", None)
                await analytics_handler.show_report(message, acc, staff_rank)
                return
            if digit == 5:
                await q.set_session_window(uid, "A.8.1.5", None)
                await gdossier_handler.show_menu(message, acc, staff_rank)
                return
            return

    if win in ("A.8.1.1", "A.8.1.2", "A.8.1.3", "A.8.1.4"):
        if digit == 0:
            await q.set_session_window(uid, "A.8.1", None)
            await analytics_handler.show_menu(message, acc, staff_rank)
            return
        return

    if win == "A.8.1.5":
        if digit == 0:
            await q.set_session_window(uid, "A.8.1", None)
            await analytics_handler.show_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.8.1.5.1", None)
            await gdossier_handler.show_scan(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.8.1.5.2", None)
            await gdossier_handler.show_dangerous(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.8.1.5.3", None)
            await gdossier_handler.show_by_id(message, acc, staff_rank)
            return
        return

    if win in ("A.8.1.5.1", "A.8.1.5.2", "A.8.1.5.3"):
        if digit == 0:
            await q.set_session_window(uid, "A.8.1.5", None)
            await gdossier_handler.show_menu(message, acc, staff_rank)
            return
        return
    # ========== [A.9.1] ПРОГНОЗЫ ==========
    if win == "A.9.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.9.1.1", None)
            await forecasts_handler.show_create(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.9.1.2", None)
            await forecasts_handler.show_dept(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.9.1.3", None)
            await forecasts_handler.show_threat(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.9.1.4", None)
            await forecasts_handler.show_archive(message, acc, staff_rank)
            return
        return

    if win in ("A.9.1.1", "A.9.1.2", "A.9.1.3", "A.9.1.4"):
        if digit == 0:
            await q.set_session_window(uid, "A.9.1", None)
            await forecasts_handler.show_menu(message, acc, staff_rank)
            return
        return
                # ========== [A.9.1] ПРОГНОЗЫ ==========
    if win == "A.9.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.9.1.1", None)
            await forecasts_handler.show_create(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.9.1.2", None)
            await forecasts_handler.show_dept(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.9.1.3", None)
            await forecasts_handler.show_threat(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.9.1.4", None)
            await forecasts_handler.show_archive(message, acc, staff_rank)
            return
        return

    if win in ("A.9.1.1", "A.9.1.2", "A.9.1.3", "A.9.1.4"):
        if digit == 0:
            await q.set_session_window(uid, "A.9.1", None)
            await forecasts_handler.show_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.10.1] ЛОЯЛЬНОСТЬ ==========
    if win == "A.10.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.10.1.1", None)
            await loyalty_handler.show_start(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.10.1.2", None)
            await loyalty_handler.show_questions(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.10.1.3", None)
            await loyalty_handler.show_result(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.10.1.4", None)
            await loyalty_handler.show_dispute(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "A.10.1.5", None)
            await loyalty_handler.show_journal(message, acc, staff_rank)
            return
        return

    if win in ("A.10.1.1", "A.10.1.2", "A.10.1.3", "A.10.1.4", "A.10.1.5"):
        if digit == 0:
            await q.set_session_window(uid, "A.10.1", None)
            await loyalty_handler.show_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.11.1] ЛИКВИДАЦИЯ ==========
    if win == "A.11.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.11.1.1", None)
            await liquidation_handler.show_create(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.11.1.2", None)
            await liquidation_handler.show_confirm(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.11.1.3", None)
            await liquidation_handler.show_assign(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.11.1.4", None)
            await liquidation_handler.show_status(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "A.11.1.5", None)
            await liquidation_handler.show_archive(message, acc, staff_rank)
            return
        return

    if win in ("A.11.1.1", "A.11.1.2", "A.11.1.3", "A.11.1.4", "A.11.1.5"):
        if digit == 0:
            await q.set_session_window(uid, "A.11.1", None)
            await liquidation_handler.show_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.12.1] ОТЧЁТЫ ==========
    if win == "A.12.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.12.1.1", None)
            await reports_out_handler.show_create(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.12.1.2", None)
            await reports_out_handler.show_send(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.12.1.3", None)
            await reports_out_handler.show_my(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.12.1.4", None)
            await reports_out_handler.show_review(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "A.12.1.5", None)
            await reports_out_handler.show_archive(message, acc, staff_rank)
            return
        return

    if win in ("A.12.1.1", "A.12.1.2", "A.12.1.3", "A.12.1.4", "A.12.1.5"):
        if digit == 0:
            await q.set_session_window(uid, "A.12.1", None)
            await reports_out_handler.show_menu(message, acc, staff_rank)
            return
        return

    # ========== [A.13.1] АРХИВ ==========
    if win == "A.13.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.13.1.1", None)
            await archive_handler.show_search(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.13.1.2", None)
            await archive_handler.show_add(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.13.1.3", None)
            await archive_handler.show_extract(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.13.1.4", None)
            await archive_handler.show_delete(message, acc, staff_rank)
            return
        if digit == 5:
            await q.set_session_window(uid, "A.13.1.5", None)
            await archive_handler.show_list(message, acc, staff_rank)
            return
        return

    if win == "A.14.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.14.1.1", None)
            await codenames_handler.show_create(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.14.1.2", None)
            await codenames_handler.show_change(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.14.1.3", None)
            await codenames_handler.show_list(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.14.1.4", None)
            await codenames_handler.show_delete(message, acc, staff_rank)
            return
        return

    if win in ("A.13.1.1", "A.13.1.2", "A.13.1.3", "A.13.1.4", "A.13.1.5"):
        if digit == 0:
            await q.set_session_window(uid, "A.13.1", None)
            await archive_handler.show_menu(message, acc, staff_rank)
            return
        return

    if win == "A.14.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.14.1.1", None)
            await codenames_handler.show_create(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.14.1.2", None)
            await codenames_handler.show_change(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.14.1.3", None)
            await codenames_handler.show_list(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.14.1.4", None)
            await codenames_handler.show_delete(message, acc, staff_rank)
            return
        return
        
    # ========== [A.15.1] ШИФРЫ ==========
    if win == "A.15.1":
        if digit == 0:
            await q.set_session_window(uid, "A.1.2", None)
            await _send_main_menu(message, acc, staff_rank)
            return
        if digit == 1:
            await q.set_session_window(uid, "A.15.1.1", None)
            await ciphers_handler.show_create(message, acc, staff_rank)
            return
        if digit == 2:
            await q.set_session_window(uid, "A.15.1.2", None)
            await ciphers_handler.show_decrypt(message, acc, staff_rank)
            return
        if digit == 3:
            await q.set_session_window(uid, "A.15.1.3", None)
            await ciphers_handler.show_list(message, acc, staff_rank)
            return
        if digit == 4:
            await q.set_session_window(uid, "A.15.1.4", None)
            await ciphers_handler.show_delete(message, acc, staff_rank)
            return
        return

    if win in ("A.15.1.1", "A.15.1.2", "A.15.1.3", "A.15.1.4"):
        if digit == 0:
            await q.set_session_window(uid, "A.15.1", None)
            await ciphers_handler.show_menu(message, acc, staff_rank)
            return
        return
        
    # ========== ПРОЧИЕ ==========
    if digit == 0:
        await q.set_session_window(uid, "A.1.2", None)
        await _send_main_menu(message, acc, staff_rank)
        return
    await message.channel.send("Раздел в разработке (Этап 3.4+).")

async def main():
    try:
        async with bot:
            await bot.start(TOKEN)
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
