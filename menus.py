import discord
from discord.ui import View
import asyncio


class TagListPaginator(View):
    def __init__(self, bot, pages):
        super().__init__()
        self.ctx = None
        self.bot = bot
        self.pages = pages
        self.current_page = 0
        self.message = None

    async def send_page(self, page_number):
        embed = self.pages[page_number]
        if self.message is None:
            self.message = await self.ctx.send(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)
        self.current_page = page_number

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="prev_button", row=1,
                       emoji="<:l_arrow:1169754353326903407>")
    async def on_prev_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Defer the interaction to prevent timeout
        await interaction.response.defer()

        # Show the previous page
        self.current_page = max(0, self.current_page - 1)
        await self.send_page(self.current_page)
        print('Prev button clicked!')

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="next_button", row=1,
                       emoji="<:arrow:1169695690784518154>️")
    async def on_next_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Defer the interaction to prevent timeout
        await interaction.response.defer()

        # Show the next page
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        await self.send_page(self.current_page)
        print('Next button clicked!')

    async def start(self, ctx, *, wait=False):
        self.ctx = ctx
        await self.send_page(self.current_page)

        if wait:
            return await self.wait()

        return self


class DeleteButton(discord.ui.View):
    """A view that allows users to delete messages."""
    allowed_role_id = 988055417907200010

    def __init__(self, bot_instance, message_id, channel_id, response_message, jump_url, *, timeout=None):
        super().__init__(timeout=timeout)
        self.bot = bot_instance
        self.message_id = message_id
        self.channel_id = channel_id
        self.response_message = response_message
        self.jump_url = jump_url

    @discord.ui.button(label="Quick Delete", style=discord.ButtonStyle.red)
    async def quick_delete_callback(self, interaction: discord.Interaction, _: discord.ui.Button):
        try:
            channel = await self.bot.fetch_channel(int(self.channel_id))

            member, message = await asyncio.gather(
                interaction.guild.fetch_member(interaction.user.id),
                channel.fetch_message(self.message_id),
            )

            if self.allowed_role_id in [role.id for role in member.roles]:
                deletion_tasks = [
                    self.response_message.delete(),
                    message.delete(),
                    interaction.message.delete()
                ]
                await asyncio.gather(*deletion_tasks)

                self.stop()
            else:
                await interaction.response.send_message("You do not have the required role to delete this message.",
                                                        ephemeral=True, delete_after=3)

        except discord.NotFound as e:
            self.bot.logger.error(f"Message with ID {self.message_id} not found. Error: {e}")
        except discord.Forbidden as e:
            self.bot.logger.error(f"Bot does not have permission to delete messages in channel {self.channel_id}. "
                                  f"Error: {e}")
        except Exception as e:
            self.bot.logger.error(f"An error occurred: {e}")
