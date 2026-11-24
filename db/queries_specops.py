from db.connection import pool


async def insert_specops(name, goal, department, duration, expires_at,
                         access_level, actor_callsign, actor_discord):
    return await pool().fetchrow(
        """INSERT INTO specops (name, goal, department, duration, expires_at,
                                access_level, created_by_callsign, created_by_discord)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *""",
        name, goal, department, duration, expires_at,
        access_level, actor_callsign, actor_discord
    )


async def get_specops_by_id(sid):
    return await pool().fetchrow("SELECT * FROM specops WHERE id=$1", sid)


async def get_specops_by_name(name):
    return await pool().fetchrow(
        "SELECT * FROM specops WHERE name=$1 AND status='active'", name
    )


async def list_active_specops(limit=20):
    return await pool().fetch(
        """SELECT * FROM specops WHERE status IN ('active','waiting')
           ORDER BY created_at DESC LIMIT $1""",
        limit
    )


async def add_member(specops_id, callsign, discord_id):
    return await pool().fetchrow(
        """INSERT INTO specops_members (specops_id, callsign, discord_id)
           VALUES ($1,$2,$3) RETURNING *""",
        specops_id, callsign, discord_id
    )


async def get_members(specops_id):
    return await pool().fetch(
        "SELECT * FROM specops_members WHERE specops_id=$1", specops_id
    )


async def set_status(sid, status, reason=None):
    if reason:
        return await pool().fetchrow(
            """UPDATE specops SET status=$1, cancel_reason=$2, cancelled_at=NOW()
               WHERE id=$3 RETURNING *""",
            status, reason, sid
        )
    return await pool().fetchrow(
        "UPDATE specops SET status=$1 WHERE id=$2 RETURNING *", status, sid
    )


async def add_report(sid, report_text):
    return await pool().fetchrow(
        """UPDATE specops SET report_text=$1, reported_at=NOW()
           WHERE id=$2 RETURNING *""",
        report_text, sid
    )