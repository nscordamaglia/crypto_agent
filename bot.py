"""
Discord Trading Bot - Binance Futures Testnet
Scalping 1m | RSI + EMA | SL 0.2% | TP 1% | DCA | Max 3 posiciones
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands, tasks
import numpy as np
from binance import AsyncClient, BinanceSocketManager
from binance.enums import (
    FUTURE_ORDER_TYPE_MARKET,
    SIDE_BUY,
    SIDE_SELL,
    KLINE_INTERVAL_1MINUTE,
)
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

import config

load_dotenv()

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Discord Bot Setup ────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Estado Global ────────────────────────────────────────────────────────────
class BotState:
    def __init__(self):
        self.running: bool = False
        self.client: Optional[AsyncClient] = None
        self.positions: dict = {}          # symbol -> {side, entry, qty, sl, tp, size_usdt}
        self.consecutive_losses: int = 0   # para DCA
        self.discord_channel = None        # canal de logs
        self.trade_history: list = []      # historial local

state = BotState()

# ─── Helpers ──────────────────────────────────────────────────────────────────

def current_size_usdt() -> float:
    """Calcula el tamaño en USDT aplicando DCA si corresponde."""
    base = config.INITIAL_SIZE_USDT
    if state.consecutive_losses > 0:
        return base * (config.DCA_MULTIPLIER ** state.consecutive_losses)
    return base

async def log_discord(msg: str, embed: Optional[discord.Embed] = None):
    """Envía mensaje al canal de Discord y al logger."""
    logger.info(msg)
    if state.discord_channel:
        try:
            if embed:
                await state.discord_channel.send(embed=embed)
            else:
                await state.discord_channel.send(f"`{msg}`")
        except Exception as e:
            logger.warning(f"No se pudo enviar a Discord: {e}")

# ─── Análisis Técnico (Pure NumPy) ────────────────────────────────────────────

def compute_ema(data: np.ndarray, window: int) -> np.ndarray:
    """Calcula EMA usando NumPy."""
    if len(data) < window:
        return np.zeros_like(data)
    alpha = 2 / (window + 1.0)
    ema = np.zeros_like(data)
    ema[window - 1] = np.mean(data[:window])
    for i in range(window, len(data)):
        ema[i] = data[i] * alpha + ema[i - 1] * (1 - alpha)
    return ema

def compute_rsi(data: np.ndarray, window: int = 14) -> np.ndarray:
    """Calcula RSI usando suavizado de Wilder (NumPy)."""
    if len(data) <= window:
        return np.zeros_like(data)
    
    diff = np.diff(data)
    gain = np.where(diff > 0, diff, 0.0)
    loss = np.where(diff < 0, -diff, 0.0)
    
    avg_gain = np.zeros_like(data)
    avg_loss = np.zeros_like(data)
    
    avg_gain[window] = np.mean(gain[:window])
    avg_loss[window] = np.mean(loss[:window])
    
    for i in range(window + 1, len(data)):
        avg_gain[i] = (avg_gain[i - 1] * (window - 1) + gain[i - 1]) / window
        avg_loss[i] = (avg_loss[i - 1] * (window - 1) + loss[i - 1]) / window
        
    rs = np.divide(avg_gain, avg_loss, out=np.zeros_like(avg_gain), where=avg_loss != 0)
    rsi = 100 - (100 / (1 + rs))
    return rsi

async def fetch_klines(symbol: str, limit: int = 100) -> Optional[dict]:
    """Trae velas 1m de Binance Futures. Retorna dict con arrays de NumPy."""
    try:
        raw = await state.client.futures_klines(
            symbol=symbol,
            interval=KLINE_INTERVAL_1MINUTE,
            limit=limit,
        )
        # Extraemos solo lo necesario para ahorrar memoria en Termux
        closes = np.array([float(k[4]) for k in raw])
        return {"close": closes}
    except BinanceAPIException as e:
        logger.error(f"fetch_klines {symbol}: {e}")
        return None

def compute_signals(data_dict: dict) -> dict:
    """
    Calcula RSI(14), EMA5, EMA20 usando NumPy.
    Retorna dict con valores y señal: 'BUY' | 'SELL' | None
    """
    closes = data_dict["close"]
    
    rsi_arr  = compute_rsi(closes, window=config.RSI_PERIOD)
    ema5_arr = compute_ema(closes, window=config.EMA_FAST)
    ema20_arr= compute_ema(closes, window=config.EMA_SLOW)

    rsi    = rsi_arr[-1]
    ema5   = ema5_arr[-1]
    ema20  = ema20_arr[-1]
    price  = closes[-1]
    
    prev_ema5  = ema5_arr[-2]
    prev_ema20 = ema20_arr[-2]

    # EMA cross actual vs anterior
    cross_up   = (prev_ema5 <= prev_ema20) and (ema5 > ema20)
    cross_down = (prev_ema5 >= prev_ema20) and (ema5 < ema20)

    signal = None
    if rsi < config.RSI_OVERSOLD and cross_up:
        signal = "BUY"
    elif rsi > config.RSI_OVERBOUGHT and cross_down:
        signal = "SELL"

    return {"rsi": rsi, "ema5": ema5, "ema20": ema20, "price": price, "signal": signal}

# ─── Gestión de Posiciones ────────────────────────────────────────────────────

async def set_leverage(symbol: str):
    """Fija el leverage en Binance Futures."""
    try:
        await state.client.futures_change_leverage(
            symbol=symbol, leverage=config.LEVERAGE
        )
    except BinanceAPIException as e:
        logger.warning(f"set_leverage {symbol}: {e}")

async def get_futures_balance() -> float:
    """Obtiene balance disponible de USDT en Futures testnet."""
    try:
        balances = await state.client.futures_account_balance()
        for b in balances:
            if b["asset"] == "USDT":
                return float(b["availableBalance"])
    except BinanceAPIException as e:
        logger.error(f"get_futures_balance: {e}")
    return 0.0

async def get_symbol_price(symbol: str) -> float:
    """Precio actual de mercado."""
    try:
        ticker = await state.client.futures_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except BinanceAPIException as e:
        logger.error(f"get_symbol_price {symbol}: {e}")
        return 0.0

async def open_position(symbol: str, side: str, price: float):
    """
    Abre posición de mercado en Futures.
    side: 'BUY' o 'SELL'
    Coloca SL y TP como órdenes stop-market / take-profit-market.
    """
    await set_leverage(symbol)

    size_usdt = current_size_usdt()
    balance   = await get_futures_balance()

    if balance < size_usdt:
        await log_discord(
            f"⚠️ Balance insuficiente para {symbol}: disponible {balance:.2f} USDT, "
            f"necesario {size_usdt:.2f} USDT"
        )
        return

    # Calcular cantidad de contratos
    info = await state.client.futures_exchange_info()
    qty_precision = 3  # fallback
    price_precision = 2
    for s in info["symbols"]:
        if s["symbol"] == symbol:
            qty_precision   = s["quantityPrecision"]
            price_precision = s["pricePrecision"]
            break

    notional  = size_usdt * config.LEVERAGE
    quantity  = round(notional / price, qty_precision)

    if quantity <= 0:
        await log_discord(f"⚠️ Cantidad calculada inválida para {symbol}: {quantity}")
        return

    # SL / TP direction
    if side == "BUY":
        sl_price = round(price * (1 - config.SL_PERCENT), price_precision)
        tp_price = round(price * (1 + config.TP_PERCENT), price_precision)
        sl_side  = SIDE_SELL
    else:
        sl_price = round(price * (1 + config.SL_PERCENT), price_precision)
        tp_price = round(price * (1 - config.TP_PERCENT), price_precision)
        sl_side  = SIDE_BUY

    try:
        # Orden principal
        order = await state.client.futures_create_order(
            symbol=symbol,
            side=side,
            type=FUTURE_ORDER_TYPE_MARKET,
            quantity=quantity,
        )

        # Stop-Loss
        await state.client.futures_create_order(
            symbol=symbol,
            side=sl_side,
            type="STOP_MARKET",
            stopPrice=sl_price,
            closePosition=True,
        )

        # Take-Profit
        await state.client.futures_create_order(
            symbol=symbol,
            side=sl_side,
            type="TAKE_PROFIT_MARKET",
            stopPrice=tp_price,
            closePosition=True,
        )

        # Guardar en estado
        state.positions[symbol] = {
            "side":       side,
            "entry":      price,
            "qty":        quantity,
            "sl":         sl_price,
            "tp":         tp_price,
            "size_usdt":  size_usdt,
            "time":       datetime.utcnow(),
        }

        emb = discord.Embed(
            title=f"🟢 OPEN {side} - {symbol}",
            color=discord.Color.green() if side == "BUY" else discord.Color.red(),
        )
        emb.add_field(name="Entry",    value=f"{price:.4f}",    inline=True)
        emb.add_field(name="SL",       value=f"{sl_price:.4f}", inline=True)
        emb.add_field(name="TP",       value=f"{tp_price:.4f}", inline=True)
        emb.add_field(name="Qty",      value=str(quantity),      inline=True)
        emb.add_field(name="Size USDT",value=f"{size_usdt:.2f}", inline=True)
        emb.add_field(name="Leverage", value=f"{config.LEVERAGE}x", inline=True)
        emb.set_footer(text=f"Testnet: {config.TESTNET}")
        await log_discord(f"OPEN {side} {symbol} @ {price}", embed=emb)

    except BinanceAPIException as e:
        await log_discord(f"❌ Error abriendo posición {symbol}: {e}")

async def check_closed_positions():
    """
    Verifica si alguna posición fue cerrada (SL/TP alcanzado).
    Actualiza consecutive_losses y notifica.
    """
    if not state.positions:
        return

    for symbol in list(state.positions.keys()):
        try:
            pos_list = await state.client.futures_position_information(symbol=symbol)
            for p in pos_list:
                if p["symbol"] == symbol:
                    amt = float(p["positionAmt"])
                    if abs(amt) < 1e-8:  # posición cerrada
                        info = state.positions.pop(symbol)
                        current_price = await get_symbol_price(symbol)
                        if info["side"] == "BUY":
                            pnl = (current_price - info["entry"]) * info["qty"]
                        else:
                            pnl = (info["entry"] - current_price) * info["qty"]

                        won = pnl > 0
                        if won:
                            state.consecutive_losses = 0
                            emoji = "✅ WIN"
                            color = discord.Color.green()
                        else:
                            state.consecutive_losses += 1
                            emoji = "❌ LOSS"
                            color = discord.Color.red()

                        state.trade_history.append({
                            "symbol":    symbol,
                            "side":      info["side"],
                            "entry":     info["entry"],
                            "exit":      current_price,
                            "pnl":       pnl,
                            "time":      datetime.utcnow(),
                        })

                        emb = discord.Embed(title=f"{emoji} - {symbol}", color=color)
                        emb.add_field(name="Side",  value=info["side"],          inline=True)
                        emb.add_field(name="Entry", value=f"{info['entry']:.4f}", inline=True)
                        emb.add_field(name="Exit",  value=f"{current_price:.4f}", inline=True)
                        emb.add_field(name="P&L",   value=f"{pnl:+.4f} USDT",    inline=True)
                        emb.add_field(name="DCA streak", value=str(state.consecutive_losses), inline=True)
                        await log_discord(f"{emoji} {symbol} PnL={pnl:+.4f}", embed=emb)
        except BinanceAPIException as e:
            logger.error(f"check_closed_positions {symbol}: {e}")

# ─── Trading Loop ─────────────────────────────────────────────────────────────

@tasks.loop(seconds=config.LOOP_INTERVAL)
async def trading_loop():
    """Loop principal: analiza señales y gestiona posiciones."""
    if not state.running or not state.client:
        return

    await check_closed_positions()

    if len(state.positions) >= config.MAX_OPEN_POSITIONS:
        logger.info("Max posiciones alcanzado, esperando...")
        return

    for symbol in config.SYMBOLS:
        if symbol in state.positions:
            continue  # ya tenemos posición en este par

        data = await fetch_klines(symbol)
        if data is None or len(data["close"]) < 30:
            continue

        sig = compute_signals(data)
        logger.info(
            f"{symbol} | RSI={sig['rsi']:.1f} | EMA5={sig['ema5']:.2f} | "
            f"EMA20={sig['ema20']:.2f} | Signal={sig['signal']}"
        )

        if sig["signal"] in ("BUY", "SELL"):
            await open_position(symbol, sig["signal"], sig["price"])

        # Pequeño delay entre símbolo y símbolo para no saturar la API
        await asyncio.sleep(1)

@trading_loop.before_loop
async def before_trading_loop():
    await bot.wait_until_ready()

# ─── Comandos Discord ─────────────────────────────────────────────────────────

@bot.command(name="start_bot")
async def start_bot(ctx):
    """!start_bot — arranca el loop de trading."""
    if state.running:
        await ctx.send("⚠️ El bot ya está corriendo.")
        return

    state.discord_channel = ctx.channel

    if not state.client:
        try:
            if config.BINANCE_USE_RSA:
                state.client = await AsyncClient.create(
                    api_key=config.BINANCE_API_KEY,
                    private_key=config.BINANCE_PRIVATE_KEY_PATH,
                    testnet=config.TESTNET,
                )
            else:
                state.client = await AsyncClient.create(
                    api_key=config.BINANCE_API_KEY,
                    api_secret=config.BINANCE_SECRET,
                    testnet=config.TESTNET,
                )
        except Exception as e:
            await ctx.send(f"❌ Error conectando a Binance: {e}")
            return

    state.running = True
    if not trading_loop.is_running():
        trading_loop.start()

    await ctx.send(
        f"✅ **Bot iniciado!**\n"
        f"```\n"
        f"Testnet : {config.TESTNET}\n"
        f"Pares   : {', '.join(config.SYMBOLS)}\n"
        f"Size    : {config.INITIAL_SIZE_USDT} USDT\n"
        f"Leverage: {config.LEVERAGE}x\n"
        f"SL/TP   : {config.SL_PERCENT*100}% / {config.TP_PERCENT*100}%\n"
        f"Loop    : cada {config.LOOP_INTERVAL}s\n"
        f"```"
    )

@bot.command(name="stop_bot")
async def stop_bot(ctx):
    """!stop_bot — detiene el loop de trading."""
    if not state.running:
        await ctx.send("⚠️ El bot no está corriendo.")
        return
    state.running = False
    trading_loop.stop()
    await ctx.send("🛑 **Bot detenido.**")

@bot.command(name="balance")
async def balance(ctx):
    """!balance — muestra el balance de USDT en Futures."""
    if not state.client:
        await ctx.send("⚠️ Binance no conectado. Usa `!start_bot` primero.")
        return
    bal = await get_futures_balance()
    await ctx.send(f"💰 **Balance USDT Futures**: `{bal:.4f} USDT`")

@bot.command(name="positions")
async def positions_cmd(ctx):
    """!positions — muestra posiciones abiertas."""
    if not state.positions:
        await ctx.send("📭 No hay posiciones abiertas.")
        return

    emb = discord.Embed(title="📊 Posiciones Abiertas", color=discord.Color.blue())
    for sym, info in state.positions.items():
        val = (
            f"Side: {info['side']}\n"
            f"Entry: {info['entry']:.4f}\n"
            f"SL: {info['sl']:.4f} | TP: {info['tp']:.4f}\n"
            f"Qty: {info['qty']} | Size: {info['size_usdt']:.2f} USDT"
        )
        emb.add_field(name=sym, value=val, inline=False)
    await ctx.send(embed=emb)

@bot.command(name="backtest")
async def backtest(ctx, symbol: str = "BTCUSDT"):
    """!backtest [SYMBOL] — simula señales en últimas 200 velas 1m."""
    if not state.client:
        state.client = await AsyncClient.create(
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_SECRET,
            testnet=config.TESTNET,
        )

    await ctx.send(f"🔍 Corriendo backtest en {symbol} (200 velas 1m)...")
    full_data = await fetch_klines(symbol, limit=200)
    if full_data is None:
        await ctx.send("❌ No se pudieron obtener datos.")
        return

    closes = full_data["close"]
    wins = losses = 0
    total_pnl = 0.0

    for i in range(30, len(closes) - 1):
        # Simular ventana deslizante
        window = {"close": closes[:i]}
        sig = compute_signals(window)
        entry = closes[i]
        nxt   = closes[i + 1]

        if sig["signal"] == "BUY":
            sl = entry * (1 - config.SL_PERCENT)
            tp = entry * (1 + config.TP_PERCENT)
            if nxt >= tp:
                wins += 1; total_pnl += entry * config.TP_PERCENT
            elif nxt <= sl:
                losses += 1; total_pnl -= entry * config.SL_PERCENT
        elif sig["signal"] == "SELL":
            sl = entry * (1 + config.SL_PERCENT)
            tp = entry * (1 - config.TP_PERCENT)
            if nxt <= tp:
                wins += 1; total_pnl += entry * config.TP_PERCENT
            elif nxt >= sl:
                losses += 1; total_pnl -= entry * config.SL_PERCENT

    total_trades = wins + losses
    winrate = (wins / total_trades * 100) if total_trades else 0

    emb = discord.Embed(title=f"📈 Backtest: {symbol}", color=discord.Color.gold())
    emb.add_field(name="Trades", value=str(total_trades), inline=True)
    emb.add_field(name="Wins",   value=str(wins),         inline=True)
    emb.add_field(name="Losses", value=str(losses),       inline=True)
    emb.add_field(name="Winrate",value=f"{winrate:.1f}%", inline=True)
    emb.add_field(name="P&L estimado", value=f"{total_pnl:+.4f} USDT", inline=True)
    emb.set_footer(text="Backtest simple next-candle — sin comisiones, referencial")
    await ctx.send(embed=emb)

# ─── Eventos Bot ──────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    logger.info(f"Discord bot conectado como {bot.user} (ID: {bot.user.id})")
    logger.info(f"Testnet: {config.TESTNET}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Argumento faltante: `{error.param}`")
    elif isinstance(error, commands.CommandNotFound):
        pass  # ignorar comandos desconocidos
    else:
        logger.error(f"Error en comando: {error}")
        await ctx.send(f"❌ Error: {error}")

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    token = config.DISCORD_TOKEN
    if not token:
        raise ValueError("DISCORD_TOKEN no configurado en .env")
    
    bot.run(token)
