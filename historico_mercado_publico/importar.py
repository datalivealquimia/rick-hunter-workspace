#!/usr/bin/env python3
"""
Importador optimizado de datos COT Mercado Público a SQLite
"""
import csv
import sqlite3
import os

DB_PATH = '/Users/einstein/.openclaw/workspace/historico_mercado_publico.db'
CSV_FILES = [
    ('/Users/einstein/Downloads/COT1_2026-02.csv', 'COT_2026-02'),
    ('/Users/einstein/Downloads/COT2_2026-02.csv', 'COT_2026-02'),
]

HEADERS = [
    'RazonSocialUnidaddeCompra', 'NombreUnidaddeCompra', 'RUTUnidaddeCompra',
    'CodigoUnidaddeCompra', 'CodigoCotizacion', 'NombreCotizacion',
    'DescripcionCotizacion', 'DireccionEntrega', 'Region',
    'FechaPublicacionParaCotizar', 'FechaCierreParaCotizar', 'PlazoEntrega',
    'MontoTotalDisponble', 'ProductoCotizado', 'CodigoProducto',
    'NombreProductoGenerico', 'CantidadSolicitada', 'Estado',
    'NOMBRECONTACTO', 'RazonSocialProveedor', 'RUTProveedor', 'Tamano',
    'DetalleCotizacion', 'ProveedorSeleccionado', 'moneda', 'MontoTotal',
    'NombreCriterio', 'CodigoOC', 'EstadoOC', 'FechaAceptacionOCProveedor',
    'MotivoCancelacion', 'ConsideraRequisitosMedioambientales',
    'ConsideraRequisitosImpactoSocialEconomico'
]

# Headers para la DB (33 del CSV + 1 archivo_fuente)
HEADERS_WITH_SOURCE = HEADERS + ['archivo_fuente']

NUM_COLS = 33  # Columnas en el CSV original

def main():
    # Eliminar DB anterior
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🗑️ DB anterior eliminada")
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    
    # Crear tabla
    cols_def = ', '.join([f'"{c}" TEXT' for c in HEADERS_WITH_SOURCE])
    conn.execute(f'CREATE TABLE cotizaciones ({cols_def})')
    conn.commit()
    
    total = 0
    for csv_path, fuente in CSV_FILES:
        if not os.path.exists(csv_path):
            print(f"⚠️ No encontrado: {csv_path}")
            continue
            
        print(f"\n📂 Importando {os.path.basename(csv_path)}...")
        
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f, delimiter=';')
            headers = next(reader)
            
            batch = []
            batch_size = 10000
            
            for row in reader:
                if len(row) >= NUM_COLS:
                    row.append(fuente)  # Agregar fuente
                    batch.append(row[:NUM_COLS + 1])  # 33 + 1 = 34
                    
                    if len(batch) >= batch_size:
                        placeholders = ','.join(['?' for _ in range(NUM_COLS + 1)])
                        cols = ','.join([f'"{h}"' for h in HEADERS_WITH_SOURCE])
                        conn.executemany(f'INSERT INTO cotizaciones ({cols}) VALUES ({placeholders})', batch)
                        conn.commit()
                        total += len(batch)
                        print(f"   {total:,}...")
                        batch = []
            
            if batch:
                placeholders = ','.join(['?' for _ in range(NUM_COLS + 1)])
                cols = ','.join([f'"{h}"' for h in HEADERS_WITH_SOURCE])
                conn.executemany(f'INSERT INTO cotizaciones ({cols}) VALUES ({placeholders})', batch)
                conn.commit()
                total += len(batch)
        
        print(f"   ✅ Total: {total:,}")
    
    # Validar
    print("\n🔍 Validación:")
    cur = conn.execute("SELECT COUNT(*) FROM cotizaciones")
    print(f"   Total registros: {cur.fetchone()[0]:,}")
    
    cur = conn.execute("SELECT COUNT(DISTINCT CodigoCotizacion) FROM cotizaciones")
    print(f"   Cotizaciones únicas: {cur.fetchone()[0]:,}")
    
    cur = conn.execute("SELECT COUNT(DISTINCT RUTProveedor) FROM cotizaciones WHERE RUTProveedor != ''")
    print(f"   Proveedores únicos: {cur.fetchone()[0]:,}")
    
    print("\n📋 Muestra:")
    cur = conn.execute("""
        SELECT CodigoCotizacion, NombreCotizacion, Region, 
               RazonSocialProveedor, MontoTotal, archivo_fuente
        FROM cotizaciones LIMIT 3
    """)
    for i, row in enumerate(cur, 1):
        print(f"   {i}. {row[0]} | {row[2][:20]} | {row[5]}")
    
    conn.close()
    size = os.path.getsize(DB_PATH) / 1024 / 1024
    print(f"\n✅ Listo: {DB_PATH} ({size:.1f} MB)")

if __name__ == '__main__':
    main()
