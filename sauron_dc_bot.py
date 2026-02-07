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

print(f"🚀 Starting Sauron Bot at {datetime.now()}")
print(f"📁 Data directory: {os.getenv('DATA_DIR', '/app/data')}")

# Konfigurace bota
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Cesta k databázi - pro Docker/Coolify
DATA_DIR = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)) if __file__ else '.')
DB_FILE = os.path.join(DATA_DIR, 'sauron_db.json')

# Vytvoř složku, pokud neexistuje
os.makedirs(DATA_DIR, exist_ok=True)

# Počítadlo zpráv pro Sauronovu výzvu (náhodný interval)
message_counter = 0
next_sauron_trigger = random.randint(8, 12)  # První trigger mezi 8-12 zprávami
last_message_author = None  # ID posledního autora zprávy
second_last_author = None  # ID předposledního autora zprávy

# ID kanálů, kde se BUDE zobrazovat Sauron (whitelist)
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

# Globální proměnná pro stav hry
BOT_ENABLED = True  # Hra je ve výchozím stavu zapnutá

# Globální proměnná pro číslo sezóny
CURRENT_SEASON = 1

# Hlavní postavy (dobré postavy)
HLAVNI_POSTAVY = [
    # Původní hobiti a společenstvo (SEASON 1)
    "Frodo",
    "Sam",
    "Gandalf",
    "Aragorn",
    "Legolas",    
    "Pipin",
    "Boromir",    
    "Elrond",
    "Faramir",
    
    # Nové postavy - Hobiti
    "Smíšek",
    "Bilbo",
    
    # Nové postavy - Elfové
    "Galadriel",
    "Arwen",    
    "Haldir",        
    
    # Nové postavy - Trpaslíci
    "Gimli",
    "Thorin",
    "Balin",
    "Dwalin",
    "Fíli",
    "Kíli",
    
    # Nové postavy - Lidé
    "Éowyn",
    "Théoden",
    "Éomer",    
    
    # Nové postavy - Čarodějové a Enti
    "Radagast",
    "Stromovous",       
    
]

# Záporné postavy
ZLE_POSTAVY = [
    # Původní záporáci(SEASON 1)
    "Glum",  
    "Saruman",
    "Skřet",
    "Nazgûl",    
    "Lurtz",
    
    # Nové postavy - Hlavní antagonisté    
    "Odula",
    "Balrog",    
    
    # Nové postavy - Skřeti a Orkové
    "Azog",
    "Bolg",
    "Gothmog",
    "Grishnákh",
    "Shagrat",
    "Gorbag",
    "Uglúk",
    "Mauhúr",   
    
    # Nové postavy - Vedlejší antagonisté
    "Gríma Červivec",       
    
]

# Story mód - Lokace a jejich úrovně (podle cesty Společenstva prstenu)
LOKACE = [
    {"nazev": "Kraj", "min_body": 0, "max_body": 9, "emoji": "🌾", "popis": "Začínáš svou cestu v poklidném Hobitíně"},
    {"nazev": "Hůrka", "min_body": 10, "max_body": 19, "emoji": "🍺", "popis": "Dorazil jsi do hostince Skákavý poník"},
    {"nazev": "Větrov", "min_body": 20, "max_body": 29, "emoji": "⛰️", "popis": "Noc přečkáš na zřícenině Amon Sûl"},
    {"nazev": "Roklinka", "min_body": 30, "max_body": 39, "emoji": "🏰", "popis": "Našel jsi útočiště v Elrondově sídle"},
    {"nazev": "Moria", "min_body": 40, "max_body": 49, "emoji": "⚒️", "popis": "Procházíš temnými doly Khazad-dûm"},
    {"nazev": "Lothlórien", "min_body": 50, "max_body": 59, "emoji": "🌳", "popis": "Odpočíváš ve zlatém lese paní Galadriel"},
    {"nazev": "Rohan", "min_body": 60, "max_body": 69, "emoji": "🐎", "popis": "Země jezdců Rohirů tě vítá"},
    {"nazev": "Helmův žleb", "min_body": 70, "max_body": 79, "emoji": "🛡️", "popis": "Připravuješ se na obranu pevnosti"},
    {"nazev": "Minas Tirith", "min_body": 80, "max_body": 89, "emoji": "🏛️", "popis": "Bílé město Gondoru stojí před obležením"},
    {"nazev": "Černá brána", "min_body": 90, "max_body": 99, "emoji": "🚪", "popis": "Stojíš před Morannon, branou do Mordoru"},
    {"nazev": "Mordor", "min_body": 100, "max_body": 999999, "emoji": "🌋", "popis": "Vystupuješ na Orodruinu, Horu osudu!"}
]


