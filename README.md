# 🤖 Discord Trading Bot — Binance Futures Testnet en TV Box Android

Bot de scalping automático en Python para Binance Futures Testnet, con alertas y comandos vía Discord. Diseñado para correr 24/7 de forma grauita en un **TV Box Android (Termux)** como mini-servidor de bajísimo consumo eléctrico. También incluye instrucciones como alternativa para plataformas en la nube como **Railway.app**.

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

## 📱 Deploy Principal: Mini Servidor 24/7 (TV Box Android)

¡Puedes usar tu TV Box como un mini-servidor 24/7 de bajísimo consumo eléctrico para correr este bot de forma nativa!

### 1. Preparar Android
1. Abre **Termux** y ejecuta `termux-wake-lock` (esto asegura que la CPU del TV Box no se suspenda aunque se apague la pantalla).
2. Ve a los **Ajustes de tu TV Box > Aplicaciones > Termux > Batería** y selecciona "Sin restricciones" o "No optimizar".

### 2. Instalar el entorno de Termux Nativo
A diferencia de las distribuciones Linux emuladas (como Ubuntu o Debian) que tienen problemas de permisos, el **Termux nativo** tiene acceso libre al hardware criptográfico de Android, por lo que **evitarás por completo los letales errores de `SSL` o `PRNG is not seeded`**.

```bash
# 1. Actualizar e instalar el repositorio científico (Tur-Repo)
pkg update && pkg upgrade -y
pkg install tur-repo -y

# 2. Instalar Python, tmux, git y las versiones pre-compiladas de Pandas/Numpy
pkg install python git tmux python-pandas python-numpy -y
```

### 3. Traer credenciales SSH y Clonar
Para clonar repositorios privados (sin teclear contraseñas) usa tu certificado SSH:

**Opción A: Pegar tu llave (Recomendada y más fácil)**
```bash
mkdir -p ~/.ssh
nano ~/.ssh/id_ed25519   # O usa id_rsa dependiento de tu llave
```
Pega el texto de tu llave privada adentro, guarda (`Ctrl+O`, `Enter`) y ajusta sus permisos de seguridad obligatoria:
```bash
chmod 600 ~/.ssh/id_ed25519
ssh-keyscan github.com >> ~/.ssh/known_hosts
```

**Opción B: Transferir por SCP** (Desde tu PC al TV Box por red local)
```bash
scp -P 8022 ~/.ssh/id_ed25519 tu_usuario@IP_DEL_TVBOX:~/.ssh/
```

**Finalmente, clona el repositorio:**
```bash
git clone git@github.com:nscordamaglia/crypto_agent.git
cd crypto_agent
```

### 4. Setup del Bot

Como Termux funciona de por sí como un "contenedor" blindado frente al resto de Android, **crear un entorno virtual adentro (venv) es redundante y puedes instalar globalmente directamente**. 

Además, dado que Termux instaló su propia versión hiper-optimizada de Pandas (`tur-repo`), debemos quitarle la cadena estricta de versión a tu archivo para que _pip_ no intente compilar uno viejo sobreescribiéndolo:

```bash
# Quitar versión estricta de pandas en el archivo
sed -i 's/pandas==2.2.1/pandas/g' requirements.txt

# Instalar dependencias globalmente
pip install -r requirements.txt --break-system-packages

# Configurar variables usando el ejemplo
cp .env.example .env
nano .env  # Edita este archivo agregándole tus tokens de Binance y Discord
```

### 5. Mantener el bot 24/7 con Tmux

```bash
tmux new -s bot
python bot.py
```
*Tip: Para dejar el bot corriendo en el fondo: presiona la combinación `Ctrl + b` y suelta, luego presiona la letra `d`. Para recuperar la consola visualmente horas después: escribe `tmux attach -t bot`.*

---

## 🚀 Setup Rápido (Local / PC)

Si solo quieres probar el bot en tu computadora personal:

### 1. Clonar y preparar entorno

```bash
git clone git@github.com:nscordamaglia/crypto_agent.git
cd crypto_agent
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus tokens:
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

## 🚂 Deploy Alternativo: Nube (Railway.app)

Como alternativa al local y al TV Box, puedes subir el bot a un servicio en la nube como Railway.

### Paso 1 — Subir código a GitHub

Opcional si usas tu propio fork:
```bash
git init
git add .
git commit -m "feat: trading bot continuo"
git remote add origin git@github.com:nscordamaglia/crypto_agent.git
git push -u origin main
```

### Paso 2 — Crear proyecto en Railway

1. Ir a [railway.app](https://railway.app) y loguearte con GitHub.
2. Hacer clic en **New Project → Deploy from GitHub repo**.
3. Seleccionar tu repositorio `crypto_agent`.

### Paso 3 — Configurar Variables de Entorno

En el dashboard de Railway ve a la sección **Variables** y agrega:

```
DISCORD_TOKEN       = tu_token_discord
BINANCE_API_KEY     = tu_api_key_testnet
BINANCE_SECRET      = tu_secret_testnet
BINANCE_TESTNET     = True
```

### Paso 4 — Verificar Procfile

Railway detecta el archivo `Procfile` de la raíz automáticamente:
```
worker: python bot.py
```

> ⚠️ Asegúrate de que el servicio esté configurado internamente como **Worker** (y no como servicio Web) en la configuración de Railway para evitar cobros innecesarios por dejar un puerto HTTP expuesto.

### Paso 5 — Deploy

Railway hará el deploy del código automáticamente cada vez que hagas un push a la rama `main`, y el bot arrancará como proceso contínuo en el background.

---

## 🐘 PostgreSQL (Opcional — historial de trades)

1. En Railway: **New → Database → PostgreSQL**
2. Railway agrega automáticamente `DATABASE_URL` a las variables.
3. Puedes usar librerías como `asyncpg` o `psycopg2` para guardar la variable `state.trade_history` en una tabla llamada `trades`.

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
crypto_agent/
├── bot.py            # Main: Discord bot + loop de trading
├── config.py         # Parámetros técnicos (SL, TP, RSI, leverage, etc.)
├── requirements.txt  # Dependencias de Python
├── Procfile          # Pautas para Railway: "worker: python bot.py"
├── .env.example      # Archivo para basar las variables de entorno
├── .gitignore        # Excluye .env, cache y carpetas bin/venv
└── README.md         # Documentación y Setup
```

---

## ⚠️ Disclaimer

Este bot opera transacciones de derivados en **Testnet** (entorno de pruebas) por defecto. Para usarlo con dinero real, setear la variable de entorno a `BINANCE_TESTNET=False`.  
Pese a ser un bot educativo, el trading automático de criptomonedas y futuros con apalancamiento es altamente riesgoso y puede llevar a la pérdida de tu capital completo en minutos. Utilizar la versión en Mainnet **estritamente bajo su propia responsabilidad**.
