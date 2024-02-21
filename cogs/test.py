import discord
from discord.ext import commands
from pymongo.mongo_client import MongoClient



class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx, txt):
        await ctx.send(txt)

    @commands.command() 
    async def hello(self, ctx): 
        await ctx.send('Hello!')






async def setup(bot):
    await bot.add_cog(Test(bot))