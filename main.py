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


@bot.command(name='status', help='$status [validator id]')
@commands.has_any_role("Mod", "team", "admin")
async def status(ctx, val_id: int):

    no_of_checkpoints = (100-get_val_uptime_from_id(str(val_id)))*2
    message = get_val_name_from_id(str(val_id)) + " has missed " + str(no_of_checkpoints) + " out of the last 200 checkpoints. \n" \
              "Validator has " + ("not " if get_val_missed_latest_checkpoint_from_id(str(val_id)) > 0 else "") + \
              "signed the latest checkpoint."
    await ctx.send(message)


@bot.command(name='missed', help='$missed')
@commands.has_any_role("None")
async def missed(ctx):
    # input: $missed
    # output: iterate over all validators and respond with a message similar to:
    # "[validator name 1], [validator name 2], ... has not signed the latest checkpoint.
    message = ""
    await ctx.send(message)
    return


@bot.command(name='details', help='$details [validator id]')
@commands.has_any_role("Mod", "team", "admin")
async def details(ctx, val_id: str):
    embed = discord.Embed(title= get_val_name_from_id(str(val_id)),
                          color=discord.Color.blue())
    embed.add_field(name="Contacts", value=get_val_contacts_from_id(str(val_id)), inline=False)
    embed.add_field(name="Commission", value=(str(get_val_commission_percent_from_id(str(val_id))) + "%"), inline=False)
    embed.add_field(name="Self Stake", value="{:,}".format(get_val_self_stake_from_id(str(val_id))), inline=False)
    embed.add_field(name="Delegated Stake", value="{:,}".format(get_val_delegated_stake_from_id(str(val_id))), inline=False)
    embed.add_field(name="Uptime", value=(str(get_val_uptime_from_id(str(val_id))) + "%"), inline=False)

    await ctx.send(embed=embed)


@bot.command(name='contacts', help='$contacts [validator id]')
@commands.has_any_role("Mod", "team", "admin")
async def contacts(ctx, val_id: str):
    message = get_val_name_from_id(str(val_id)) + " has the following contacts: " + get_val_contacts_from_id(str(val_id))
    await ctx.send(message)


@bot.command(name='contacts-add', help='$contacts-add [validator id] @user1 (@user2 @user3...)')
@commands.has_any_role("None")
async def contacts_add(ctx, val_id: int, user_one, user_two="", user_three="", user_four="", user_five=""):
    contact = user_one
    if user_two != "":
        contact += ", " + user_two
    if user_three != "":
        contact += ", " + user_three
    if user_four != "":
        contact += ", " + user_four
    if user_five != "":
        contact += ", " + user_five

    set_val_contacts_from_id(str(val_id), contact)
    message = get_val_name_from_id(str(val_id)) + " now has the following contacts: " + get_val_contacts_from_id(
        str(val_id))
    await ctx.send(message)
    return


@bot.command(name='contacts-remove', help='$contacts-remove [validator id] @user1 (@user2 @user3...)')
@commands.has_any_role("None")
async def contacts_remove(ctx, validator: int, users: str):
    return


@tasks.loop(minutes = 1)
async def check_latest_checkpoint():
    log('Checking for new checkpoint')

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
        raw_audit_log("New Checkpoint: " + str(current_checkpoint))
        print("New Checkpoint: " + str(current_checkpoint))
        await get_new_checkpoint(current_checkpoint, saved_checkpoint)
    else:
        print("No New Checkpoint.")

#    await update_validator_details()

async def get_new_checkpoint(current_checkpoint: int, last_saved_checkpoint: int):
    await bot.wait_until_ready()
    checkpoint_channel = bot.get_channel(id=secrets.MISSED_CHECKPOINTS_CHANNEL)
    vault_checkpoint_channel = bot.get_channel(id=secrets.VAULT_CHECKPOINT_CHANNEL)
    notify_missed_cp = [0, 1, 2, 5, 9, 19, 34, 49, 99, 199]
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
                if current_checkpoint != validator_checkpoint:
                    await vault_checkpoint_channel.send("invalid checkpoint: " + str(current_checkpoint))

            # notify if a validator missed a checkpoint
            if (current_checkpoint - validator_checkpoint) in notify_missed_cp:
                await checkpoint_channel.send(get_val_contacts_from_id(str(i)) + ", please check **" + get_val_name_from_id(str(i)) + "**, " \
                                      "it has missed the last " + str((current_checkpoint - validator_checkpoint)) + " checkpoints.")

            # check if the validator is back in sync
            elif (current_checkpoint - validator_checkpoint) == 0 and last_saved_checkpoint - get_last_validator_checkpoint(str(i)) >= 1:
                await checkpoint_channel.send(get_val_contacts_from_id(str(i)) + ", " + get_val_name_from_id(str(i)) + " is back in sync.")

            # save validator's latest checkpoint
            update_validator_checkpoint(str(i), str(validator_checkpoint))

        except Exception as e:
            raw_audit_log(str(e))
    if current_checkpoint % 1 == 0:
        await vault_checkpoint_channel.send("Completed Checkpoint: " + str(current_checkpoint))
    raw_audit_log("done")


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

check_latest_checkpoint.start()
bot.run(token)
