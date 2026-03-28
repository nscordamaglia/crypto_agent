# 🤖 Discord Trading Bot — Binance Futures Testnet + Railway

Bot de scalping automático en Python para Binance Futures Testnet, con alertas y comandos vía Discord. Desplegable en Railway.app con costo $0 inicial.

---

## 📋 Estrategia

| Parámetro       | Valor                        |
|-----------------|------------------------------|
| Pares           | BTCUSDT, ETHUSDT, SOLUSDT, FLOKIUSDT (Perp) |
| Timeframe       | 1 minuto                     |
| Señal BUY       | RSI(14) < 25 + EMA5 cruza arriba EMA20 |
| Señal SELL      | RSI(14) > 75 + EMA5 cruza abajo EMA20  |
| Stop-Loss       | 0.2%                         |
| Take-Profit     | 1%                           |
| Leverage        | 3x máximo                    |
| Capital inicial | $10 USDT                     |
| DCA             | +50% size por cada loss consecutivo, reset en win |
| Max posiciones  | 3 simultáneas                |
| Loop            | Cada 30 segundos             |

---

## 🚀 Setup Local

### 1. Clonar y preparar entorno

```bash
git clone <tu-repo>
cd railway_bot
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env`:
```env
DISCORD_TOKEN=tu_token_de_discord
BINANCE_API_KEY=tu_api_key_testnet
BINANCE_SECRET=tu_secret_testnet
BINANCE_TESTNET=True
```

### 3. Ejecutar

```bash
python bot.py
```

---

## 🔑 Obtener credenciales Binance Testnet

1. Ir a [testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Crear cuenta con GitHub
3. **API Management** → **Create API**
4. Copiar `API Key` y `Secret Key`
5. El saldo testnet es virtual (de ejemplo: 10,000 USDT)

---

## 🤖 Crear Bot en Discord

1. Ir a [discord.com/developers/applications](https://discord.com/developers/applications)
2. **New Application** → darle nombre
3. **Bot** → **Add Bot** → copiar el **Token**
4. **OAuth2 → URL Generator**:
   - Scope: `bot`
   - Permissions: `Send Messages`, `Read Message History`, `Embed Links`
5. Abrir la URL generada e invitar el bot a tu servidor

---

## 💬 Comandos Discord

| Comando          | Descripción                                |
|------------------|--------------------------------------------|
| `!start_bot`     | Inicia el loop de trading                  |
| `!stop_bot`      | Detiene el bot                             |
| `!balance`       | Muestra balance USDT disponible            |
| `!positions`     | Lista posiciones abiertas                  |
| `!backtest [SYM]`| Backtest rápido en las últimas 200 velas   |

---

## 🚂 Deploy en Railway.app

### Paso 1 — Subir código a GitHub

```bash
git init
git add .
git commit -m "feat: trading bot inicial"
git remote add origin https://github.com/tuusuario/tu-repo.git
git push -u origin main
```

### Paso 2 — Crear proyecto en Railway

1. Ir a [railway.app](https://railway.app) y loguear con GitHub
2. **New Project → Deploy from GitHub repo**
3. Seleccionar tu repositorio

### Paso 3 — Configurar Variables de Entorno

En el dashboard de Railway → **Variables**:

```
DISCORD_TOKEN       = tu_token_discord
BINANCE_API_KEY     = tu_api_key_testnet
BINANCE_SECRET      = tu_secret_testnet
BINANCE_TESTNET     = True
```

### Paso 4 — Verificar Procfile

Railway detecta el `Procfile` automáticamente:
```
worker: python bot.py
```

> ⚠️ Asegúrate de que el servicio esté configurado como **Worker** (no Web) en Railway para evitar cobros por puerto HTTP abierto.

### Paso 5 — Deploy

Railway hace el deploy automáticamente al hacer push a `main`. El bot arrancará como proceso background.

---

## 📱 Deploy Nivel Servidor en TV Box Android (Termux)

¡Puedes usar tu TV Box como un mini-servidor 24/7 de bajísimo consumo!

### 1. Preparar Android
1. Abre **Termux** y ejecuta `termux-wake-lock` (esto asegura que la CPU no se suspenda).
2. Ve a los **Ajustes de tu TV Box > Aplicaciones > Termux > Batería** y selecciona "Sin restricciones" o "No optimizar".

### 2. Crear entorno Linux (Ubuntu)
Usaremos `proot-distro` para evitar errores al compilar dependencias pesadas como `pandas` en ARM nativo:

```bash
pkg update && pkg upgrade -y
pkg install proot-distro -y
proot-distro install ubuntu
proot-distro login ubuntu
```

### 3. Setup dentro del Ubuntu virtualizado

```bash
apt update && apt upgrade -y
apt install python3 python3-pip python3-venv git tmux -y
git clone <tu-repo>
cd railway_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita tu archivo .env con nano o vi
```

### 4. Mantener el bot 24/7 con Tmux

```bash
tmux new -s bot
python3 bot.py
```
*Para dejar el bot en segundo plano, presiona `Ctrl + b` y luego `d`. Para recuperar la consola después, usa `tmux attach -t bot` dentro de Ubuntu.*

### 🛠️ Solución a errores comunes (Troubleshooting)

**Error al instalar paquetes:** `Failed to take /etc/passwd lock: Invalid argument`
- **Causa:** Las restricciones de seguridad del kernel de Android impiden que `systemd` administre los usuarios.
- **Solución (ejecutar dentro del entorno Ubuntu):**
```bash
# 1. Engañar al sistema para que ignore el bloqueo
mv /usr/bin/systemd-sysusers /usr/bin/systemd-sysusers.bak
ln -s /usr/bin/true /usr/bin/systemd-sysusers

# 2. Terminar la instalación que quedó pendiente
dpkg --configure -a
apt update && apt upgrade -y
```

---

## 🐘 PostgreSQL (Opcional — historial de trades)

1. En Railway: **New → Database → PostgreSQL**
2. Railway agrega automáticamente `DATABASE_URL` a las variables
3. Puedes usar `asyncpg` o `psycopg2` para guardar `state.trade_history` en una tabla `trades`

```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    side VARCHAR(4),
    entry NUMERIC,
    exit NUMERIC,
    pnl NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📁 Estructura de Archivos

```
railway_bot/
├── bot.py            # Main: Discord bot + trading loop
├── config.py         # Parámetros (SL, TP, RSI, leverage, etc.)
├── requirements.txt  # Dependencias Python
├── Procfile          # Railway: worker: python bot.py
├── .env.example      # Template de variables de entorno
├── .gitignore        # Excluye .env y cache
└── README.md         # Este archivo
```

---

## ⚠️ Disclaimer

Este bot opera en **testnet** por defecto. Para mainnet, setear `BINANCE_TESTNET=False`.  
El trading de futuros con apalancamiento involucra riesgo de pérdida total del capital. Usar bajo su propia responsabilidad.
