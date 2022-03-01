import json
import urllib.request

from discord.ext.commands import MissingRequiredArgument, MissingRole, BadArgument, CommandInvokeError

from logger import raw_audit_log, log

import discord
from discord.ext import commands, tasks

import secrets
from checkpoint_db import get_latest_saved_checkpoint, get_last_validator_checkpoint, \
    update_validator_checkpoint, set_new_checkpoint, send_email
from validator_db import get_val_name_from_id, get_val_contacts_from_id, get_val_uptime_from_id, \
    get_val_missed_latest_checkpoint_from_id, get_val_commission_percent_from_id, get_val_self_stake_from_id, \
    get_val_delegated_stake_from_id, set_val_contacts_from_id, remove_val_contacts_from_id

token = secrets.DISCORD_TOKEN
bot = commands.Bot(command_prefix='$')


@bot.event
async def on_ready():
    raw_audit_log(f'Logged in as {bot.user} (ID: {bot.user.id})')
    raw_audit_log('-----------------')
    print("ready")


@bot.command(name='status', help='$status [validator id]')
@commands.has_any_role(*secrets.LISTENER_ROLES)
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
@commands.has_any_role(*secrets.LISTENER_ROLES)
async def details(ctx, val_id: str):
    embed = discord.Embed(title= get_val_name_from_id(str(val_id)),
                          color=discord.Color.blue())
    embed.add_field(name="Contacts", value=get_val_contacts_from_id(str(val_id)), inline=False)
    embed.add_field(name="Commission", value=(str(get_val_commission_percent_from_id(str(val_id))) + "%"), inline=False)
    embed.add_field(name="Self Stake", value="{:,.2f}".format(float(get_val_self_stake_from_id(str(val_id)))/1e18), inline=False)
    embed.add_field(name="Delegated Stake", value="{:,.2f}".format(float(get_val_delegated_stake_from_id(str(val_id)))/1e18), inline=False)
    embed.add_field(name="Uptime", value=(str(get_val_uptime_from_id(str(val_id))) + "%"), inline=False)

    await ctx.send(embed=embed)


@bot.command(name='contacts', help='$contacts [validator id]')
@commands.has_any_role(*secrets.LISTENER_ROLES)
async def contacts(ctx, val_id: str):
    message = get_val_name_from_id(str(val_id)) + " has the following contacts: " + get_val_contacts_from_id(str(val_id))
    await ctx.send(message)


@bot.command(name='contacts-add', help='$contacts-add [validator id] @user1 (@user2 @user3...)')
@commands.has_any_role(*secrets.LISTENER_ROLES)
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
@commands.has_any_role(*secrets.LISTENER_ROLES)
async def contacts_remove(ctx, val_id: int, *users):
    for user in users:
        remove_val_contacts_from_id(str(val_id), user)
        message = get_val_name_from_id(str(val_id)) + " now has the following contacts: " + get_val_contacts_from_id(
            str(val_id))
        await ctx.send(message)
        return


#### Error methods ####

@status.error
async def status_error(ctx, error):
    if isinstance(error, CommandInvokeError):
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(str(error))
        raise error
    elif isinstance(error, BadArgument):
        await ctx.send("usage: `$status [validator id]`. \n"
                       "There was a bad argument.")
        raise error
    elif isinstance(error, MissingRequiredArgument):
        await ctx.send("Missing argument, try: `$status [validator id]`")
        raise error
    elif isinstance(error, MissingRole):
        await ctx.send("Role '" + secrets.LISTENER_ROLES + "' is required to run this command.")
        raise error
    else:
        raw_audit_log(error)
        raise error

@missed.error
async def missed_error(ctx, error):
    if isinstance(error, CommandInvokeError):
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(str(error))
        raise error
    elif isinstance(error, BadArgument):
        await ctx.send("usage: `$missed`. \n"
                       "There was a bad argument.")
        raise error
    elif isinstance(error, MissingRequiredArgument):
        await ctx.send("Missing argument, try: `$missed`")
        raise error
    elif isinstance(error, MissingRole):
        await ctx.send("Role '" + secrets.LISTENER_ROLES + "' is required to run this command.")
        raise error
    else:
        raw_audit_log(error)
        raise error

@details.error
async def details_error(ctx, error):
    if isinstance(error, CommandInvokeError):
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(str(error))
        raise error
    elif isinstance(error, BadArgument):
        await ctx.send("usage: `$details [validator id]`. \n"
                       "There was a bad argument.")
        raise error
    elif isinstance(error, MissingRequiredArgument):
        await ctx.send("Missing argument, try: `$details [validator id]`")
        raise error
    elif isinstance(error, MissingRole):
        await ctx.send("Role '" + secrets.LISTENER_ROLES + "' is required to run this command.")
        raise error
    else:
        raw_audit_log(error)
        raise error

@contacts.error
async def contacts_error(ctx, error):
    if isinstance(error, CommandInvokeError):
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(str(error))
        raise error
    elif isinstance(error, BadArgument):
        await ctx.send("usage: `$contacts [validator id]`. \n"
                       "There was a bad argument.")
        raise error
    elif isinstance(error, MissingRequiredArgument):
        await ctx.send("Missing argument, try: `$contacts [validator id]`")
        raise error
    elif isinstance(error, MissingRole):
        await ctx.send("Role '" + secrets.LISTENER_ROLES + "' is required to run this command.")
        raise error
    else:
        raw_audit_log(error)
        raise error

@contacts_add.error
async def contacts_add_error(ctx, error):
    if isinstance(error, CommandInvokeError):
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(str(error))
        raise error
    elif isinstance(error, BadArgument):
        await ctx.send("usage: `$contacts-add [validator id] @user1 (@user2 @user3...)`. \n"
                       "There was a bad argument.")
        raise error
    elif isinstance(error, MissingRequiredArgument):
        await ctx.send("Missing argument, try: `$contacts-add [validator id] @user1 (@user2 @user3...)`")
        raise error
    elif isinstance(error, MissingRole):
        await ctx.send("Role '" + secrets.LISTENER_ROLES + "' is required to run this command.")
        raise error
    else:
        raw_audit_log(error)
        raise error

@contacts_remove.error
async def contacts_remove_error(ctx, error):
    if isinstance(error, CommandInvokeError):
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(str(error))
        raise error
    elif isinstance(error, BadArgument):
        await ctx.send("usage: `$contacts-remove [validator id] @user1 (@user2 @user3...)`. \n"
                       "There was a bad argument.")
        raise error
    elif isinstance(error, MissingRequiredArgument):
        await ctx.send("Missing argument, try: `$contacts-remove [validator id] @user1 (@user2 @user3...)`")
        raise error
    elif isinstance(error, MissingRole):
        await ctx.send("Role '" + secrets.LISTENER_ROLES + "' is required to run this command.")
        raise error
    else:
        raw_audit_log(error)
        raise error

bot.run(token)
