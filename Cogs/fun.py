import discord
from discord.ext import commands
import json
import aiohttp
import logging


class Fun(commands.Cog):
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.session = aiohttp.ClientSession()
        self.logger = logging.getLogger(__name__)

        # Load configuration from config.json
        self.config = self.load_config()

        self.headers = {
            "Dog-API": self.config["DOG_API_KEY"],
            "Cat-API": self.config["CAT_API_KEY"],
            "Accept": 'application/json',
        }

    @staticmethod
    def load_config():
        with open('./config.json', 'r') as config_file:
            return json.load(config_file)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @staticmethod
    def _is_non_empty_list(data):
        return isinstance(data, list) and bool(data)

    async def _fetch_data(self, url, headers=None, data_type='json'):
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await getattr(response, data_type)()
                else:
                    return f"Error fetching API.\n* **Status Code:** {response.status}"
        except aiohttp.ClientError as e:
            self.logger.error(f"Request error: {e}")
            return "Error fetching API. Please try again later."

    async def _process_image(self, ctx, data):
        if isinstance(data, str):
            await ctx.reply(data)
        elif self._is_non_empty_list(data) and isinstance(data[0], dict):
            image_url = data[0].get("url")
            if image_url:
                embed = discord.Embed(color=discord.Color.from_rgb(43, 45, 49))
                embed.set_image(url=image_url)
                await ctx.reply(embed=embed)
            else:
                await ctx.reply("Error extracting image URL from API response.")
        else:
            await ctx.reply("Unexpected response from API.")

    async def _create_embed(self, description, title=None, footer=None, image_url=None, author=None):
        embed = discord.Embed(
            description=description,
            color=discord.Color.from_rgb(43, 45, 49)
        )
        if title:
            embed.title = title
        if footer:
            embed.set_footer(text=footer)
        if image_url:
            embed.set_image(url=image_url)
        if author:
            embed.set_author(name=author)
        return embed

    @commands.hybrid_command(name="insult", with_app_command=True, description="Get a random insult")
    async def insult(self, ctx):
        insult_data = await self._fetch_data(self.config['INSULT_API_URL'], data_type='text')
        embed = await self._create_embed(insult_data)
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="buzzword", with_app_command=True, description="Get a random buzzword")
    async def buzzword(self, ctx):
        buzzword_data = await self._fetch_data(self.config['BUZZWORD_API_URL'])
        if isinstance(buzzword_data, str):
            await ctx.reply(buzzword_data)
        else:
            phrase = buzzword_data.get("phrase")
            if phrase:
                embed = await self._create_embed(phrase)
                await ctx.reply(embed=embed)
            else:
                await ctx.reply("Error extracting phrase from Buzzword API response.")

    @commands.hybrid_command(name="joke", with_app_command=True, description="Get a random joke")
    async def joke(self, ctx):
        joke_data = await self._fetch_data(self.config['JOKE_API_URL'])
        if isinstance(joke_data, str):
            await ctx.reply(joke_data)
        else:
            joke_type = joke_data.get("type")
            if joke_type == "single":
                joke = joke_data.get("joke")
            elif joke_type == "twopart":
                joke = f"{joke_data.get('setup')} - {joke_data.get('delivery')}"
            else:
                joke = None

            if joke:
                embed = await self._create_embed(
                    joke,
                    footer=f"Joke type: {joke_type} - This API is known to not produce very kind jokes. "
                           f"ERM is not responsible for the content of the jokes."
                )
                await ctx.reply(embed=embed)
            else:
                await ctx.reply("Error extracting joke from Joke API response.")

    @commands.hybrid_command(name="dog", with_app_command=True, description="Get a random dog image")
    async def dog(self, ctx):
        data = await self._fetch_data(self.config['DOG_API_URL'], headers=self.headers)
        await self._process_image(ctx, data)

    @commands.hybrid_command(name="cat", with_app_command=True, description="Get a random cat image")
    async def cat(self, ctx):
        data = await self._fetch_data(self.config['CAT_API_URL'], headers=self.headers)
        await self._process_image(ctx, data)

    @commands.hybrid_command(name="meme", with_app_command=True, description="Get a random meme")
    async def meme(self, ctx):
        meme_data = await self._fetch_data(self.config['MEME_API_URL'])

        if isinstance(meme_data, str):
            await ctx.reply(meme_data)
        elif isinstance(meme_data, dict):
            title = meme_data.get('title')
            image_url = meme_data.get('url')

            if title and image_url:
                embed = await self._create_embed(
                    description=title,
                    image_url=image_url
                )
                await ctx.reply(embed=embed)
            else:
                await ctx.reply("Error extracting title or image URL from Meme API response.")
        else:
            await ctx.reply("Unexpected response from Meme API.")

    @commands.hybrid_command(name="age", with_app_command=True, description="Get the age of a person")
    async def age(self, ctx, name):
        if name.lower() in ['noah']:
            embed = await self._create_embed(
                description="After consulting Noah's mother, she says that Noah is **69420**.",
                title='Noah'
            )
            await ctx.reply(embed=embed)
            return
    
        capitalized_name = name.capitalize()
        age_data = await self._fetch_data(f"{self.config['AGEIFY_URL']}?name={capitalized_name}")
        if isinstance(age_data, str):
            await ctx.reply(age_data)
        else:
            age_data_response = age_data.get("age", None)
            if age_data_response is None:
                embed = await self._create_embed(
                    description=f"Unfortunately, {capitalized_name} appears to not have an age.",
                    title="No Age :("
                )
            else:
                embed = await self._create_embed(
                    description=f"After consulting {capitalized_name}'s mother, she says that {capitalized_name} is **{age_data_response}**.",
                    title=capitalized_name
                )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name="country", with_app_command=True, description="Get information about a country")
    async def country(self, ctx, *, country_name: str):
        if country_name.lower() in ["africa", "african"]:
            embed = await self._create_embed(
                description="Africa is not a country, it's a continent..",
                image_url="https://media3.giphy.com/media/3o85xnoIXebk3xYx4Q/giphy.gif"
            )
            await ctx.reply(embed=embed)
            return

        country_data = await self._fetch_data(f"{self.config['REST_COUNTRIES_API_URL']}{country_name}")

        if isinstance(country_data, str):
            await ctx.reply(country_data)
        else:
            country_info = country_data[0] if isinstance(country_data, list) and len(country_data) > 0 else None

            if country_info:
                embed = discord.Embed(
                    title=f"Information for {country_info['name']['common']}",
                    color=discord.Color.from_rgb(43, 45, 49),
                )
                embed.add_field(name="Capital", value=country_info.get("capital", ["Not available"])[0], inline=True)
                embed.add_field(name="Region", value=country_info.get("region", "Not available"), inline=True)
                embed.add_field(name="Population", value=country_info.get("population", "Not available"), inline=True)
                await ctx.reply(embed=embed)
            else:
                await ctx.reply("No information available for the specified country.")

    @commands.hybrid_command(name="trump", with_app_command=True, description="Get a random quote from Donald Trump")
    async def trump(self, ctx):
        quote_data = await self._fetch_data(self.config['TRONALD_DUMP_API_URL'], headers=self.headers)
        if isinstance(quote_data, str):
            await ctx.reply(quote_data)
        else:
            quote_response = quote_data.get("value", "No quote available")
            embed = await self._create_embed(
                description=quote_response,
                author="Donald Trump"
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name="fact", with_app_command=True, description="Get a random fact")
    async def fact(self, ctx):
        fact_data = await self._fetch_data(self.config['FACT_API_URL'])
        if isinstance(fact_data, str):
            await ctx.reply(fact_data)
        else:
            fact_response = fact_data.get("text", "No fact available")
            embed = await self._create_embed(fact_response)
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name="quote", with_app_command=True, description="Get a random quote")
    async def quote(self, ctx):
        quote_data = await self._fetch_data(self.config['QUOTE_API_URL'])
        if isinstance(quote_data, str):
            await ctx.reply(quote_data)
        else:
            quote_response = quote_data.get("content", "No quote available")
            quote_author = quote_data.get("author", "No author available")
            embed = await self._create_embed(
                description=f"'{quote_response}' - {quote_author}"
            )
            await ctx.reply(embed=embed)

    @commands.hybrid_command(name="urban", with_app_command=True, description="Get a definition from Urban Dictionary")
    async def urban(self, ctx, *, term):
        term = term.replace(" ", "+")
        url = f"{self.config['URBAN_DICTIONARY_API_URL']}{term}"
        urban_data = await self._fetch_data(url)
        if isinstance(urban_data, str):
            await ctx.reply(urban_data)
        else:
            urban_response = urban_data.get("list", "No definition available")
            if urban_response:
                definition = urban_response[0].get("definition", "No definition available")
                example = urban_response[0].get("example", "No example available")
                embed = await self._create_embed(
                    description=definition
                )
                embed.add_field(name="Example", value=example, inline=False)
                await ctx.reply(embed=embed)
            else:
                await ctx.reply("No definition available for the specified term.")


async def setup(bot_instance):
    await bot_instance.add_cog(Fun(bot_instance))
