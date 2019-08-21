import discord
import inspect
import traceback

from discord.ext import commands
from rethinkdb import RethinkDB
from io import StringIO
from contextlib import redirect_stdout
from textwrap import indent

r = RethinkDB()
r.set_loop_type("asyncio")


class RethinkCog(commands.Cog):
    """
    RethinkDB evaluation
    """

    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.initialised = False

    async def init(self):
        if self.initialised is True:
            return True
        else:
            connection = await r.connect()
            self.r, self.connection = r, connection
            return True

    @commands.command(aliases=["r"])
    @commands.is_owner()
    async def rethink(self, ctx: commands.Context, *, query: str):
        """Evaluate Rethink Database"""

        await self.init()

        env = {
            "ctx": ctx,
            "bot": self.bot,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "source": inspect.getsource,
            "discord": __import__("discord"),
            "r": self.r,
            "connection": self.connection
        }

        env.update(globals())

        body = self.cleanup_code(query)
        stdout = StringIO()

        to_compile = f'async def func():\n{indent(body, "  ")}'

        def paginate(text: str):
            """Simple generator that paginates text."""
            last = 0
            pages = []
            appd_index = curr = None
            for curr in range(0, len(text)):
                if curr % 1980 == 0:
                    pages.append(text[last:curr])
                    last = curr
                    appd_index = curr
            if appd_index != len(text) - 1:
                pages.append(text[last:curr])
            return list(filter(lambda a: a != "", pages))

        try:
            exec(to_compile, env)
        except Exception as exc:
            await ctx.send(f"```py\n{exc.__class__.__name__}: {exc}\n```")
            return await ctx.message.add_reaction("\u2049")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")
            return await ctx.message.add_reaction("\u2049")

        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    try:
                        await ctx.send(f"```py\n{value}\n```")
                    except Exception:
                        paginated_text = paginate(value)
                        for page in paginated_text:
                            if page == paginated_text[-1]:
                                await ctx.send(f"```py\n{page}\n```")
                                break
                            await ctx.send(f"```py\n{page}\n```")
            else:
                try:
                    await ctx.send(f"```py\n{value}{ret}\n```")
                except Exception:
                    paginated_text = paginate(f"{value}{ret}")
                    for page in paginated_text:
                        if page == paginated_text[-1]:
                            await ctx.send(f"```py\n{page}\n```")
                            break
                        await ctx.send(f"```py\n{page}\n```")

        try:
            exec(to_compile, env)
        except Exception as exc:
            await ctx.send(f"```py\n{exc.__class__.__name__}: {exc}\n```")
            return await ctx.message.add_reaction("\u2049")


    def cleanup_code(self, content: str) -> str:
        """
        Automatically removes code blocks from the code.
        Parameters
        ----------
        content : str
            The content to be cleaned.
        Returns
        -------
        str
            The cleaned content.
        """
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        # remove `foo`
        return content.strip("` \n")

def setup(bot: commands.Bot):
    bot.add_cog(RethinkCog(bot))
