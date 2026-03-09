#!/usr/bin/env python3
"""
Dashboard de Decisiones - Compra Ágil
Con editor de prompts desde la web
"""
from flask import Flask, jsonify, render_template_string, request
import sqlite3
import os
import json

app = Flask(__name__)
DB_PATH = '/Users/einstein/.openclaw/workspace/historico_mercado_publico.db'
CONFIG_FILE = '/Users/einstein/.openclaw/workspace/chat_config.json'

# Cargar o crear configuración
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        return {
            "saludo": "¡Hola! Soy tu asesor de Mercado Público 🧠\n\nTe ayudo a encontrar los mejores productos para vender.\n\nPreguntame:\n• ¿Qué productos son buenos?\n• ¿Conviene vender aseo?\n• ¿Dónde hay oportunidades?",
            "categorias": {
                "aseo": {"recomendacion": "Mercado grande pero competitivo. Márgenes bajos.", "consejo": "Enfocarte en productos específicos o de nicho."},
                "tóner": {"recomendacion": "EL PRODUCTO TOP. Alta demanda, buenos precios.", "consejo": "Si conseguís buen proveedor, es oro."},
                "médico": {"recomendacion": "Menos competencia, buenos precios.", "consejo": "Productos dentales y hospitalarios andan muy bien."}
            },
            "preguntas": {
                "que_vender": "🎯 MIS RECOMENDACIONES:\n\n1. TÓNER/TINTA - #1 demanda\n2. TECNOLOGÍA - Demanda creciente\n3. MÉDICO - Menos competencia\n4. ASEO - Mucha demanda pero competitivo"
            },
            "estilo": "amigable"
        }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_filter():
    filter_val = request.args.get('ganadas', 'todas')
    if filter_val == 'si':
        return "AND (ProveedorSeleccionado = 'si')"
    elif filter_val == 'no':
        return "AND (ProveedorSeleccionado = 'no' OR ProveedorSeleccionado = '')"
    return ""

def get_data_for_query(pregunta, filter_sql):
    conn = get_db()
    pregunta = pregunta.lower()
    results = {}
    
    categorias = {
        'aseo': ['aseo', 'limpieza', 'detergente', 'jabón', 'cloro', 'desinfectante'],
        'tóner': ['tóner', 'toner', 'cartucho', 'tinta'],
        'médico': ['médico', 'medico', 'dental', 'hospital'],
        'tecnología': ['comput', 'laptop', 'mouse', 'teclado']
    }
    
    for cat, keywords in categorias.items():
        for kw in keywords:
            if kw in pregunta:
                results['categoria'] = cat
                cur = conn.execute(f"""
                    SELECT NombreProductoGenerico, CodigoProducto, COUNT(*) as demandas,
                           COUNT(DISTINCT RUTProveedor) as proveedores,
                           ROUND(AVG(CAST(REPLACE(REPLACE(MontoTotal, '.', ''), ',', '.') AS REAL)), 0) as precio
                    FROM cotizaciones WHERE LOWER(NombreProductoGenerico) LIKE '%{kw}%' {filter_sql}
                    GROUP BY CodigoProducto ORDER BY demandas DESC LIMIT 10
                """)
                results['productos'] = [dict(row) for row in cur.fetchall()]
                if results['productos']:
                    p = results['productos'][0]
                    results['analisis'] = {
                        'demandas': sum(x['demandas'] for x in results['productos']),
                        'proveedores': sum(x['proveedores'] for x in results['productos']),
                        'precio': p['precio'] or 0
                    }
                break
    
    if 'top' in pregunta or 'más' in pregunta:
        cur = conn.execute(f"SELECT NombreProductoGenerico, CodigoProducto, COUNT(*) as demandas FROM cotizaciones WHERE NombreProductoGenerico != '' {filter_sql} GROUP BY CodigoProducto ORDER BY demandas DESC LIMIT 10")
        results['top'] = [dict(row) for row in cur.fetchall()]
    
    if 'oportunidad' in pregunta or 'conviene' in pregunta or 'renta' in pregunta:
        cur = conn.execute(f"SELECT NombreProductoGenerico, CodigoProducto, COUNT(DISTINCT CodigoCotizacion) as demandas, COUNT(DISTINCT RUTProveedor) as proveedores, ROUND(AVG(CAST(REPLACE(REPLACE(MontoTotal, '.', ''), ',', '.') AS REAL)), 0) as precio FROM cotizaciones WHERE NombreProductoGenerico != '' {filter_sql} GROUP BY CodigoProducto")
        prods = [dict(row) for row in cur.fetchall()]
        opp = []
        for p in prods:
            if p['proveedores'] and p['demandas']:
                score = (p['demandas'] * (p['precio'] or 0)) / (p['proveedores'] + 1)
                if score > 500000:
                    opp.append({'producto': p['NombreProductoGenerico'], 'demandas': p['demandas'], 'proveedores': p['proveedores'], 'precio': p['precio'], 'score': round(score, 0)})
        results['oportunidades'] = sorted(opp, key=lambda x: x['score'], reverse=True)[:10]
    
    if 'líquido' in pregunta or 'liquido' in pregunta:
        cur = conn.execute(f"SELECT NombreProductoGenerico, COUNT(*) as demandas FROM cotizaciones WHERE (LOWER(NombreProductoGenerico) LIKE '%liquido%' OR LOWER(NombreProductoGenerico) LIKE '%líquido%') {filter_sql} GROUP BY CodigoProducto ORDER BY demandas DESC LIMIT 15")
        results['liquidos'] = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    return results

