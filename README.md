# 👁️ Sauron Discord Bot

Discord bot inspirovaný Pánem Prstenů. Hráči sbírají body odpovídáním na Sauronovy výzvy a postupují skrz Středozem až do Mordoru, kde získávají Prsteny Moci.

## 🎮 Jak hra funguje

- V rozmezí 10-15 zpráv (odpovídá zhruba 10-15% šanci) se po zprávě objeví Sauronova výzva
- Hráči si vybírají mezi dvěma postavami (jedna dobrá, jedna zlá)
- Správná volba = +1 bod, špatná volba = -1 bod
- Při dosažení 100 bodů získává hráč Prsten Moci a začíná znovu
- Prsteny zůstávají ve sbírce navždy

## 🗺️ Lokace (Story mód)

- 🌾 **0-19 bodů:** Kraj (Shire)
- 🏰 **20-39 bodů:** Roklinka (Rivendell)
- 🐎 **40-59 bodů:** Rohan
- ⚔️ **60-79 bodů:** Gondor
- 🚪 **80-99 bodů:** Černá brána
- � **100+ bodů:** Mordor - VÝHRA! 💍

## � Příkazy

- `!body` - Zobrazí tvůj postup a aktuální lokaci
- `!zebricek` - Žebříček hráčů podle počtu prstenů
- `!help_sauron` - Nápověda ke hře


---

## 🚀 Deploy na VPS přes Coolify

Tento návod ti ukáže, jak nasadit bota na tvůj VPS pomocí Coolify a GitHub.

### 📋 Předpoklady

