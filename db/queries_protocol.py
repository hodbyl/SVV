from db.connection import pool


async def get_active_protocol():
    return await pool().fetchrow(
        "SELECT * FROM protocols WHERE status='active' ORDER BY created_at DESC LIMIT 1"
    )


async def insert_protocol(level, reason, expires_at, actor_callsign, actor_discord):
    return await pool().fetchrow(
        """INSERT INTO protocols (level, reason, expires_at, actor_callsign, actor_discord)
           VALUES ($1,$2,$3,$4,$5) RETURNING *""",
        level, reason, expires_at, actor_callsign, actor_discord
    )


async def cancel_active_protocol(reason):
    return await pool().fetchrow(
        """UPDATE protocols SET status='cancelled', cancel_reason=$1, cancelled_at=NOW()
           WHERE status='active' RETURNING *""",
        reason
    )


async def list_history(limit=15):
    return await pool().fetch(
        "SELECT * FROM protocols ORDER BY created_at DESC LIMIT $1", limit
    )   