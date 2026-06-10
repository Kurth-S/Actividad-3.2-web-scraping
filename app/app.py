from flask import Flask, jsonify, request
from flask_cors import CORS
import urllib.request
import json
import ssl

app = Flask(__name__)

CORS(app)

# --- BASE DE DATOS TEMPORAL (EN MEMORIA) ---
db_usuarios = {"admin": "1234"}
db_inventario = []

# --- MÓDULO DE SCRAPING NATIVO ---
def obtener_datos_externos():
    url = "https://okwu.cl/collections/labiales/products.json"

    # Bypass para problemas de certificados SSL
    context = ssl._create_unverified_context()

    try:
        # Petición HTTP usando librería estándar de Python
        with urllib.request.urlopen(url, context=context, timeout=10) as response:
            if response.status != 200:
                return None

            # Procesamiento de JSON
            raw_data = json.loads(response.read().decode())
            productos_api = raw_data.get('products', [])

            # Normalización de campos según pedido
            resultado = []
            for p in productos_api:
                v = p['variants'][0]

                prod_normalizado = {
                    "id_interno": p['id'],
                    "nombre": p['title'],
                    "precio_regular": float(v['compare_at_price'] or v['price']),
                    "precio_oferta": float(v['price']) if v['compare_at_price'] else None,
                    "variantes": [var['title'] for var in p['variants']],
                    "imagen": p['images'][0]['src'] if p['images'] else "sin_imagen.jpg",
                    "stock": sum(int(var.get('inventory_quantity', 0)) for var in p['variants'])
                }
                resultado.append(prod_normalizado)
            return resultado

    except Exception as e:
        print(f"DEBUG: Error capturado en scraping: {e}")
        return None

# --- ENDPOINTS API REST ---

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    usuario = data.get('username')
    password = data.get('password')

    if db_usuarios.get(usuario) == password:
        return jsonify({"status": "success", "token": "TOKEN-DSY1106-2026", "user": usuario}), 200
    return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401

@app.route('/api/productos', methods=['GET'])
def get_productos():
    global db_inventario

    datos_frescos = obtener_datos_externos()

    if datos_frescos:
        db_inventario = datos_frescos
        return jsonify(db_inventario), 200
    else:
        if db_inventario:
            return jsonify(db_inventario), 200
        return jsonify({"error": "No se pudo obtener el catálogo de okwu.cl"}), 503

@app.route('/api/pedidos', methods=['POST'])
def crear_pedido():
    data = request.json
    return jsonify({"message": "Pedido recibido", "detalle": data}), 201

# --- EJECUCIÓN DEL SERVIDOR ---
if __name__ == '__main__':
    print("--- Servidor eCommerce-X Iniciado ---")
    print("Endpoints activos:")
    print("1. POST http://localhost:5000/api/auth/login")
    print("2. GET  http://localhost:5000/api/productos")
    print("3. POST http://localhost:5000/api/pedidos")
    app.run(debug=True, port=5000)
