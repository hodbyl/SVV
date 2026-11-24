from db.connection import pool


async def insert_analytics(report_type, target, period, text, actor_callsign, actor_discord):
    return await pool().fetchrow(
        """INSERT INTO analytics_reports (report_type, target, period, text,
                                          actor_callsign, actor_discord)
           VALUES ($1,$2,$3,$4,$5,$6) RETURNING *""",
        report_type, target, period, text, actor_callsign, actor_discord
    )


async def list_analytics(limit=20):
    return await pool().fetch(
        """SELECT * FROM analytics_reports ORDER BY created_at DESC LIMIT $1""",
        limit
    )


async def get_analytics(rid):
    return await pool().fetchrow(
        "SELECT * FROM analytics_reports WHERE id=$1", rid
    )