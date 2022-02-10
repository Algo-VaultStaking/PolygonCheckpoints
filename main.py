import json
import urllib.request
from logger import raw_audit_log

from discord.ext import commands, tasks

import secrets
from checkpoint_db import get_latest_saved_checkpoint, get_last_validator_checkpoint, \
    update_validator_checkpoint, get_val_name_from_id, get_val_contacts_from_id, set_new_checkpoint, send_email


token = secrets.DISCORD_TOKEN
bot = commands.Bot(command_prefix='$')


@bot.event
async def on_ready():
    raw_audit_log(f'Logged in as {bot.user} (ID: {bot.user.id})')
    raw_audit_log('-----------------')

@bot.command(name='status', help='usage: faucet-send  [address] [tokens')
async def status(ctx):
    await ctx.send("still alive")

@tasks.loop(minutes = 1)
async def check_latest_checkpoint():
    raw_audit_log('Checking for new checkpoint')

    trusted_validators = [1, 2, 3, 4, 5, 12, 13, 15, 32, 37, 97, 123]
    estimated_checkpoints = []

    for index in trusted_validators:
        contents = urllib.request.urlopen(
            "https://sentinel.matic.network/api/v2/validators/" + str(index) + "/checkpoints-signed").read()
        estimated_checkpoints.append(json.loads(contents)["result"][0]["checkpointNumber"])

    current_checkpoint = max(estimated_checkpoints)
    saved_checkpoint = get_latest_saved_checkpoint()

    #if there is a new checkpoint we haven't evaluated yet
    if current_checkpoint > saved_checkpoint:
        raw_audit_log("New Checkpoint: ")
        await get_new_checkpoint(current_checkpoint, saved_checkpoint)
        return True
    else:
        return False

async def get_new_checkpoint(current_checkpoint: int, last_saved_checkpoint: int):
    await bot.wait_until_ready()
    checkpoint_channel = bot.get_channel(id=secrets.MISSED_CHECKPOINTS_CHANNEL)
    vault_checkpoint_channel = bot.get_channel(id=secrets.VAULT_CHECKPOINT_CHANNEL)
    notify_missed_cp = [2, 5, 9, 19, 34, 49, 99, 199]
    for i in range(len(notify_missed_cp)):
        notify_missed_cp[i] += (current_checkpoint - last_saved_checkpoint)

    set_new_checkpoint(str(current_checkpoint))
    for i in range(1, secrets.total_validators + 1):
        contents = urllib.request.urlopen(
            "https://sentinel.matic.network/api/v2/validators/" + str(i) + "/checkpoints-signed").read()
        try:
            validator_checkpoint = int(json.loads(contents)["result"][0]["checkpointNumber"])

            # notify me
            if i == 37:
                if current_checkpoint != validator_checkpoint or current_checkpoint % 3 == 0:
                    send_email(current_checkpoint, validator_checkpoint)

            # notify if a validator missed a checkpoint
            if (current_checkpoint - validator_checkpoint) in notify_missed_cp:
                await checkpoint_channel.send(get_val_contacts_from_id(str(i)) + ", please check **" + get_val_name_from_id(str(i)) + "**, " \
                                      "it has missed the last " + str((current_checkpoint - validator_checkpoint)) + " checkpoints.")

            # check if the validator is back in sync
            elif (current_checkpoint - validator_checkpoint) == 0 and get_last_validator_checkpoint(str(i)) - current_checkpoint >= 4:
                await checkpoint_channel.send(get_val_contacts_from_id(str(i)) + ", " + get_val_name_from_id(str(i)) + " is back in sync.")

            # save validator's latest checkpoint
            update_validator_checkpoint(str(i), str(validator_checkpoint))

        except Exception as e:
            raw_audit_log(e)
    await vault_checkpoint_channel.send("Completed Checkpoint: " + str(current_checkpoint))
    raw_audit_log("done")


check_latest_checkpoint.start()
bot.run(token)
