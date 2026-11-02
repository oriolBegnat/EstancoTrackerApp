import os
from dotenv import load_dotenv

# 1. Calculamos la ruta exacta
directorio_actual = os.path.dirname(os.path.abspath(__file__))
ruta_env = os.path.join(directorio_actual, ".env")

# 2. Leemos el archivo manualmente (a prueba de caracteres invisibles)
if os.path.exists(ruta_env):
    with open(ruta_env, "r", encoding="utf-8-sig") as f:
        for linea in f:
            linea = linea.strip()
            if "=" in linea and not linea.startswith("#"):
                llave, valor = linea.split("=", 1)
                os.environ[llave] = valor

API_KEY = os.environ.get("GOOGLE_API_KEY")

import requests
import csv
from io import StringIO
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

# Inicializamos la API
app = FastAPI(title="EstancoTracker Web")

URL_GOOGLE_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQJHZIKV0rgQ04qR-Wndaa8kAfhvEAMv9ZqjuoqG3f7H-btUW8s9akOySvDgQyWuwIZsF3MJtVaxKEz/pub?output=csv"

# ==========================================
# INTERFAZ WEB (FRONTEND)
# ==========================================
@app.get("/", response_class=HTMLResponse)
def cargar_interfaz_web():
    """Sirve la página web principal al usuario."""
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EstancoTracker</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; display: flex; flex-direction: column; align-items: center; padding: 2rem; margin: 0; }
            .container { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 580px; width: 100%; box-sizing: border-box; }
            h1 { text-align: center; color: #2c3e50; margin-top: 0; }
            .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
            input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; }
            button { padding: 10px 20px; background-color: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; transition: background 0.3s; }
            button:hover { background-color: #2980b9; }
            .loading { text-align: center; color: #7f8c8d; font-style: italic; display: none; }
            .result-card { background: #f8f9fa; border-left: 4px solid #3498db; padding: 18px; margin-top: 20px; border-radius: 4px; display: none; }
            .error { color: #e74c3c; margin-top: 15px; text-align: center; display: none; }
            .tag { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-bottom: 10px; }
            .tag.open { background: #d4edda; color: #155724; }
            .tag.closed { background: #f8d7da; color: #721c24; }
            .reviews-container { margin-top: 15px; border-top: 1px solid #e1e8ed; padding-top: 15px; }
            .review-item { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 12px; margin-bottom: 10px; font-size: 14px; }
            .review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-weight: bold; color: #2c3e50; font-size: 13px; }
            .review-stars { color: #f39c12; }
            .review-time { color: #888; font-weight: normal; font-size: 12px; }
            .review-text { margin: 0; color: #4a5568; line-height: 1.4; white-space: pre-line; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📍 EstancoTracker</h1>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Ej: MADRID-12 o ALOVERA" onkeypress="if(event.key === 'Enter') buscar()">
                <button onclick="buscar()">Buscar</button>
            </div>
            
            <div id="loading" class="loading">Buscando información en Google...</div>
            <div id="error" class="error"></div>
            
            <div id="result" class="result-card">
                <h2 id="r-nombre" style="margin-top: 0;"></h2>
                <span id="r-estado" class="tag"></span>
                <p><strong>Dirección:</strong> <span id="r-direccion"></span></p>
                <p><strong>Teléfono:</strong> <span id="r-telefono"></span></p>
                <p><strong>Horarios:</strong><br><span id="r-horarios" style="white-space: pre-line;"></span></p>
                <p><a id="r-maps" href="#" target="_blank" style="color: #3498db; text-decoration: none; font-weight: bold;">Ver en Google Maps 🌍</a></p>
                
                <div class="reviews-container">
                    <strong>Reseñas:</strong>
                    <div id="r-resenas" style="margin-top: 10px;"></div>
                </div>
            </div>
        </div>

        <script>
            async function buscar() {
                const query = document.getElementById('searchInput').value.trim();
                if (!query) return;

                document.getElementById('result').style.display = 'none';
                document.getElementById('error').style.display = 'none';
                document.getElementById('loading').style.display = 'block';

                try {
                    const response = await fetch(`/estanco/${query}`);
                    const data = await response.json();

                    if (!response.ok) {
                        throw new Error(data.detail || 'Error desconocido');
                    }

                    document.getElementById('r-nombre').textContent = data.nombre_google;
                    document.getElementById('r-direccion').textContent = data.direccion_buscada;
                    document.getElementById('r-telefono').textContent = data.telefono;
                    
                    const estadoTag = document.getElementById('r-estado');
                    estadoTag.textContent = data.estado;
                    estadoTag.className = 'tag ' + (data.estado.includes('Abierto') ? 'open' : 'closed');
                    
                    document.getElementById('r-horarios').textContent = data.horarios.join('\\n') || 'No disponible';
                    document.getElementById('r-maps').href = data.url_maps;

                    // Renderizado de las reseñas
                    const contenedorResenas = document.getElementById('r-resenas');
                    contenedorResenas.innerHTML = '';
                    
                    if (data.resenas && data.resenas.length > 0) {
                        data.resenas.forEach(resena => {
                            const card = document.createElement('div');
                            card.className = 'review-item';
                            
                            const stars = resena.calificacion ? '⭐'.repeat(resena.calificacion) : '';
                            
                            card.innerHTML = `
                                <div class="review-header">
                                    <span>${resena.autor} <span class="review-stars">${stars}</span></span>
                                    <span class="review-time">${resena.fecha_relativa}</span>
                                </div>
                                <p class="review-text">${resena.texto || '<em>Sin comentario escrito.</em>'}</p>
                            `;
                            contenedorResenas.appendChild(card);
                        });
                    } else {
                        contenedorResenas.innerHTML = '<p style="color: #7f8c8d; font-style: italic;">No hay reseñas disponibles para este local.</p>';
                    }

                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('result').style.display = 'block';
                } catch (error) {
                    document.getElementById('loading').style.display = 'none';
                    const errorDiv = document.getElementById('error');
                    errorDiv.textContent = error.message;
                    errorDiv.style.display = 'block';
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

# ==========================================
# EL PUENTE DE DATOS Y LÓGICA (BACKEND)
# ==========================================
def cargar_base_datos_online(url):
    print("\n[DEBUG SHEETS] Intentando descargar datos...")
    try:
        response = requests.get(url)
        print(f"[DEBUG SHEETS] Código respuesta Google: {response.status_code}")
        print(f"[DEBUG SHEETS] Tipo de archivo recibido: {response.headers.get('Content-Type', '')}")
        
        if 'text/html' in response.headers.get('Content-Type', ''):
            print("[DEBUG SHEETS] ERROR: Google devuelve una web bloqueada, no un CSV.")
            return None
            
        response.raise_for_status() 
        response.encoding = 'utf-8'
        
        archivo_virtual = StringIO(response.text)
        lector = csv.DictReader(archivo_virtual, delimiter=',')
        
        cabeceras = lector.fieldnames
        print(f"[DEBUG SHEETS] Columnas detectadas en tu Excel: {cabeceras}")
        
        if not cabeceras or 'Nombre Estanco' not in cabeceras:
            print("[DEBUG SHEETS] ERROR: Falta la columna 'Nombre Estanco'.")
            return None
            
        base_datos = {}
        for fila in lector:
            if not fila.get('Nombre Estanco'): continue
            id_estanco = str(fila['Nombre Estanco']).strip().upper()
            base_datos[id_estanco] = {
                "direccion": str(fila.get('Dirección estanco', fila.get('Direccion estanco', ''))).strip(),
                "municipio": str(fila.get('Municipio', '')).strip(),
                "codPostal": str(fila.get('Codigo Postal', fila.get('Código Postal', fila.get('CP', '')))).strip()
            }
        print(f"[DEBUG SHEETS] Éxito: {len(base_datos)} estancos cargados.\n")
        return base_datos
        
    except Exception as e:
        print(f"[DEBUG SHEETS] ERROR INTERNO en Python: {e}\n")
        return None

@app.get("/estanco/{id_completo}")
def consultar_estanco(id_completo: str):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key no configurada.")
        
    base_datos = cargar_base_datos_online(URL_GOOGLE_SHEETS)
    if base_datos is None:
        raise HTTPException(status_code=500, detail="Error de conexión con Sheets.")
    
    id_busqueda = id_completo.strip().upper()
    
    if id_busqueda not in base_datos:
        coincidencias = [k for k in base_datos.keys() if id_busqueda.split('-')[0] in k]
        msg = f"El ID '{id_busqueda}' no existe."
        if coincidencias:
            msg += f" ¿Quizás quisiste decir: {', '.join(coincidencias[:5])}?"
        raise HTTPException(status_code=404, detail=msg)

    datos_reales = base_datos[id_busqueda]
    query_places = f"Estanco {datos_reales['direccion']}, {datos_reales['codPostal']} {datos_reales['municipio']}".strip()
    
    # PASO 1: Buscar el estanco para obtener los datos básicos y el ID único del lugar
    search_url = "https://places.googleapis.com/v1/places:searchText"
    search_payload = {
        "textQuery": query_places,
        "languageCode": "es"
    }
    search_headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.businessStatus,places.nationalPhoneNumber,places.regularOpeningHours,places.googleMapsUri"
    }
    
    search_resp = requests.post(search_url, json=search_payload, headers=search_headers)
    search_data = search_resp.json()
    
    if "error" in search_data or not search_data.get("places"):
        raise HTTPException(status_code=404, detail="Google no encontró este estanco.")
        
    estanco = search_data["places"][0]
    place_id = estanco.get("id")
    
    # PASO 2: Obtener las reseñas del lugar mediante Place Details
    resenas_procesadas = []
    if place_id:
        details_url = f"https://places.googleapis.com/v1/places/{place_id}"
        details_headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "reviews"
        }
        params = {"languageCode": "es"}
        details_resp = requests.get(details_url, headers=details_headers, params=params)
        details_data = details_resp.json()
        
        raw_reviews = details_data.get("reviews", [])
        for rev in raw_reviews[:5]:
            resenas_procesadas.append({
                "autor": rev.get("authorAttribution", {}).get("displayName", "Usuario anónimo"),
                "calificacion": rev.get("rating", 0),
                "fecha_relativa": rev.get("relativePublishTimeDescription", ""),
                "texto": rev.get("text", {}).get("text", "").strip()
            })
    
    estados_es = {
        "OPERATIONAL": "Abierto / Operativo",
        "CLOSED_TEMPORARILY": "Cerrado temporalmente",
        "CLOSED_PERMANENTLY": "Cerrado permanentemente"
    }
    
    return {
        "nombre_google": estanco.get("displayName", {}).get("text", "Desconocido"),
        "direccion_buscada": f"{datos_reales['direccion']}, {datos_reales['codPostal']} {datos_reales['municipio']}",
        "estado": estados_es.get(estanco.get("businessStatus", ""), "Estado desconocido"),
        "telefono": estanco.get("nationalPhoneNumber", "No disponible"),
        "url_maps": estanco.get("googleMapsUri", "#"),
        "horarios": estanco.get("regularOpeningHours", {}).get("weekdayDescriptions", []),
        "resenas": resenas_procesadas
    }