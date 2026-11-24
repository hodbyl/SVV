from db.connection import pool


async def insert_report(author_callsign, author_discord, report_type, text):
    return await pool().fetchrow(
        """INSERT INTO reports_in (author_callsign, author_discord, report_type, text)
           VALUES ($1,$2,$3,$4) RETURNING *""",
        author_callsign, author_discord, report_type, text
    )


async def get_my_reports(callsign, limit=20):
    return await pool().fetch(
        """SELECT * FROM reports_in WHERE author_callsign=$1
           ORDER BY created_at DESC LIMIT $2""",
        callsign, limit
    )


async def get_incoming_reports(limit=30):
    return await pool().fetch(
        """SELECT * FROM reports_in WHERE status='pending'
           ORDER BY created_at DESC LIMIT $1""",
        limit
    )


async def get_report_by_id(rid):
    return await pool().fetchrow("SELECT * FROM reports_in WHERE id=$1", rid)


async def review_report(rid, status, comment, reviewer_callsign):
    return await pool().fetchrow(
        """UPDATE reports_in
           SET status=$1, reviewer_comment=$2, reviewer_callsign=$3, reviewed_at=NOW()
           WHERE id=$4 RETURNING *""",
        status, comment, reviewer_callsign, rid
    )


async def get_archive_reports(limit=30):
    return await pool().fetch(
        """SELECT * FROM reports_in WHERE status IN ('accepted','rejected')
           ORDER BY reviewed_at DESC LIMIT $1""",
        limit
    )   