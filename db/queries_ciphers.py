from db.connection import pool


async def insert_cipher(cipher_type, original, encrypted, key, author):
    return await pool().fetchrow(
        """INSERT INTO ciphers (cipher_type, original_text, encrypted_text, cipher_key, author_callsign)
           VALUES ($1,$2,$3,$4,$5) RETURNING *""",
        cipher_type, original, encrypted, key, author
    )


async def list_ciphers(limit=20):
    return await pool().fetch(
        "SELECT * FROM ciphers ORDER BY created_at DESC LIMIT $1", limit
    )


async def delete_cipher(cid):
    return await pool().fetchrow(
        "DELETE FROM ciphers WHERE id=$1 RETURNING *", cid
    )