- VPS server s nainstalovaným Coolify
- GitHub účet
- Discord bot token ([získej zde](https://discord.com/developers/applications))

### 1️⃣ Příprava GitHub repozitáře

```bash
# V lokální složce projektu
git init
git add .
git commit -m "Initial commit - Sauron Discord Bot"
git branch -M main
git remote add origin https://github.com/TVOJE_UZIVATELSKE_JMENO/sauron-bot.git
git push -u origin main
```

⚠️ **DŮLEŽITÉ:** Soubor `bot token!!!!.txt` se NEBUDE nahrát (je v .gitignore). Token nastavíš později v Coolify.

### 2️⃣ Vytvoření aplikace v Coolify

1. Přihlaš se do svého Coolify dashboardu
2. Klikni na **"+ New Resource"** → **"Application"**
3. Vyber **"Public Repository"**
4. Vlož URL svého GitHub repozitáře:
   ```
   https://github.com/TVOJE_UZIVATELSKE_JMENO/sauron-bot
   ```
5. Klikni **"Continue"**

### 3️⃣ Konfigurace aplikace

#### Základní nastavení:
- **Name:** `sauron-bot` (nebo libovolný název)
- **Branch:** `main`
- **Build Pack:** `Dockerfile` (detekuje se automaticky)
- **Port:** Nevyplňuj (Discord bot nepotřebuje exposed port)

#### Environment Variables (Proměnné prostředí):

Přejdi na záložku **"Environment Variables"** a přidej:

```
DISCORD_BOT_TOKEN=<tvůj_discord_bot_token>
DATA_DIR=/app/data
```

**Kde získat Discord Bot Token:**
1. Jdi na https://discord.com/developers/applications
2. Vyber svou aplikaci (nebo vytvoř novou)
3. Jdi na **Bot** → **Token** → **Reset Token** / **Copy**
4. Vlož token do Coolify jako hodnotu `DISCORD_BOT_TOKEN`

### 4️⃣ Nastavení Persistent Storage (Databáze)

Pro zachování databáze při restartech je potřeba nastavit volume:

1. V Coolify přejdi na záložku **"Storages"**
2. Klikni na **"+ Add"**
3. Nastav:
   - **Name:** `sauron-data`
   - **Source Path:** `/data/sauron-bot` (na VPS)
   - **Destination Path:** `/app/data` (v kontejneru)
   - **Type:** `Volume`
4. Klikni **"Save"**

✅ Tím se zajistí, že databáze `sauron_db.json` přežije restart kontejneru.

### 5️⃣ Deploy

1. Klikni na **"Deploy"** v pravém horním rohu
2. Coolify automaticky:
   - Stáhne kód z GitHubu
   - Sestaví Docker image podle `Dockerfile`
   - Nainstaluje závislosti z `requirements.txt`
   - Spustí bota
   - Zajistí restart při pádu/restartu VPS

### 6️⃣ Monitorování

Po úspěšném deployi můžeš sledovat:

- **Logs:** Záložka "Logs" - uvidíš zprávy jako "✅ Bot je připraven!"
- **Status:** Zelená ikona = běží, červená = problém
- **Restart Policy:** Coolify automaticky restartuje bot při pádu

---

## � Alternativní deploy - Docker Compose (bez Coolify)

Pokud chceš použít čistý Docker:

```bash
# Vytvoř .env soubor s tokenem
echo "DISCORD_BOT_TOKEN=tvuj_token_zde" > .env

# Spusť kontejner
docker compose up -d

# Sleduj logy
docker compose logs -f

# Zastavení
docker compose down
```

---

## 🔧 Technické detaily

### Struktura projektu

```
sauron-bot/
├── Dockerfile              # Definice Docker image
├── requirements.txt        # Python závislosti
├── sauron dc bot.py        # Hlavní kód bota
├── docker-compose.yml      # (Volitelné) Docker Compose konfigurace
├── .dockerignore          # Soubory ignorované při Docker buildu
├── .gitignore             # Soubory ignorované v Gitu
└── README.md              # Tato dokumentace
```

### Jak funguje persistent storage

- Databáze se ukládá do `/app/data/sauron_db.json` v kontejneru
- Tento adresář je namapován na `/data/sauron-bot` na VPS
- Při restartu kontejneru se data zachovají
- Při restartu VPS se data také zachovají

### Auto-restart

Coolify automaticky zajišťuje:
- ✅ Restart při pádu aplikace
- ✅ Restart při restartu VPS
- ✅ Restart při deployi nové verze
- ✅ Healthcheck každých 30 sekund

---

## 🔄 Aktualizace bota

Když změníš kód:

```bash
git add .
git commit -m "Popis změn"
git push
```

Pak v Coolify:
1. Přejdi na aplikaci
2. Klikni **"Deploy"**
3. Coolify stáhne nový kód a přebuiluje kontejner

---

## 🛠️ Řešení problémů

### Bot se nespustí

1. Zkontroluj logy v Coolify (záložka "Logs")
2. Ověř, že `DISCORD_BOT_TOKEN` je správně nastavený
3. Zkontroluj, že bot má správná oprávnění v Discord Developer Portal

### Databáze se maže

1. Ověř, že máš nastavený Storage volume v Coolify
2. Zkontroluj, že `DATA_DIR=/app/data` je nastavené v Environment Variables

### Bot nereaguje

1. Zkontroluj ID kanálů v `POVOLENE_KANALY` v kódu
2. Ověř, že bot má oprávnění "Read Messages" a "Send Messages"
3. Ověř, že máš zapnutý Message Content Intent v Discord Developer Portal

---

## � Discord Bot Permissions

V Discord Developer Portal musíš povolit:

**Privileged Gateway Intents:**
- ✅ Message Content Intent
- ✅ Server Members Intent (volitelné)

**Bot Permissions:**
- ✅ Read Messages/View Channels
- ✅ Send Messages
- ✅ Embed Links
- ✅ Add Reactions
- ✅ Read Message History

---

## 📜 Licence

Tento projekt je volně k použití pro osobní i komerční účely.

---

## 👥 Autor

Vytvořeno pro Discord server s motivy Pána Prstenů 🌋

---

**Užij si hru a ať Sauronovo oko nad tebou bdí!** 👁️

### ♻️ Co se stane po výhře?
- 💍 **Prsten zůstává navždy** ve tvé sbírce
- 🔄 **Body se vynulují** na 0
- 🎯 **Začínáš novou cestu** od Kraje
- 👑 **Sbírej více prstenů** a staň se legendou!

---

## 📋 PŘÍKAZY

| Příkaz | Popis |
|--------|-------|
| `!body` | Zobrazí tvůj aktuální postup, lokaci a počet prstenů |
| `!zebricek` | Žebříček hráčů s nejvíce prsteny |
| `!help_sauron` | Zobrazí detailní nápovědu (smaže se po 20 sekundách) |

### 🔧 Admin příkazy

| Příkaz | Popis |
|--------|-------|
| `!sauron_test` | Manuálně vyvolá Sauronovu výzvu (pouze admin) |
| `!reset_db` | Smaže celou databázi po potvrzení (pouze admin) |

---

## ✨ DOBRÉ POSTAVY

Tyto postavy jsou **správná volba** (+1 bod):

- Frodo
- Sam
- Gandalf
- Aragorn
- Legolas
- Pippin
- Boromir
- Elrond
- Faramir

---

## 🔥 ZLÉ POSTAVY

Tyto postavy jsou **špatná volba** (-1 bod):

- Glum (Gollum)
- Saruman
- Skřet
- Nazgûl
- Lurtz

---

## 💡 TIPY A TRIKY

- 🧠 **Číst jména!** - Obě tlačítka vypadají stejně
- 📚 **Znalost PotP pomáhá** - znáš všechny postavy?
- ⚡ **Každý hraje za sebe** - tvé body nikoho neovlivní
- 🗑️ **Zprávy se automaticky mažou** - chat zůstává čistý
- 🎲 **10% šance** - Sauron se objeví náhodně při každé zprávě

---

## 🚀 TECHNICKÉ INFORMACE

### 📦 Databáze
- **Formát:** JSON
- **Ukládání:** Automatické po každé akci
- **Lokace:** `sauron_db.json` (lokálně) nebo `/data/sauron_db.json` (Docker/VPS)

### 🔒 Bezpečnost
- Body databáze nelze upravit přímo
- Pouze admin může resetovat databázi
- Všechny akce jsou logovány v konzoli

### 🌐 Nasazení
- **Lokální:** Spusť `sauron dc bot.py`
- **VPS/Coolify:** Nastav `DATA_DIR=/data` a připoj persistent volume
- **Token:** Nastavit jako `DISCORD_BOT_TOKEN` environment proměnnou

---

## 🎊 Hodně štěstí na cestě do Mordoru!

> **"Jeden prsten jim všem vládne, jeden všechny najde..."**

---

*Vytvořeno s ❤️ pro fanoušky Pána prstenů*
