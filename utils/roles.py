import discord
from config import GUILD_ID, STAFF_ROLES, DEPARTMENTS


async def get_members_by_role(bot, role_id: int):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return []
    role = guild.get_role(role_id)
    if not role:
        return []
    return [m for m in role.members if not m.bot]


async def get_department_members(bot, dept_name: str):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return []
    dept_upper = dept_name.upper()
    result = set()
    for role in guild.roles:
        role_name = role.name.upper()
        if dept_upper in role_name:
            for m in role.members:
                if not m.bot:
                    result.add(m)
    return list(result)


async def get_members_by_rank(bot, rank: int):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return []
    role_id = STAFF_ROLES.get(rank)
    if not role_id:
        return []
    role = guild.get_role(role_id)
    if not role:
        return []
    return [m for m in role.members if not m.bot]


async def get_members_by_rank_range(bot, rank_min: int = 1, rank_max: int = 8):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return []
    result = set()
    for r in range(rank_min, rank_max + 1):
        role_id = STAFF_ROLES.get(r)
        if not role_id:
            continue
        role = guild.get_role(role_id)
        if role:
            for m in role.members:
                if not m.bot:
                    result.add(m)
    return list(result)


async def get_all_staff(bot):
    return await get_members_by_rank_range(bot, 1, 8)


async def get_all_server_members(bot):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return []
    return [m for m in guild.members if not m.bot]
    

async def get_department_stats_from_discord(bot, dept_name: str):
    """Возвращает статистику отдела напрямую из Discord-ролей."""
    from config import GUILD_ID, DEPARTMENT_ROLES

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return {"members": 0, "leaders": 0, "high": 0, "regular": 0, "names": []}

    role_ids = DEPARTMENT_ROLES.get(dept_name.upper(), [])
    if not role_ids:
        return {"members": 0, "leaders": 0, "high": 0, "regular": 0, "names": []}

    leader_id, high_id, regular_id = role_ids

    leader_role = guild.get_role(leader_id)
    high_role = guild.get_role(high_id)
    regular_role = guild.get_role(regular_id)

    leaders = set()
    highs = set()
    regulars = set()

    if leader_role:
        for m in leader_role.members:
            if not m.bot:
                leaders.add(m)
    if high_role:
        for m in high_role.members:
            if not m.bot:
                highs.add(m)
    if regular_role:
        for m in regular_role.members:
            if not m.bot:
                regulars.add(m)

    # Убираем дубли: лидер и high не считаются в regular
    highs -= leaders
    regulars -= leaders
    regulars -= highs

    all_members = leaders | highs | regulars

    return {
        "members": len(all_members),
        "leaders": len(leaders),
        "high": len(highs),
        "regular": len(regulars),
        "names": [m.display_name for m in all_members],
    }