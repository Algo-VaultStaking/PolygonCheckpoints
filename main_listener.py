from discord.ext.commands import MissingRequiredArgument, MissingRole, BadArgument, MissingAnyRole

from logger import raw_audit_log

import discord
from discord.ext import commands

import secrets
from validator_db import get_val_name_from_id, get_val_contacts_from_id, get_val_uptime_from_id, \
    get_val_missed_latest_checkpoint_from_id, get_val_commission_percent_from_id, get_val_self_stake_from_id, \
    get_val_delegated_stake_from_id, set_val_contacts_from_id, remove_val_contacts_from_id, get_db_connection

token = secrets.DISCORD_TOKEN
bot = commands.Bot(command_prefix='$')


@bot.event
async def on_ready():
    raw_audit_log(f'Logged in as {bot.user} (ID: {bot.user.id})')
    raw_audit_log('-----------------')
    print("ready")


@bot.command(name='listener', help='')
@commands.has_any_role("Mod", "admin")
async def up(ctx):

    await ctx.send("Yes")


@bot.command(name='status', help='$status [validator id]')
async def status(ctx, val_id: int):
    db_connection = get_db_connection()
    no_of_checkpoints = round((100-get_val_uptime_from_id(db_connection, str(val_id)))*7,0)
    message = get_val_name_from_id(db_connection, str(val_id)) + " has missed " + str(no_of_checkpoints) + " out of the last 700 checkpoints. \n" \
              "Validator has " + ("not " if get_val_missed_latest_checkpoint_from_id(db_connection, str(val_id)) > 0 else "") + \
              "signed the latest checkpoint."
    await ctx.send(message)
    db_connection.close()


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
async def details(ctx, val_id: int):
    db_connection = get_db_connection()

    embed = discord.Embed(title= get_val_name_from_id(db_connection, str(val_id)),
                          color=discord.Color.blue())
    embed.add_field(name="Contacts", value=get_val_contacts_from_id(db_connection, str(val_id)), inline=False)
    embed.add_field(name="Commission", value=(str(get_val_commission_percent_from_id(db_connection, str(val_id))) + "%"), inline=False)
    embed.add_field(name="Self Stake", value="{:,.2f}".format(float(get_val_self_stake_from_id(db_connection, str(val_id)))/1e18), inline=False)
    embed.add_field(name="Delegated Stake", value="{:,.2f}".format(float(get_val_delegated_stake_from_id(db_connection, str(val_id)))/1e18), inline=False)
    embed.add_field(name="Uptime", value=(str(get_val_uptime_from_id(db_connection, str(val_id))) + "%"), inline=False)

    await ctx.send(embed=embed)
    db_connection.close()


@bot.command(name='contacts', help='$contacts [validator id]')
async def contacts(ctx, val_id: int):
    db_connection = get_db_connection()
    message = get_val_name_from_id(db_connection, str(val_id)) + " has the following contacts: " + \
              get_val_contacts_from_id(db_connection, str(val_id))
    await ctx.send(message)


@bot.command(name='contacts-add', help='$contacts-add [validator id] @user1 (@user2...)')
# @commands.has_any_role(*secrets.LISTENER_ROLES)
async def contacts_add(ctx, val_id: int, user_one, user_two="", user_three="", user_four="", user_five=""):
    db_connection = get_db_connection()
    contact = user_one
    if user_two != "":
        contact += ", " + user_two
    if user_three != "":
        contact += ", " + user_three
    if user_four != "":
        contact += ", " + user_four
    if user_five != "":
        contact += ", " + user_five

    set_val_contacts_from_id(db_connection, str(val_id), contact)
    message = get_val_name_from_id(db_connection, str(val_id)) + " now has the following contacts: " + \
              get_val_contacts_from_id(db_connection, str(val_id))
    await ctx.send(message)
    db_connection.close()
    return


@bot.command(name='contacts-remove', help='$contacts-remove [validator id] @user1 (@user2...)')
# @commands.has_any_role(*secrets.LISTENER_ROLES)
async def contacts_remove(ctx, val_id: int, *users):
    db_connection = get_db_connection()
    for user in users:
        remove_val_contacts_from_id(db_connection, str(val_id), user)
        message = get_val_name_from_id(db_connection, str(val_id)) + " now has the following contacts: " + \
                  get_val_contacts_from_id(db_connection, str(val_id))
        await ctx.send(message)
    db_connection.close()
    return


#### Error methods ####

@status.error
async def status_error(ctx, error):
    if isinstance(error, MissingAnyRole):
        await ctx.send("Role '" + ", ".join(secrets.LISTENER_ROLES) + "' is required to run this command.")
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
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(error)
        raise error

@missed.error
async def missed_error(ctx, error):
    if isinstance(error, MissingAnyRole):
        await ctx.send("Role '" + ", ".join(secrets.LISTENER_ROLES) + "' is required to run this command.")
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
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(error)
        raise error

@details.error
async def details_error(ctx, error):
    if isinstance(error, MissingAnyRole):
        await ctx.send("Role '" + ", ".join(secrets.LISTENER_ROLES) + "' is required to run this command.")
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
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(error)
        raise error

@contacts.error
async def contacts_error(ctx, error):
    if isinstance(error, MissingAnyRole):
        await ctx.send("Role '" + ", ".join(secrets.LISTENER_ROLES) + "' is required to run this command.")
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
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(error)
        raise error

@contacts_add.error
async def contacts_add_error(ctx, error):
    if isinstance(error, MissingAnyRole):
        await ctx.send("Role '" + ", ".join(secrets.LISTENER_ROLES) + "' is required to run this command.")
        raise error
    elif isinstance(error, BadArgument):
        await ctx.send("usage: `$contacts-add [validator id] @user1 (@user2...)`. \n"
                       "There was a bad argument.")
        raise error
    elif isinstance(error, MissingRequiredArgument):
        await ctx.send("Missing argument, try: `$contacts-add [validator id] @user1 (@user2...)`")
        raise error
    elif isinstance(error, MissingRole):
        await ctx.send("Role '" + secrets.LISTENER_ROLES + "' is required to run this command.")
        raise error
    else:
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(error)
        raise error

@contacts_remove.error
async def contacts_remove_error(ctx, error):
    if isinstance(error, MissingAnyRole):
        await ctx.send("Role '" + ", ".join(secrets.LISTENER_ROLES) + "' is required to run this command.")
        raise error
    elif isinstance(error, BadArgument):
        await ctx.send("usage: `$contacts-remove [validator id] @user1 (@user2...)`. \n"
                       "There was a bad argument.")
        raise error
    elif isinstance(error, MissingRequiredArgument):
        await ctx.send("Missing argument, try: `$contacts-remove [validator id] @user1 (@user2...)`")
        raise error
    elif isinstance(error, MissingRole):
        await ctx.send("Role '" + secrets.LISTENER_ROLES + "' is required to run this command.")
        raise error
    else:
        await ctx.send("There was error that <@712863455467667526> needs to fix. Please try again later.")
        raw_audit_log(error)
        raise error

bot.run(token)
