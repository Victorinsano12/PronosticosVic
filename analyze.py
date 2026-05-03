import os
import json
import re
import requests
from datetime import datetime
from twilio.rest import Client

GEMINI_API_KEY      = os.environ["GEMINI_API_KEY"]
FOOTYSTATS_API_KEY  = os.environ["FOOTYSTATS_API_KEY"]
TWILIO_ACCOUNT_SID  = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN   = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM         = os.environ["TWILIO_WHATSAPP_FROM"]
TWILIO_TO           = os.environ["TWILIO_WHATSAPP_TO"]

LIGAS_IDS = {
    "Premier League":        2012,
    "La Liga":               2014,
    "Serie A":               2019,
    "Bundesliga":            2002,
    "Champions League":      2001,
    "Ligue 1":               2015,
    "Eredivisie":            2003,
    "Brasileirao":           2013,
    "Liga BetPlay Colombia": 2010,
}

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY
)


def footy_get(endpoint, params=None):
    base = "https://api.football-data.org/v4"
    headers = {"X-Auth-Token": FOOTYSTATS_API_KEY}
    r = requests.get(f"{base}{endpoint}", headers=headers, params=params or {}, timeout=15)
    r.raise_for_status()
    return r.json()


def get_matches_today():
    today = datetime.now().strftime("%Y-%m-%d")
    data = footy_get("/matches", {"dateFrom": today, "dateTo": today})
    matches = data.get("matches", [])
    resultado = []
    for m in matches:
        comp = m.get("competition", {}).get("name", "")
        home = m.get("homeTeam", {}).get("name", "")
        away = m.get("awayTeam", {}).get("name", "")
        hora = m.get("utcDate", "")[:16].replace("T", " ")
        if home and away:
            resultado.append({
                "partido": f"{home} vs {away}",
                "liga": comp,
                "hora_utc": hora,
            })
    return resultado


def ask_gemini(matches_json: str, fecha: str) -> dict:
    prompt = f"""Eres un analista experto en apuestas deportivas de valor positivo (value betting).

Fecha de hoy: {fecha}

Estos son los partidos que se juegan hoy:
{matches_json}

Tu tarea:
1. Para cada partido analiza mentalmente estadísticas típicas recientes: forma de equipos, goles por partido, corners, tarjetas, tendencias local/visitante, h2h histórico.
2. Estima la probabilidad real (%) de distintos mercados: 1X2, ambos anotan sí/no, over/under 2.5 goles, corners +9.5, hándicap asiático, resultado al descanso.
3. Calcula EV% = (prob_real / 100 × cuota_mínima_estimada) - 1
4. Filtra SOLO picks donde: EV% ≥ 0.15 Y cuota_mínima ≥ 1.40
5. Devuelve máximo 8 picks ordenados por EV descendente.
6. Confianza: "alta" si prob_real ≥ 65%, "media" si entre 55-64%.
7. Si no hay picks genuinos con valor real, devuelve array vacío.

RESPONDE ÚNICAMENTE con JSON válido, sin backticks, sin texto adicional:
{{
  "fecha": "{fecha}",
  "total_analizados": <número de partidos revisados>,
  "picks": [
    {{
      "partido": "Equipo A vs Equipo B",
      "liga": "nombre liga",
      "hora_utc": "YYYY-MM-DD HH:MM",
      "mercado": "tipo de mercado",
      "seleccion": "descripción concreta del pick",
      "prob_real": 72,
      "cuota_min": 1.65,
      "ev": 19.8,
      "confianza": "alta",
      "razon": "razón estadística máx 80 caracteres"
    }}
  ]
}}"""

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1500}
    }
    r = requests.post(GEMINI_URL, json=body, timeout=60)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        raise ValueError("Gemini no devolvió JSON válido")
    return json.loads(match.group(0))


def utc_to_colombia(hora_utc: str) -> str:
    try:
        dt = datetime.strptime(hora_utc, "%Y-%m-%d %H:%M")
        col_hour = (dt.hour - 5) % 24
        return f"{col_hour:02d}:{dt.minute:02d}"
    except Exception:
        return hora_utc


def format_whatsapp(data: dict) -> str:
    fecha   = data.get("fecha", "hoy")
    picks   = data.get("picks", [])
    total   = data.get("total_analizados", 0)

    lines = [
        f"*PICKS CON VALOR — {fecha}*",
        f"Partidos revisados: {total} | Picks encontrados: {len(picks)}",
        f"Filtros: EV ≥15% · Cuota ≥1.40 · Rushbet Colombia",
        "━" * 28,
    ]

    if not picks:
        lines += [
            "Sin picks con valor detectado hoy.",
            "No se encontró ventaja suficiente. Mejor no apostar.",
        ]
    else:
        for i, p in enumerate(picks, 1):
            hora_col = utc_to_colombia(p.get("hora_utc", ""))
            icon = "🟢" if p.get("confianza") == "alta" else "🟡"
            lines.append(
                f"{icon} *Pick {i} — {p['partido']}*\n"
                f"   {p['liga']} · {hora_col} (COL)\n"
                f"   Mercado: {p['mercado']}\n"
                f"   Selección: *{p['seleccion']}*\n"
                f"   Cuota mín: *{p['cuota_min']:.2f}* · EV: *+{p['ev']:.1f}%*\n"
                f"   {p['razon']}"
            )
            if i < len(picks):
                lines.append("─" * 20)

    lines += ["━" * 28, "_Análisis IA · Solo informativo · Juega responsablemente_"]
    return "\n".join(lines)


def send_whatsapp(message: str):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    msg = client.messages.create(from_=TWILIO_FROM, to=TWILIO_TO, body=message)
    print(f"WhatsApp enviado: {msg.sid}")


def main():
    fecha = datetime.now().strftime("%d/%m/%Y")
    print(f"Iniciando análisis — {fecha}")

    matches = get_matches_today()
    print(f"Partidos encontrados hoy: {len(matches)}")

    if not matches:
        print("No hay partidos hoy en las ligas configuradas.")
        send_whatsapp(f"*PICKS CON VALOR — {fecha}*\n\nNo se encontraron partidos hoy en las ligas monitoreadas.")
        return

    matches_json = json.dumps(matches, ensure_ascii=False, indent=2)
    data = ask_gemini(matches_json, fecha)
    print(f"Picks con valor: {len(data.get('picks', []))}")

    mensaje = format_whatsapp(data)
    print("\nMensaje generado:\n", mensaje)
    send_whatsapp(mensaje)
    print("Listo.")


if __name__ == "__main__":
    main()
