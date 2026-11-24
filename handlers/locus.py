import json
from db import queries_locus as ql

SEP = "-" * 90
MARK = "L.O.C.U.S *Team*® Не принадлежит распространению"
LINE = "L.O.C.U.S *Team*®"
INFO = "Вопросы к Discord -> nob_fa"

def frame(title, window, content, footer="0. Назад"):
    return (
        f"{SEP}\n{LINE}\n{SEP}\n"
        f"{title} [{window}]\n{SEP}\n"
        f"{MARK}\n{SEP}\n{content}\n{SEP}\n"
        f"{footer}\n{SEP}\n{MARK}\n{INFO}\n{SEP}"
    )

def rz_11():
    content = (
        "Добро пожаловать, оперативник\n\n"
        "1. Регистрация\n2. Вход\n3. Тех поддержка\n4. Спец код\n0. Выход"
    )
    return frame("Добро пожаловать", "RZ.1.1", content, "0. Выход")

def rz_121(temp):
    """Шаг 1: Ввод Discord ника"""
    return frame("Регистрация (Шаг 1/8)", "RZ.1.2.1", "Введите ваш Discord аккаунт (основной):", "0. Отмена")

def rz_122(temp):
    """Шаг 2: Ввод Roblox ника"""
    return frame("Регистрация (Шаг 2/8)", "RZ.1.2.2", f"Discord: {temp.get('discord_name', '')}\n\nВведите ваш Roblox аккаунт (основной):", "0. Отмена")

def rz_123(temp):
    """Шаг 3: Ввод РП звания"""
    return frame("Регистрация (Шаг 3/8)", "RZ.1.2.3", "Введите ваш Ранг (РП звание):", "0. Отмена")

def rz_124(temp):
    """Шаг 4: Выбор отдела"""
    content = (
        "Выберите ваш отдел (напишите название):\n"
        "KOS, FUR, TOJ, SRT, CHT, SUW, DEF, C.B.A. или Нет"
    )
    return frame("Регистрация (Шаг 4/8)", "RZ.1.2.4", content, "0. Отмена")

def rz_125(temp):
    """Шаг 5: Должность админа"""
    content = "Есть ли у вас должность администрации?\nНапишите строго: Есть или Нету"
    return frame("Регистрация (Шаг 5/8)", "RZ.1.2.5", content, "0. Отмена")

def rz_126(temp):
    """Шаг 6: Кланы"""
    content = "Состоите ли вы в кланах (кроме наших)?\nНапишите: Да или Нету"
    return frame("Регистрация (Шаг 6/8)", "RZ.1.2.6", content, "0. Отмена")

def rz_127(temp):
    """Шаг 7: Позывной"""
    content = "Придумайте Позывной (русские буквы, от 3 до 8 символов, без пробелов):"
    return frame("Регистрация (Шаг 7/8)", "RZ.1.2.7", content, "0. Отмена")

def rz_128(temp):
    """Шаг 8: Пароль"""
    content = "Придумайте пароль в формате AAAA_BBBB_ZZZZ_XXXX_VVVV:"
    return frame("Регистрация (Шаг 8/8)", "RZ.1.2.8", content, "0. Отмена")

def rz_129(temp):
    """Шаг 9: Подтверждение пароля"""
    return frame("Регистрация (Подтверждение)", "RZ.1.2.9", "Повторите ваш пароль:", "0. Отмена")

def rz_16(user):
    """Главное меню"""
    content = (
        f"Добро пожаловать, {user['callsign']} [{user['department']}] ({user['rp_rank']})\n\n"
        "1. Экономика\n2. Казино\n3. Крипто-биржа\n4. Модерация\n"
        "5. Профиль\n6. Настройки\n0. Выход"
    )
    return frame("Главное меню", "RZ.1.6", content, "0. Выход")


