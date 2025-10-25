# Použij oficiální Python 3.11 slim image pro menší velikost
FROM python:3.11-slim

# Nastav pracovní adresář v kontejneru
WORKDIR /app

# Kopíruj requirements.txt a nainstaluj závislosti
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopíruj Python skript do kontejneru
COPY sauron_dc_bot.py .

# Vytvoř adresář pro persistentní data (databáze)
RUN mkdir -p /app/data

# Nastav proměnnou prostředí pro cestu k datům
ENV DATA_DIR=/app/data

# Nastav port (volitelné - Discord bot nepotřebuje exposed port)
# EXPOSE 8080

# Healthcheck - jednodušší verze
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD pgrep python > /dev/null || exit 1

# Spusť Python skript
CMD ["python", "-u", "sauron_dc_bot.py"]
