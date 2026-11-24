from db.connection import pool


# ==================== ИГРОК ====================
async def get_player_stats(callsign):
    """Возвращает словарь со всеми метриками по игроку."""
    acc = await pool().fetchrow(
        "SELECT * FROM accounts WHERE callsign=$1", callsign
    )
    if not acc:
        return None

    pun = await pool().fetch(
        "SELECT punish_type, COUNT(*) AS cnt FROM punishments WHERE target_callsign=$1 AND active=TRUE GROUP BY punish_type",
        callsign
    )
    punish_count = {row["punish_type"]: row["cnt"] for row in pun}

    orders_cnt = await pool().fetchval(
        "SELECT COUNT(*) FROM orders WHERE created_by_callsign=$1", callsign
    ) or 0

    tasks_created = await pool().fetchval(
        "SELECT COUNT(*) FROM tasks WHERE target_callsign=$1", callsign
    ) or 0
    tasks_done = await pool().fetchval(
        "SELECT COUNT(*) FROM tasks WHERE target_callsign=$1 AND status='completed'", callsign
    ) or 0
    tasks_overdue = await pool().fetchval(
        "SELECT COUNT(*) FROM tasks WHERE target_callsign=$1 AND status='expired'", callsign
    ) or 0

    reports_sent = await pool().fetchval(
        "SELECT COUNT(*) FROM reports_in WHERE author_callsign=$1", callsign
    ) or 0
    reports_ok = await pool().fetchval(
        "SELECT COUNT(*) FROM reports_in WHERE author_callsign=$1 AND status='accepted'", callsign
    ) or 0
    reports_no = await pool().fetchval(
        "SELECT COUNT(*) FROM reports_in WHERE author_callsign=$1 AND status='rejected'", callsign
    ) or 0

    promote = await pool().fetchval(
        "SELECT COUNT(*) FROM rank_history WHERE target_callsign=$1 AND new_rank > old_rank", callsign
    ) or 0
    demote = await pool().fetchval(
        "SELECT COUNT(*) FROM rank_history WHERE target_callsign=$1 AND new_rank < old_rank", callsign
    ) or 0

    last_log = await pool().fetchval(
        "SELECT MAX(created_at) FROM logs WHERE actor_discord = $1",
        acc["created_by"] if acc["created_by"] else 0
    )

    return {
        "account": acc,
        "punish": punish_count,
        "orders": orders_cnt,
        "tasks_created": tasks_created,
        "tasks_done": tasks_done,
        "tasks_overdue": tasks_overdue,
        "reports_sent": reports_sent,
        "reports_ok": reports_ok,
        "reports_no": reports_no,
        "promote": promote,
        "demote": demote,
        "last_log": last_log,
    }


# ==================== ОТДЕЛ ====================
async def get_department_stats(department):
    """Собирает статистику по отделу из досье + наказаний."""
    dossiers = await pool().fetch(
        "SELECT callsign FROM dossiers WHERE department=$1", department
    )
    callsigns = [d["callsign"] for d in dossiers]

    if not callsigns:
        return {"members": 0, "avg_rank": 0, "punish_total": 0,
                "active_orders": 0, "active_tasks": 0,
                "departed": 0}

    avg_rank = await pool().fetchval(
        "SELECT AVG(rank) FROM dossiers WHERE department=$1", department
    ) or 0

    punish_total = await pool().fetchval(
        "SELECT COUNT(*) FROM punishments WHERE target_callsign = ANY($1) AND active=TRUE",
        callsigns
    ) or 0

    active_orders = await pool().fetchval(
        """SELECT COUNT(*) FROM orders
           WHERE status='active' AND target_type='Отдел' AND target_value=$1""",
        department
    ) or 0

    active_tasks = await pool().fetchval(
        "SELECT COUNT(*) FROM tasks WHERE department=$1 AND status IN ('new','active')",
        department
    ) or 0

    return {
        "members": len(callsigns),
        "avg_rank": round(float(avg_rank), 2),
        "punish_total": punish_total,
        "active_orders": active_orders,
        "active_tasks": active_tasks,
    }


# ==================== ОБЩАЯ ====================
async def get_overall_stats():
    """Общая статистика по системе."""
    accounts = await pool().fetchval("SELECT COUNT(*) FROM accounts") or 0
    blocked = await pool().fetchval("SELECT COUNT(*) FROM accounts WHERE is_blocked=TRUE") or 0
    orders_active = await pool().fetchval("SELECT COUNT(*) FROM orders WHERE status='active'") or 0
    tasks_active = await pool().fetchval("SELECT COUNT(*) FROM tasks WHERE status IN ('new','active')") or 0
    punish_active = await pool().fetchval("SELECT COUNT(*) FROM punishments WHERE active=TRUE") or 0
    dossiers_cnt = await pool().fetchval("SELECT COUNT(*) FROM dossiers") or 0
    return {
        "accounts": accounts,
        "blocked": blocked,
        "orders_active": orders_active,
        "tasks_active": tasks_active,
        "punish_active": punish_active,
        "dossiers": dossiers_cnt,
    }