def generar_respuesta(pregunta, datos_extra, config):
    pregunta = pregunta.lower()
    r = []
    
    # Saludo
    if 'hola' in pregunta or pregunta.strip() in ['', 'buenas']:
        return config.get('saludo', '¡Hola! Soy tu asesor 🧠')
    
    # Líquidos
    if datos_extra.get('liquidos'):
        r.append("🧴 **LÍQUIDOS DEMANDADOS:**\n")
        for i, p in enumerate(datos_extra['liquidos'][:10], 1):
            r.append(f"  {i}. {p['NombreProductoGenerico'][:45]} - {p['demandas']} demandas")
        return "\n".join(r)
    
    # Por categoría
    if datos_extra.get('categoria') and datos_extra.get('productos'):
        cat = datos_extra['categoria']
        anal = datos_extra['analisis']
        prods = datos_extra['productos']
        
        cat_config = config.get('categorias', {}).get(cat, {"recomendacion": "Analicemos...", "consejo": "Evaluá bien."})
        
        r.append(f"🧠 **{cat.upper()}**\n")
        
        if anal['proveedores'] > 0:
            competencia = anal['demandas'] / anal['proveedores']
        else:
            competencia = 0
        
        r.append("🎯 **MI RECOMENDACIÓN:**\n")
        r.append(cat_config.get('recomendacion', 'Analicemos...'))
        
        r.append(f"\n📈 Demanda: **{anal['demandas']:,}** | 🏢 Competidores: **{anal['proveedores']}**")
        r.append(f"💰 Precio promedio: **${anal['precio']:,.0f}**")
        
        r.append(f"\n💡 **{cat_config.get('consejo', 'Evaluá bien.')}**")
        
        if len(prods) > 1:
            r.append(f"\n📦 **Top {cat}:**")
            for i, p in enumerate(prods[:5], 1):
                r.append(f"  {i}. {p['NombreProductoGenerico'][:40]} ({p['demandas']})")
        
        return "\n".join(r)
    
    # Oportunidades
    if datos_extra.get('oportunidades'):
        opp = datos_extra['oportunidades']
        r.append("💎 **MEJORES OPORTUNIDADES:**\n")
        for i, o in enumerate(opp[:5], 1):
            r.append(f"  {i}. **{o['producto'][:35]}**")
            r.append(f"     📈 {o['demandas']} | 🏢 {o['proveedores']} | 💰 ${o['precio']:,.0f}")
        return "\n".join(r)
    
    # Qué vender
    if any(x in pregunta for x in ['qué vender', 'que vender', 'productos buenos']):
        return config.get('preguntas', {}).get('que_vender', 'Tóner, tecnología y médico son buenas opciones.')
    
    # Default
    r.append("📊 Preguntame algo específico como:")
    r.append("• ¿Qué productos vender?")
    r.append("• ¿Conviene [producto]?")
    r.append("• ¿Qué líquidos buscan?")
    return "\n".join(r)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/config', methods=['GET'])
