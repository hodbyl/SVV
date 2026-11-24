import json
from db.connection import pool


# ---------- CODES ----------
async def get_code(code: str):
    return await pool().fetchrow("SELECT * FROM codes WHERE code = $1", code)


async def insert_account_code(code, callsign, rank, expiry, created_by):
    return await pool().fetchrow(
        """INSERT INTO codes (code, code_type, callsign, rank, expiry, created_by)
           VALUES ($1, 'account', $2, $3, $4, $5)
           RETURNING *""",
        code, callsign, rank, expiry, created_by
    )


async def insert_unban_code(code, expiry, created_by):
    return await pool().fetchrow(
        """INSERT INTO codes (code, code_type, expiry, created_by)
           VALUES ($1, 'unban', $2, $3)
           RETURNING *""",
        code, expiry, created_by
    )


async def mark_code_activated(code: str):
    await pool().execute("UPDATE codes SET activated_at = NOW() WHERE code = $1", code)


# ---------- ACCOUNTS ----------
async def get_account_by_code(code: str):
    return await pool().fetchrow("SELECT * FROM accounts WHERE password_code = $1", code)


async def get_account_by_id(acc_id: int):
    return await pool().fetchrow("SELECT * FROM accounts WHERE id = $1", acc_id)


async def create_account(callsign, rank, password_code, created_by):
    return await pool().fetchrow(
        """INSERT INTO accounts (callsign, rank, password_code, created_by)
           VALUES ($1, $2, $3, $4)
           RETURNING *""",
        callsign, rank, password_code, created_by
    )


async def unblock_account(acc_id: int):
    await pool().execute(
        "UPDATE accounts SET is_blocked = FALSE, block_reason = NULL WHERE id = $1",
        acc_id
    )


# ---------- SESSIONS ----------
async def get_session(discord_id: int):
    return await pool().fetchrow("SELECT * FROM sessions WHERE discord_id = $1", discord_id)


async def upsert_session(discord_id: int, **fields):
    existing = await get_session(discord_id)
    if not existing:
        await pool().execute("INSERT INTO sessions (discord_id) VALUES ($1)", discord_id)
    for k, v in fields.items():
        await pool().execute(
            f"UPDATE sessions SET {k} = $1, last_activity = NOW() WHERE discord_id = $2",
            v, discord_id
        )
    return await get_session(discord_id)


async def set_session_window(discord_id: int, window: str, menu_message_id: int | None = None):
    if menu_message_id is not None:
        await pool().execute(
            """UPDATE sessions
               SET current_window = $1, menu_message_id = $2, last_activity = NOW()
               WHERE discord_id = $3""",
            window, menu_message_id, discord_id
        )
    else:
        await pool().execute(
            "UPDATE sessions SET current_window = $1, last_activity = NOW() WHERE discord_id = $2",
            window, discord_id
        )


async def reset_wrong_attempts(discord_id: int):
    await pool().execute("UPDATE sessions SET wrong_attempts = 0 WHERE discord_id = $1", discord_id)


async def inc_wrong_attempts(discord_id: int) -> int:
    row = await pool().fetchrow(
        """UPDATE sessions SET wrong_attempts = wrong_attempts + 1
           WHERE discord_id = $1 RETURNING wrong_attempts""",
        discord_id
    )
    return row["wrong_attempts"]


# ---------- LOGS ----------
async def log_action(action, actor_discord=None, target=None, payload=None):
    await pool().execute(
        """INSERT INTO logs (action, actor_discord, target, payload)
           VALUES ($1, $2, $3, $4)""",
        action, actor_discord, target, json.dumps(payload or {})
    )
    

# ---------- DEACTIVATION ----------
async def deactivate_account(callsign, reason, actor_callsign):
    return await pool().fetchrow(
        """UPDATE accounts
           SET is_deactivated=TRUE, deactivated_reason=$1,
               deactivated_by=$2, deactivated_at=NOW()
           WHERE callsign=$3 RETURNING *""",
        reason, actor_callsign, callsign
    )


async def activate_account(callsign):
    return await pool().fetchrow(
        """UPDATE accounts
           SET is_deactivated=FALSE, deactivated_reason=NULL,
               deactivated_by=NULL, deactivated_at=NULL
           WHERE callsign=$1 RETURNING *""",
        callsign
    )


async def list_deactivated(limit=30):
    return await pool().fetch(
        """SELECT * FROM accounts WHERE is_deactivated=TRUE
           ORDER BY deactivated_at DESC LIMIT $1""",
        limit
    )


async def get_account_by_callsign(callsign):
    return await pool().fetchrow(
        "SELECT * FROM accounts WHERE callsign=$1", callsign
    )

    # ---------- DEACTIVATION ----------
async def deactivate_account(callsign, reason, actor_callsign):
    return await pool().fetchrow(
        """UPDATE accounts
           SET is_deactivated=TRUE, deactivated_reason=$1,
               deactivated_by=$2, deactivated_at=NOW()
           WHERE callsign=$3 RETURNING *""",
        reason, actor_callsign, callsign
    )


async def activate_account(callsign):
    return await pool().fetchrow(
        """UPDATE accounts
           SET is_deactivated=FALSE, deactivated_reason=NULL,
               deactivated_by=NULL, deactivated_at=NULL
           WHERE callsign=$1 RETURNING *""",
        callsign
    )


async def list_deactivated(limit=30):
    return await pool().fetch(
        """SELECT * FROM accounts WHERE is_deactivated=TRUE
           ORDER BY deactivated_at DESC LIMIT $1""",
        limit
    )


async def get_account_by_callsign(callsign):
    return await pool().fetchrow(
        "SELECT * FROM accounts WHERE callsign=$1", callsign
    )


async def full_restore_account(callsign):
    return await pool().fetchrow(
        """UPDATE accounts
           SET is_blocked=FALSE, block_reason=NULL,
               is_deactivated=FALSE, deactivated_reason=NULL,
               deactivated_by=NULL, deactivated_at=NULL
           WHERE callsign=$1 RETURNING *""",
        callsign
    )