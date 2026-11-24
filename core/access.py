import discord
from config import GUILD_ID, STAFF_ROLES


def get_staff_rank(member: discord.Member) -> int:
    """Возвращает максимальный ранг Staff по ролям Discord. 0 если нет ролей."""
    if member is None:
        return 0
    member_role_ids = {r.id for r in member.roles}
    for rank in sorted(STAFF_ROLES.keys(), reverse=True):
        if STAFF_ROLES[rank] in member_role_ids:
            return rank
    return 0


async def fetch_guild_member(bot, discord_id: int):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return None
    try:
        return await guild.fetch_member(discord_id)
    except discord.NotFound:
        return None
    except discord.HTTPException:
        return None