def nacti_databazi():
    """Načte databázi ze souboru JSON."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def uloz_databazi(data):
    """Uloží databázi do souboru JSON."""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def pridej_body(user_id, user_name, body):
    """Přidá body uživateli do databáze."""
    db = nacti_databazi()
    user_id_str = str(user_id)
    
    if user_id_str not in db:
        db[user_id_str] = {
            'name': user_name,
            'body': 0,
            'prsteny': 0
        }
    
    stare_body = db[user_id_str]['body']
    db[user_id_str]['body'] += body
    
    # Zabránění minusovým bodům - minimum je 0
    if db[user_id_str]['body'] < 0:
        db[user_id_str]['body'] = 0
    
    db[user_id_str]['name'] = user_name  # Aktualizace jména
    
    # Kontrola, jestli hráč dosáhl 100 bodů (dokončil příběh)
    nove_body = db[user_id_str]['body']
    
    if nove_body >= 100 and stare_body < 100:
        # Hráč dokončil příběh!
        db[user_id_str]['prsteny'] = db[user_id_str].get('prsteny', 0) + 1
        db[user_id_str]['body'] = 0  # Reset bodů
        uloz_databazi(db)
        return {'body': 0, 'prsten_ziskan': True, 'celkem_prstenu': db[user_id_str]['prsteny']}
    
    uloz_databazi(db)
    return {'body': db[user_id_str]['body'], 'prsten_ziskan': False}


def ziskej_body(user_id):
    """Získá aktuální počet bodů uživatele."""
    db = nacti_databazi()
    user_id_str = str(user_id)
    
    if user_id_str in db:
        return db[user_id_str]['body']
    return 0


def ziskej_lokaci(body):
    """Určí lokaci podle počtu bodů."""
    for lokace in LOKACE:
        if lokace['min_body'] <= body <= lokace['max_body']:
            return lokace
    return LOKACE[0]  # Default Roklinka


def ziskej_statistiky(user_id):
    """Získá kompletní statistiky hráče."""
    db = nacti_databazi()
    user_id_str = str(user_id)
    
    if user_id_str in db:
        return {
            'body': db[user_id_str].get('body', 0),
            'prsteny': db[user_id_str].get('prsteny', 0),
            'name': db[user_id_str].get('name', 'Neznámý')
        }
    return {'body': 0, 'prsteny': 0, 'name': 'Neznámý'}


class SauronView(discord.ui.View):
    """View s tlačítky pro výběr postavy."""
    
    def __init__(self, spravna_postava, vsechny_postavy):
        super().__init__(timeout=300)  # 5 minut timeout
        self.spravna_postava = spravna_postava
        self.vsechny_postavy = vsechny_postavy
        self.responded_users = set()  # Sada uživatelů, kteří už odpověděli
        self.correct_answers = []  # Seznam hráčů, kteří klikli správně (jméno, body, lokace, prsten)
        self.wrong_answers = []  # Seznam hráčů, kteří klikli špatně (jméno, body, lokace)
        self.cleanup_task = None  # Task pro úklid zpráv
        self.first_correct_answer = False  # Flag pro první správnou odpověď
        self.summary_message = None  # Souhrnná zpráva
        self.choice_map = {}  # Map custom_id -> True/False (správnost volby)
        
        # Vytvoření 3 tlačítek - VŠECHNY ŠEDÉ (secondary) aby hráči museli číst!
        # Postavy jsou už zamíchané náhodně
        button1 = discord.ui.Button(
            label=vsechny_postavy[0],
            style=discord.ButtonStyle.secondary,
            custom_id='choice_0'
        )
        button2 = discord.ui.Button(
            label=vsechny_postavy[1],
            style=discord.ButtonStyle.secondary,
            custom_id='choice_1'
        )
        button3 = discord.ui.Button(
            label=vsechny_postavy[2],
            style=discord.ButtonStyle.secondary,
            custom_id='choice_2'
        )

        # Unikátní custom_id vyžaduje mapování správné volby
        self.choice_map['choice_0'] = (vsechny_postavy[0] == spravna_postava)
        self.choice_map['choice_1'] = (vsechny_postavy[1] == spravna_postava)
        self.choice_map['choice_2'] = (vsechny_postavy[2] == spravna_postava)
        
        button1.callback = self.button1_callback
        button2.callback = self.button2_callback
        button3.callback = self.button3_callback
        
        self.add_item(button1)
        self.add_item(button2)
        self.add_item(button3)
    
    async def button1_callback(self, interaction: discord.Interaction):
        """Callback pro první tlačítko."""
        await self.handle_button_click(interaction, self.children[0].custom_id)
    
    async def button2_callback(self, interaction: discord.Interaction):
        """Callback pro druhé tlačítko."""
        await self.handle_button_click(interaction, self.children[1].custom_id)
    
    async def button3_callback(self, interaction: discord.Interaction):
        """Callback pro třetí tlačítko."""
        await self.handle_button_click(interaction, self.children[2].custom_id)
    
    async def handle_button_click(self, interaction: discord.Interaction, custom_id: str):
        """Zpracování kliknutí na tlačítko."""
        user_id = interaction.user.id
        user_name = interaction.user.display_name
        
        # Zkontroluj, jestli uživatel už kliknul
        if user_id in self.responded_users:
            await interaction.response.send_message(
                "❌ Už jsi v této výzvě odpověděl(a)! Nemůžeš kliknout znovu.",
                ephemeral=True
            )
            return
        
        # Přidej uživatele do seznamu, kteří odpověděli
        self.responded_users.add(user_id)
        
        # Potvrď interakci bez viditelné zprávy
        await interaction.response.defer(ephemeral=True)
        
        if self.choice_map.get(custom_id, False):
            # Správná volba - přidej +1 bod
            vysledek = pridej_body(user_id, user_name, 1)
            
            # Kontrola, jestli je výsledek dict (nový formát) nebo int (starý)
            if isinstance(vysledek, dict):
                nove_body = vysledek['body']
                prsten_ziskan = vysledek['prsten_ziskan']
                
                if prsten_ziskan:
                    # HRÁČ DOKONČIL PŘÍBĚH! - Pošli OKAMŽITĚ výherní zprávu
                    embed_win = discord.Embed(
                        title="🏆 VÝHRA! PRSTEN ZNIČEN! 🏆",
                        description=(
                            f"**{user_name}** dokončil(a) epickou cestu a dostal(a) se do Mordoru!\n\n"
                            f"🌋 Prsten byl shozen do Hory Osudu a zničen!\n\n"
                            f"💍 Získává **PRSTEN MOCI** do sbírky!\n"
                            f"✨ Celkem prstenů: **{vysledek['celkem_prstenu']}**\n\n"
                            f"🔄 Cesta začíná znovu od Kraje..."
                        ),
                        color=discord.Color.gold()
                    )
                    embed_win.set_footer(text="🎉 Gratulujeme k dokončení příběhu!")
                    await interaction.channel.send(embed=embed_win)
                    
                    lokace = ziskej_lokaci(nove_body)
                    self.correct_answers.append({
                        'name': user_name,
                        'body': nove_body,
                        'lokace': lokace,
                        'prsten': True,
                        'celkem_prstenu': vysledek['celkem_prstenu']
                    })
                else:
                    lokace = ziskej_lokaci(nove_body)
                    self.correct_answers.append({
                        'name': user_name,
                        'body': nove_body,
                        'lokace': lokace,
                        'prsten': False
                    })
            else:
                # Starý formát (pro zpětnou kompatibilitu)
                nove_body = vysledek
                lokace = ziskej_lokaci(nove_body)
                self.correct_answers.append({
                    'name': user_name,
                    'body': nove_body,
                    'lokace': lokace,
                    'prsten': False
                })
            
            # Pokud je to PRVNÍ správná odpověď, naplánuj úklid
            if not self.first_correct_answer:
                self.first_correct_answer = True
                # Vytvoř task pro smazání zpráv po 3 sekundách (doba pro další hráče)
                self.cleanup_task = asyncio.create_task(self.cleanup_messages(interaction.message, interaction.channel))
        else:
            # Špatná volba - odečti -1 bod, ale HRA POKRAČUJE pro ostatní
            vysledek = pridej_body(user_id, user_name, -1)
            
            if isinstance(vysledek, dict):
                nove_body = vysledek['body']
            else:
                nove_body = vysledek
            
            lokace = ziskej_lokaci(max(0, nove_body))
            self.wrong_answers.append({
                'name': user_name,
                'body': nove_body,
                'lokace': lokace
            })
    
    async def cleanup_messages(self, original_message, channel):
        """Smaže všechny zprávy po 3 sekundách od první správné odpovědi."""
        await asyncio.sleep(3)  # Počkej 3 sekundy na další hráče
        
        # Vypni tlačítka
        for child in self.children:
            child.disabled = True
        
        try:
            await original_message.edit(view=self)
        except:
            pass
        
        # Vytvoř souhrnnou zprávu
        embed = discord.Embed(
            title="📊 Výsledky výzvy",
            color=discord.Color.blue()
        )
        
        # Přidej správné odpovědi
        if self.correct_answers:
            correct_text = ""
            for player in self.correct_answers:
                if player.get('prsten', False):
                    # Prsten - nezobrazuj v souhrnu, už byla samostatná zpráva
                    correct_text += f"🏆 **{player['name']}** - 💍 Získal(a) PRSTEN! (Reset na 0 bodů)\n"
                else:
                    correct_text += f"✅ **{player['name']}** - {player['lokace']['emoji']} {player['body']} bodů ({player['lokace']['nazev']})\n"
            
            embed.add_field(
                name=f"✅ Správná volba: {self.spravna_postava}",
                value=correct_text,
                inline=False
            )
        
        # Přidej špatné odpovědi
        if self.wrong_answers:
            wrong_text = ""
            for player in self.wrong_answers:
                wrong_text += f"❌ **{player['name']}** - {player['lokace']['emoji']} {player['body']} bodů ({player['lokace']['nazev']})\n"
            
            # Zjisti špatné postavy (všechny kromě správné)
            spatne_postavy = [p for p in self.vsechny_postavy if p != self.spravna_postava]
            spatne_text = ", ".join(spatne_postavy)
            
            embed.add_field(
                name=f"❌ Špatné volby: {spatne_text}",
                value=wrong_text,
                inline=False
            )
        
        embed.set_footer(text="Zpráva se automaticky smaže za 12 sekund")
        
        # Pošli souhrnnou zprávu
        self.summary_message = await channel.send(embed=embed)
        
        # Počkej dalších 12 sekund (celkem 15s) pro přečtení výsledků
        await asyncio.sleep(12)
        
        # Smaž původní zprávu
        try:
            await original_message.delete()
        except:
            pass
        
        # Smaž souhrnnou zprávu
        try:
            await self.summary_message.delete()
        except:
            pass


@bot.event
async def on_ready():
    """Event při spuštění bota."""
    print(f'✅ {bot.user.name} je připraven!')
    print(f'Bot ID: {bot.user.id}')
    print('------')


@bot.event
async def on_message(message):
    """Event při každé nové zprávě."""
    global message_counter, next_sauron_trigger, last_message_author, second_last_author
    
    # Ignoruj zprávy od botů
    if message.author.bot:
        return
    
    # 🛑 KONTROLA: Pokud je bot vypnutý, nereaguj na zprávy (pouze příkazy)
    if not BOT_ENABLED:
        await bot.process_commands(message)
        return
    
    # KONTROLA: Zkontroluj, jestli je kanál povolen
    if POVOLENE_KANALY and message.channel.id not in POVOLENE_KANALY:
        await bot.process_commands(message)
        return  # Sauron se nezobrazí v nepovoleném kanálu
    
    current_author = message.author.id
    
    # 🛡️ ANTI-SPAM: Pokročilá ochrana proti vzájemnému spamování
    # Zpráva se NEPOČÍTÁ pokud:
    # 1. Je od stejného autora jako poslední zpráva (původní ochrana)
    # 2. Je od autora, který se střídá s předposledním (vzájemný spam)
    
    if (current_author == last_message_author or 
        (current_author == second_last_author and second_last_author is not None)):
        # Zpráva se NEPOČÍTÁ (spam nebo vzájemný spam)
        await bot.process_commands(message)
        return
    
    # Zpráva se POČÍTÁ - aktualizuj historii autorů
    message_counter += 1
    
    # Posuň historii autorů
    second_last_author = last_message_author
    last_message_author = current_author
    
    # Zkontroluj, jestli je čas na Sauronovu výzvu (každých 10-15 zpráv)
    if message_counter >= next_sauron_trigger:
        # Vyber náhodnou hlavní postavu (správná) a 2 náhodné záporné postavy (špatné)
        spravna_postava = random.choice(HLAVNI_POSTAVY)
        zle_postavy = random.sample(ZLE_POSTAVY, 2)  # Vyber 2 různé záporné postavy
        
        # Vytvoř seznam všech 3 postav a zamíchej je náhodně
        vsechny_postavy = [spravna_postava] + zle_postavy
        random.shuffle(vsechny_postavy)
        
        # Vytvoření embedu
        embed = discord.Embed(
            title="👁️ SAURON HLEDÁ SVŮJ PRSTEN! 👁️",
            description=(
                "Temný pán Sauron se probouzí a hledá svůj Prsten Moci!\n\n"
                "Musíš se rozhodnout, komu svěříš svůj osud a s kým půjdeš na své cestě k jeho zničení.\n"
                "**Vyber moudře, tvá volba bude mít následky...**"
            ),
            color=discord.Color.dark_red()  # Tmavě červená - barví jen levý pruh embedu
        )
        # Thumbnail odstraněn - bot má vlastní ikonu
        embed.set_footer(text="Vyber si jednu z postav níže")
        
        # Vytvoření view s tlačítky
        view = SauronView(spravna_postava, vsechny_postavy)
        
        # Odeslání zprávy
        await message.channel.send(embed=embed, view=view)
        
        # Reset počítadla a nastav nový náhodný trigger (8-12 zpráv)
        message_counter = 0
        next_sauron_trigger = random.randint(8, 12)
        last_message_author = None  # Reset posledního autora
        second_last_author = None  # Reset předposledního autora
    
    # Zpracování příkazů
    await bot.process_commands(message)


@bot.command(name='body')
async def zobraz_body(ctx):
    """Příkaz pro zobrazení bodů a postupu uživatele."""
    user_id = ctx.author.id
    stats = ziskej_statistiky(user_id)
    body = stats['body']
    prsteny = stats['prsteny']
    
    lokace = ziskej_lokaci(body)
    
    # Výpočet postupu do další lokace
    nasledujici_lokace = None
    body_do_dalsi = 0
    
    for lok in LOKACE:
        if lok['min_body'] > body:
            nasledujici_lokace = lok
            body_do_dalsi = lok['min_body'] - body
            break
    
    embed = discord.Embed(
        title=f"📊 Postup hráče {ctx.author.display_name}",
        description=f"💍 **Prstenů získano:** {prsteny}\n",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📍 Aktuální lokace",
        value=f"{lokace['emoji']} **{lokace['nazev']}**\n_{lokace['popis']}_",
        inline=False
    )
    
    embed.add_field(
        name="⭐ Body v tomto kole",
        value=f"**{body}** bodů",
        inline=True
    )
    
    if nasledujici_lokace:
        embed.add_field(
            name="🎯 Další lokace",
            value=f"{nasledujici_lokace['emoji']} {nasledujici_lokace['nazev']}\n(zbývá **{body_do_dalsi}** bodů)",
            inline=True
        )
    else:
        embed.add_field(
            name="🎯 Další krok",
            value=f"🌋 Dosáhni **100 bodů** pro zničení prstenu!",
            inline=True
        )
    
    embed.set_footer(text="Používej !zebricek pro aktuální žebříček.")
    
    message = await ctx.send(embed=embed)
    
    # Počkej 20 sekund a smaž zprávu
    import asyncio
    await asyncio.sleep(20)
    try:
        await message.delete()
        await ctx.message.delete()  # Smaž i příkaz uživatele
    except:
        pass


@bot.command(name='zebricek')
async def zobraz_zebricek(ctx):
    """Příkaz pro zobrazení žebříčku hráčů podle prstenů."""
    db = nacti_databazi()
    
    if not db:
        await ctx.send("Zatím nikdo nehrál!")
        return
    
    # Seřazení podle prstenů (hlavní), pak podle bodů
    serazeni = sorted(
        db.items(), 
        key=lambda x: (x[1].get('prsteny', 0), x[1].get('body', 0)), 
        reverse=True
    )
    
    # Rozdělení do sekcí
    vitezove = [(uid, d) for uid, d in serazeni if d.get('prsteny', 0) > 0]
    hraci = [(uid, d) for uid, d in serazeni if d.get('prsteny', 0) == 0]
    
    embed = discord.Embed(
        title="🏆 Žebříček Pánů Prstenů",
        color=discord.Color.gold()
    )
    
    # Sekce: Vítězové s prsteny
    if vitezove:
        vitez_text = "**🏅 Legendární hrdinové, kteří zničili prsten:**\n\n"
        for i, (user_id, data) in enumerate(vitezove[:10], 1):  # Top 10 vítězů
            prsteny = data.get('prsteny', 0)
            body = data.get('body', 0)
            medaile = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            lokace = ziskej_lokaci(body)
            
            # Získej aktuální display_name ze serveru
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                jmeno = member.display_name
            except:
                jmeno = data.get('name', 'Neznámý')
            
            vitez_text += f"{medaile} **{jmeno}** - 💍 {prsteny} {'prsten' if prsteny == 1 else 'prsteny' if prsteny < 5 else 'prstenů'} | {lokace['emoji']} {body} bodů\n"
        embed.description = vitez_text
    
    # Sekce: Aktuální hráči na cestě
    if hraci:
        hraci_text = ""
        for i, (user_id, data) in enumerate(hraci[:10], 1):  # Top 10 aktuálních hráčů
            body = data.get('body', 0)
            lokace = ziskej_lokaci(body)
            pozice = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            # Získej aktuální display_name ze serveru
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                jmeno = member.display_name
            except:
                jmeno = data.get('name', 'Neznámý')
            
            hraci_text += f"{pozice} **{jmeno}** - {lokace['emoji']} **{body}** bodů ({lokace['nazev']})\n"
        
        embed.add_field(
            name="⚔️ Aktuální hráči na cestě:",
            value=hraci_text if hraci_text else "Nikdo není na cestě.",
            inline=False
        )
    
    if not vitezove and not hraci:
        embed.description = "🌟 Zatím nikdo nehrál! Buď první, kdo se vydá na cestu do Mordoru!"
    
    embed.set_footer(text="Dosáhni 100 bodů pro zničení prstenu a vstup do síně slávy!")
    
    message = await ctx.send(embed=embed)
    
    # Počkej 20 sekund a smaž zprávu
    import asyncio
    await asyncio.sleep(20)
    try:
        await message.delete()
        await ctx.message.delete()  # Smaž i příkaz uživatele
    except:
        pass


@bot.command(name='sauron_test')
@commands.has_permissions(administrator=True)
async def sauron_test(ctx):
    """Příkaz pro adminy - manuálně vyvolá Sauronovu výzvu pro testování."""
    # Vyber náhodnou hlavní postavu (správná) a 2 náhodné záporné postavy (špatné)
    spravna_postava = random.choice(HLAVNI_POSTAVY)
    zle_postavy = random.sample(ZLE_POSTAVY, 2)
    
    # Vytvoř seznam všech 3 postav a zamíchej je náhodně
    vsechny_postavy = [spravna_postava] + zle_postavy
    random.shuffle(vsechny_postavy)
    
    # Vytvoření embedu
    embed = discord.Embed(
        title="👁️ SAURON HLEDÁ SVŮJ PRSTEN! 👁️",
        description=(
            "Temný pán Sauron se probouzí a hledá svůj Prsten Moci!\n\n"
            "Musíš se rozhodnout, komu svěříš svůj osud a s kým půjdeš na své cestě k jeho zničení.\n"
            "**Vyber moudře, tvá volba bude mít následky...**"
        ),
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="⚠️ TESTOVACÍ REŽIM - Vyvolání adminem | Vyber si jednu z postav níže")
    
    # Vytvoření view s tlačítky
    view = SauronView(spravna_postava, vsechny_postavy)
    
    # Odeslání zprávy
    await ctx.send(embed=embed, view=view)
    
    # Smaž příkaz
    try:
        await ctx.message.delete()
    except:
        pass


@bot.event
async def on_command_error(ctx, error):
    """Zpracování chyb příkazů."""
    if isinstance(error, commands.MissingPermissions):
        if ctx.command.name in ['sauron_test', 'konec_sezony', 'nova_sezona', 'stav_bota', 'reset_db']:
            await ctx.send("❌ Pouze administrátoři mohou použít tento příkaz!", delete_after=5)
            try:
                await ctx.message.delete()
            except:
                pass


class ConfirmView(discord.ui.View):
    """View s tlačítky pro potvrzení smazání databáze."""
    
    def __init__(self, user_id):
        super().__init__(timeout=30)  # 30 sekund timeout
        self.user_id = user_id
        self.value = None
    
    @discord.ui.button(label="✅ ANO, smazat vše", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Potvrzení smazání."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Pouze autor příkazu může potvrdit!", ephemeral=True)
            return
        
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @discord.ui.button(label="❌ NE, zrušit", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Zrušení akce."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Pouze autor příkazu může zrušit!", ephemeral=True)
            return
        
        self.value = False
        self.stop()
        await interaction.response.defer()


@bot.command(name='reset_db')
@commands.has_permissions(administrator=True)
async def reset_databaze(ctx):
    """Příkaz pro adminy - smaže celou databázi po potvrzení."""
    # Vytvoření potvrzovací zprávy
    embed = discord.Embed(
        title="⚠️ VAROVÁNÍ - Smazání databáze",
        description=(
            "Chystáš se **SMAZAT CELOU DATABÁZI**!\n\n"
            "⚠️ Tato akce:\n"
            "• Smaže **všechny body** všech hráčů\n"
            "• Smaže **všechny prsteny** všech hráčů\n"
            "• **NELZE VRÁTIT ZPĚT**\n\n"
            "Opravdu chceš pokračovat?"
        ),
        color=discord.Color.red()
    )
    embed.set_footer(text="Máš 30 sekund na rozhodnutí")
    
    # Vytvoření view s tlačítky
    view = ConfirmView(ctx.author.id)
    
    # Odeslání potvrzovací zprávy
    message = await ctx.send(embed=embed, view=view)
    
    # Počkej na odpověď
    await view.wait()
    
    # Smaž příkaz
    try:
        await ctx.message.delete()
    except:
        pass
    
    if view.value is None:
        # Timeout - žádná odpověď
        embed_timeout = discord.Embed(
            title="⏱️ Časový limit vypršel",
            description="Smazání databáze bylo zrušeno (žádná odpověď).",
            color=discord.Color.orange()
        )
        await message.edit(embed=embed_timeout, view=None)
        await message.delete(delay=5)
        
    elif view.value:
        # Potvrzeno - smaž databázi
        try:
            # Smaž soubor databáze
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            
            embed_success = discord.Embed(
                title="✅ Databáze smazána",
                description=(
                    "Databáze byla **úspěšně smazána**!\n\n"
                    "• Všechny body a prsteny byly vymazány\n"
                    "• Hra začíná znovu od začátku\n"
                    "• Nová databáze se vytvoří automaticky při první hře"
                ),
                color=discord.Color.green()
            )
            await message.edit(embed=embed_success, view=None)
            await message.delete(delay=10)
            
            print(f"🗑️ Databáze smazána administrátorem: {ctx.author.name} ({ctx.author.id})")
            
        except Exception as e:
            embed_error = discord.Embed(
                title="❌ Chyba",
                description=f"Při mazání databáze došlo k chybě:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await message.edit(embed=embed_error, view=None)
            await message.delete(delay=10)
            print(f"❌ Chyba při mazání DB: {e}")
    
    else:
        # Zrušeno
        embed_cancel = discord.Embed(
            title="❌ Zrušeno",
            description="Smazání databáze bylo zrušeno. Žádné změny nebyly provedeny.",
            color=discord.Color.blue()
        )
        await message.edit(embed=embed_cancel, view=None)
        await message.delete(delay=5)


@bot.command(name='konec_sezony')
@commands.has_permissions(administrator=True)
async def konec_sezony(ctx):
    """Příkaz pro adminy - ukončí aktuální sezónu a vypne bota."""
    global BOT_ENABLED, CURRENT_SEASON
    
    # Načti databázi
    db = nacti_databazi()
    
    if not db:
        await ctx.send("❌ Databáze je prázdná, nelze ukončit sezónu!", delete_after=10)
        try:
            await ctx.message.delete()
        except:
            pass
        return
    
    # Filtruj hráče s alespoň jedním prstenem
    vitezove = {uid: data for uid, data in db.items() if data.get('prsteny', 0) > 0}
    
    if not vitezove:
        await ctx.send("❌ Žádný hráč nezískal prsten! Nelze ukončit sezónu.", delete_after=10)
        try:
            await ctx.message.delete()
        except:
            pass
        return
    
    # Seřaď vítěze podle prstenů (hlavní), pak podle bodů
    serazeni_vitezove = sorted(
        vitezove.items(),
        key=lambda x: (x[1].get('prsteny', 0), x[1].get('body', 0)),
        reverse=True
    )
    
    # Vytvoř výsledkovou zprávu
    embed = discord.Embed(
        title=f"🏆 KONEC {CURRENT_SEASON}. SEZÓNY 🏆",
        description=(
            f"Sezóna **#{CURRENT_SEASON}** byla úspěšně dokončena!\n\n"
            f"🎉 **Gratulujeme všem hrdinům, kteří dokázali zničit Prsten Moci!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        ),
        color=discord.Color.gold()
    )
    
    # Přidej TOP 10 vítězů
    vitez_text = ""
    for i, (user_id, data) in enumerate(serazeni_vitezove[:10], 1):
        prsteny = data.get('prsteny', 0)
        body = data.get('body', 0)
        
        # Medaile
        if i == 1:
            medaile = "🥇"
        elif i == 2:
            medaile = "🥈"
        elif i == 3:
            medaile = "🥉"
        else:
            medaile = f"{i}."
        
        # Získej aktuální display_name ze serveru
        try:
            member = await ctx.guild.fetch_member(int(user_id))
            jmeno = member.display_name
        except:
            jmeno = data.get('name', 'Neznámý')
        
        # Počet prstenů s českými tvary
        if prsteny == 1:
            prsten_text = "prsten"
        elif 2 <= prsteny <= 4:
            prsten_text = "prsteny"
        else:
            prsten_text = "prstenů"
        
        vitez_text += f"{medaile} **{jmeno}** - 💍 **{prsteny}** {prsten_text}\n"
    
    embed.add_field(
        name="🌟 Konečné pořadí - Síň slávy",
        value=vitez_text,
        inline=False
    )
    
    # Statistiky
    celkem_hracu = len(db)
    celkem_vitezov = len(vitezove)
    celkem_prstenu = sum(data.get('prsteny', 0) for data in vitezove.values())
    
    embed.add_field(
        name="📊 Statistiky sezóny",
        value=(
            f"👥 Celkem hráčů: **{celkem_hracu}**\n"
            f"🏆 Hráčů s prstenem: **{celkem_vitezov}**\n"
            f"💍 Celkem zničených prstenů: **{celkem_prstenu}**"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Sezóna #{CURRENT_SEASON} ukončena {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    # Pošli výsledkovou zprávu (nezmaže se automaticky)
    await ctx.send(embed=embed)
    
    # Vypni bota
    BOT_ENABLED = False
    
    # Info zpráva
    info_embed = discord.Embed(
        title="⏸️ Sauron Bot VYPNUT",
        description=(
            f"Hra byla **pozastavena** po ukončení {CURRENT_SEASON}. sezóny.\n\n"
            "🎮 Pro spuštění nové sezóny použij příkaz:\n"
            "`!nova_sezona`"
        ),
        color=discord.Color.orange()
    )
    
    await ctx.send(embed=info_embed)
    
    # Smaž příkaz
    try:
        await ctx.message.delete()
    except:
        pass
    
    print(f"⏸️ Sezóna {CURRENT_SEASON} ukončena administrátorem: {ctx.author.name}")
    print(f"🛑 Bot VYPNUT - čeká na spuštění nové sezóny")


@bot.command(name='nova_sezona')
@commands.has_permissions(administrator=True)
async def nova_sezona(ctx):
    """Příkaz pro adminy - spustí novou sezónu a zapne bota."""
    global BOT_ENABLED, CURRENT_SEASON, message_counter, next_sauron_trigger, last_message_author, second_last_author
    
    if BOT_ENABLED:
        await ctx.send("⚠️ Bot je již zapnutý! Použij `!konec_sezony` pro ukončení aktuální sezóny.", delete_after=10)
        try:
            await ctx.message.delete()
        except:
            pass
        return
    
    # Vytvoření potvrzovací zprávy
    view = ConfirmView(ctx.author.id)
    
    embed = discord.Embed(
        title="🎮 Spuštění nové sezóny",
        description=(
            f"Chystáš se spustit **{CURRENT_SEASON + 1}. sezónu**!\n\n"
            "⚠️ Tato akce:\n"
            "• **SMAŽE všechny body a prsteny** všech hráčů\n"
            "• Spustí novou sezónu od začátku\n"
            "• **NELZE VRÁTIT ZPĚT**\n\n"
            "💡 **TIP:** Před spuštěním nové sezóny si ulož výsledky předchozí!\n\n"
            "Opravdu chceš pokračovat?"
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="Máš 30 sekund na rozhodnutí")
    
    message = await ctx.send(embed=embed, view=view)
    
    # Počkej na odpověď
    await view.wait()
    
    # Smaž příkaz
    try:
        await ctx.message.delete()
    except:
        pass
    
    if view.value is None:
        # Timeout
        embed_timeout = discord.Embed(
            title="⏱️ Časový limit vypršel",
            description="Spuštění nové sezóny bylo zrušeno (žádná odpověď).",
            color=discord.Color.orange()
        )
        await message.edit(embed=embed_timeout, view=None)
        await message.delete(delay=5)
        
    elif view.value:
        # Potvrzeno - smaž databázi a spusť novou sezónu
        try:
            # Smaž soubor databáze
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            
            # Zvýš číslo sezóny
            CURRENT_SEASON += 1
            
            # Zapni bota
            BOT_ENABLED = True
            
            # Resetuj počítadla
            message_counter = 0
            next_sauron_trigger = random.randint(8, 12)
            last_message_author = None
            second_last_author = None
            
            embed_success = discord.Embed(
                title=f"✅ {CURRENT_SEASON}. SEZÓNA SPUŠTĚNA! 🎮",
                description=(
                    f"**Nová sezóna #{CURRENT_SEASON} úspěšně zahájena!**\n\n"
                    "🎉 Co se změnilo:\n"
                    "• Všechny body a prsteny byly vynulovány\n"
                    "• Databáze byla resetována\n"
                    "• Hra začíná znovu od začátku\n\n"
                    f"👁️ **Sauron je opět aktivní!**\n"
                    "Začni psát zprávy a čekej na výzvy...\n\n"
                    "📖 Použij `!help_sauron` pro zobrazení pravidel."
                ),
                color=discord.Color.green()
            )
            embed_success.set_footer(text=f"Sezóna #{CURRENT_SEASON} spuštěna {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            
            await message.edit(embed=embed_success, view=None)
            
            print(f"✅ Sezóna {CURRENT_SEASON} spuštěna administrátorem: {ctx.author.name}")
            print(f"🎮 Bot ZAPNUT - hra běží")
            
        except Exception as e:
            embed_error = discord.Embed(
                title="❌ Chyba",
                description=f"Při spouštění nové sezóny došlo k chybě:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await message.edit(embed=embed_error, view=None)
            await message.delete(delay=10)
            print(f"❌ Chyba při spouštění nové sezóny: {e}")
    
    else:
        # Zrušeno
        embed_cancel = discord.Embed(
            title="❌ Zrušeno",
            description="Spuštění nové sezóny bylo zrušeno. Bot zůstává vypnutý.",
            color=discord.Color.blue()
        )
        await message.edit(embed=embed_cancel, view=None)
        await message.delete(delay=5)


@bot.command(name='stav_bota')
@commands.has_permissions(administrator=True)
async def stav_bota(ctx):
    """Příkaz pro adminy - zobrazí aktuální stav bota."""
    global BOT_ENABLED, CURRENT_SEASON
    
    db = nacti_databazi()
    celkem_hracu = len(db)
    celkem_prstenu = sum(data.get('prsteny', 0) for data in db.values())
    hraci_s_prsteny = len([d for d in db.values() if d.get('prsteny', 0) > 0])
    
    stav = "🟢 **ZAPNUT**" if BOT_ENABLED else "🔴 **VYPNUT**"
    
    embed = discord.Embed(
        title="🤖 Stav Sauron Bota",
        color=discord.Color.green() if BOT_ENABLED else discord.Color.red()
    )
    
    embed.add_field(
        name="⚙️ Stav hry",
        value=stav,
        inline=True
    )
    
    embed.add_field(
        name="📅 Aktuální sezóna",
        value=f"Sezóna **#{CURRENT_SEASON}**",
        inline=True
    )
    
    embed.add_field(
        name="📊 Statistiky",
        value=(
            f"👥 Hráčů: **{celkem_hracu}**\n"
            f"🏆 S prstenem: **{hraci_s_prsteny}**\n"
            f"💍 Celkem prstenů: **{celkem_prstenu}**"
        ),
        inline=False
    )
    
    if BOT_ENABLED:
        embed.add_field(
            name="🎮 Dostupné příkazy",
            value="`!konec_sezony` - Ukončí aktuální sezónu",
            inline=False
        )
    else:
        embed.add_field(
            name="🎮 Dostupné příkazy",
            value="`!nova_sezona` - Spustí novou sezónu",
            inline=False
        )
    
    message = await ctx.send(embed=embed)
    
    # Smaž po 15 sekundách
    await asyncio.sleep(15)
    try:
        await message.delete()
        await ctx.message.delete()
    except:
        pass


@bot.command(name='help_sauron')
async def napoveda(ctx):
    """Příkaz pro zobrazení nápovědy."""
    embed = discord.Embed(
        title="📖 Nápověda - Sauron Bot",
        description="Vítej v epické cestě za zničením prstenu!",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="🎮 Jak hra funguje?",
        value=(
            "• S **10% pravděpodobností** se objeví Sauronova výzva\n"
            "• Vyber si, komu svěříš svůj osud\n"
            "• **Pozor!** Obě tlačítka mají stejnou barvu - musíš číst jména!\n"
            "• Za správnou volbu (dobrá postava) získáš **+1 bod**\n"
            "• Za špatnou volbu (zlá postava) ztratíš **-2 body**"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🗺️ Příběhový mód - Cesta do Mordoru",
        value=(
            "🌾 **0-9:** Kraj | 🍺 **10-19:** Bri | ⛰️ **20-29:** Zvětrník\n"
            "🏰 **30-39:** Roklinka | ⚒️ **40-49:** Moria\n"
            "🌳 **50-59:** Lothlórien | 🐎 **60-69:** Rohan\n"
            "🛡️ **70-79:** Helmův žleb | 🏛️ **80-89:** Minas Tirith\n"
            "🚪 **90-99:** Černá brána\n"
            "🌋 **100 bodů:** Mordor - **VÝHRA! Získáváš PRSTEN!** 💍"
        ),
        inline=False
    )
    
    embed.add_field(
        name="💍 Prsteny Moci",
        value=(
            "• Při dosažení **100 bodů** zničíš prsten a získáš jej do sbírky\n"
            "• Body se vynulují a začínáš novou cestu\n"
            "• Prsteny zůstávají navždy ve tvé sbírce\n"
            "• Staň se legendou s nejvíce prsteny!"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📋 Příkazy",
        value=(
            "`!body` - Zobrazí tvůj postup a lokaci\n"
            "`!zebricek` - Žebříček nositelů prstenů\n"
            "`!help_sauron` - Zobrazí tuto nápovědu"
        ),
        inline=False
    )
    
    embed.set_footer(text="🎯 Cíl: Dostaň se do Mordoru a zniž prsten!")
    
    message = await ctx.send(embed=embed)
    
    # Počkej 20 sekund a smaž zprávu
    import asyncio
    await asyncio.sleep(20)
    try:
        await message.delete()
        await ctx.message.delete()  # Smaž i příkaz uživatele
    except:
        pass


# Spuštění bota
if __name__ == '__main__':
    print("✅ Token loaded successfully")
    print("🤖 Connecting to Discord...")
    bot.run(TOKEN)
