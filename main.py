
from flask import Flask
from threading import Thread
import discord
import asyncio
import aiohttp
import os
from discord.ext import commands, tasks
from bs4 import BeautifulSoup

app = Flask('')

@app.route('/')
def home():
    return "HermesDropBot läuft ✅"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = os.environ['DISCORD_TOKEN']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])

HERMES_URLS = [
    "https://www.hermes.com/de/de/category/damen/taschen-und-kleinlederwaren/handtaschen-und-clutches/",
    "https://www.hermes.com/fr/fr/category/femmes/sacs-et-petite-maroquinerie/sacs-a-main/",
    "https://www.hermes.com/it/it/category/donna/borse-e-piccola-pelletteria/borse/"
]

MODELS = ['Kelly', 'Birkin', 'Constance', 'Picotin', 'Herbag']
CHECK_INTERVAL = 10

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot ist online als {bot.user}')
    check_hermes.start()

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_hermes():
    async with aiohttp.ClientSession() as session:
        for url in HERMES_URLS:
            try:
                async with session.get(url) as response:
                    print(f"Checking {url} – Status: {response.status}")
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        products = soup.find_all("a", href=True)

                        for link in products:
                            text = link.get_text().lower()
                            for model in MODELS:
                                if model.lower() in text:
                                    full_url = "https://www.hermes.com" + link['href']
                                    image = link.find("img")
                                    image_url = image['src'] if image and 'src' in image.attrs else None

                                    embed = discord.Embed(
                                        title=f"{model} gefunden!",
                                        description=f"[🔗 Zum Produkt]({full_url})",
                                        color=0xE07A5F
                                    )
                                    embed.set_footer(text="HermesDropBot")
                                    if image_url:
                                        embed.set_thumbnail(url=image_url)

                                    channel = bot.get_channel(CHANNEL_ID)
                                    await channel.send(embed=embed)
                                    await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ Fehler bei {url}: {e}")

@bot.command()
async def check(ctx):
    await ctx.send("🔍 Manuelle Überprüfung läuft...")
    await check_hermes()

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
