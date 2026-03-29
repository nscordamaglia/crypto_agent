import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET = os.getenv('BINANCE_SECRET')
BINANCE_USE_RSA = os.getenv('BINANCE_USE_RSA', 'False').lower() == 'true'
BINANCE_PRIVATE_KEY_PATH = os.getenv('BINANCE_PRIVATE_KEY_PATH', './private_key.pem')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_APPLICATION_ID = os.getenv('DISCORD_APPLICATION_ID')
TESTNET = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'

# Trading Parameters
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'FLOKIUSDT']
LEVERAGE = 3
INITIAL_SIZE_USDT = 10.0
# Risk Logic
SL_PERCENT = 0.002  # 0.2%
TP_PERCENT = 0.01   # 1%
RSI_PERIOD = 14
RSI_OVERSOLD = 25
RSI_OVERBOUGHT = 75
EMA_FAST = 5
EMA_SLOW = 20

# DCA / Martingale Logic
DCA_MULTIPLIER = 1.5  # +50% size
MAX_OPEN_POSITIONS = 3
LOOP_INTERVAL = 30  # seconds
