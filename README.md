# Bot de picks con valor — WhatsApp diario

Corre automáticamente cada mañana a las 8:00 AM (Colombia).
Usa **Gemini 1.5 Flash** (Google, gratis) + **football-data.org** (gratis) + **Twilio WhatsApp sandbox** (gratis).

---

## APIs necesarias (todas gratis)

| Servicio | Para qué | Link |
|----------|----------|------|
| Google AI Studio | Gemini API key | https://aistudio.google.com |
| football-data.org | Partidos del día | https://www.football-data.org |
| Twilio | Enviar WhatsApp | https://www.twilio.com |
| GitHub | Automatización | https://github.com |

---

## Paso 1 — Gemini API key (Google AI Studio)

1. Ve a https://aistudio.google.com
2. Inicia sesión con tu cuenta Google
3. Clic en **"Get API key"** → **"Create API key"**
4. Copia la key (empieza con `AIza...`)
5. Es 100% gratis con límites generosos (hasta 1,500 requests/día)

---

## Paso 2 — football-data.org API key

1. Ve a https://www.football-data.org/client/register
2. Regístrate gratis
3. Recibes la API key por email
4. Plan gratuito: 10 requests/minuto, acceso a las principales ligas

> Nota: el plan gratuito cubre Premier League, La Liga, Serie A, Bundesliga, Champions League, Ligue 1, Eredivisie y Brasileirao. Las ligas de Colombia, Bélgica y Turquía requieren plan de pago, pero las demás son más que suficientes.

---

## Paso 3 — Twilio WhatsApp Sandbox

1. Crea cuenta gratis en https://www.twilio.com
2. En el dashboard ve a **Messaging → Try it out → Send a WhatsApp message**
3. Guarda el número de Twilio sandbox en tus contactos (ej: +1 415 523 8886)
4. Desde tu WhatsApp envía el código que te muestran (ej: `join <palabra>`) a ese número
5. Cuando te respondan, el sandbox está activo
6. Copia del dashboard:
   - **Account SID** (empieza con `AC...`)
   - **Auth Token**
   - El número sandbox: `whatsapp:+14155238886`

---

## Paso 4 — Crear repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre: `betting-picks-bot`
3. Visibilidad: **Privado** (importante, tiene tus keys)
4. Crea el repo y sube estos archivos manteniendo la estructura:

```
betting-picks-bot/
├── analyze.py
├── requirements.txt
└── .github/
    └── workflows/
        └── daily_picks.yml
```

Para subir: en el repo recién creado haz clic en **"uploading an existing file"** y arrastra los archivos.

> El archivo `.github/workflows/daily_picks.yml` tienes que crearlo a mano en GitHub:
> - Crea la carpeta `.github/workflows/` usando el botón **Add file → Create new file**
> - Escribe `.github/workflows/daily_picks.yml` como nombre
> - Pega el contenido del archivo

---

## Paso 5 — Agregar los Secrets

1. En tu repo ve a **Settings → Secrets and variables → Actions**
2. Clic en **"New repository secret"** y agrega estos 6:

| Nombre | Valor |
|--------|-------|
| `GEMINI_API_KEY` | Tu key de Google AI Studio |
| `FOOTYSTATS_API_KEY` | Tu key de football-data.org |
| `TWILIO_ACCOUNT_SID` | Tu Account SID de Twilio |
| `TWILIO_AUTH_TOKEN` | Tu Auth Token de Twilio |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+14155238886` |
| `TWILIO_WHATSAPP_TO` | `whatsapp:+57TUNUMERO` |

Ejemplo de `TWILIO_WHATSAPP_TO`: `whatsapp:+573001234567`

---

## Paso 6 — Probar manualmente

1. En tu repo ve a la pestaña **Actions**
2. Clic en **"Picks con valor — análisis diario"**
3. Clic en **"Run workflow"** → **"Run workflow"**
4. Espera 1-2 minutos
5. Revisa tu WhatsApp — debería llegarte el mensaje

---

## Horario automático

Corre todos los días a las **13:00 UTC = 8:00 AM Colombia**.

Para cambiarlo edita en `daily_picks.yml`:
```yaml
- cron: '0 13 * * *'
```
Usa https://crontab.guru para calcular el UTC correcto.

---

## Resumen de costos

| Servicio | Costo |
|----------|-------|
| GitHub Actions | Gratis (2,000 min/mes) |
| Gemini 1.5 Flash | Gratis (1,500 req/día) |
| football-data.org | Gratis |
| Twilio WhatsApp Sandbox | Gratis |
| **Total** | **$0/mes** |

---

## Ejemplo de mensaje WhatsApp

```
PICKS CON VALOR — 03/05/2026
Partidos revisados: 24 | Picks encontrados: 3
Filtros: EV ≥15% · Cuota ≥1.40 · Rushbet Colombia
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 Pick 1 — Arsenal vs Chelsea
   Premier League · 14:30 (COL)
   Mercado: Over/Under
   Selección: Over 2.5 goles
   Cuota mín: 1.72 · EV: +22.3%
   Ambos equipos promedian 2.8 goles últimos 5
────────────────────
🟡 Pick 2 — Real Madrid vs Atlético
   La Liga · 18:00 (COL)
   Mercado: Corners
   Selección: Over 9.5 corners
   Cuota mín: 1.55 · EV: +17.8%
   Promedio 11.2 corners en derbis recientes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Análisis IA · Solo informativo · Juega responsablemente
```
