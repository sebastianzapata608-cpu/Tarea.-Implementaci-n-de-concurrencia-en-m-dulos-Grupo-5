# Simulación concurrente del SIGET

Solución del problema productor-consumidor adaptado a un sistema inteligente de gestión de tráfico. Tres sensores producen lecturas, dos módulos las analizan y un supervisor informa el estado mientras todos se ejecutan concurrentemente.

## Requisitos

- Python 3.10 o posterior.
- No requiere paquetes externos.

## Ejecución

```powershell
python siget_concurrencia.py
```

Para una demostración más larga, con un búfer pequeño que haga visibles las esperas de los productores:

```powershell
python siget_concurrencia.py --lecturas 12 --capacidad 3
```

La ejecución termina con `VERIFICACION DE INTEGRIDAD: APROBADA` si no hubo pérdidas, duplicados ni datos pendientes. El código de salida es 0 cuando la prueba es correcta.

## Pruebas

```powershell
python -m unittest -v
```

## Mecanismos demostrados

- Semáforo `espacios`, inicializado con la capacidad del búfer.
- Semáforo `elementos`, inicializado en cero.
- Mutex para proteger el búfer FIFO y las métricas compartidas.
- Evento de inicio para liberar simultáneamente los hilos.
- Marcadores de cierre para evitar consumidores bloqueados al finalizar.
- Comprobación de integridad mediante identificadores únicos.

## Entrega sugerida

1. Cree un repositorio público o privado en GitHub.
2. Suba `siget_concurrencia.py`, `test_siget_concurrencia.py`, `README.md` y `output/pdf/relatoria_tecnica_SIGET.pdf`.
3. Grabe el video siguiendo `guion_video.md`, súbalo a Drive o YouTube y pegue el enlace en la plataforma educativa.
4. Verifique que el tutor tenga permiso de lectura sobre el repositorio y el video.
