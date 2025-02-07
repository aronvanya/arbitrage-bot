import requests
import time
import json
import os
from telegram import Bot

# ==========================
# Конфигурация
# ==========================

# Токен бота (тот же, что вы используете в bot_with_storage.py)
TELEGRAM_BOT_TOKEN = '8062354527:AAHzSfeM-PIsPV1NIXutCxHSDUsD9s6nx0Q'

# Файл, где хранятся Chat ID пользователей, зарегистрированных через /start
STORAGE_FILE = 'chat_ids.json'

# Список монет для отслеживания (можете добавить или убрать монеты)
SYMBOLS = ['BTC_USDT', 'ETH_USDT']

# Порог для отправки уведомления (в процентах)
ALERT_THRESHOLD = 0.5  # Например, уведомление при разнице 0.5% или больше

# ==========================
# Функции для работы с Chat ID
# ==========================

def load_chat_ids():
    """Загружает список сохранённых Chat ID из файла STORAGE_FILE."""
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    return []

def send_telegram_alert_to_all(message):
    """
    Отправляет сообщение всем пользователям, чей Chat ID сохранён в STORAGE_FILE.
    """
    chat_ids = load_chat_ids()
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            print(f"Не удалось отправить сообщение в {chat_id}: {e}")

# ==========================
# Функции для получения цен с бирж
# ==========================

def get_mexc_future_price(symbol):
    """
    Получает цену фьючерса для указанной монеты с биржи MEXC.
    """
    try:
        url = f'https://contract.mexc.com/api/v1/contract/ticker?symbol={symbol}'
        response = requests.get(url)
        data = response.json()
        return float(data['data']['lastPrice'])
    except Exception as e:
        print(f'Ошибка получения фьючерсной цены для {symbol} с MEXC: {e}')
        return None

def get_gate_spot_price(symbol):
    """
    Получает спотовую цену для указанной монеты с биржи Gate.io.
    Преобразует, например, BTC_USDT в BTCUSDT.
    """
    try:
        gate_symbol = symbol.replace('_', '')
        url = f'https://api.gateio.ws/api/v4/spot/tickers?currency_pair={gate_symbol}'
        response = requests.get(url)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return float(data[0]['last'])
        else:
            print(f'Нет данных для {symbol} с Gate.io')
            return None
    except Exception as e:
        print(f'Ошибка получения спотовой цены для {symbol} с Gate.io: {e}')
        return None

# ==========================
# Основная логика арбитраж-бота
# ==========================

def check_arbitrage():
    """
    Для каждой монеты:
      - Получает цену фьючерса с MEXC.
      - Получает спотовую цену с Gate.io.
      - Вычисляет процентную разницу.
      - Выводит данные в консоль.
      - Если разница по модулю превышает ALERT_THRESHOLD, отправляет уведомление всем зарегистрированным пользователям.
    """
    for symbol in SYMBOLS:
        future_price = get_mexc_future_price(symbol)
        spot_price = get_gate_spot_price(symbol)
        
        if future_price is not None and spot_price is not None:
            percentage_diff = ((future_price - spot_price) / spot_price) * 100
            print(f"{symbol}: Фьючерс = {future_price}, Спот = {spot_price}, Разница = {percentage_diff:.2f}%")
            
            if abs(percentage_diff) >= ALERT_THRESHOLD:
                message = (
                    f"⚠️ {symbol} ALERT!\n"
                    f"Фьючерс: {future_price}\n"
                    f"Спот: {spot_price}\n"
                    f"Разница: {percentage_diff:.2f}%"
                )
                send_telegram_alert_to_all(message)
        else:
            print(f"Невозможно получить данные для {symbol}")

# ==========================
# Запуск цикла проверки
# ==========================

if __name__ == "__main__":
    while True:
        check_arbitrage()
        print("Ожидание 10 секунд...\n")
        time.sleep(10)
