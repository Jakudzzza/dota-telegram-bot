import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY", "")

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Получение списка профессиональных матчей
def get_pro_matches():
    url = "https://api.opendota.com/api/proMatches"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()[:5]
    return []

# Получение информации о команде
def get_team_info(team_id):
    url = f"https://api.opendota.com/api/teams/{team_id}"
    if API_KEY:
        url += f"?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {}

# Получение последних матчей команды
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

# Расчёт вероятности победы
def predict_winner(radiant_form, dire_form):
    radiant_score = radiant_form.count("W")
    dire_score = dire_form.count("W")
    total = radiant_score + dire_score
    if total == 0:
        return "Ничья", 50
    radiant_prob = int((radiant_score / total) * 100)
    return ("Radiant", radiant_prob) if radiant_prob > 50 else ("Dire", 100 - radiant_prob)

# Генерация текста прогноза
def build_prediction_text(match):
    radiant = match.get("radiant_name", "Radiant")
    dire = match.get("dire_name", "Dire")

    radiant_id = match.get("radiant_team_id")
    dire_id = match.get("dire_team_id")

    radiant_form = analyze_form(get_team_matches(radiant_id)) if radiant_id else "N/A"
    dire_form = analyze_form(get_team_matches(dire_id)) if dire_id else "N/A"

    winner, prob = predict_winner(radiant_form, dire_form)
    recommendation = "Ставить можно" if prob >= 60 else "Лучше пропустить"

    return f"""Матч: {radiant} vs {dire}
Прогноз: Победит {winner} ({prob}%)
Форма команд:
{radiant}: {radiant_form}
{dire}: {dire_form}
Рекомендация: {recommendation}
"""

# Команда /прогноз
async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Собираю прогнозы, подожди пару секунд...")
    matches = get_pro_matches()
    for match in matches:
        text = build_prediction_text(match)
        await update.message.reply_text(text)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-прогнозист для матчей Dota 2.\n\n"
        "Команды:\n"
        "/прогноз — получить прогнозы на ближайшие матчи\n"
        "/help — показать список команд\n\n"
        "Спроси — я подскажу!"
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start — информация о боте\n"
        "/прогноз — прогнозы на ближайшие матчи\n"
        "/help — список всех команд"
    )

# Запуск бота
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("forecast", forecast))
    app.add_handler(CommandHandler("прогноз", forecast))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.run_polling()

if __name__ == '__main__':
    main()