def api_get_config():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def api_save_config():
    config = request.json
    save_config(config)
    return jsonify({'status': 'ok', 'message': 'Configuración guardada!'})

@app.route('/api/chat', methods=['POST'])
def api_chat():
    config = load_config()
    pregunta = request.json.get('message', '')
    f = request.json.get('filter', 'todas')
    
    if f == 'si':
        fs = "AND (ProveedorSeleccionado = 'si')"
    elif f == 'no':
        fs = "AND (ProveedorSeleccionado = 'no' OR ProveedorSeleccionado = '')"
    else:
        fs = ""
    
    datos_extra = get_data_for_query(pregunta, fs)
    resp = generar_respuesta(pregunta, datos_extra, config)
    return jsonify({'response': resp})

@app.route('/api/productos-top')
def api_productos_top():
    fs = get_filter()
    conn = get_db()
    cur = conn.execute(f"SELECT NombreProductoGenerico, CodigoProducto, COUNT(*) as total FROM cotizaciones WHERE NombreProductoGenerico != '' {fs} GROUP BY CodigoProducto ORDER BY total DESC LIMIT 20")
    results = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(results)

@app.route('/api/proveedores-top')
def api_proveedores_top():
    fs = get_filter()
    conn = get_db()
    cur = conn.execute(f"SELECT RazonSocialProveedor, RUTProveedor, COUNT(*) as cotizaciones FROM cotizaciones WHERE RUTProveedor != '' {fs} GROUP BY RUTProveedor ORDER BY cotizaciones DESC LIMIT 20")
    results = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(results)

@app.route('/api/por-region')
def api_por_region():
    fs = get_filter()
    conn = get_db()
    cur = conn.execute(f"SELECT Region, COUNT(*) as total FROM cotizaciones WHERE Region != '' {fs} GROUP BY Region ORDER BY total DESC")
    results = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(results)

@app.route('/api/oportunidades')
def api_oportunidades():
    fs = get_filter()
    conn = get_db()
    cur = conn.execute(f"SELECT NombreProductoGenerico, CodigoProducto, COUNT(DISTINCT CodigoCotizacion) as demandas, COUNT(DISTINCT RUTProveedor) as proveedores, ROUND(AVG(CAST(REPLACE(REPLACE(MontoTotal, '.', ''), ',', '.') AS REAL)), 0) as precio FROM cotizaciones WHERE NombreProductoGenerico != '' {fs} GROUP BY CodigoProducto")
    prods = [dict(row) for row in cur.fetchall()]
    conn.close()
    opp = []
    for p in prods:
        if p['proveedores'] and p['demandas']:
            score = (p['demandas'] * (p['precio'] or 0)) / (p['proveedores'] + 1)
            if score > 500000:
                opp.append({'NombreProductoGenerico': p['NombreProductoGenerico'], 'CodigoProducto': p['CodigoProducto'], 'demandas': p['demandas'], 'proveedores': p['proveedores'], 'precio': p['precio'], 'score': round(score, 0)})
    return jsonify(sorted(opp, key=lambda x: x['score'], reverse=True)[:15])

