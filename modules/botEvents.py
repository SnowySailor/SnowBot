from discord.ext import commands
from modules.messageHandler import handle, handlePersonalMessage, handleBotMention

class BotEvents:
    def __init__(self, client, bot):
        self.client = client
        self.bot = bot

    @commands.event
    async def on_message(self, msg):
        await self.client.process_commands(msg)
        if msg.author == self.client.user or msg.author.bot:
            # Don't let the bot reply to itself and if the sender is a bot
            # then don't process that message. It could cause a loop.
            return

        # Server is None if the msg is a PM.
        # Use direct reference to "None" to avoid confusion
        if msg.server is None:
            await handlePersonalMessage(msg, self.bot, self.client)
            return

        # Check to see if the server is registered in the bot
        if msg.server.id not in self.bot.servers:
            # Add a new server to the server dict.
            self.bot.addServer(msg.server, self.bot.defaultServerSettings)

        # If the bot was mentioned directly handle that in a special way
        if msg.content.startswith("<@{}>".format(self.client.user.id)):
            await handleBotMention(msg, self.bot, self.client)
            # We don't return afterwards because it could also be a valid
            # message for handle()

        if not msg.content.startswith(self.bot.settings['prefix']):
            await handle(msg, self.bot, self.client)
            return


    @commands.event
    async def on_ready(self):
        print('Logged in as')
        print(self.client.user.name)
        print(self.client.user.id)
        print('------')