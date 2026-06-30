"""
=============================================================
  app.py - Backend CajeroSinComisión
  Funciona en local (puerto 5000) y en Render (puerto dinámico)
=============================================================
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from math import radians, sin, cos, sqrt, atan2
import json
import os

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────────────────────
# CARGAR DATOS
# ─────────────────────────────────────────────────────────────

def cargar_cajeros():
    ruta = os.path.join(os.path.dirname(__file__), "cajeros_chile_limpio.json")
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        cajeros = datos["cajeros"]
        print(f"✅ {len(cajeros)} cajeros cargados")
        return cajeros
    except FileNotFoundError:
        print("❌ No se encontró cajeros_chile_limpio.json")
        return []

CAJEROS = cargar_cajeros()


# ─────────────────────────────────────────────────────────────
# DISTANCIA HAVERSINE
# ─────────────────────────────────────────────────────────────

def distancia_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ─────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({
        "app":              "CajeroSinComisión API",
        "version":          "1.0",
        "estado":           "funcionando",
        "cajeros_cargados": len(CAJEROS),
        "endpoints": {
            "bancos":   "/api/bancos",
            "cercanos": "/api/cajeros/cercanos?lat=-33.45&lon=-70.65&banco=BancoEstado&radio=2",
        }
    })


@app.route("/api/bancos")
def get_bancos():
    bancos = sorted(set(c["banco"] for c in CAJEROS))
    return jsonify({"bancos": bancos, "total": len(bancos)})


@app.route("/api/cajeros/cercanos")
def get_cajeros_cercanos():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"error": "lat y lon son requeridos"}), 400

    banco = request.args.get("banco", "").strip()
    if not banco:
        return jsonify({"error": "banco es requerido"}), 400

    radio = float(request.args.get("radio", 5))
    limit = int(request.args.get("limit", 30))

    if not (-56 <= lat <= -17) or not (-76 <= lon <= -65):
        return jsonify({"error": "Coordenadas fuera de Chile"}), 400

    cajeros_banco = [c for c in CAJEROS if banco.lower() in c["banco"].lower()]

    resultado = []
    for cajero in cajeros_banco:
        dist = distancia_km(lat, lon, cajero["lat"], cajero["lon"])
        if dist <= radio:
            resultado.append({
                "id":           cajero["id"],
                "banco":        cajero["banco"],
                "lat":          cajero["lat"],
                "lon":          cajero["lon"],
                "direccion":    cajero.get("direccion", ""),
                "ciudad":       cajero.get("ciudad", ""),
                "horario":      cajero.get("horario", ""),
                "nombre_lugar": cajero.get("nombre_lugar", ""),
                "distancia_km": round(dist, 3),
                "distancia_m":  round(dist * 1000),
            })

    resultado.sort(key=lambda x: x["distancia_km"])
    resultado = resultado[:limit]

    return jsonify({
        "banco":     banco,
        "ubicacion": {"lat": lat, "lon": lon},
        "radio_km":  radio,
        "total":     len(resultado),
        "cajeros":   resultado
    })


@app.route("/api/cajeros/todos")
def get_todos():
    banco = request.args.get("banco", "").strip()
    cajeros = [c for c in CAJEROS if banco.lower() in c["banco"].lower()] if banco else CAJEROS
    return jsonify({"total": len(cajeros), "cajeros": cajeros})


# ─────────────────────────────────────────────────────────────
# INICIAR
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    print(f"\n🚀 Servidor en http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