# ================= ЛОГИКА РЕГИСТРАЦИИ =================
async def handle_registration(message, sess, text):
    uid = message.author.id
    window = sess['current_window']
    temp = sess['temp_data']
    
    # Если temp_data пришло как строка (из БД), превращаем в словарь
    if isinstance(temp, str):
        temp = json.loads(temp)
    if not temp:
        temp = {}
    
    # Если игрок нажал 0 — отмена
    if text == "0":
        await ql.set_locus_window(uid, "RZ.1.1", {})
        await message.channel.send(rz_11())
        return

    # Шаг 1: Discord
    if window == "RZ.1.2.1":
        temp['discord_name'] = text
        await ql.set_locus_window(uid, "RZ.1.2.2", temp)
        await message.channel.send(rz_122(temp))
        
    # Шаг 2: Roblox
    elif window == "RZ.1.2.2":
        temp['roblox_name'] = text
        await ql.set_locus_window(uid, "RZ.1.2.3", temp)
        await message.channel.send(rz_123(temp))
        
    # Шаг 3: РП Ранг
    elif window == "RZ.1.2.3":
        temp['rp_rank'] = text
        await ql.set_locus_window(uid, "RZ.1.2.4", temp)
        await message.channel.send(rz_124(temp))
        
    # Шаг 4: Отдел
    elif window == "RZ.1.2.4":
        dept = text.upper()
        valid_depts = ["KOS", "FUR", "TOJ", "SRT", "CHT", "SUW", "DEF", "C.B.A.", "НЕТ"]
        if dept not in valid_depts:
            await message.channel.send("❌ Неверный отдел. Введите KOS, FUR, TOJ, SRT, CHT, SUW, DEF, C.B.A. или Нет.")
            return
        temp['department'] = dept if dept != "НЕТ" else "Нет"
        await ql.set_locus_window(uid, "RZ.1.2.5", temp)
        await message.channel.send(rz_125(temp))
        
    # Шаг 5: Админ (Валидация)
    elif window == "RZ.1.2.5":
        if text.lower() not in ["есть", "нету"]:
            await message.channel.send("❌ Неправильный ввод. Напишите строго: Есть или Нету.")
            return
        temp['is_admin'] = text.lower()
        await ql.set_locus_window(uid, "RZ.1.2.6", temp)
        await message.channel.send(rz_126(temp))
        
    # Шаг 6: Кланы
    elif window == "RZ.1.2.6":
        if text.lower() not in ["да", "нету", "нет"]:
            await message.channel.send("❌ Неправильный ввод. Напишите строго: Да или Нету.")
            return
        temp['in_clans'] = text.lower()
        await ql.set_locus_window(uid, "RZ.1.2.7", temp)
        await message.channel.send(rz_127(temp))
        
    # Шаг 7: Позывной (Валидация)
    elif window == "RZ.1.2.7":
        callsign = text.strip()
        # Проверка на русские буквы, 3-8 символов
        import re
        if not re.match(r"^[А-Яа-яЁё]{3,8}$", callsign):
            await message.channel.send("❌ Позывной должен быть только на русском, без пробелов, от 3 до 8 символов.")
            return
        # Проверка, не занят ли
        existing = await ql.get_locus_user_by_callsign(callsign)
        if existing:
            await message.channel.send("❌ Этот позывной уже занят. Придумайте другой.")
            return
        temp['callsign'] = callsign
        await ql.set_locus_window(uid, "RZ.1.2.8", temp)
        await message.channel.send(rz_128(temp))
        
    # Шаг 8: Пароль (Валидация)
    elif window == "RZ.1.2.8":
        pwd = text.strip()
        # Формат: 5 блоков по 4 символа через _
        import re
        if not re.match(r"^[A-Za-z0-9]{4}_[A-Za-z0-9]{4}_[A-Za-z0-9]{4}_[A-Za-z0-9]{4}_[A-Za-z0-9]{4}$", pwd):
            await message.channel.send("❌ Неверный формат. Пример: ABCD_1234_EFGH_5678_IJKL")
            return
        temp['password'] = pwd
        await ql.set_locus_window(uid, "RZ.1.2.9", temp)
        await message.channel.send(rz_129(temp))
        
    # Шаг 9: Подтверждение пароля
    elif window == "RZ.1.2.9":
        if text.strip() != temp.get('password'):
            await message.channel.send("❌ Пароли не совпадают. Введите пароль заново.")
            return
        
        # СОЗДАНИЕ АККАУНТА
        temp['discord_id'] = uid
        user = await ql.create_locus_user(temp)
        
        # Очищаем сессию и выдаем главное меню
        await ql.set_locus_window(uid, "RZ.1.6", {})
        await message.channel.send("✅ Регистрация успешно завершена!")
        await message.channel.send(rz_16(user))
def rz_13():
    """Вход в аккаунт"""
    return frame("Вход в аккаунт", "RZ.1.3", "Введите ваш позывной:", "0. Назад")

def rz_132():
    """Вход: пароль"""
    return frame("Вход в аккаунт", "RZ.1.3.2", "Введите ваш пароль:", "0. Назад")

