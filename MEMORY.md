## Mi Identidad
- **Nombre:** Rick Hunter
- **Emoji:** 🤖
- **Origen:** Nombrado por Flaco en honor al personaje de Robotech

## About Flaco (César Vergara)
- Dueño del proyecto "Compra Ágil"
- Empresa: datalivealquimia
- Ubicación: Chile (America/Santiago)
- Preferir "tú" en vez de "vos"

## Proyecto: Compra Ágil Chile (Base de datos)

### Datos importados
- Archivos: COT_2026-01.zip + COT_2026-02.zip
- DB: ~/.openclaw/workspace/compra_agil.db
- Registros: 3.4 millones
- Período: Enero-Febrero 2026

### Estadísticas
- 57.685 cotizaciones únicas
- 14.202 proveedores únicos
- 686 ventas ganadas

### Script consultas
- Ubicación: ~/.openclaw/workspace/consultas.py
- Comandos:
  - python3 consultas.py stats
  - python3 consultas.py productos
  - python3 consultas.py proveedores
  - python3 consultas.py ventas
  - python3 consultas.py region

### Productos top
- Tóner (44103103): 14.120
- Cartuchos tinta (44103105): 8.775
- Papelería (14111509): 7.063
- Desinfectantes: 5.945
- Limpiadores: 5.704

### Top proveedores
- 78.185.337-2: 391 ventas ($2.710.524.018)
- 76.319.288-1: 53 ventas ($132.838.021)
- Soluciones Industriales Julio Lazo: 33 ventas

## Proyecto: Mercado Público Scraper
- Scraper con Puppeteer creado
- Mercado Público bloqueó requests (403)
- Repo GitHub: https://github.com/datalivealquimia/mercado-publico-chile

## Base de Datos Mercado Público
- DB principal: ~/.openclaw/workspace/historico_mercado_publico.db
- Registros: 1,026,955 cotizaciones (período COT_2026-02)
- Columnas: Region, NombreProductoGenerico, RazonSocialProveedor, Estado, MontoTotal, etc.
- Consultas lentas (>30s) con funciones de agregado, rápidas con SELECT simple

## Proyecto: Scrapping Immobiliario Lo Barnechea
- Programa horario: cada hora de 8 AM a 8 PM (Chile)
- Destinatarios: cvergarach@gmail.com + cevm75@gmail.com
- Comuna: Lo Barnechea
- Configurado con delays lentos para evitar bloqueos

## Links
- Compra Ágil: https://buscador.mercadopublico.cl/compra-agil

## Módulo de Correo (2025-03)
- Archivo: ~/.openclaw/workspace/correo.py
- Email: datalive.alquimia@gmail.com
- App Password configurado (listo para usar)
- Uso: `from correo import send_email`
- Para enviar: send_email('destino@email.com', 'Asunto', 'Cuerpo')

## Base de Datos Historico MP (2026-03)
- Ubicación: /Users/einstein/Documents/Antigravity /Base/historico_mp.db
- Registros: ~1.8M cotizaciones con proveedor seleccionado = "SI"
- CSV exportado: ~/.openclaw/workspace/productos_vendidos.csv (2000 registros, últimos 6 meses)
- Nota: Encoding con problemas (acentos mal)

## Scraper API Mercado Público (2026-03)
- Script: ~/.openclaw/workspace/api_scraper.py
- Resultado: Solo 4 licitaciones (rate limits + errores 400)
- Log: ~/.openclaw/workspace/api_scraper.log

## Estructura de Proyectos
- **Carpeta:** `~/.openclaw/workspace/proyectos/`
- **Formato:** `SIGLA_AAAA-MM-DD`
- Cada proyecto incluye: README.md + archivos del proyecto

## Proyectos Activos
1. **PF_2026-03-23** - Portfolio Datalive Alquimia (web portafolio)
2. **NC_2026-03-23** - Not Cookie (Galletas saludables)
3. **CA_2026-01-15** - Compra Ágil (Base de datos 3.4M registros)
4. **MPS_2026-03-01** - Mercado Público Scraper (datos + scraper)
5. **MC_2025-03-01** - Módulo de Correo
6. **AIC_2026-01-15** - AI Factory (sistema de agentes)
7. **CAA_2026-03-10** - Chat Avatar App
8. **CVM_2026-01-15** - CV Mejorador
9. **LB_2026-01-15** - Luna Bot
10. **MAP_2026-01-15** - Mercado Agente
11. **MPA_2026-01-15** - MP Agent
12. **TS_2026-01-01** - Tesis Santiago

## Proyecto: Compra Ágil Scraper (2026-03-20)
- Objetivo: Buscar licitaciones por fecha, descargar Excel, crear DB
- URL base: https://buscador.mercadopublico.cl/compra-agil
- Problema: Sitio bloquea requests directos (403 CloudFront)
- Solución: Browser automation para descargar Excel
- Carpeta: ~/.openclaw/workspace/compra_agil/
- Excel original: ~/Downloads/20260320221948.xlsx (3.192 registros para 2026-03-19)
- Progreso: 12 cotizaciones procesadas con detalles
- Base: compra_agil_detalles.db (12 cotizaciones, 27 productos)

## Proyecto: Not Cookie (NC_2026-03-23)
- **Emprendimiento:** Galletas caseras saludables
- **Web:** https://ahistorical-elise-unswatheable.ngrok-free.dev (ngrok temporal)
- **Carpeta:** `~/.openclaw/workspace/proyectos/NC_2026-03-23/`
- **Estado:** Activo
- **Tareas:** Desplegar en hosting permanente, integrar WhatsApp

### Estructura DB
- cotizaciones: codigo, nombre, descripcion, direccion, plazo, presupuesto, fechas, organismo, rut, cotizaciones
- productos: cotizacion_codigo, codigo_producto, nombre, cantidad
