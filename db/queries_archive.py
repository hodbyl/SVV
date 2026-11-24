from db.connection import pool


async def insert_archive(doc_type, title, content, author_callsign, author_discord):
    return await pool().fetchrow(
        """INSERT INTO archive (doc_type, title, content, author_callsign, author_discord)
           VALUES ($1,$2,$3,$4,$5) RETURNING *""",
        doc_type, title, content, author_callsign, author_discord
    )


async def search_archive(query, limit=20):
    pattern = f"%{query}%"
    return await pool().fetch(
        """SELECT * FROM archive
           WHERE title ILIKE $1 OR content ILIKE $1 OR doc_type ILIKE $1
           ORDER BY created_at DESC LIMIT $2""",
        pattern, limit
    )


async def get_archive(limit=30):
    return await pool().fetch(
        "SELECT * FROM archive ORDER BY created_at DESC LIMIT $1", limit
    )


async def delete_archive(aid):
    return await pool().fetchrow(
        "DELETE FROM archive WHERE id=$1 RETURNING *", aid
    )