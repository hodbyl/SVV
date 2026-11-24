from db.connection import pool


async def insert_order(target_type, target_value, text, duration, expires_at,
                       created_by, created_by_callsign):
    return await pool().fetchrow(
        """INSERT INTO orders
           (target_type, target_value, text, duration, expires_at,
            created_by, created_by_callsign)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           RETURNING *""",
        target_type, target_value, text, duration, expires_at,
        created_by, created_by_callsign
    )


async def get_active_orders(limit: int = 20):
    return await pool().fetch(
        """SELECT * FROM orders
           WHERE status = 'active'
           ORDER BY created_at DESC
           LIMIT $1""",
        limit
    )


async def get_order_by_id(order_id: int):
    return await pool().fetchrow(
        "SELECT * FROM orders WHERE id = $1", order_id
    )


async def get_history_orders(limit: int = 20):
    return await pool().fetch(
        """SELECT * FROM orders
           WHERE status IN ('completed', 'deleted', 'expired')
           ORDER BY created_at DESC
           LIMIT $1""",
        limit
    )


async def delete_order(order_id: int):
    return await pool().fetchrow(
        """UPDATE orders SET status = 'deleted'
           WHERE id = $1 RETURNING *""",
        order_id
    )


async def mark_order_completed(order_id: int):
    await pool().execute(
        "UPDATE orders SET status = 'completed' WHERE id = $1", order_id
    )


async def mark_expired_orders():
    await pool().execute(
        """UPDATE orders SET status = 'expired'
           WHERE status = 'active' AND expires_at IS NOT NULL AND expires_at < NOW()"""
    )