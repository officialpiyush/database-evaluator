import os
from discord.ext import commands

def get_prefix(bot, message):
    prefixes = ["!", "-"]
    return commands.when_mentioned_or(*prefixes)(bot, message)

client = commands.Bot(command_prefix=get_prefix, description="Personal bot nothing else!")

initial_extensions = ["cogs.rethink"]

if __name__ == "__main__":
    for extension in initial_extensions:
        client.load_extension(extension)
        print(f"Loaded Cog - {extension}")

@client.event
async def ready():
    print("Bot ready to roll.")

client.run(os.getenv("TOKEN"))
