# 🚀 Rychlý návod k nasazení

## Pro Coolify (doporučeno)

### 1. Nahraj na GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/TVOJE_JMENO/sauron-bot.git
git push -u origin main
```

### 2. V Coolify
1. **New Application** → **Public Repository**
2. Vlož URL tvého GitHub repo
3. **Environment Variables:**
   ```
   DISCORD_BOT_TOKEN=tvůj_token
   DATA_DIR=/app/data
   ```
4. **Storage:**
   - Source: `/data/sauron-bot`
   - Destination: `/app/data`
5. **Deploy** ✅

## Pro Docker Compose

```bash
# 1. Vytvoř .env soubor
cp .env.example .env
# Uprav .env a vlož svůj token

# 2. Spusť
docker compose up -d

# 3. Sleduj logy
docker compose logs -f
```

---

**Token získáš zde:** https://discord.com/developers/applications

Více info v `README.md`
