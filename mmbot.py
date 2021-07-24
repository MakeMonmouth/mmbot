#!/usr/bin/env python
# mmbot.py
import logging
import operator
import os

import aiohttp
import arrow

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
    logging.info("Meetup routine called")

    async with aiohttp.ClientSession(headers=tendenci_headers) as session:
        logging.info("Session Created")
        async with session.get(meeting_uri) as response:
            if response.status == 200:
                logging.info("Request to Tendenci was successful")
                logging.info("Processing the JSON document")
                meetings = await response.json()
                logging.info("JSON Document has been processed")
                # 2021-09-17T19:30:00+00:00
                meeting_list = meetings['objects']
                meeting_list.sort(key = operator.itemgetter('start_dt'))
                for meeting in meeting_list:
                    logging.info("Processing meeting")
                    logging.info(meeting)
                    if meeting['title'] == "Weekly Meetup!":
                        logging.info("Meetup found")
                        start_date =arrow.get( meeting['start_dt'])
                        end_date =arrow.get( meeting['end_dt'])
                        venue_name = "Woolly Monmouth"
                        event_url = f"{os.getenv('TENDENCI_URI')}/events/{meeting['id']}/"
                        logging.info("Creating message")
                        msg = f"Our next meetup is {start_date.humanize()} "
                        msg += f"from now, on {start_date.day}/{start_date.month}/{start_date.year} "
                        msg += f"from {start_date.hour}:{start_date.minute} until {end_date.hour}:{end_date.minute}. "
                        msg += f"We'll be at {venue_name}, and you can find more details about how to get there at {event_url}"
                        logging.info(msg)
                        break
                    else:
                        msg = "Sorry, no upcoming meetups right now :("
            else:
                logging.info(f"Request to Tendenci failed, status code was {response.status}")
                msg = "Sorry, I can't retrieve details of our next meeting right now :("

            await ctx.send(msg)


bot.run(TOKEN)
