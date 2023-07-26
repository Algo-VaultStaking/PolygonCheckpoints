import datetime
import json
import urllib.request
from logger import raw_audit_log, log
import http.client


import discord
from discord.ext import commands, tasks

import secrets
from checkpoint_db import get_latest_saved_checkpoint, get_last_validator_checkpoint, update_validator_checkpoint, \
    set_new_checkpoint, create_pagerduty_alert
from validator_db import get_val_name_from_id, get_val_contacts_from_id, get_db_connection, get_val_status_from_id

token = secrets.DISCORD_TOKEN
bot = commands.Bot(command_prefix='cp')


@bot.event
async def on_ready():
    raw_audit_log(f'Logged in as {bot.user} (ID: {bot.user.id})')
    raw_audit_log('-----------------')
    print("ready")


@bot.command(name=':', help='')
@commands.has_any_role("Mod", "team", "admin")
async def status(ctx):
    await ctx.send("Yes")


@tasks.loop(minutes=1)
async def check_latest_checkpoint():

    trusted_validators = [12, 13, 23, 31, 32, 37, 77, 82, 123]
    estimated_checkpoints = []

    for index in trusted_validators:
        url = f"https://staking-api.polygon.technology/api/v2/validators/{index}/checkpoints-signed"
        hdr = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive'}

        request_site = urllib.request.Request(url, headers=hdr)
        contents = urllib.request.urlopen(request_site).read()
        estimated_checkpoints.append(json.loads(contents)["result"][0]["checkpointNumber"])

    current_checkpoint = max(estimated_checkpoints)
    saved_checkpoint = get_latest_saved_checkpoint()

    # if there is a new checkpoint we haven't evaluated yet
    if current_checkpoint > saved_checkpoint:
        raw_audit_log(f"{datetime.datetime.now()}: New Checkpoint: {str(current_checkpoint)}")
        print(f"{datetime.datetime.now()}: New Checkpoint: " + str(current_checkpoint))
        await get_new_checkpoint(current_checkpoint, saved_checkpoint)
    else:
        print(f"{datetime.datetime.now()}: No New Checkpoint.")


#    await update_validator_details()

async def get_new_checkpoint(current_checkpoint: int, last_saved_checkpoint: int):
    await bot.wait_until_ready()
    db_connection = get_db_connection()
    checkpoint_channel = bot.get_channel(id=secrets.MISSED_CHECKPOINTS_CHANNEL)
    vault_checkpoint_channel = bot.get_channel(id=secrets.VAULT_CHECKPOINT_CHANNEL)
    shard_checkpoint_channel = bot.get_channel(id=secrets.SHARD_CHECKPOINT_CHANNEL)
    notify_missed_cp = [0, 1, 2, 5, 9, 19, 34, 49, 99, 199]
    for i in range(len(notify_missed_cp)):
        notify_missed_cp[i] += (current_checkpoint - last_saved_checkpoint)

    set_new_checkpoint(str(current_checkpoint))
    for i in range(1, secrets.total_validators + 1):
        if get_val_status_from_id(db_connection, str(i)) == "unstaked":
            continue
        url = f"https://staking-api.polygon.technology/api/v2/validators/{i}/checkpoints-signed"
        hdr = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive'}

        request_site = urllib.request.Request(url, headers=hdr)
        contents = urllib.request.urlopen(request_site).read()
        try:
            validator_checkpoint = int(json.loads(contents)["result"][0]["checkpointNumber"])

            # notify me
            if i == 37 or i == 23:
                if current_checkpoint != validator_checkpoint:
                    await vault_checkpoint_channel.send(
                        f"<@712863455467667526>, invalid checkpoint {i}: {str(current_checkpoint)}")
                    create_pagerduty_alert(i, int(current_checkpoint - validator_checkpoint))

            # notify Shard Labs
            if i == 54:
                if current_checkpoint != validator_checkpoint:
                    await shard_checkpoint_channel.send(
                        get_val_contacts_from_id(db_connection, str(i)) + ", please check **" + get_val_name_from_id(
                            db_connection, str(i)) + "**, it has missed the last " + str(
                            (current_checkpoint - validator_checkpoint)) + " checkpoints.")

            # notify if a validator missed a checkpoint
            if (current_checkpoint - validator_checkpoint) in notify_missed_cp:
                if i != 14:
                    await checkpoint_channel.send(
                        get_val_contacts_from_id(db_connection, str(i)) + ", please check **" + get_val_name_from_id(
                            db_connection, str(i)) + "**, it has missed the last " + str(
                            (current_checkpoint - validator_checkpoint)) + " checkpoints.")

            # check if the validator is back in sync
            elif (current_checkpoint - validator_checkpoint) == 0 and \
                    last_saved_checkpoint - get_last_validator_checkpoint(str(i), last_saved_checkpoint) >= 1:
                # notify me
                if i == 37:
                    if current_checkpoint != validator_checkpoint:
                        await vault_checkpoint_channel.send(get_val_contacts_from_id(db_connection, str(i)) + ", " + get_val_name_from_id(db_connection,
                                                                                                  str(i)) + " is back in sync.")
                # notify Shard Labs
                if i == 54:
                    if current_checkpoint != validator_checkpoint:
                        await shard_checkpoint_channel.send(get_val_contacts_from_id(db_connection, str(i)) + ", " + get_val_name_from_id(db_connection,
                                                                                                  str(i)) + " is back in sync.")

                await checkpoint_channel.send(
                    get_val_contacts_from_id(db_connection, str(i)) + ", " + get_val_name_from_id(db_connection,
                                                                                                  str(i)) + " is back in sync.")

            # save validator's latest checkpoint
            update_validator_checkpoint(str(i), str(validator_checkpoint))

        except Exception as e:
            raw_audit_log(str(e))
    if current_checkpoint % 20 == 0:
        await vault_checkpoint_channel.send("Completed Checkpoint: " + str(current_checkpoint))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"Checkpoint: {current_checkpoint}"))
    raw_audit_log("done")
    db_connection.close()


check_latest_checkpoint.start()
bot.run(token)
