import discord
from discord.ext import commands
import sys
from classes import DiscordBot

from cogs.botAudio import Music
from cogs.botSettings import SettingsCommands
from cogs.botUtilities import UtilityCommands
from cogs.botMisc import MiscCommands
from cogs.botEvents import BotEvents
from cogs.botUserManagement import BotUserManagement
from cogs.botMessenger import BotMessenger

from utilities.parseSettings import getSettings, parseTypedSettings

parsedSettings = getSettings('config.yaml')
parsedReactions = getSettings('reactions.yaml')
botSettings = parsedSettings['bot']
defaultServerSettings = parseTypedSettings(parsedSettings['serverSettings'])

bot = DiscordBot(defaultServerSettings, botSettings, parsedReactions)
client = commands.Bot(command_prefix=commands
                      .when_mentioned_or(bot.botSettings['prefix']), 
                      description="I am your best friend")

if not discord.opus.is_loaded():
    if 'opusLocation' in bot.botSettings:
        discord.opus.load_opus(bot.botSettings['opusLocation'])
    else:
        sys.exit("Failed to find opusLocation in config.yaml")

@client.event
async def on_message(msg):
    return

client.add_cog(Music(client))
client.add_cog(SettingsCommands(client, bot))
client.add_cog(UtilityCommands(client, bot))
client.add_cog(MiscCommands(client, bot))
client.add_cog(BotEvents(client, bot))
client.add_cog(BotUserManagement(client, bot))
client.add_cog(BotMessenger(client, bot))

# @client.command(description="Server info")
# async def serverinfo():
#     output = os.popen('serverinfo.sh').read()
#     output.strip()
#     return output

# Bot token from config.yaml
client.run(bot.botSettings['token'])
