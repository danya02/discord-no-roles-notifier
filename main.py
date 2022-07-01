import discord
from discord.ext import commands, tasks
import os
import time

import logging
logging.basicConfig(level=logging.DEBUG)

import json

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='?', intents=intents)

def get_config():
    with open('/config.json', 'r') as f:
        return json.load(f)

LAST_UPDATE = 0
TIMER_MESSAGE = None
LAST_TIMER_UPDATE = 0

@tasks.loop(seconds=1, reconnect=True)
async def check_status():
    global LAST_UPDATE
    global LAST_TIMER_UPDATE
    global TIMER_MESSAGE
    config = get_config()
    if time.time() - LAST_UPDATE > config['update_interval']:
        TIMER_MESSAGE = await run_update(config)
        LAST_UPDATE = time.time()
    elif time.time() - LAST_TIMER_UPDATE > config['refresh_interval']:
        await update_timer(config, TIMER_MESSAGE)
        await update_channel_permissions(bot.get_channel(config['channel_id']))
        LAST_TIMER_UPDATE = time.time()
        



async def run_update(config):
    # Wipe the notification channel.
    channel: discord.TextChannel = bot.get_channel(config['channel_id'])
    await channel.purge()

    guild: discord.Guild = channel.guild

    # Get list of members without roles.
    members = [member for member in guild.members if len(member.roles) == 1]

    if members:
        # Send the pre-list message.
        await channel.send(config['text_pre'])

        # Send the list of members.
        for member in members:
            await channel.send(member.mention, allowed_mentions=discord.AllowedMentions(everyone=False, users=True))
        
        # Send the post-list message.
        await channel.send(config['text_post'])

    # Send the timer message
    return await channel.send(config['text_time_until_update'].format(f'{config["update_interval"]} seconds'))


async def update_timer(config, message):
    try:
        remaining_time = config['update_interval'] - (time.time() - LAST_UPDATE)
        hour, minute = divmod(remaining_time, 3600)
        hour = int(hour)
        minute = int(minute)
        minute, second = divmod(minute, 60)
        minute = int(minute)
        second = int(second)
        if message is None:
            raise Exception
        await message.edit(content=config['text_time_until_update'].format(f'{hour}:{minute:02d}:{second:02d}'))
    except Exception as e:
        logging.error(e)
        pass

async def update_channel_permissions(channel: discord.TextChannel):
    for role in channel.guild.roles:
        if channel.overwrites.get(role):
            overwrite = channel.overwrites[role]
        else:
            overwrite = discord.PermissionOverwrite()
        if role.is_default():
            # This is the everyone role
            if overwrite.view_channel:
                continue
            elif overwrite.view_channel is None or overwrite.view_channel is False:
                await channel.set_permissions(role, view_channel=True, reason="Everyone must be able to see this channel.")
        else:
            # This is a regular role
            if overwrite.view_channel or overwrite.view_channel is None:
                await channel.set_permissions(role, view_channel=False, reason="This role must not be able to see this channel.")
            elif overwrite.view_channel is False:
                continue

                    

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name}')
    check_status.start()

bot.run(TOKEN)
