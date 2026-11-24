from db.connection import pool


async def insert_codename(callsign, codename, expires_at, created_by):
    return await pool().fetchrow(
        """INSERT INTO codenames (target_callsign, codename, expires_at, created_by)
           VALUES ($1,$2,$3,$4) RETURNING *""",
        callsign, codename, expires_at, created_by
    )


async def get_codename(callsign):
    return await pool().fetchrow(
        "SELECT * FROM codenames WHERE target_callsign=$1 ORDER BY created_at DESC LIMIT 1",
        callsign
    )


async def update_codename(callsign, new_codename):
    return await pool().fetchrow(
        "UPDATE codenames SET codename=$1 WHERE target_callsign=$2 RETURNING *",
        new_codename, callsign
    )


async def list_codenames(limit=20):
    return await pool().fetch(
        "SELECT * FROM codenames ORDER BY created_at DESC LIMIT $1", limit
    )


async def delete_codename(codename):
    return await pool().fetchrow(
        "DELETE FROM codenames WHERE codename=$1 RETURNING *", codename
    )