#!/usr/bin/env python
# mmbot.py
import logging
import os

import aiohttp

logging.basicConfig(level=logging.INFO)
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')
api_creds = {
        "user": os.getenv('TENDENCI_API_USER'),
        "key": os.getenv('TENDENCI_API_KEY')
        }
meeting_uri = f"{os.getenv('TENDENCI_URI')}/api_tasty/v1/event/?format=json"
tendenci_headers = {"Authorization": f" ApiKey {api_creds['user']}:{api_creds['key']}"}

@bot.command(name='create-channel')
@commands.has_role('@admin')
async def create_channel(ctx, channel_name='real-python'):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        logging.info(f'Creating a new channel: {channel_name}')
        await guild.create_text_channel(channel_name)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

@bot.command(name='meetup')
async def meetup(ctx):

    async with aiohttp.ClientSession(headers=tendenci_headers) as session:
        async with session.get(meeting_uri) as response:

            meetings = await response.json()
            for meeting in meetings['objects']:
                logging.info(meeting)


bot.run(TOKEN)
