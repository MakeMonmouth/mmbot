# MMBot

MMBot (no relation to the similar sounding song by Hanson) is the bot who helps with the management of the [Make Monmouth](https://www.makemonmouth.co.uk/) Discord Channel.

## Getting started

1. Clone this repo
2. Create a virtualenv
3. Install the requirements (`pip install -r requirements.txt`)
4. Copy `.env.example` to `.env` and update the values as appropriate
5. Run the bot (`./mmbot.py`)

## Docker

We automatically build docker containers for x86_64, ARMv6, ARMv7, and ARM64 architectures, so MMBot should run on just about any bit of kit that's lying around.

You'll need to set the following environment variables before running the container, and you'll want to make sure they are passed to the container at launch:

```
DISCORD_TOKEN="Your Discord API Token"
DISCORD_GUILD="Your Discord Guild/Server"
TENDENCI_URI="The URI of your Tendenci instance"
TENDENCI_API_KEY="The API Key for Tendenci"
TENDENCI_API_USER="The username you use to log in to tendenci"
```


