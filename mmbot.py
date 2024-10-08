#!/usr/bin/env python
# mmbot.py
import logging
import logging.handlers
import operator
import os

import aiohttp
import arrow

import humanize
from dotenv import load_dotenv
load_dotenv()

import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from prometheus_client import start_http_server, Summary, Counter
import time

meetup_counter = Counter(
        'meetup_details',
        'The number of times we have been asked for the next meetup date'
        )

component_lookup_counter = Counter(
        'component_lookups',
        'The number of times we have been asked to lookup a component'
        )


class CustomHttpHandler(logging.Handler):
    def __init__(self, url: str, token: str, silent: bool = True):
        '''
        Initializes the custom http handler
        Parameters:
            url (str): The URL that the logs will be sent to
            token (str): The Authorization token being used
            silent (bool): If False the http response and logs will be sent 
                           to STDOUT for debug
        '''
        self.url = url
        self.token = token
        self.silent = silent

        # sets up a session with the server
        self.MAX_POOLSIZE = 100
        self.session = session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % (self.token)
        })
        self.session.mount('https://', HTTPAdapter(
            max_retries=Retry(
                total=5,
                backoff_factor=0.5,
                status_forcelist=[403, 500]
            ),
            pool_connections=self.MAX_POOLSIZE,
            pool_maxsize=self.MAX_POOLSIZE
        ))

        super().__init__()

    def emit(self, record):
        '''
        This function gets called when a log event gets emitted. It recieves a
        record, formats it and sends it to the url
        Parameters:
            record: a log record
        '''
        logEntry = self.format(record)
        response = self.session.post(self.url, data=logEntry)

        if not self.silent:
            print(logEntry)
            print(response.content)


# create formatter - this formats the log messages accordingly
formatter = logging.Formatter(json.dumps({
    'time': '%(asctime)s',
    'pathname': '%(pathname)s',
    'line': '%(lineno)d',
    'logLevel': '%(levelname)s',
    'message': '%(message)s'
}))

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger("mmbot")

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

logger.addHandler(ch)

logger.info(f"Setup logging handlers")


import discord

intents = discord.Intents.default()
intents.message_content = True


from discord.ext import commands

import datetime as dt
from calendar import monthrange


TOKEN = os.getenv('DISCORD_TOKEN')
MVENTORY_URI = os.getenv('MVENTORY_URI')
MVENTORY_TLS_CHECK = os.getenv('MVENTORY_TLS_CHECK') or True

bot = commands.Bot(command_prefix='!', intents=intents)

def first_and_third_tuesday(year, month):
    dates = [dt.date(year, month, x + 1) for x in range(monthrange(year, month)[1])]
    return [x for x in dates if x.weekday() == 1][0:3:2]

def get_next_meeting():
    date = dt.date.today()
    first, second = first_and_third_tuesday(date.year, date.month)
    if date < first:
        return first
    if date < second:
        return second
    first, _ = first_and_third_tuesday(date.year + (1 if date.month == 12 else 0), (date.month % 12) + 1)
    return first

@bot.command(name='create-channel')
@commands.has_role('@admin')
async def create_channel(ctx, channel_name='real-python'):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        logger.info(f'Creating a new channel: {channel_name}')
        await guild.create_text_channel(channel_name)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

# Decorate function with metric.
@bot.command(name='meetup')
async def meetup(ctx):
    meetup_counter.inc()
    logger.info("Meetup routine called")
    next_mtg = get_next_meeting()
    msg = f"Our next meeting is on {dt.datetime.strftime(next_mtg, '%A, %d %B')}"
    msg = msg + f" between 7pm and 9pm at Woodland Stores, Wyesham"
    await ctx.send(msg)

@bot.command(name='findit')
async def findit(ctx, arg):
    component_lookup_counter.inc()
    msg = "MVentory is not configured, please export MVENTORY_URI in the mmbot environment"
    if MVENTORY_URI is not None:
        logger.info(f"Searching mventory for {arg}")
        results = {}
        results['count'] = 0
        results['items'] = {}
        search_uri = f"{MVENTORY_URI}/rest/components/?search={arg}"
        logger.info(f"Searching {search_uri}")
        async with aiohttp.ClientSession() as mv_session:
            logger.info("Session Created")
            async with mv_session.get(search_uri) as mv_response:
                if mv_response.status == 200:
                    logger.info("Reponse was fine, continuing to get details")
                    search_data = await mv_response.json()
                    results['count'] = len(search_data)
                    if results['count'] > 0:
                        logger.info(f"Found {results['count']} results")
                        msg = f"{results['count']} results found:\n\n"
                        for i in search_data:
                            logger.info(i)
                            msg = msg + f"{i['name']} was found at {i['storage_bin'][0]['name']} ( {i['storage_bin'][0]['unit_row']}, {i['storage_bin'][0]['unit_column']})\n"
                    else:
                        msg = f"No results found for {arg}"
                else:
                    msg = f"Error contacting mventory - {response.status}"

    await ctx.send(msg)

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(int(os.getenv("PORT")))
    bot.run(TOKEN)
