from db.connection import pool


async def upsert_global_dossier(data: dict):
    """Вставляет или обновляет досье по discord_id."""
    existing = await pool().fetchrow(
        "SELECT id FROM global_dossiers WHERE discord_id=$1",
        data["discord_id"]
    )

    if existing:
        await pool().execute(
            """UPDATE global_dossiers SET
                username=$1, display_name=$2, joined_at=$3, account_created=$4,
                roles=$5, message_count=$6, channels_scanned=$7, avg_msg_length=$8,
                caps_ratio=$9, exclaim_count=$10, swear_count=$11,
                night_activity=$12, day_activity=$13,
                aggressive_score=$14, loyalty_score=$15, activity_score=$16,
                danger_level=$17, strengths=$18, weaknesses=$19, notes=$20,
                scanned_at=NOW(), scanned_by=$21
               WHERE discord_id=$22""",
            data["username"], data["display_name"], data["joined_at"],
            data["account_created"], data["roles"], data["message_count"],
            data["channels_scanned"], data["avg_msg_length"],
            data["caps_ratio"], data["exclaim_count"], data["swear_count"],
            data["night_activity"], data["day_activity"],
            data["aggressive_score"], data["loyalty_score"],
            data["activity_score"], data["danger_level"],
            data["strengths"], data["weaknesses"], data["notes"],
            data["scanned_by"], data["discord_id"]
        )
    else:
        await pool().execute(
            """INSERT INTO global_dossiers
               (discord_id, username, display_name, joined_at, account_created,
                roles, message_count, channels_scanned, avg_msg_length,
                caps_ratio, exclaim_count, swear_count,
                night_activity, day_activity,
                aggressive_score, loyalty_score, activity_score,
                danger_level, strengths, weaknesses, notes, scanned_by)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,
                       $15,$16,$17,$18,$19,$20,$21,$22)""",
            data["discord_id"], data["username"], data["display_name"],
            data["joined_at"], data["account_created"], data["roles"],
            data["message_count"], data["channels_scanned"], data["avg_msg_length"],
            data["caps_ratio"], data["exclaim_count"], data["swear_count"],
            data["night_activity"], data["day_activity"],
            data["aggressive_score"], data["loyalty_score"],
            data["activity_score"], data["danger_level"],
            data["strengths"], data["weaknesses"], data["notes"],
            data["scanned_by"]
        )


async def get_global_dossier(discord_id: int):
    return await pool().fetchrow(
        "SELECT * FROM global_dossiers WHERE discord_id=$1", discord_id
    )


async def list_global_dossiers(limit=30):
    return await pool().fetch(
        """SELECT * FROM global_dossiers
           ORDER BY danger_level DESC, scanned_at DESC LIMIT $1""",
        limit
    )