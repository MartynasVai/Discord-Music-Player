import discord
from discord.ext import commands
import asyncio
import os
from pymongo.mongo_client import MongoClient

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/',intents=intents)

uri = "<MONGODB URI>"
db= MongoClient(uri)
bot.db=db
#try:
#    db.admin.command('ping')
#    print("Pinged your deployment. You successfully connected to MongoDB!")
#except Exception as e:
#    print(e)

@bot.event
async def on_command(ctx):
    # Delete the user's command message to reduce chat spam for all commands
    await ctx.message.delete()

async def load_extensions():
    await bot.load_extension('cogs.test')
    await bot.load_extension('cogs.test2')

async def main():
    async with bot:
        await load_extensions()
        await bot.start('<BOT CODE HERE>')

asyncio.run(main())

