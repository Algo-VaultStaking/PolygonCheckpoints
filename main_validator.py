
from logger import raw_audit_log

from discord.ext import commands, tasks

import secrets

from validator_db import get_db_connection, update_validator_data

token = secrets.DISCORD_TOKEN
bot = commands.Bot(command_prefix='$')


@bot.event
async def on_ready():
    raw_audit_log(f'Logged in as {bot.user} (ID: {bot.user.id})')
    raw_audit_log('-----------------')
    print("ready")


@tasks.loop(minutes = 5)
async def update_validator_details():
    db_connection = get_db_connection()

    await bot.wait_until_ready()
    print("updating validators")
    checkpoint_channel = bot.get_channel(id=secrets.VAULT_CHECKPOINT_CHANNEL)
    for i in range(1, secrets.total_validators):
        try:
            message = update_validator_data(db_connection, str(i))
            if message != "":
                raw_audit_log(message)
                await checkpoint_channel.send(message)
        except Exception as e:
            print("Error in main_val: " + str(e))
    db_connection.close()
    return

update_validator_details.start()
bot.run(token)
