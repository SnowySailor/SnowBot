from discord.ext import commands
from modules.messageHandler import handle, handlePersonalMessage, handleBotMention
from classes import AccessData
from utilities.utilities import safe_format, loadMarkovFromServer, getChannelById
import re

class BotEvents:
    def __init__(self, client, bot):
        self.client = client
        self.bot = bot

    async def on_message(self, msg):
        if msg.author == self.client.user or msg.author.bot:
            # Don't let the bot reply to itself and if the sender is a bot
            # then don't process that message. It could cause a loop.
            return

        # Check to see if the server is registered in the bot
        if msg.server and msg.server.id not in self.bot.servers:
            # Add a new server to the server dict.
            self.bot.addServer(msg.server, self.bot.defaultServerSettings, self.bot.defaultServerReactions)
            if 'botChannel' in self.bot.servers[msg.server.id].settings:
                self.bot.servers[msg.server.id].botChannel = getChannelById(self.client,
                    self.bot.servers[msg.server.id].settings["botChannel"][0])

        await self.client.process_commands(msg)

        # Server is None if the msg is a PM.
        # Use direct reference to "None" to avoid confusion
        if msg.channel.is_private:
            await handlePersonalMessage(msg, self.bot, self.client)
            return

        # If the bot was mentioned directly handle that in a special way
        if msg.content.startswith("<@{}>".format(self.client.user.id)):
            await handleBotMention(msg, self.bot, self.client)
            # We don't return afterwards because it could also be a valid
            # message for handle()

        # Make sure we don't handle a message that's a command
        if not msg.content.startswith(self.bot.botSettings['prefix']):
            await handle(msg, self.bot, self.client)
            return

    async def on_command_error(self, error, ctx):
        if isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.bot.send_message(ctx.message.channel,
                            "You can't use this command in private messages.")
        else:
            print(type(error))
        #elif isinstance(error, commands.errors.)

    async def on_message_delete(self, msg):
        # If a user sends an echo command then deletes their message,
        # we delete the message that the bot sent (the echo)
        if (msg.server is not None and 
                msg.id in self.bot.servers[msg.server.id].echoMessages):
            msgDel = self.bot.servers[msg.server.id].echoMessages[msg.id]
            await self.client.delete_message(msgDel)
        return

    async def on_message_edit(self, b_msg, a_msg):
        if (b_msg.server is not None and
                b_msg.id in self.bot.servers[a_msg.server.id].echoMessages):
            msgEdit = self.bot.servers[a_msg.server.id].echoMessages[b_msg.id]
            newReply = re.sub(("^(\\"+self.bot.botSettings['prefix']+"echo|<@"+self.client.user.id+">\secho)\s"), "", a_msg.content)
            newMsg = await self.client.edit_message(msgEdit, newReply)
            self.bot.servers[a_msg.server.id].echoMessages[a_msg.id] = newMsg
            return

    async def on_member_join(self, member):
        if member.server.id not in self.bot.servers:
            self.bot.addServer(member.server, self.bot.defaultServerSettings, self.bot.defaultServerReactions)

        botChan = member.server.default_channel
        if 'botChannel' in self.bot.servers[ctx.message.server.id].settings:
            botChan = getChannelById(self.client, self.bot.servers[member.server.id].settings['botChannel'][0])

        settings = self.bot.servers[member.server.id].settings
        if 'welcomeMessage' in settings:
            reply = settings['welcomeMessage'][0]
            channel = member.server.default_channel
            if member.id is not self.client.user.id:
                data = AccessData(member, self.client.user)
                try:
                    await self.client.send_message(channel, safe_format(reply, data))
                except AttributeError:
                    await self.client.send_message(botChan, "Something is fishy with this reply: `{}`"
                        .format(reply))
                return
            return

    async def on_server_join(self, server):
        # Check to see if the server is registered in the bot
        if server and server.id not in self.bot.servers:
            # Add a new server to the server dict.
            self.bot.addServer(server, self.bot.defaultServerSettings, self.bot.defaultServerReactions)
        success = await loadMarkovFromServer(server, self.bot, self.client)
        #await self.client.send_message(server.default_channel, "Hi! I'm WaifuBot. Type `$help` for commands.")
        
    async def on_ready(self):
        print('Logged in as')
        print(self.client.user.name)
        print(self.client.user.id)
        print('------')
