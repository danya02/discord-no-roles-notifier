import discord
from discord.ext import commands, tasks
import os
import time

import logging
logging.basicConfig(level=logging.DEBUG)

import json

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
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
    config = get_config()
    if time.time() - LAST_UPDATE > config['update_interval']:
        TIMER_MESSAGE = await run_update(config)
        LAST_UPDATE = time.time()
    if time.time() - LAST_TIMER_UPDATE > config['timer_interval']:
        await update_timer(config, TIMER_MESSAGE)
        LAST_TIMER_UPDATE = time.time()



async def run_update(config):
    # Wipe the notification channel.
    channel: discord.TextChannel = bot.get_channel(config['notification_channel'])
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
    return await channel.send(config['timer_message'].format(f'{config["update_interval"]} seconds'))


async def update_timer(config, message):
    try:
        remaining_time = config['update_interval'] - (time.time() - LAST_UPDATE)
        hour, minute = divmod(remaining_time, 60)
        minute, second = divmod(minute, 60)
        second = int(second)
        if message is None:
            raise Exception
        await message.edit(content=config['timer_message'].format(f'{hour}:{minute:02d}:{second:02d}'))
    except Exception as e:
        logging.error(e)
        pass

bot.run(TOKEN)
