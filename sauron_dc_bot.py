import discord
from discord.ext import commands
import random
import json
import os
from datetime import datetime
import asyncio

# Načti token z environment variable
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

if not TOKEN:
    print("❌ ERROR: DISCORD_BOT_TOKEN environment variable is not set!")
    print("📝 Please set it in Coolify Environment Variables.")
    print("🔗 Get your token at: https://discord.com/developers/applications")
    exit(1)

print(f"🚀 Starting Film Quiz Bot at {datetime.now()}")
print(f"📁 Data directory: {os.getenv('DATA_DIR', '/app/data')}")

# Konfigurace bota
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Cesty k datům
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if __file__ else '.'
DATA_DIR = os.getenv('DATA_DIR', SCRIPT_DIR)
DB_FILE = os.path.join(DATA_DIR, 'sauron_db.json')
QUESTIONS_FILE = os.path.join(SCRIPT_DIR, 'questions.json')
DISCORD_BUTTON_LABEL_MAX = 80

os.makedirs(DATA_DIR, exist_ok=True)

# Počítadlo zpráv pro kvízovou výzvu (náhodný interval)
message_counter = 0
next_kviz_trigger = random.randint(10, 15)
last_message_author = None
second_last_author = None

# ID kanálů, kde se kvíz zobrazuje (whitelist)
POVOLENE_KANALY = [
    1418609726186586184,
    1418616294646743171,
    1418617290471243818,
    1418615240744108185,
    1418615287015800832,
    1418618157668765736,
    1418624588665065683,
    1418629007510868189
]

BOT_ENABLED = True


