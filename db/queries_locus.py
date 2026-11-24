from db.connection import pool

# ---------- SESSIONS ----------
async def get_locus_session(discord_id: int):
    return await pool().fetchrow("SELECT * FROM locus_sessions WHERE discord_id = $1", discord_id)

async def set_locus_window(discord_id: int, window: str, temp_data: dict = None):
    if temp_data is not None:
        import json
        await pool().execute(
            "UPDATE locus_sessions SET current_window = $1, temp_data = $2 WHERE discord_id = $3",
            window, json.dumps(temp_data), discord_id
        )
    else:
        await pool().execute(
            "UPDATE locus_sessions SET current_window = $1 WHERE discord_id = $2",
            window, discord_id
        )

async def create_locus_session(discord_id: int):
    existing = await get_locus_session(discord_id)
    if not existing:
        await pool().execute("INSERT INTO locus_sessions (discord_id) VALUES ($1)", discord_id)

# ---------- USERS ----------
async def get_locus_user_by_id(discord_id: int):
    return await pool().fetchrow("SELECT * FROM locus_users WHERE discord_id = $1", discord_id)

async def get_locus_user_by_callsign(callsign: str):
    return await pool().fetchrow("SELECT * FROM locus_users WHERE callsign = $1", callsign)

async def create_locus_user(data: dict):
    return await pool().fetchrow(
        """INSERT INTO locus_users 
           (discord_id, discord_name, roblox_name, rp_rank, department, is_admin, in_clans, callsign, password) 
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *""",
        data['discord_id'], data['discord_name'], data['roblox_name'], 
        data['rp_rank'], data['department'], data['is_admin'], data['in_clans'], 
        data['callsign'], data['password']
    )
    # ---------- БАЛАНС И ЭКОНОМИКА ----------
async def update_balance(discord_id: int, coins_delta: int = 0, fishki_delta: int = 0):
    """Изменяет баланс игрока (плюс или минус)."""
    return await pool().fetchrow(
        """UPDATE locus_users 
           SET coins = coins + $1, fishki = fishki + $2 
           WHERE discord_id = $3 RETURNING *""",
        coins_delta, fishki_delta, discord_id
    )

async def log_transaction(sender_id: int, receiver_id: int, amount: int):
    """Записывает перевод в историю."""
    await pool().execute(
        "INSERT INTO locus_transactions (sender_id, receiver_id, amount) VALUES ($1, $2, $3)",
        sender_id, receiver_id, amount
    )

async def claim_daily_reward(discord_id: int):
    """Выдает ежедневный бонус 500 монет."""
    user = await get_locus_user_by_id(discord_id)
    if not user:
        return False, "Аккаунт не найден."
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    if user['last_daily_reward']:
        diff = now - user['last_daily_reward']
        if diff.total_seconds() < 86400: # 24 часа
            hours_left = 24 - int(diff.total_seconds() // 3600)
            return False, f"Бонус уже получен. Следующий через {hours_left} ч."
    
    # Выдаем 500 монет
    await update_balance(discord_id, coins_delta=500)
    await pool().execute("UPDATE locus_users SET last_daily_reward = NOW() WHERE discord_id = $1", discord_id)
    
    return True, "Вы получили 500 монет!"