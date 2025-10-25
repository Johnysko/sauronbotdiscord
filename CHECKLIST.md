# ✅ Kontrolní seznam před nasazením

## Discord Bot Setup
- [ ] Bot vytvořen na https://discord.com/developers/applications
- [ ] **Message Content Intent** zapnutý (Bot → Privileged Gateway Intents)
- [ ] Bot má správná oprávnění:
  - [ ] Read Messages/View Channels
  - [ ] Send Messages
  - [ ] Embed Links
  - [ ] Add Reactions
  - [ ] Read Message History
- [ ] Bot přidán na Discord server (přes OAuth2 URL)

## Coolify Setup
- [ ] GitHub repozitář vytvořen a kód nahrán
- [ ] Aplikace v Coolify vytvořena
- [ ] **DISCORD_BOT_TOKEN** nastaven v Environment Variables
- [ ] **DATA_DIR=/app/data** nastaven v Environment Variables
- [ ] Storage volume vytvořen:
  - [ ] Source: `/data/sauron-bot`
  - [ ] Destination: `/app/data`
- [ ] Aplikace deployována

## Ověření funkčnosti
- [ ] V Coolify Logs vidíš "✅ Bot je připraven!"
- [ ] Bot je online na Discordu (zelená tečka)
- [ ] Napíšeš pár zpráv a čekáš na Sauronovu výzvu (10% šance)
- [ ] Příkaz `!help_sauron` funguje
- [ ] Příkaz `!body` funguje
- [ ] Příkaz `!zebricek` funguje

## Test persistence
- [ ] Zahraj si a získej nějaké body
- [ ] V Coolify udělej restart aplikace
- [ ] Po restartu zkontroluj `!body` - body by měly zůstat

## Troubleshooting
Pokud něco nefunguje:
1. Zkontroluj Logy v Coolify
2. Ověř Environment Variables
3. Zkontroluj Discord Developer Portal nastavení
4. Podívej se do README.md sekce "Řešení problémů"
