from db.connection import pool


async def insert_task(target_callsign, target_discord, department, text,
                      duration, expires_at, priority, actor_callsign, actor_discord):
    return await pool().fetchrow(
        """INSERT INTO tasks (target_callsign, target_discord, department, text,
                              duration, expires_at, priority,
                              created_by_callsign, created_by_discord)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING *""",
        target_callsign, target_discord, department, text,
        duration, expires_at, priority, actor_callsign, actor_discord
    )


async def get_my_tasks(callsign):
    return await pool().fetch(
        """SELECT * FROM tasks
           WHERE target_callsign=$1 AND status IN ('new','active')
           ORDER BY created_at DESC""",
        callsign
    )


async def get_dept_tasks(department):
    return await pool().fetch(
        """SELECT * FROM tasks
           WHERE department=$1 AND status IN ('new','active')
           ORDER BY created_at DESC""",
        department
    )


async def get_task_by_id(task_id):
    return await pool().fetchrow("SELECT * FROM tasks WHERE id=$1", task_id)


async def close_task(task_id, report):
    return await pool().fetchrow(
        """UPDATE tasks SET status='completed', close_report=$1, closed_at=NOW()
           WHERE id=$2 RETURNING *""",
        report, task_id
    )


async def mark_expired_tasks():
    await pool().execute(
        """UPDATE tasks SET status='expired'
           WHERE status IN ('new','active') AND expires_at IS NOT NULL AND expires_at < NOW()"""
    )


async def get_overdue_tasks():
    return await pool().fetch(
        """SELECT * FROM tasks WHERE status='expired'
           ORDER BY expires_at ASC LIMIT 20"""
    )