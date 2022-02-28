import json
import urllib.request
from logger import raw_audit_log, log

import discord
from discord.ext import commands, tasks

import secrets
from checkpoint_db import get_latest_saved_checkpoint, get_last_validator_checkpoint, \
    update_validator_checkpoint, set_new_checkpoint, send_email
from validator_db import get_val_name_from_id, get_val_contacts_from_id, get_val_uptime_from_id, \
    get_val_missed_latest_checkpoint_from_id, get_val_commission_percent_from_id, get_val_self_stake_from_id, \
    get_val_delegated_stake_from_id, set_val_contacts_from_id, update_validator_data

token = secrets.DISCORD_TOKEN
bot = commands.Bot(command_prefix='$')


@bot.event
async def on_ready():
    raw_audit_log(f'Logged in as {bot.user} (ID: {bot.user.id})')
    raw_audit_log('-----------------')
    print("ready")


@tasks.loop(minutes = 1)
async def update_validator_details():
    await bot.wait_until_ready()
    print("updating validators")
    checkpoint_channel = bot.get_channel(id=secrets.MISSED_CHECKPOINTS_CHANNEL)
    for i in range(1, secrets.total_validators):
        try:
            message = update_validator_data(str(i))
            raw_audit_log(message)
            await checkpoint_channel.send(message)
        except:
            pass
    return

update_validator_details.start()
bot.run(token)
