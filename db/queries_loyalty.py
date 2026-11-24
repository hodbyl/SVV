import json
from db.connection import pool


async def insert_check(target_callsign, target_discord, level,
                       questions, actor_callsign, actor_discord):
    return await pool().fetchrow(
        """INSERT INTO loyalty_checks
           (target_callsign, target_discord, level, questions,
            actor_callsign, actor_discord, status)
           VALUES ($1,$2,$3,$4,$5,$6,'started') RETURNING *""",
        target_callsign, target_discord, level,
        json.dumps(questions), actor_callsign, actor_discord
    )


async def save_answers(check_id, answers, score, verdict):
    return await pool().fetchrow(
        """UPDATE loyalty_checks
           SET answers=$1, score=$2, verdict=$3, status='finished', finished_at=NOW()
           WHERE id=$4 RETURNING *""",
        json.dumps(answers), score, verdict, check_id
    )


async def get_check(check_id):
    return await pool().fetchrow(
        "SELECT * FROM loyalty_checks WHERE id=$1", check_id
    )


async def get_checks_by_target(callsign, limit=10):
    return await pool().fetch(
        """SELECT * FROM loyalty_checks WHERE target_callsign=$1
           ORDER BY created_at DESC LIMIT $2""",
        callsign, limit
    )


async def list_checks(limit=20):
    return await pool().fetch(
        "SELECT * FROM loyalty_checks ORDER BY created_at DESC LIMIT $1",
        limit
    )


async def dispute_check(check_id, reason):
    return await pool().fetchrow(
        """UPDATE loyalty_checks
           SET dispute_reason=$1, disputed_at=NOW()
           WHERE id=$2 RETURNING *""",
        reason, check_id
    )