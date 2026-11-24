from db.connection import pool


async def add_punishment(target_callsign, target_discord_id, punish_type,
                         reason, actor_discord, actor_callsign, evidence=None):
    return await pool().fetchrow(
        """INSERT INTO punishments
           (target_callsign, target_discord_id, punish_type, reason,
            evidence, actor_discord, actor_callsign)
           VALUES ($1,$2,$3,$4,$5,$6,$7)
           RETURNING *""",
        target_callsign, target_discord_id, punish_type, reason,
        evidence, actor_discord, actor_callsign
    )


async def count_active_warnings(callsign):
    return await pool().fetchval(
        """SELECT COUNT(*) FROM punishments
           WHERE target_callsign=$1 AND punish_type='предупреждение' AND active=TRUE""",
        callsign
    )


async def count_active_rebukes(callsign):
    return await pool().fetchval(
        """SELECT COUNT(*) FROM punishments
           WHERE target_callsign=$1 AND punish_type='выговор' AND active=TRUE""",
        callsign
    )


async def list_punishments(limit=50):
    return await pool().fetch(
        "SELECT * FROM punishments ORDER BY created_at DESC LIMIT $1",
        limit
    )


async def add_rank_history(callsign, discord_id, old_rank, new_rank,
                           reason, actor_callsign):
    return await pool().fetchrow(
        """INSERT INTO rank_history
           (target_callsign, target_discord_id, old_rank, new_rank,
            reason, actor_callsign)
           VALUES ($1,$2,$3,$4,$5,$6)
           RETURNING *""",
        callsign, discord_id, old_rank, new_rank, reason, actor_callsign
    )


async def list_rank_history(limit=50):
    return await pool().fetch(
        "SELECT * FROM rank_history ORDER BY created_at DESC LIMIT $1",
        limit
    )


async def update_account_rank_by_callsign(callsign, new_rank):
    return await pool().fetchrow(
        "UPDATE accounts SET rank=$1 WHERE callsign=$2 RETURNING *",
        new_rank, callsign
    )


async def get_account_by_callsign(callsign):
    return await pool().fetchrow(
        "SELECT * FROM accounts WHERE callsign=$1", callsign
    )


async def block_account_by_callsign(callsign, reason):
    return await pool().fetchrow(
        """UPDATE accounts SET is_blocked=TRUE, block_reason=$1
           WHERE callsign=$2 RETURNING *""",
        reason, callsign
    )