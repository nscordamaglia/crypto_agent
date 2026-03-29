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

## 📦 Dependencias (requirements.txt)

- `discord.py==2.3.2`
- `python-binance==1.0.19`
- `python-dotenv==1.0.1`
- `aiohttp==3.9.3`

### ⚙️ Librería de Sistema (Obligatoria)
- **`numpy`**: Debe instalarse a través del gestor de paquetes del sistema (`pkg install python-numpy` en Termux o `apt install` en Linux) para asegurar compatibilidad binaria y rendimiento.

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

# 2. Instalar Python, tmux, git y la versión pre-compilada de Numpy
# Nota: Ya NO usamos pandas ni ta-lib para ser ultra-ligeros.
pkg install python git tmux python-numpy -y
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

### 4. Setup del Bot (Gestión de Dependencias)

⚠️ **IMPORTANTE:** Hemos removido `pandas` de `requirements.txt` para evitar conflictos de binarios en Android/Termux. Dependiendo de dónde corras el bot, la instalación varía:

#### Escenario A: TV Box (Termux Nativo)
En Android no uses `pip` para librerías pesadas. El bot ahora usa **NumPy puro** para que sea ultra-rápido:
```bash
# 1. Instalar NumPy desde el sistema (TUR)
pkg install python-numpy -y

# 2. Instalar el resto de dependencias ligeras (discord.py, binance, etc.)
pip install -r requirements.txt --break-system-packages
```

#### Escenario B: Linux / WSL / Railway / PC
En sistemas convencionales:
```bash
# 1. Activar venv (opcional)
python -m venv .venv && source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt
```

#### 5. Configurar Variables de Entorno
```bash
cp .env.example .env
nano .env  # Agrega tus tokens de Binance y Discord
```

### 5. Mantener el bot 24/7 con Tmux

```bash
tmux new -s bot
python bot.py
```
*Tip: Para dejar el bot corriendo en el fondo: presiona la combinación `Ctrl + b` y suelta, luego presiona la letra `d`. Para recuperar la consola visualmente horas después: escribe `tmux attach -t bot`.*


---

## 💻 Desarrollo y Sincronización (WSL -> TV Box) (Recomendado)

Si estás desarrollando desde **Windows (WSL/Ubuntu)**, la forma más estable de enviar tus cambios al TV Box sin desconexiones es usando `rsync`.

### 1. Preparación
Asegúrate de tener `rsync` en ambos lados:
- **WSL:** Ya viene instalado por defecto.
- **Termux:** Ejecuta `pkg install rsync -y`.

### 2. Comando de Sincronización
Ejecuta el siguiente comando desde la carpeta raíz del proyecto en WSL:

```bash
rsync -avz -e "ssh -p 8022" ./ TU_USUARIO@IP_DEL_TVBOX:/data/data/com.termux/files/home/crypto_agent/ --exclude '.git' --exclude '.venv'
```

> **Tip:** El flag `--exclude '.git'` evita que se suba toda la carpeta de historial de Git, haciendo que la transferencia sea casi instantánea.

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
DISCORD_APPLICATION_ID=tu_application_id
BINANCE_API_KEY=tu_api_key_testnet
BINANCE_SECRET=tu_secret_testnet
BINANCE_TESTNET=True

# Seguridad (Opcional pero recomendado)
BINANCE_USE_RSA=False
BINANCE_PRIVATE_KEY_PATH=./private_key.pem
```

### 3. Ejecutar

```bash
python bot.py
```

---

## 🔑 Obtener credenciales Binance Testnet (HMAC vs RSA)

Binance ofrece dos formas de autenticar tu bot. El bot soporta ambas:

### Opción A: HMAC (Rápida y por defecto)
1. Ir a [testnet.binancefuture.com](https://testnet.binancefuture.com)
2. **API Management** → **Create API**
3. Copiar `API Key` y `Secret Key` en tu `.env`.
4. Deja `BINANCE_USE_RSA=False`.

### Opción B: RSA (Máxima Seguridad - Recomendada)
Este método es más seguro porque Binance nunca conoce tu "secreto", solo tu llave pública.
1. Genera un par de llaves RSA (privada y pública).
2. Sube la **Llave Pública** (.pub) a Binance API Management.
3. Configura en tu `.env`:
   - `BINANCE_USE_RSA=True`
   - `BINANCE_PRIVATE_KEY_PATH=ruta/a/tu/llave_privada.pem`
4. Borra (o deja vacío) `BINANCE_SECRET`.

---

## 🤖 Configuración del Bot en Discord

Para que el bot funcione, necesitas tener un **Servidor de Discord** propio (puedes crear uno gratis en el signo `+` de tu lista de servidores).

### 1. Obtener el Token (Paso Crítico)
1. Ve al [Discord Developer Portal](https://discord.com/developers/applications).
2. Selecciona tu Aplicación -> **Bot** (menú lateral).
3. Busca la sección **Token** y dale al botón **Reset Token**. 
   *   *Nota: No confundir con la 'Public Key' de la pestaña General. El Token es el que permite al bot iniciar sesión.*
4. Copia el token generado y pégalo en tu `.env`.

### 2. Activar Permisos Especiales (Intents)
Sin esto, el bot no podrá leer tus comandos:
1. En la misma pestaña **Bot**, baja hasta **Privileged Gateway Intents**.
2. **Activa el interruptor "MESSAGE CONTENT INTENT"**.
3. Dale a **Save Changes**.

### 3. Invitar el Bot a tu Servidor
1. Ve a **OAuth2** → **URL Generator**.
2. Scopes: Selecciona `bot`.
3. Bot Permissions: Selecciona `Send Messages`, `Embed Links`, `Read Message History`.
4. Copia la URL generada, ábrela en tu navegador e invita al bot a tu servidor.

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
├── deploy.sh         # Script de sincronización WSL -> TV Box (Rsync)
└── README.md         # Documentación y Setup
```

---

## 🛠️ Troubleshooting (Solución de Problemas)

### Error: "Transport endpoint is not connected"
Este error ocurre si alguna vez intentaste usar un montaje SSHFS y la conexión se rompió. La terminal queda bloqueada intentando acceder a una carpeta fantasma.
**Solución:**
1. Sal de cualquier carpeta de proyecto: `cd ~`
2. Limpia el montaje zombi:
   ```bash
   sudo umount -l /home/rustycius/portal_tvbox
   ```
3. Vuelve a tu carpeta de proyecto y el comando de `rsync` funcionará normalmente.

---

## ⚠️ Disclaimer

Este bot opera transacciones de derivados en **Testnet** (entorno de pruebas) por defecto. Para usarlo con dinero real, setear la variable de entorno a `BINANCE_TESTNET=False`.  
Pese a ser un bot educativo, el trading automático de criptomonedas y futuros con apalancamiento es altamente riesgoso y puede llevar a la pérdida de tu capital completo en minutos. Utilizar la versión en Mainnet **estritamente bajo su propia responsabilidad**.
