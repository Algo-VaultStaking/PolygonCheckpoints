import json
import urllib.request
from logger import log

from discord.ext import commands, tasks

import secrets
from checkpoint_db import get_latest_saved_checkpoint, get_last_validator_checkpoint, \
    update_validator_checkpoint, get_val_name_from_id, get_val_contacts_from_id, set_new_checkpoint, send_email
from logger import log

token = secrets.DISCORD_TOKEN
bot = commands.Bot(command_prefix='$')


@bot.event
async def on_ready():
    log(f'Logged in as {bot.user} (ID: {bot.user.id})')
    log('-----------------')

@bot.command(name='status', help='usage: faucet-send  [address] [tokens')
async def status(ctx):
    await ctx.send("still alive")

@tasks.loop(minutes = 1)
async def check_latest_checkpoint():
    log('Checking for new checkpoint')

    trusted_validators = [1, 2, 3, 4, 5, 12, 13, 15, 32, 37, 97, 123]
    estimated_checkpoints = []

    for index in trusted_validators:
        contents = urllib.request.urlopen(
            "https://sentinel.matic.network/api/v2/validators/" + str(index) + "/checkpoints-signed").read()
        estimated_checkpoints.append(json.loads(contents)["result"][0]["checkpointNumber"])

    latest_checkpoint = max(estimated_checkpoints)
    saved_checkpoint = get_latest_saved_checkpoint()

    #if there is a new checkpoint we haven't evaluated yet
    if latest_checkpoint > saved_checkpoint:
        log("New Checkpoint")
        await get_new_checkpoint(latest_checkpoint)
        return True
    else:
        log("No new Checkpoint")
        return False

async def get_new_checkpoint(latest_checkpoint: int):
    await bot.wait_until_ready()
    channel = bot.get_channel(id=secrets.MISSED_CHECKPOINTS_CHANNEL)
    notify_missed_cp = [3, 6, 10, 20, 35, 50, 100, 200]

    set_new_checkpoint(str(latest_checkpoint))
    for i in range(1, secrets.total_validators + 1):
        contents = urllib.request.urlopen(
            "https://sentinel.matic.network/api/v2/validators/" + str(i) + "/checkpoints-signed").read()
        try:
            validator_checkpoint = int(json.loads(contents)["result"][0]["checkpointNumber"])

            # notify me
            if i == 37:
                if latest_checkpoint != validator_checkpoint or latest_checkpoint % 1 == 0:
                    send_email(latest_checkpoint, validator_checkpoint)

            # notify if a validator missed a checkpoint
            if (latest_checkpoint - validator_checkpoint) in notify_missed_cp:
                await channel.send(get_val_contacts_from_id(str(i)) + ", please check **" + get_val_name_from_id(str(i)) + "**, " \
                                      "it has missed the last " + str((latest_checkpoint - validator_checkpoint)) + " checkpoints.")

            # check if the validator is back in sync
            elif (latest_checkpoint - validator_checkpoint) == 0 and get_last_validator_checkpoint(str(i)) != latest_checkpoint-1:
                await channel.send(get_val_contacts_from_id(str(i)) + ", " + get_val_name_from_id(str(i)) + " is back in sync.")

            # save validator's latest checkpoint
            update_validator_checkpoint(str(i), str(validator_checkpoint))

        except Exception as e:
            log(e)
    log("done")


check_latest_checkpoint.start()
bot.run(token)
