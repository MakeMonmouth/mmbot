#!/usr/bin/env python
# mmbot.py
import logging
import operator
import os

import aiohttp
import arrow

import humanize

logging.basicConfig(level=logging.INFO)
import discord
from discord.ext import commands
from dotenv import load_dotenv

import datetime as dt
from calendar import monthrange

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MVENTORY_URI = os.getenv('MVENTORY_URI')
MVENTORY_TLS_CHECK = os.getenv('MVENTORY_TLS_CHECK') or True

bot = commands.Bot(command_prefix='!')

def first_and_last_thursday(year, month):
    dates = [dt.date(year, month, x + 1) for x in range(monthrange(year, month)[1])]
    return [x for x in dates if x.weekday() == 3][0:3:2]

def get_next_meeting():
    date = dt.date.today()
    first, second = first_and_last_thursday(date.year, date.month)
    if date < first:
        return first
    if date < second:
        return second
    first, _ = first_and_last_thursday(date.year + (1 if date.month == 12 else 0), (date.month % 12) + 1)
    return first

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
    logging.info("Meetup routine called")
    next_mtg = get_next_meeting()
    msg = f"Our next meeting is on {dt.datetime.strftime(next_mtg, '%A, %d %B')}"
    msg = msg + f" between 8pm and 10pm at Woodland Stores, Wyesham"
    await ctx.send(msg)

@bot.command(name='findit')
async def findit(ctx, arg):
    msg = "MVentory is not configured, please export MVENTORY_URI in the mmbot environment"
    if MVENTORY_URI is not None:
        logging.info(f"Searching mventory for {arg}")
        results = {}
        results['count'] = 0
        results['items'] = {}
        search_uri = f"{MVENTORY_URI}/rest/components/?search={arg}"
        logging.info(f"Searching {search_uri}")
        async with aiohttp.ClientSession() as mv_session:
            logging.info("Session Created")
            async with mv_session.get(search_uri) as mv_response:
                if mv_response.status == 200:
                    logging.info("Reponse was fine, continuing to get details")
                    search_data = await mv_response.json()
                    results['count'] = len(search_data)
                    if results['count'] > 0:
                        logging.info(f"Found {results['count']} results")
                        msg = f"{results['count']} results found:\n\n"
                        for i in search_data:
                            logging.info(i)
                            msg = msg + f"{i['name']} was found at {i['storage_bin'][0]['name']} ( {i['storage_bin'][0]['unit_row']}, {i['storage_bin'][0]['unit_column']})\n"
                    else:
                        msg = f"No results found for {arg}"
                else:
                    msg = f"Error contacting mventory - {response.status}"

    await ctx.send(msg)

bot.run(TOKEN)
