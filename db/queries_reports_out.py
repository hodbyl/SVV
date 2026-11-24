from db.connection import pool


async def insert_report(callsign, discord_id, rtype, text, period):
    return await pool().fetchrow(
        """INSERT INTO reports_out (author_callsign, author_discord, report_type, text, period)
           VALUES ($1,$2,$3,$4,$5) RETURNING *""",
        callsign, discord_id, rtype, text, period
    )


async def get_my_reports(callsign, limit=20):
    return await pool().fetch(
        """SELECT * FROM reports_out WHERE author_callsign=$1
           ORDER BY created_at DESC LIMIT $2""",
        callsign, limit
    )


async def get_report(rid):
    return await pool().fetchrow("SELECT * FROM reports_out WHERE id=$1", rid)


async def update_status(rid, status, reviewer, comment=None):
    return await pool().fetchrow(
        """UPDATE reports_out
           SET status=$1, reviewer_callsign=$2, reviewer_comment=$3, reviewed_at=NOW()
           WHERE id=$4 RETURNING *""",
        status, reviewer, comment, rid
    )


async def get_incoming_reports(limit=20):
    return await pool().fetch(
        """SELECT * FROM reports_out WHERE status='sent'
           ORDER BY created_at DESC LIMIT $1""",
        limit
    )


async def get_archive_reports(limit=30):
    return await pool().fetch(
        """SELECT * FROM reports_out WHERE status IN ('accepted','rejected')
           ORDER BY reviewed_at DESC LIMIT $1""",
        limit
    )