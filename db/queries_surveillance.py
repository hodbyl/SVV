from db.connection import pool


async def insert_surveillance(target_id, target_name, reason, duration, expires_at,
                              actor_callsign, actor_discord):
    return await pool().fetchrow(
        """INSERT INTO surveillance (target_id, target_name, reason, duration, expires_at,
                                      actor_callsign, actor_discord)
           VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *""",
        target_id, target_name, reason, duration, expires_at,
        actor_callsign, actor_discord
    )


async def get_active_surveillance(limit=20):
    return await pool().fetch(
        """SELECT * FROM surveillance WHERE status='active'
           ORDER BY created_at DESC LIMIT $1""",
        limit
    )


async def get_surveillance_by_id(sid):
    return await pool().fetchrow("SELECT * FROM surveillance WHERE id=$1", sid)


async def get_surveillance_by_target(target_id):
    return await pool().fetchrow(
        """SELECT * FROM surveillance WHERE target_id=$1 AND status='active'
           ORDER BY created_at DESC LIMIT 1""",
        target_id
    )


async def stop_surveillance(sid):
    return await pool().fetchrow(
        """UPDATE surveillance SET status='stopped', stopped_at=NOW()
           WHERE id=$1 RETURNING *""",
        sid
    )


async def add_surv_report(sid, text, actor_callsign):
    return await pool().fetchrow(
        """INSERT INTO surveillance_reports (surveillance_id, text, actor_callsign)
           VALUES ($1,$2,$3) RETURNING *""",
        sid, text, actor_callsign
    )


async def get_surv_reports(sid):
    return await pool().fetch(
        """SELECT * FROM surveillance_reports WHERE surveillance_id=$1
           ORDER BY created_at DESC""",
        sid
    )