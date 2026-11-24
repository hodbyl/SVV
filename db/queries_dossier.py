from db.connection import pool


async def insert_dossier(callsign, rank, department, notes, created_by):
    return await pool().fetchrow(
        """INSERT INTO dossiers (callsign, rank, department, notes, created_by)
           VALUES ($1,$2,$3,$4,$5) RETURNING *""",
        callsign, rank, department, notes, created_by
    )


async def get_dossier(callsign):
    return await pool().fetchrow(
        "SELECT * FROM dossiers WHERE callsign=$1", callsign
    )


async def update_field(callsign, field, value, updated_by):
    allowed = {"rank", "department", "status", "violations",
               "awards", "connections", "notes"}
    if field not in allowed:
        return None
    return await pool().fetchrow(
        f"""UPDATE dossiers SET {field}=$1, updated_by=$2, updated_at=NOW()
            WHERE callsign=$3 RETURNING *""",
        value, updated_by, callsign
    )


async def delete_dossier(callsign):
    return await pool().fetchrow(
        "DELETE FROM dossiers WHERE callsign=$1 RETURNING *", callsign
    )


async def search_dossiers(query, limit=20):
    pattern = f"%{query}%"
    return await pool().fetch(
        """SELECT * FROM dossiers
           WHERE callsign ILIKE $1 OR notes ILIKE $1 OR department ILIKE $1
           ORDER BY updated_at DESC LIMIT $2""",
        pattern, limit
    )


async def list_all_dossiers(limit=50):
    return await pool().fetch(
        "SELECT * FROM dossiers ORDER BY updated_at DESC LIMIT $1", limit
    )