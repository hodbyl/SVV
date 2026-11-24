from db.connection import pool


async def insert_forecast(forecast_type, target, scenario, probability,
                          duration, expires_at, actor_callsign, actor_discord):
    return await pool().fetchrow(
        """INSERT INTO forecasts (forecast_type, target, scenario, probability,
                                  duration, expires_at, actor_callsign, actor_discord)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *""",
        forecast_type, target, scenario, probability,
        duration, expires_at, actor_callsign, actor_discord
    )


async def list_forecasts(limit=20):
    return await pool().fetch(
        "SELECT * FROM forecasts ORDER BY created_at DESC LIMIT $1", limit
    )


async def list_forecasts_by_type(ftype, limit=20):
    return await pool().fetch(
        """SELECT * FROM forecasts WHERE forecast_type=$1
           ORDER BY created_at DESC LIMIT $2""",
        ftype, limit
    )