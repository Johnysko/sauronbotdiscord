# 📁 Struktura projektu

```
sauron-bot/
│
├── 🐍 sauron dc bot.py          # Hlavní kód Discord bota
│
├── 🐳 Docker soubory:
│   ├── Dockerfile               # Definice Docker image
│   ├── docker-compose.yml       # Docker Compose pro lokální běh
│   ├── .dockerignore           # Ignorované soubory při buildu
│   └── requirements.txt         # Python závislosti
│
├── 📝 Git soubory:
│   ├── .gitignore              # Ignorované soubory v Gitu
│   └── .github/workflows/       # GitHub Actions (auto-testy)
│       └── docker-build.yml
│
├── 📖 Dokumentace:
│   ├── README.md               # Kompletní dokumentace
│   ├── DEPLOY.md               # Rychlý návod k nasazení
│   └── CHECKLIST.md            # Kontrolní seznam
│
├── ⚙️ Konfigurace:
│   └── .env.example            # Vzorový soubor s tokeny
│
└── 🚫 Ignorované soubory (lokální):
    ├── bot token!!!!.txt       # Token (NEBUDE v Gitu)
    ├── .env                    # Token pro Docker Compose
    ├── data/                   # Databáze (na VPS persistentní)
    └── sauron_db.json         # JSON databáze s body hráčů
```

## 🔑 Klíčové soubory pro Coolify

Pro nasazení na VPS **potřebuješ nahrát do GitHubu**:
- ✅ `sauron dc bot.py` - hlavní kód
- ✅ `Dockerfile` - jak postavit kontejner
- ✅ `requirements.txt` - Python závislosti
- ✅ `.dockerignore` - co vynechat z buildu
- ✅ `README.md` - dokumentace

**NEPOTŘEBUJEŠ nahrát:**
- ❌ `bot token!!!!.txt` - token nastavíš v Coolify
- ❌ `.env` - používá se jen lokálně
- ❌ `data/` nebo `*.json` - databáze se vytvoří na VPS

## 🎯 Co dělá každý soubor

| Soubor | Účel |
|--------|------|
| `Dockerfile` | Instrukce pro Docker, jak postavit image bota |
| `requirements.txt` | Seznam Python knihoven k instalaci |
| `.dockerignore` | Co NEkopírovat do Docker image |
| `.gitignore` | Co NEnahrávat na GitHub |
| `docker-compose.yml` | Pro snadné lokální testování |
| `.env.example` | Vzor pro vytvoření vlastního .env |
| `README.md` | Kompletní dokumentace a návody |
| `DEPLOY.md` | Zkrácený deploy návod |
| `CHECKLIST.md` | Kontrolní seznam před spuštěním |

## 🔒 Bezpečnost

**NIKDY necommituj:**
- 🔴 Discord Bot Token
- 🔴 Soubory s hesly
- 🔴 `.env` soubor s citlivými daty

**Token nastav:**
- 🟢 V Coolify → Environment Variables
- 🟢 V lokálním `.env` (ten je v .gitignore)

## 🚀 Jak začít

1. **Lokální vývoj:**
   ```bash
   cp .env.example .env
   # Uprav .env a vlož token
   docker compose up -d
   ```

2. **Deploy na VPS:**
   - Viz `DEPLOY.md` nebo sekce v `README.md`
   - Postupuj podle `CHECKLIST.md`

---

Vše je připraveno pro bezproblémové nasazení! 🎉