def rz_21(user):
    """Меню Экономики"""
    content = (
        f"💰 Кошелек: {user['coins']} монет\n"
        f"🪙 Фишки: {user['fishki']}\n\n"
        "1. Перевести монеты\n"
        "2. Ежедневный бонус (500 монет)\n"
        "3. История операций\n"
        "0. Назад"
    )
    return frame("Экономика и Банк", "RZ.2.1", content, "0. Назад")

def rz_211():
    """Перевод монет"""
    return frame("Перевод монет", "RZ.2.1.1", "Введите: (Позывной) (Сумма)\nПример: Сокол 100", "0. Назад")
    """Перевод монет"""
    return frame("Перевод монет", "RZ.2.1.1", "Введите: (Позывной) (Сумма)\nПример: Сокол 100", "0. Назад")
async def handle_login(message, sess, text):
    uid = message.author.id
    window = sess['current_window']
    temp = sess['temp_data']
    if isinstance(temp, str):
        temp = json.loads(temp)
    if not temp:
        temp = {}

    if text == "0":
        await ql.set_locus_window(uid, "RZ.1.1", {})
        await message.channel.send(rz_11())
        return

    if window == "RZ.1.3":
        user = await ql.get_locus_user_by_callsign(text.strip())
        if not user:
            await message.channel.send("❌ Позывной не найден. Попробуйте еще раз или нажмите 0.")
            return
        temp['login_callsign'] = text.strip()
        await ql.set_locus_window(uid, "RZ.1.3.2", temp)
        await message.channel.send(rz_132())

    elif window == "RZ.1.3.2":
        user = await ql.get_locus_user_by_callsign(temp['login_callsign'])
        if user['password'] != text.strip():
            await message.channel.send("❌ Неверный пароль. Попробуйте еще раз или нажмите 0.")
            return
        
        # Успешный вход
        await ql.set_locus_window(uid, "RZ.1.6", {})
        await message.channel.send("✅ Вход выполнен успешно!")
        await message.channel.send(rz_16(user))

async def handle_economy(message, sess, text):
    uid = message.author.id
    window = sess['current_window']
    user = await ql.get_locus_user_by_id(uid)

    if text == "0":
        await ql.set_locus_window(uid, "RZ.1.6", {})
        await message.channel.send(rz_16(user))
        return

    if window == "RZ.2.1":
        if text == "1":
            await ql.set_locus_window(uid, "RZ.2.1.1", {})
            await message.channel.send(rz_211())
        elif text == "2":
            success, msg = await ql.claim_daily_reward(uid)
            user = await ql.get_locus_user_by_id(uid) # Обновляем данные
            await message.channel.send(f"{'✅' if success else '❌'} {msg}")
            await message.channel.send(rz_21(user))
        elif text == "3":
            await message.channel.send("История операций пока в разработке.")
            
    elif window == "RZ.2.1.1":
        parts = text.split()
        if len(parts) != 2:
            await message.channel.send("❌ Неверный формат. Введите: (Позывной) (Сумма)")
            return
        target_callsign, amount_str = parts
        try:
            amount = int(amount_str)
        except ValueError:
            await message.channel.send("❌ Сумма должна быть числом.")
            return

        target = await ql.get_locus_user_by_callsign(target_callsign)
        if not target:
            await message.channel.send("❌ Игрок с таким позывным не найден.")
            return
        if target['discord_id'] == uid:
            await message.channel.send("❌ Нельзя перевести монеты самому себе.")
            return
        if amount <= 0:
            await message.channel.send("❌ Сумма должна быть больше нуля.")
            return
        if user['coins'] < amount:
            await message.channel.send("❌ Недостаточно монет на балансе.")
            return

        # Перевод
        await ql.update_balance(uid, coins_delta=-amount)
        await ql.update_balance(target['discord_id'], coins_delta=amount)
        await ql.log_transaction(uid, target['discord_id'], amount)

        user = await ql.get_locus_user_by_id(uid)
        await message.channel.send(f"✅ Вы перевели {amount} монет игроку {target['callsign']}.")
        await message.channel.send(rz_21(user))
        
        # Уведомление получателю
        try:
            guild = message.guild
            if not guild: # Если в ЛС, ищем сервер
                guild = bot.get_guild(1462104321461063773)
            member = await guild.fetch_member(target['discord_id']) if guild else None
            if member:
                await member.send(f"💰 Вам перевели {amount} монет от {user['callsign']}!")
        except:
            pass