def truncate_label(text, limit=DISCORD_BUTTON_LABEL_MAX):
    """Zkrátí popisek tlačítka na Discord limit 80 znaků."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def nacti_otazky():
    """Načte kvízové otázky z JSON databáze."""
    if not os.path.exists(QUESTIONS_FILE):
        print(f"❌ ERROR: Soubor s otázkami neexistuje: {QUESTIONS_FILE}")
        exit(1)

    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"❌ ERROR: Nepodařilo se načíst otázky: {exc}")
        exit(1)

    questions = data.get("questions") or []
    valid = []
    for item in questions:
        options = item.get("options") or []
        correct = item.get("correct")
        question = (item.get("question") or "").strip()
        if question and len(options) == 4 and correct in options:
            valid.append({
                "id": item.get("id"),
                "question": question,
                "options": [truncate_label(option) for option in options],
                "correct": truncate_label(correct),
                "note": item.get("note") or None,
            })

    if not valid:
        print("❌ ERROR: Databáze otázek je prázdná nebo neplatná.")
        exit(1)

    print(f"🎬 Načteno {len(valid)} kvízových otázek ze souboru {QUESTIONS_FILE}")
    return valid


QUESTIONS = nacti_otazky()


def nacti_databazi():
    """Načte databázi skóre ze souboru JSON."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def uloz_databazi(data):
    """Uloží databázi skóre do souboru JSON."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def pridej_body(user_id, user_name, body):
    """Přidá body uživateli. Minimum je 0, bez resetu na 100."""
    db = nacti_databazi()
    user_id_str = str(user_id)

    if user_id_str not in db:
        db[user_id_str] = {
            "name": user_name,
            "body": 0,
        }

    db[user_id_str]["body"] = max(0, db[user_id_str].get("body", 0) + body)
    db[user_id_str]["name"] = user_name
    uloz_databazi(db)
    return db[user_id_str]["body"]


def ziskej_statistiky(user_id):
    """Získá statistiky hráče (jméno a body)."""
    db = nacti_databazi()
    user_id_str = str(user_id)

    if user_id_str in db:
        return {
            "body": db[user_id_str].get("body", 0),
            "name": db[user_id_str].get("name", "Neznámý"),
        }
    return {"body": 0, "name": "Neznámý"}


def priprav_otazku():
    """Vybere náhodnou otázku a zamíchá možnosti."""
    otazka = random.choice(QUESTIONS)
    moznosti = list(otazka["options"])
    random.shuffle(moznosti)
    return otazka, moznosti


def vytvor_kviz_embed(otazka, test=False):
    """Vytvoří embed filmového kvízu."""
    embed = discord.Embed(
        title="🎬 Filmový kvíz",
        description=otazka["question"],
        color=discord.Color.gold(),
    )
    if test:
        embed.set_footer(text="⚠️ TESTOVACÍ REŽIM")
    return embed


class KvizView(discord.ui.View):
    """View se 4 šedými tlačítky pro filmový kvíz."""

    def __init__(self, spravna_odpoved, moznosti, note=None):
        super().__init__(timeout=300)
        self.spravna_odpoved = spravna_odpoved
        self.moznosti = moznosti
        self.note = note
        self.responded_users = set()
        self.correct_answers = []
        self.wrong_answers = []
        self.cleanup_task = None
        self.first_correct_answer = False
        self.summary_message = None
        self.choice_map = {}

        for index, moznost in enumerate(moznosti):
            custom_id = f"choice_{index}"
            button = discord.ui.Button(
                label=truncate_label(moznost),
                style=discord.ButtonStyle.secondary,
                custom_id=custom_id,
            )
            self.choice_map[custom_id] = (moznost == spravna_odpoved)
            button.callback = self._make_callback(custom_id)
            self.add_item(button)

    def _make_callback(self, custom_id):
        async def callback(interaction: discord.Interaction):
            await self.handle_button_click(interaction, custom_id)
        return callback

    async def handle_button_click(self, interaction: discord.Interaction, custom_id: str):
        """Zpracování kliknutí na tlačítko."""
        user_id = interaction.user.id
        user_name = interaction.user.display_name

        if user_id in self.responded_users:
            await interaction.response.send_message(
                "❌ Už jsi v této výzvě odpověděl(a)! Nemůžeš kliknout znovu.",
                ephemeral=True,
            )
            return

        self.responded_users.add(user_id)
        await interaction.response.defer(ephemeral=True)

        if self.choice_map.get(custom_id, False):
            nove_body = pridej_body(user_id, user_name, 1)
            self.correct_answers.append({
                "name": user_name,
                "body": nove_body,
            })

            if not self.first_correct_answer:
                self.first_correct_answer = True
                self.cleanup_task = asyncio.create_task(
                    self.cleanup_messages(interaction.message, interaction.channel)
                )
        else:
            nove_body = pridej_body(user_id, user_name, -1)
            self.wrong_answers.append({
                "name": user_name,
                "body": nove_body,
            })

    async def cleanup_messages(self, original_message, channel):
        """Po první správné odpovědi počká 3 s, obarví tlačítka a ukáže souhrn."""
        await asyncio.sleep(3)

        for child in self.children:
            child.disabled = True
            if isinstance(child, discord.ui.Button):
                if self.choice_map.get(child.custom_id, False):
                    child.style = discord.ButtonStyle.success
                else:
                    child.style = discord.ButtonStyle.danger

        try:
            await original_message.edit(view=self)
        except Exception:
            pass

        embed = discord.Embed(
            title="📊 Výsledky kvízu",
            color=discord.Color.blue(),
        )

        if self.correct_answers:
            correct_text = ""
            for player in self.correct_answers:
                correct_text += f"✅ **{player['name']}** - {player['body']} bodů\n"
            embed.add_field(
                name=f"✅ Správná odpověď: {self.spravna_odpoved}",
                value=correct_text,
                inline=False,
            )
        else:
            embed.add_field(
                name=f"✅ Správná odpověď: {self.spravna_odpoved}",
                value="Nikdo neodpověděl správně.",
                inline=False,
            )

        if self.wrong_answers:
            wrong_text = ""
            for player in self.wrong_answers:
                wrong_text += f"❌ **{player['name']}** - {player['body']} bodů\n"
            spatne = [p for p in self.moznosti if p != self.spravna_odpoved]
            embed.add_field(
                name=f"❌ Špatné volby: {', '.join(spatne)}",
                value=wrong_text,
                inline=False,
            )

        if self.note:
            embed.add_field(
                name="ℹ️ Poznámka",
                value=self.note[:1024],
                inline=False,
            )

        embed.set_footer(text="Zpráva se smaže za 12 sekund")
        self.summary_message = await channel.send(embed=embed)

        await asyncio.sleep(12)

        try:
            await original_message.delete()
        except Exception:
            pass

        try:
            await self.summary_message.delete()
        except Exception:
            pass


@bot.event
async def on_ready():
    """Event při spuštění bota."""
    print(f"✅ {bot.user.name} je připraven!")
    print(f"Bot ID: {bot.user.id}")
    print("------")


@bot.event
async def on_message(message):
    """Event při každé nové zprávě."""
    global message_counter, next_kviz_trigger, last_message_author, second_last_author

    if message.author.bot:
        return

    if not BOT_ENABLED:
        await bot.process_commands(message)
        return

    if POVOLENE_KANALY and message.channel.id not in POVOLENE_KANALY:
        await bot.process_commands(message)
        return

    current_author = message.author.id

    if (
        current_author == last_message_author
        or (current_author == second_last_author and second_last_author is not None)
    ):
        await bot.process_commands(message)
        return

    message_counter += 1
    second_last_author = last_message_author
    last_message_author = current_author

    if message_counter >= next_kviz_trigger:
        otazka, moznosti = priprav_otazku()
        embed = vytvor_kviz_embed(otazka)
        view = KvizView(otazka["correct"], moznosti, note=otazka.get("note"))
        await message.channel.send(embed=embed, view=view)

        message_counter = 0
        next_kviz_trigger = random.randint(10, 15)
        last_message_author = None
        second_last_author = None

    await bot.process_commands(message)


@bot.command(name="body")
async def zobraz_body(ctx):
    """Příkaz pro zobrazení bodů uživatele."""
    stats = ziskej_statistiky(ctx.author.id)
    embed = discord.Embed(
        title=f"📊 Skóre hráče {ctx.author.display_name}",
        description=f"⭐ **{stats['body']}** bodů",
        color=discord.Color.blue(),
    )
    embed.set_footer(text="Používej !zebricek pro aktuální žebříček.")

    message = await ctx.send(embed=embed)
    await asyncio.sleep(20)
    try:
        await message.delete()
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="zebricek")
async def zobraz_zebricek(ctx):
    """Příkaz pro zobrazení žebříčku hráčů podle bodů."""
    db = nacti_databazi()

    if not db:
        await ctx.send("Zatím nikdo nehrál!")
        return

    serazeni = sorted(
        db.items(),
        key=lambda x: x[1].get("body", 0),
        reverse=True,
    )

    embed = discord.Embed(
        title="🏆 Žebříček filmového kvízu",
        color=discord.Color.gold(),
    )

    hraci_text = ""
    for i, (user_id, data) in enumerate(serazeni[:10], 1):
        body = data.get("body", 0)
        pozice = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        try:
            member = await ctx.guild.fetch_member(int(user_id))
            jmeno = member.display_name
        except Exception:
            jmeno = data.get("name", "Neznámý")
        hraci_text += f"{pozice} **{jmeno}** - **{body}** bodů\n"

    embed.description = hraci_text or "Zatím nikdo nehrál!"
    embed.set_footer(text="Řazeno podle počtu bodů")

    message = await ctx.send(embed=embed)
    await asyncio.sleep(20)
    try:
        await message.delete()
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="kviz_test")
@commands.has_permissions(administrator=True)
async def kviz_test(ctx):
    """Příkaz pro adminy - manuálně vyvolá filmový kvíz."""
    otazka, moznosti = priprav_otazku()
    embed = vytvor_kviz_embed(otazka, test=True)
    view = KvizView(otazka["correct"], moznosti, note=otazka.get("note"))
    await ctx.send(embed=embed, view=view)

    try:
        await ctx.message.delete()
    except Exception:
        pass


@bot.event
async def on_command_error(ctx, error):
    """Zpracování chyb příkazů."""
    if isinstance(error, commands.MissingPermissions):
        if ctx.command and ctx.command.name in [
            "kviz_test",
            "kviz_stop",
            "kviz_start",
            "stav_bota",
            "reset_db",
        ]:
            await ctx.send("❌ Pouze administrátoři mohou použít tento příkaz!", delete_after=5)
            try:
                await ctx.message.delete()
            except Exception:
                pass


class ConfirmView(discord.ui.View):
    """View s tlačítky pro potvrzení smazání databáze."""

    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.value = None

    @discord.ui.button(label="✅ ANO, smazat vše", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Pouze autor příkazu může potvrdit!", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="❌ NE, zrušit", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Pouze autor příkazu může zrušit!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.defer()


@bot.command(name="reset_db")
@commands.has_permissions(administrator=True)
async def reset_databaze(ctx):
    """Příkaz pro adminy - smaže celou databázi skóre po potvrzení."""
    embed = discord.Embed(
        title="⚠️ VAROVÁNÍ - Smazání databáze",
        description=(
            "Chystáš se **SMAZAT CELOU DATABÁZI**!\n\n"
            "⚠️ Tato akce:\n"
            "• Smaže **všechny body** všech hráčů\n"
            "• **NELZE VRÁTIT ZPĚT**\n\n"
            "Opravdu chceš pokračovat?"
        ),
        color=discord.Color.red(),
    )
    embed.set_footer(text="Máš 30 sekund na rozhodnutí")

    view = ConfirmView(ctx.author.id)
    message = await ctx.send(embed=embed, view=view)
    await view.wait()

    try:
        await ctx.message.delete()
    except Exception:
        pass

    if view.value is None:
        embed_timeout = discord.Embed(
            title="⏱️ Časový limit vypršel",
            description="Smazání databáze bylo zrušeno (žádná odpověď).",
            color=discord.Color.orange(),
        )
        await message.edit(embed=embed_timeout, view=None)
        await message.delete(delay=5)
    elif view.value:
        try:
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)

            embed_success = discord.Embed(
                title="✅ Databáze smazána",
                description=(
                    "Databáze byla **úspěšně smazána**!\n\n"
                    "• Všechny body byly vymazány\n"
                    "• Nová databáze se vytvoří automaticky při první hře"
                ),
                color=discord.Color.green(),
            )
            await message.edit(embed=embed_success, view=None)
            await message.delete(delay=10)
            print(f"🗑️ Databáze smazána administrátorem: {ctx.author.name} ({ctx.author.id})")
        except Exception as e:
            embed_error = discord.Embed(
                title="❌ Chyba",
                description=f"Při mazání databáze došlo k chybě:\n```{str(e)}```",
                color=discord.Color.red(),
            )
            await message.edit(embed=embed_error, view=None)
            await message.delete(delay=10)
            print(f"❌ Chyba při mazání DB: {e}")
    else:
        embed_cancel = discord.Embed(
            title="❌ Zrušeno",
            description="Smazání databáze bylo zrušeno. Žádné změny nebyly provedeny.",
            color=discord.Color.blue(),
        )
        await message.edit(embed=embed_cancel, view=None)
        await message.delete(delay=5)


@bot.command(name="kviz_stop")
@commands.has_permissions(administrator=True)
async def kviz_stop(ctx):
    """Příkaz pro adminy - vypne automatické kvízové výzvy."""
    global BOT_ENABLED

    BOT_ENABLED = False
    embed = discord.Embed(
        title="⏸️ Filmový kvíz VYPNUT",
        description="Automatické výzvy jsou pozastavené. Příkazy fungují dál.\nPro zapnutí použij `!kviz_start`.",
        color=discord.Color.orange(),
    )
    await ctx.send(embed=embed, delete_after=10)
    try:
        await ctx.message.delete()
    except Exception:
        pass
    print(f"⏸️ Kvíz vypnut administrátorem: {ctx.author.name}")


@bot.command(name="kviz_start")
@commands.has_permissions(administrator=True)
async def kviz_start(ctx):
    """Příkaz pro adminy - zapne automatické kvízové výzvy."""
    global BOT_ENABLED, message_counter, next_kviz_trigger, last_message_author, second_last_author

    BOT_ENABLED = True
    message_counter = 0
    next_kviz_trigger = random.randint(10, 15)
    last_message_author = None
    second_last_author = None

    embed = discord.Embed(
        title="▶️ Filmový kvíz ZAPNUT",
        description="Automatické výzvy znovu běží. Začni psát zprávy a čekej na kvíz.",
        color=discord.Color.green(),
    )
    await ctx.send(embed=embed, delete_after=10)
    try:
        await ctx.message.delete()
    except Exception:
        pass
    print(f"▶️ Kvíz zapnut administrátorem: {ctx.author.name}")


@bot.command(name="stav_bota")
@commands.has_permissions(administrator=True)
async def stav_bota(ctx):
    """Příkaz pro adminy - zobrazí aktuální stav bota."""
    db = nacti_databazi()
    celkem_hracu = len(db)
    stav = "🟢 **ZAPNUT**" if BOT_ENABLED else "🔴 **VYPNUT**"

    embed = discord.Embed(
        title="🤖 Stav filmového kvízu",
        color=discord.Color.green() if BOT_ENABLED else discord.Color.red(),
    )
    embed.add_field(name="⚙️ Stav hry", value=stav, inline=True)
    embed.add_field(
        name="📊 Statistiky",
        value=f"👥 Hráčů: **{celkem_hracu}**\n🎬 Otázek v DB: **{len(QUESTIONS)}**",
        inline=False,
    )
    embed.add_field(
        name="🎮 Dostupné příkazy",
        value="`!kviz_stop` / `!kviz_start` - vypnutí a zapnutí kvízu\n`!kviz_test` - testovací otázka",
        inline=False,
    )

    message = await ctx.send(embed=embed)
    await asyncio.sleep(15)
    try:
        await message.delete()
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="help_kviz")
async def napoveda(ctx):
    """Příkaz pro zobrazení nápovědy."""
    embed = discord.Embed(
        title="📖 Nápověda - Filmový kvíz",
        description="Po několika zprávách v kanálu vyskočí otázka ze světa filmu a seriálů.",
        color=discord.Color.purple(),
    )
    embed.add_field(
        name="🎮 Jak hra funguje?",
        value=(
            "• Po **10–15 zprávách** se objeví kvízová otázka\n"
            "• Vyber jednu ze **4 možností** (všechna tlačítka jsou šedá)\n"
            "• Správná odpověď = **+1 bod**, špatná = **-1 bod** (minimum 0)\n"
            "• První správná odpověď zavře kolo za 3 sekundy"
        ),
        inline=False,
    )
    embed.add_field(
        name="📋 Příkazy",
        value=(
            "`!body` - Zobrazí tvoje body\n"
            "`!zebricek` - Žebříček hráčů\n"
            "`!help_kviz` - Zobrazí tuto nápovědu"
        ),
        inline=False,
    )
    message = await ctx.send(embed=embed)
    await asyncio.sleep(20)
    try:
        await message.delete()
        await ctx.message.delete()
    except Exception:
        pass


if __name__ == "__main__":
    print("✅ Token loaded successfully")
    print("🤖 Connecting to Discord...")
    bot.run(TOKEN)
