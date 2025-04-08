import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Настройки логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY", "")

# Получение последних матчей
def get_pro_matches():
    url = "https://api.opendota.com/api/proMatches"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()[:5]
    return []

# Информация о команде
def get_team_matches(team_id):
    url = f"https://api.opendota.com/api/teams/{team_id}/matches"
    if API_KEY:
        url += f"?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()[:5]
    return []

# Анализ формы команды
def analyze_form(matches):
    form = []
    for match in matches:
        win = match.get("radiant_win") if match.get("radiant") else not match.get("radiant_win")
        form.append("W" if win else "L")
    return "-".join(form)

# Прогноз победителя
def predict_winner(radiant_form, dire_form):
    radiant_score = radiant_form.count("W")
    dire_score = dire_form.count("W")
    total = radiant_score + dire_score
    if total == 0:
        return "Draw", 50
    radiant_prob = int((radiant_score / total) * 100)
    return ("Radiant", radiant_prob) if radiant_prob >= 50 else ("Dire", 100 - radiant_prob)

# Формирование текста прогноза
def build_prediction_text(match):
    radiant = match.get("radiant_name", "Radiant")
    dire = match.get("dire_name", "Dire")
    radiant_id = match.get("radiant_team_id")
    dire_id = match.get("dire_team_id")

    radiant_form = analyze_form(get_team_matches(radiant_id)) if radiant_id else "N/A"
    dire_form = analyze_form(get_team_matches(dire_id)) if dire_id else "N/A"

    winner, prob = predict_winner(radiant_form, dire_form)
    recommendation = "Ставить можно" if prob >= 60 else "Лучше пропустить"

    return f"""Match: {radiant} vs {dire}
Forecast: Winner will be {winner} ({prob}%)
Team form:
{radiant}: {radiant_form}
{dire}: {dire_form}
Recommendation: {recommendation}
"""

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-прогнозист для матчей Dota 2.\n\n"
        "Доступные команды:\n"
        "/forecast — прогноз на ближайшие матчи\n"
        "/help — список команд"
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start — информация о боте\n"
        "/forecast — прогнозы на матчи\n"
        "/help — список команд"
    )

# Команда /forecast
async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Собираю прогнозы, подожди...")
    matches = get_pro_matches()
    for match in matches:
        text = build_prediction_text(match)
        await update.message.reply_text(text)

# Основная функция
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("forecast", forecast))

    app.run_polling()

if __name__ == "__main__":
    main()
