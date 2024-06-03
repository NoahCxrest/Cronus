import discord
from discord.ext import commands
import psutil
import json


class Utility(commands.Cog):
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.config = self.load_config()
        self.session = self.bot.session

    @staticmethod
    def load_config():
        """Load the bot's configuration from a JSON file."""
        with open('./config.json', 'r') as config_file:
            return json.load(config_file)

    @commands.hybrid_command(name="ping", with_app_command=True, description="Get the bot's latency")
    async def ping(self, ctx):
        """Command to get the bot's latency."""
        latency = self.bot.latency * 1000
        embed = discord.Embed(
            description=f'Pong: {latency:.0f}ms',
            color=discord.Color.from_rgb(43, 45, 49)
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="help", with_app_command=True, description="Get a list of commands")
    async def get_commands(self, ctx):
        """Command to get a list of all commands grouped by cog."""
        try:
            commands_by_cog = self.bot.commands_cache

            embed = discord.Embed(title="Command List", color=discord.Color.from_rgb(43, 45, 49))
            for cog_name, cog_commands in sorted(commands_by_cog.items()):
                embed.add_field(name=cog_name, value="\n".join(cog_commands), inline=False)

            if not embed.fields:
                embed.description = "Cronus is still loading commands; please try again in a few seconds."

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred while fetching the command list: {e}")

    @commands.hybrid_command(name="about", with_app_command=True, description="Learn about Cronus")
    async def about(self, ctx):
        """Command to get information about the bot."""
        embed = discord.Embed(
            title="About Cronus",
            description="Cronus is a Discord bot created by [Noah](https://discord.com/users/459374864067723275) "
                        "to help with the management of the ERM Systems Discord server.",
            color=discord.Color.from_rgb(43, 45, 49)
        )
        embed.set_thumbnail(url=self.bot.user.avatar)
        
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 ** 2
        embed.add_field(name="RAM Usage", value=f"{memory_usage:.2f} MB", inline=True)
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%", inline=True)
        embed.add_field(name="Loaded Cogs", value=len(self.bot.cogs), inline=True)

        await ctx.send(embed=embed)


async def setup(bot_instance):
    await bot_instance.add_cog(Utility(bot_instance))