@app.route('/api/recomendaciones')
def api_recomendaciones():
    fs = get_filter()
    conn = get_db()
    recs = []
    cur = conn.execute(f"SELECT NombreProductoGenerico, CodigoProducto, COUNT(DISTINCT CodigoCotizacion) as demandas, COUNT(DISTINCT RUTProveedor) as proveedores FROM cotizaciones WHERE NombreProductoGenerico != '' {fs} GROUP BY CodigoProducto")
    for row in cur.fetchall():
        if row['proveedores'] and row['demandas']:
            ratio = row['demandas'] / row['proveedores']
            if ratio > 5:
                recs.append({'tipo': 'OPORTUNIDAD', 'producto': row['NombreProductoGenerico'], 'codigo': row['CodigoProducto'], 'descripcion': f'{row["demandas"]} demandas vs {row["proveedores"]} proveedores'})
    conn.close()
    return jsonify(recs[:20])
@app.route('/api/rangos')
def api_rangos():
    fs = get_filter()
    conn = get_db()
    cur = conn.execute(f"""
        SELECT 
            CASE 
                WHEN CAST(REPLACE(REPLACE(MontoTotal, '.', ''), ',', '.') AS REAL) < 100000 THEN 'Bajo (<$100K)'
                WHEN CAST(REPLACE(REPLACE(MontoTotal, '.', ''), ',', '.') AS REAL) < 500000 THEN 'Medio ($100K-$500K)'
                WHEN CAST(REPLACE(REPLACE(MontoTotal, '.', ''), ',', '.') AS REAL) < 2000000 THEN 'Alto ($500K-$2M)'
                ELSE 'Muy Alto (>$2M)'
            END as rango,
            COUNT(*) as cantidad
        FROM cotizaciones 
        WHERE MontoTotal != '' {fs}
        GROUP BY rango
    """)
    results = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(results)

@app.route('/api/competencia')
def api_competencia():
    fs = get_filter()
    conn = get_db()
    cur = conn.execute(f"""
        SELECT NombreProductoGenerico, CodigoProducto,
               COUNT(DISTINCT RUTProveedor) as num_proveedores,
               COUNT(*) as total_cotizaciones,
               ROUND(AVG(CAST(REPLACE(REPLACE(MontoTotal, '.', ''), ',', '.') AS REAL)), 0) as precio_promedio
        FROM cotizaciones 
        WHERE NombreProductoGenerico != '' AND RUTProveedor != '' {fs}
        GROUP BY CodigoProducto
        HAVING num_proveedores > 1
        ORDER BY total_cotizaciones DESC
        LIMIT 20
    """)
    results = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(results)



HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 Dashboard IA - Compra Ágil</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); min-height: 100vh; color: #fff; padding: 20px; }
        .header { text-align: center; padding: 20px; background: linear-gradient(90deg, #00d4ff, #7b2cbf); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }
        .header h1 { font-size: 2rem; }
        .filter-bar { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; margin-bottom: 20px; display: flex; gap: 15px; align-items: center; }
        .filter-bar label { color: #00d4ff; font-weight: 600; }
        .filter-bar select { padding: 10px; border-radius: 8px; border: 2px solid #00d4ff; background: #1a1a2e; color: #fff; }
        .tab-buttons { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab-btn { padding: 12px 20px; background: rgba(255,255,255,0.1); border: none; border-radius: 10px; color: #fff; cursor: pointer; }
        .tab-btn:hover, .tab-btn.active { background: linear-gradient(90deg, #00d4ff, #7b2cbf); }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .card { background: rgba(255,255,255,0.05); border-radius: 20px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
        .card h2 { font-size: 1.2rem; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { color: #00d4ff; }
        tr:hover { background: rgba(255,255,255,0.05); }
        .recommendation { padding: 15px; margin-bottom: 12px; border-radius: 12px; border-left: 4px solid #ffd700; background: rgba(255,255,255,0.05); }
        .recommendation .tipo { font-size: 0.7rem; font-weight: bold; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; background: #ffd700; color: #000; }
        .recommendation h3 { font-size: 0.95rem; margin: 5px 0; }
        .recommendation p { font-size: 0.8rem; color: #aaa; }
        .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
        .loading { text-align: center; padding: 30px; color: #00d4ff; }
        
        /* Chat */
        .chat-container { position: fixed; bottom: 20px; right: 20px; width: 420px; max-height: 650px; background: rgba(15,23,42,0.98); border-radius: 20px; border: 1px solid rgba(0,212,255,0.3); display: flex; flex-direction: column; box-shadow: 0 10px 40px rgba(0,0,0,0.5); z-index: 1000; }
        .chat-header { padding: 15px 20px; background: linear-gradient(90deg, #00d4ff, #7b2cbf); border-radius: 20px 20px 0 0; display: flex; justify-content: space-between; }
        .chat-header h3 { color: #fff; font-size: 1rem; }
        .chat-close { background: none; border: none; color: #fff; font-size: 1.5rem; cursor: pointer; }
        .chat-messages { flex: 1; overflow-y: auto; padding: 15px; max-height: 450px; }
        .chat-message { margin-bottom: 12px; padding: 12px 15px; border-radius: 15px; max-width: 90%; font-size: 0.9rem; line-height: 1.5; white-space: pre-wrap; }
        .chat-message.user { background: linear-gradient(135deg, #00d4ff, #0099cc); color: #fff; margin-left: auto; }
        .chat-message.bot { background: rgba(255,255,255,0.12); color: #fff; border-left: 3px solid #00d4ff; }
        .chat-input-container { padding: 15px; border-top: 1px solid rgba(255,255,255,0.1); display: flex; gap: 10px; }
        .chat-input { flex: 1; padding: 12px; border-radius: 25px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.1); color: #fff; }
        .chat-send { padding: 12px 20px; border-radius: 25px; border: none; background: linear-gradient(90deg, #00d4ff, #7b2cbf); color: #fff; cursor: pointer; font-weight: 600; }
        .chat-toggle { position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(90deg, #00d4ff, #7b2cbf); border: none; color: #fff; font-size: 1.5rem; cursor: pointer; box-shadow: 0 5px 20px rgba(0,212,255,0.5); z-index: 999; }
        
        /* Config Editor */
        .config-editor { background: rgba(0,0,0,0.3); padding: 20px; border-radius: 15px; }
        .config-editor label { display: block; margin-bottom: 5px; color: #00d4ff; font-weight: 600; }
        .config-editor textarea { width: 100%; height: 80px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; padding: 10px; font-size: 0.9rem; margin-bottom: 15px; }
        .config-editor input { width: 100%; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; padding: 10px; font-size: 0.9rem; margin-bottom: 15px; }
        .btn-save { background: #10b981; color: #fff; border: none; padding: 12px 30px; border-radius: 8px; cursor: pointer; font-weight: 600; }
        .btn-save:hover { background: #059669; }
        .config-section { margin-bottom: 20px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px; }
        .config-section h4 { color: #ffd700; margin-bottom: 10px; }
        .btn-edit-config { background: #f59e0b; color: #000; border: none; padding: 8px 15px; border-radius: 6px; cursor: pointer; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 Dashboard IA - Compra Ágil</h1>
        <p style="color:#aaa">Tu asesor inteligente + Editor de Prompts</p>
    </div>
    <div class="filter-bar">
        <label>📊 Filtrar:</label>
        <select id="filterSelect" onchange="applyFilter()">
            <option value="todas">Todas</option>
            <option value="si">✅ Ganadas</option>
            <option value="no">❌ No ganadas</option>
        </select>
    </div>
    <div class="tab-buttons">
        <button class="tab-btn" onclick="showTab('chat')">💬 Chat</button>
        <button class="tab-btn" onclick="showTab('config')">⚙️ Editar Prompt</button>
        <button class="tab-btn" onclick="showTab('productos')">📦 Productos</button>
        <button class="tab-btn" onclick="showTab('proveedores')">🏢 Proveedores</button>
        <button class="tab-btn" onclick="showTab('region')">🗺️ Regiones</button>
        <button class="tab-btn" onclick="showTab('rangos')">💰 Rangos</button>
        <button class="tab-btn" onclick="showTab('competencia')">⚔️ Competencia</button>
    </div>
    
    <!-- CHAT -->
    <div id="chat" class="tab-content">
        <div class="chat-container" style="position:relative; width:100%; max-width:600px; margin:0 auto;">
            <div class="chat-header"><h3>🧠 Asesor Compra Ágil</h3></div>
            <div class="chat-messages" id="chatMessages" style="max-height:400px;">
                <div class="chat-message bot">¡Hola! Soy tu asesor 🧠<br><br>Preguntame:<br>• ¿Qué productos vender?<br>• ¿Conviene aseo?<br>• ¿Qué líquidos buscan?</div>
            </div>
            <div class="chat-input-container">
                <input type="text" class="chat-input" id="chatInput" placeholder="Escribe..." onkeypress="if(event.key==='Enter')sendMessage()">
                <button class="chat-send" onclick="sendMessage()">Enviar</button>
            </div>
        </div>
    </div>
    
    <!-- CONFIG -->
    <div id="config" class="tab-content">
        <div class="card">
            <h2>⚙️ Editor de Prompt del Chat</h2>
            <p style="color:#888; margin-bottom:20px;">Editá cómo responde el asesor. Los cambios se guardan automáticamente.</p>
            
            <div class="config-editor">
                <div class="config-section">
                    <h4>📝 Saludo Inicial</h4>
                    <textarea id="configSaludo" placeholder="Mensaje de bienvenida..."></textarea>
                </div>
                
                <div class="config-section">
                    <h4>💬 Respuesta: ¿Qué productos vender?</h4>
                    <textarea id="configQueVender" placeholder="Tu recomendación..."></textarea>
                </div>
                
                <div class="config-section">
                    <h4>🧠 Recomendación: Aseo</h4>
                    <textarea id="configAseoRec" placeholder="Qué decir sobre aseo..."></textarea>
                    <label>Consejo:</label>
                    <input type="text" id="configAseoConsejo" placeholder="Consejo para aseo...">
                </div>
                
                <div class="config-section">
                    <h4>🖨️ Recomendación: Tóner</h4>
                    <textarea id="configTonerRec" placeholder="Qué decir sobre tóner..."></textarea>
                    <label>Consejo:</label>
                    <input type="text" id="configTonerConsejo" placeholder="Consejo para tóner...">
                </div>
                
                <button class="btn-save" onclick="saveConfig()">💾 Guardar Configuración</button>
                <span id="saveStatus" style="margin-left:15px; color:#10b981;"></span>
            </div>
        </div>
    </div>
    
    <!-- PRODUCTOS -->
    <div id="productos" class="tab-content">
        <div class="card"><h2>📦 Productos</h2><table id="productos-table"><thead><tr><th>#</th><th>Producto</th><th>Código</th><th>Demandas</th></tr></thead><tbody></tbody></table></div>
    </div>
    
    <!-- PROVEEDORES -->
    <div id="proveedores" class="tab-content">
        <div class="card"><h2>🏢 Proveedores</h2><table id="proveedores-table"><thead><tr><th>#</th><th>Proveedor</th><th>Cotiz.</th></tr></thead><tbody></tbody></table></div>
    </div>
    
    <!-- REGIONES -->
    <div id="region" class="tab-content">
        <div class="card"><h2>🗺️ Regiones</h2><table id="region-table"><thead><tr><th>#</th><th>Región</th><th>Total</th></tr></thead><tbody></tbody></table></div>
    </div>
    
    <script>
        let currentFilter = 'todas';
        
        function showTab(id) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.target.classList.add('active');
            if(id === 'config') loadConfig();
        }
        
        function sendMessage() {
            const m = document.getElementById('chatInput').value.trim();
            if(!m) return;
            addMessage(m, 'user');
            document.getElementById('chatInput').value = '';
            addMessage('🤔...', 'bot', true);
            fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:m, filter:currentFilter})})
                .then(r => r.json())
                .then(d => {
                    document.getElementById('chatMessages').lastChild.remove();
                    addMessage(d.response, 'bot');
                });
        }
        
        function addMessage(t, ty, typing=false) {
            const d = document.createElement('div');
            d.className = 'chat-message ' + ty;
            d.innerHTML = t;
            document.getElementById('chatMessages').appendChild(d);
            document.getElementById('chatMessages').scrollTop = 9999;
        }
        
        function applyFilter() {
            currentFilter = document.getElementById('filterSelect').value;
            loadAll();
        }
        
        function loadConfig() {
            fetch('/api/config').then(r => r.json()).then(c => {
                document.getElementById('configSaludo').value = c.saludo || '';
                document.getElementById('configQueVender').value = (c.preguntas || {}).que_vender || '';
                const aseo = (c.categorias || {}).aseo || {};
                document.getElementById('configAseoRec').value = aseo.recomendacion || '';
                document.getElementById('configAseoConsejo').value = aseo.consejo || '';
                const toner = (c.categorias || {}).tóner || {};
                document.getElementById('configTonerRec').value = toner.recomendacion || '';
                document.getElementById('configTonerConsejo').value = toner.consejo || '';
            });
        }
        
        function saveConfig() {
            const config = {
                saludo: document.getElementById('configSaludo').value,
                preguntas: { que_vender: document.getElementById('configQueVender').value },
                categorias: {
                    aseo: {
                        recomendacion: document.getElementById('configAseoRec').value,
                        consejo: document.getElementById('configAseoConsejo').value
                    },
                    "tóner": {
                        recomendacion: document.getElementById('configTonerRec').value,
                        consejo: document.getElementById('configTonerConsejo').value
                    }
                }
            };
            fetch('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(config)})
                .then(r => r.json())
                .then(d => {
                    document.getElementById('saveStatus').textContent = '✅ Guardado!';
                    setTimeout(() => document.getElementById('saveStatus').textContent = '', 3000);
                });
        }
        
        function loadAll() {
            const f = currentFilter !== 'todas' ? '?ganadas=' + currentFilter : '';
            fetch('/api/productos-top' + f).then(r => r.json()).then(d => {
                let h = '';
                d.slice(0,15).forEach((r,i) => { h += `<tr><td>${i+1}</td><td>${(r.NombreProductoGenerico||'').substring(0,35)}</td><td>${r.CodigoProducto||''}</td><td>${r.total}</td></tr>`; });
                document.querySelector('#productos-table tbody').innerHTML = h;
            });
            fetch('/api/proveedores-top' + f).then(r => r.json()).then(d => {
                let h = '';
                d.slice(0,15).forEach((r,i) => { h += `<tr><td>${i+1}</td><td>${(r.RazonSocialProveedor||'').substring(0,35)}</td><td>${r.cotizaciones}</td></tr>`; });
                document.querySelector('#proveedores-table tbody').innerHTML = h;
            });
            fetch('/api/rangos' + f).then(r => r.json()).then(d => {
                let h = '';
                d.forEach(r => { h += `<tr><td>${r.rango}</td><td>${r.cantidad.toLocaleString()}</td></tr>`; });
                document.querySelector('#rangos-table tbody').innerHTML = h;
            });
            fetch('/api/competencia' + f).then(r => r.json()).then(d => {
                let h = '';
                d.slice(0,15).forEach((r,i) => { 
                    let precio = r.precio_promedio ? '$' + Math.round(r.precio_promedio).toLocaleString('es-CL') : '$0';
                    h += `<tr><td>${i+1}</td><td>${(r.NombreProductoGenerico||'').substring(0,30)}</td><td>${r.num_proveedores}</td><td>${r.total_cotizaciones}</td><td>${precio}</td></tr>`; 
                });
                document.querySelector('#competencia-table tbody').innerHTML = h;
            });
            fetch('/api/por-region' + f).then(r => r.json()).then(d => {
                let h = '';
                d.forEach((r,i) => { h += `<tr><td>${i+1}</td><td>${r.Region||''}</td><td>${r.total}</td></tr>`; });
                document.querySelector('#region-table tbody').innerHTML = h;
            });
        }
        
        showTab('chat');
        loadAll();
    </script>
</body>
</html>'''

if __name__ == '__main__':
    print("🚀 Dashboard with Config Editor: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
