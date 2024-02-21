import discord
from discord.ext import commands
import youtube_dl
import asyncio
from pymongo.mongo_client import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class Test2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        


    
    
    @commands.command()#ping db if it works
    async def ping_db(self, ctx):
        try:
            # Ping the database
            self.bot.db.admin.command('ping')
            await ctx.send("Pinged")
        except Exception as e:
            await ctx.send(f"Error: {e}")

    ffmpeg_options = {
        'executable': 'C:/ffmpeg/bin/ffmpeg.exe', 
    }
    
    async def play_next(self, ctx):
        print("AAA")
        guild_id = ctx.guild.id
        vc = ctx.voice_client
        if guild_id in self.queues and len(self.queues[guild_id]) > 0:

            url = self.queues[guild_id].pop(0)
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                url2 = info['formats'][0]['url']

            
            vc.play(discord.FFmpegPCMAudio(url2), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            await ctx.send(f"Now playing: {info['title']}")
        # next
        if not (vc.is_playing() or vc.is_paused()):
            await ctx.send("Queue is empty. Disconnecting.")
            await vc.disconnect()

    @commands.command()
    async def play(self, ctx, *, url):
        if ctx.voice_client is not None:

            # Add to que
            self.queues[ctx.guild.id].append(url)
            await ctx.send("Added to queue.")

        else:
            if not ctx.author.voice:
                await ctx.send("You are not connected to a voice channel.")
                return
            try:
                channel = ctx.author.voice.channel
            
                vc = await channel.connect()
            except Exception as e:
                print(f"An error occurred while trying to connect to the voice channel: {e}")
            # add to que and play
            self.queues[ctx.guild.id] = [url]
            await self.play_next(ctx)

    @commands.command()
    async def skip(self, ctx):
        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) > 0:
            await ctx.send("Skipping the current song.")
            #vc = ctx.voice_client
            #print("Queue:", self.queues[ctx.guild.id])
            #print("Is Playing:", vc.is_playing())
            #print("Is Paused:", vc.is_paused())
            ctx.voice_client.stop()
            #await self.play_next(ctx)
        else:
            await ctx.send("No songs in the queue to skip")

    @commands.command()
    async def stop(self, ctx):
        if ctx.guild.id in self.queues:
            self.queues[ctx.guild.id] = [] 
            ctx.voice_client.stop()

    @commands.Cog.listener()#leave voice when bot is alone
    async def on_voice_state_update(self, member, before, after):
        if not member.bot:
            if before.channel and not any(member.id in vc.channel.members for vc in before.channel.voice_states.values()):
                await before.channel.guild.voice_client.disconnect()



    @commands.command()
    async def add_playlist(self, ctx, playlist_name: str):
        try:
            playlists_collection = self.bot.db.data.playlist

            existing_playlist = playlists_collection.find_one({"name": playlist_name})

            if existing_playlist:
                await ctx.send(f"Playlist '{playlist_name}' already exists.")
            else:
                # insert playlist
                playlists_collection.insert_one({"name": playlist_name, "songs": []})
                await ctx.send(f"Playlist '{playlist_name}' added.")
        except Exception as e:
            print(f"error: {e}")

    @commands.command()
    async def add_song(self, ctx, playlist_name: str, song_url: str):
        playlists_collection = self.bot.db.data.playlist

        playlist = playlists_collection.find_one({"name": playlist_name})

        if not playlist:
            await ctx.send(f"Playlist '{playlist_name}' not found.")
        else:
            playlists_collection.update_one(
                {"name": playlist_name},
                {"$push": {"songs": song_url}}
            )
            await ctx.send(f"Song added to playlist '{playlist_name}'.")

    @commands.command()
    async def list_songs(self, ctx, playlist_name: str):
        playlists_collection = self.bot.db.data.playlist

        playlist = playlists_collection.find_one({"name": playlist_name})

        if not playlist:
            await ctx.send(f"Playlist '{playlist_name}' not found.")
        else:
            if not playlist["songs"]:
                await ctx.send(f"Playlist '{playlist_name}' is empty.")
            else:
                await ctx.send(f"Songs in playlist '{playlist_name}':")
                for index, song_url in enumerate(playlist["songs"], start=1):
                        await ctx.send(f"{index}. {song_url}")

    @commands.command()
    async def play_playlist(self, ctx, playlist_name: str):

        if ctx.guild.id not in self.queues:#jei nera guild id que array
            self.queues[ctx.guild.id] = []

        if not ctx.author.voice:
            await ctx.send("You are not connected to a voice channel.")
            return

        playlists_collection = self.bot.db.data.playlist

        playlist = playlists_collection.find_one({"name": playlist_name})

        if not playlist:
            await ctx.send(f"Playlist '{playlist_name}' not found.")
        else:
            if not playlist["songs"]:
                await ctx.send(f"Playlist '{playlist_name}' is empty.")
            else:
                for index, song_url in enumerate(playlist["songs"], start=1):
                    self.queues[ctx.guild.id].append(song_url)
                    await ctx.send("Added to queue.")
                print("Queue:", self.queues[ctx.guild.id])
                if ctx.voice_client is None:


                    channel = ctx.author.voice.channel
                    vc = await channel.connect()
                    await self.play_next(ctx)

    @commands.command()
    async def remove_song(self, ctx, playlist_name: str, song_url: str):
        playlists_collection = self.bot.db.data.playlist

        playlist = playlists_collection.find_one({"name": playlist_name})

        if not playlist:
            await ctx.send(f"Playlist '{playlist_name}' not found.")
        else:
            if song_url in playlist["songs"]:
                playlists_collection.update_one(
                    {"name": playlist_name},
                    {"$pull": {"songs": song_url}}
                )
                await ctx.send(f"Song removed from playlist '{playlist_name}'.")
            else:
                await ctx.send(f"Song URL '{song_url}' not found in playlist '{playlist_name}'.")

    @commands.command()
    async def remove_playlist(self, ctx, playlist_name: str):
        playlists_collection = self.bot.db.data.playlist

        playlist = playlists_collection.find_one({"name": playlist_name})

        if not playlist:
            await ctx.send(f"Playlist '{playlist_name}' not found.")
        else:
            playlists_collection.delete_one({"name": playlist_name})
            await ctx.send(f"Playlist '{playlist_name}' removed.")

    @commands.command()
    async def search_soundcloud(self, ctx, *, query):
        try:




            options = webdriver.ChromeOptions()

            driver = webdriver.Chrome(options=options)

            search_url = f"https://soundcloud.com/search?q={query}"
            driver.get(search_url)
            
            driver.implicitly_wait(10)

           
            first_result = driver.find_element(By.XPATH, '//a[contains(@class, "soundTitle__title")]')

            
            result_url = first_result.get_attribute("href")

            
            #await ctx.send(f"Search result URL: {result_url}")

            await ctx.invoke(self.play, url=result_url)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


    @commands.command()
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc.is_playing():
            vc.pause()
            await ctx.send("Music paused.")
        elif vc.is_paused():
            vc.resume()
            await ctx.send("Music resumed.")
        else:
            await ctx.send("Nothing is currently playing or paused.")


async def setup(bot):
    await bot.add_cog(Test2(bot))