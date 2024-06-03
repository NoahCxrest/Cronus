import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import logging
import asyncio
import aiohttp
import time
import json


load_dotenv()


class Config:
    TOKEN = os.getenv("TOKEN")


def load_config():
    load_dotenv()
    return Config


BOT_PREFIX = '!'
CONFIG_PATH = 'config.json'
COGS_PATH = 'Cogs'


class Bot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        """Initializes the bot."""
        super().__init__(*args, **kwargs)
        self.commands_cache = {}
        self.logger = self.setup_logger()
        self.session = None
        self.is_ready = asyncio.Event()
        self.logger.info("Bot class instantiated.")
        self.config = self.load_config()

    def load_config(self):
        """Load the bot's configuration from a JSON file."""
        try:
            with open(CONFIG_PATH, 'r') as config_file:
                config = json.load(config_file)
            self.logger.info("Configuration loaded successfully.")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return {}

    @staticmethod
    def setup_logger():
        """Sets up the logger."""
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    async def on_ready(self):
        """Called when the bot is ready."""
        start_time = time.time()
        self.session = aiohttp.ClientSession()
        self.logger.info(f"Logged in as {self.user.name}#{self.user.discriminator}")

        elapsed_time = (time.time() - start_time) * 1000
        self.logger.info(f"Bot is ready. Took {elapsed_time:.2f}ms")

        await self.load_extensions()
        await self.cache_commands()
        await self.set_presence()

        self.is_ready.set()

    async def load_extensions(self):
        """Loads all extensions."""
        self.logger.debug("Loading extensions...")
        extensions = [filename[:-3] for filename in os.listdir(COGS_PATH) if filename.endswith('.py')]
        self.logger.info(f"Found extensions: {extensions}")

        tasks = [self.load_extension(f'{COGS_PATH}.{extension}') for extension in extensions]

        try:
            tasks.append(self.load_extension('jishaku'))
        except commands.ExtensionError as e:
            self.logger.error(f"Failed to load jishaku extension: {e}")

        await asyncio.gather(*tasks, return_exceptions=True)

    async def cache_commands(self):
        """Caches all commands and their descriptions. This is used for the help command."""
        url = f"https://discord.com/api/v10/applications/{self.user.id}/commands"
        headers = {"Authorization": f"Bot {self.http.token}"}
        params = {"with_localizations": "True"}

        async with self.session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            app_commands = await response.json()

        commands_by_cog = {}
        for command in app_commands:
            cmd = self.get_command(command['name'])
            cog_name = cmd.cog_name if cmd else 'No Cog'
            command_description = f"</{command['name']}:{command['id']}> - {command['description']}"
            commands_by_cog.setdefault(cog_name, []).append(command_description)

        self.commands_cache = commands_by_cog
        self.logger.info(f"Commands cached: {commands_by_cog}")

    async def set_presence(self):
        """Sets the bot's presence."""
        await self.wait_until_ready()
        await self.change_presence(activity=discord.Game(name="with ERM Systems"))
        self.logger.info("Presence was set.")

    async def close(self):
        """Closes the aiohttp.ClientSession."""
        if self.session:
            await self.session.close()
        await super().close()


intents = discord.Intents.default()
intents.message_content = True

bot = Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None, chunk_guilds_at_startup=False)


@bot.event
async def on_command_error(ctx, error):
    """Called when an error occurs while invoking a command."""
    if isinstance(error, commands.CommandNotFound):
        bot.logger.warning(f"Command not found: {ctx.message.content}")
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("You're missing some arguments.")
        return

    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("This command cannot be used in direct messages.")
        return

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"This command is on cooldown, you can try again in {error.retry_after:.2f} seconds.")
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You don't have the permissions to run this command. 😔 RIP")
        return

    if hasattr(ctx.command, 'on_error'):
        return

    error_message = f"Something went wrong. 👇\n* {str(error)}"
    await ctx.reply(content=error_message)


async def main():
    try:
        await bot.start(Config.TOKEN)
    except asyncio.CancelledError:
        bot.logger.error("The operation was cancelled.")
    except Exception as e:
        bot.logger.error(f"An unexpected error occurred: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
