from db.connection import pool


async def insert_order(target, target_discord, reason, evidence,
                       actor_callsign, actor_discord):
    return await pool().fetchrow(
        """INSERT INTO liquidation_orders
           (target, target_discord, reason, evidence,
            created_by_callsign, created_by_discord, status)
           VALUES ($1,$2,$3,$4,$5,$6,'pending') RETURNING *""",
        target, target_discord, reason, evidence, actor_callsign, actor_discord
    )


async def confirm_order(order_id, confirmed_by):
    return await pool().fetchrow(
        """UPDATE liquidation_orders
           SET status='confirmed', confirmed_by_callsign=$1, confirmed_at=NOW()
           WHERE id=$2 RETURNING *""",
        confirmed_by, order_id
    )


async def assign_executor(order_id, executor_callsign, executor_discord):
    return await pool().fetchrow(
        """UPDATE liquidation_orders
           SET executor_callsign=$1, executor_discord=$2,
               status='assigned', assigned_at=NOW()
           WHERE id=$3 RETURNING *""",
        executor_callsign, executor_discord, order_id
    )


async def complete_order(order_id, result):
    return await pool().fetchrow(
        """UPDATE liquidation_orders
           SET status='completed', result=$1, completed_at=NOW()
           WHERE id=$2 RETURNING *""",
        result, order_id
    )


async def get_order(order_id):
    return await pool().fetchrow(
        "SELECT * FROM liquidation_orders WHERE id=$1", order_id
    )


async def list_orders(limit=20):
    return await pool().fetch(
        """SELECT * FROM liquidation_orders
           ORDER BY created_at DESC LIMIT $1""",
        limit
    )


async def list_active(limit=20):
    return await pool().fetch(
        """SELECT * FROM liquidation_orders
           WHERE status IN ('pending','confirmed','assigned')
           ORDER BY created_at DESC LIMIT $1""",
        limit
    )