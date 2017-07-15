import discord

def isRateLimited(redis, server, msg):
    key = msg.server.id + "." + msg.author.id
    if redis.get(key) is None:
        redis.psetex(key, 3000, False)
        return False
    else:
        expireTime = redis.pttl(key)
        if expireTime > 10000:
            # Expire time exceeds rate limit
            return True
#        elif expireTime > 6000:
#            return 
# Figure something out to return as a "warning" sign
        elif expireTime is -1:
            # No expire time set
            return False
        elif expireTime is -2:
            # Invalid key (doesn't make much sense)
            # Only way this could happen is if the key expired
            # between the "if" condition and now.
            # In that case they wouldn't be limited
            return False
        else:
            expireTime = expireTime + 3000
            redis.pexpire(key, expireTime)
    return False

# settings is settings['spamFilter'] dict!
async def handleRateLimit(bot, client, msg, settings):
    if ("muteUser" in settings and
            settings['muteUser']):
        await muteUser(client, msg)
    if ("notifyAdmin" in settings and 
            settings['notifyAdmin']):
        await messageAdmins(client, msg)
    return

async def messageAdmins(client, msg):
    # Notify the server administrators
    # If the server is larger than 250 members we can't see all members
    # online/offline so we need to request a list of offline people
    if msg.server.large:
        await client.request_offline_members(msg.server)
    admins = []
    for member in msg.server.members:
        perms = msg.channel.permissions_for(member)
        if perms.administrator:
            admins.append(member)
    for admin in admins:
        try:
            await client.send_message(admin, "{0.author.mention} has sent "\
            "a lot of messages in a short amount of time in {0.server.name}."\
            " Channel #{0.channel.name}".format(msg))
        except Exception:
            pass
    return

async def muteUser(client, msg):
    # Locate the muted user role
    timeoutRole = tryGetMuteRole(client, msg)
    if timeoutRole is None:
        timeoutRole = await tryCreateMuteRole(client, msg)
        if timeoutRole is None:
            return
    muted = await tryAddMuteRole(client, msg, timeoutRole)
    _ = await tryOverwriteChannelPermissions(client, msg, timeoutRole,
        send_messages=False, send_tts_messages=False)
    if muted:
        # Message the user that got muted
        await client.send_message(msg.author, "You have been silenced "\
            "in {0.server.name} due to too many messages being sent in "\
            "a short period of time. Please message the server admins "\
            "if you have questions or if this shouldn't have heppened."
            .format(msg))
    return

async def giveUserWarning(client, msg):
    await client.send_message(msg.channel, "{0.author.mention} please slow "\
        "your messages down or type in full sentences.".format(msg))
    return

def tryGetMuteRole(client, msg):
    return discord.utils.get(msg.server.roles, permissions__value=66560,
        name="timeout")

async def tryCreateMuteRole(client, msg):
    try:
        # Create a role that doesn't allow the user to send messages
        newPerm = discord.Permissions(permissions=66560,
            send_messages=False, send_tts_messages=False)
        timeoutRole = await client.create_role(msg.server,
            permissions=newPerm, name="timeout",
            color=discord.Colour.default(), hoist=False,
            mentionable=False)
        return timeoutRole
    except discord.Forbidden:
        # Can't create role, message owner.
        await client.send_message(msg.server.owner, "I can't create a "\
            "role to place silenced users into. Please create a role in "\
            "{0.server.name} that is not allowed to send messages or "\
            "send TTS messages.".format(msg))
        return None
    return None

async def tryAddMuteRole(client, msg, role):
    try:
        # Try to give the role to the user
        await client.add_roles(msg.author, role)
        return True
    except discord.Forbidden:
        # Can't add the role, message owner.
        await client.send_message(msg.server.owner, "I can't add "\
            "a timeout role to a spamming user in {0.server.name}. "\
            "Please grant me those permissions or disable spam "\
            "prevention with the $settings command.".format(msg))
        return False
    return

async def tryOverwriteChannelPermissions(client, msg, muteRole, **kwargs):
    failures = []
    overwrite = discord.PermissionOverwrite()
    for k, v in kwargs:
        setattr(overwrite, k, v)
    for channel in msg.server.channels:
        try:
            await client.edit_channel_permissions(channel, muteRole, overwrite)
        except Exception:
            failures.append(channel.name)
            pass
    if len(failures) > 0:
        await client.send_message(msg.server.owner, "I was unable to edit "\
            "channel permissions in these channels for {}: {}. Please edit "\
            "the `timeout` role so that it cannot send messages or send TTS "\
            "messages in those.".format(msg.server.name, ', '.join(failures)))
    return failures
