# SIGET – Simulación de Concurrencia con Semáforos

## Descripción del proyecto

Este proyecto implementa una simulación del problema clásico **productor-consumidor**, adaptado al contexto del **Sistema Inteligente de Gestión de Tráfico (SIGET)**.

La simulación representa varios sensores de tráfico que generan información de manera concurrente y módulos de análisis que procesan dichas lecturas utilizando mecanismos de sincronización propios de los sistemas operativos.

El objetivo principal es demostrar de forma práctica el funcionamiento de conceptos como:

* Concurrencia.
* Hilos.
* Semáforos.
* Exclusión mutua.
* Secciones críticas.
* Búfer compartido.
* Sincronización.
* Prevención de condiciones de carrera.
* Terminación segura de procesos concurrentes.

---

## Escenario simulado

El sistema está compuesto por:

### Productores

Tres sensores de tráfico:

* Sensor Norte.
* Sensor Centro.
* Sensor Sur.

Cada sensor genera lecturas que contienen información como:

* Identificador único.
* Intersección.
* Velocidad del vehículo.
* Porcentaje de ocupación vial.
* Cantidad de vehículos por minuto.
* Instante de captura.

### Consumidores

Dos módulos de análisis procesan las lecturas generadas por los sensores.

Cada lectura puede ser clasificada como:

* `NORMAL`
* `CONGESTION`
* `EXCESO_VELOCIDAD`

### Supervisor

Además, existe un hilo supervisor encargado de informar periódicamente:

* Cantidad de lecturas producidas.
* Cantidad de lecturas procesadas.
* Cantidad de elementos almacenados en el búfer.

En total, la simulación utiliza **seis hilos concurrentes**:

* 3 productores.
* 2 consumidores.
* 1 supervisor.

---

## Arquitectura productor-consumidor

Los sensores y los analizadores se comunican mediante un **búfer FIFO de capacidad limitada**.

Los productores insertan información en el búfer mientras los consumidores la retiran para procesarla.

Debido a que varios hilos acceden al mismo recurso compartido, es necesario controlar el acceso para evitar problemas como:

* Condiciones de carrera.
* Pérdida de información.
* Datos duplicados.
* Corrupción de datos.
* Bloqueos indefinidos.
* Acceso simultáneo incorrecto a la memoria compartida.

Para solucionar estos problemas se utilizan semáforos y mecanismos de exclusión mutua.

---

## Mecanismos de sincronización

### Semáforo `espacios`

```python
self._espacios = threading.Semaphore(capacidad)
```

Representa la cantidad de espacios disponibles dentro del búfer.

Antes de publicar una lectura, un productor debe obtener un espacio disponible.

Si el búfer está lleno, el productor queda bloqueado hasta que un consumidor retire un elemento.

---

### Semáforo `elementos`

```python
self._elementos = threading.Semaphore(0)
```

Representa la cantidad de elementos disponibles para ser procesados.

Inicialmente comienza en cero porque el búfer está vacío.

Cuando un consumidor intenta retirar una lectura y no existen elementos disponibles, debe esperar hasta que algún productor publique información.

---

### Mutex

```python
self._mutex = threading.Lock()
```

El mutex implementa **exclusión mutua** sobre las secciones críticas.

Su función es permitir que solamente un hilo pueda modificar determinadas estructuras compartidas en un momento determinado.

Se utiliza principalmente para proteger:

* El búfer FIFO.
* Las métricas compartidas.
* Los contadores utilizados durante la simulación.

---

## Evento de inicio

El programa utiliza un evento compartido:

```python
inicio = threading.Event()
```

Los hilos esperan inicialmente hasta que el programa principal ejecuta:

```python
inicio.set()
```

Esto permite coordinar el inicio de productores, consumidores y supervisor.

---

## Terminación segura

Después de que todos los sensores terminan de generar lecturas, el programa utiliza un marcador especial:

```python
FIN
```

Se introduce una señal `FIN` por cada consumidor.

Cuando un analizador recibe esta señal entiende que no existirán nuevas lecturas y puede terminar su ejecución de forma ordenada.

Esto evita que los consumidores permanezcan bloqueados indefinidamente esperando nueva información.

---

## Verificación de integridad

Al finalizar la simulación se realiza una comprobación automática para verificar que:

* Todas las lecturas producidas hayan sido procesadas.
* No existan lecturas duplicadas.
* No se hayan perdido lecturas.
* Cada identificador aparezca exactamente una vez.
* El búfer termine completamente vacío.
* Todos los hilos finalicen correctamente.

Cuando estas condiciones se cumplen aparece:

```text
VERIFICACION DE INTEGRIDAD: APROBADA
```

---

## Requisitos

* Python 3.10 o superior.
* No requiere librerías externas.

El proyecto utiliza únicamente módulos incluidos en la biblioteca estándar de Python.

---

## Estructura del proyecto

```text
SIGET/
│
├── siget_concurrencia.py
├── test_siget_concurrencia.py
├── README.md
│
└── output/
    └── pdf/
        └── relatoria_tecnica_SIGET.pdf
```

### Archivos principales

**`siget_concurrencia.py`**

Contiene la implementación principal del sistema productor-consumidor, los sensores, analizadores, supervisor y mecanismos de sincronización.

**`test_siget_concurrencia.py`**

Contiene las pruebas automáticas utilizadas para verificar diferentes comportamientos del sistema.

**`README.md`**

Documentación general del proyecto.

**`relatoria_tecnica_SIGET.pdf`**

Documento explicativo donde se describe la implementación, los mecanismos de concurrencia utilizados y las conclusiones obtenidas.

---

# Ejecución

Ubíquese desde una terminal dentro de la carpeta del proyecto.

Para ejecutar la configuración predeterminada:

```powershell
python siget_concurrencia.py
```

---

## Ejecución recomendada para demostración

Para visualizar con mayor claridad el comportamiento concurrente puede utilizarse:

```powershell
python siget_concurrencia.py --lecturas 12 --capacidad 3
```

En esta configuración:

* Cada sensor genera 12 lecturas.
* Existen 3 sensores.
* Se producen 36 lecturas en total.
* El búfer solamente puede almacenar 3 elementos simultáneamente.

El tamaño reducido del búfer permite observar con mayor facilidad situaciones en las que los productores deben esperar por espacio disponible.

---

## Parámetros disponibles

### Número de lecturas

```powershell
--lecturas
```

Define cuántas lecturas genera cada sensor.

Ejemplo:

```powershell
python siget_concurrencia.py --lecturas 20
```

---

### Capacidad del búfer

```powershell
--capacidad
```

Define la cantidad máxima de elementos que pueden permanecer simultáneamente en el búfer.

Ejemplo:

```powershell
python siget_concurrencia.py --capacidad 4
```

---

### Ejecución rápida

```powershell
--rapido
```

Reduce las pausas internas de la simulación.

Ejemplo:

```powershell
python siget_concurrencia.py --lecturas 12 --capacidad 3 --rapido
```

---

# Ejemplo de salida

Durante la simulación se pueden observar mensajes similares a:

```text
[Sensor Norte] PUBLICA Sensor Norte-001 | buffer 1/3

[Sensor Centro] PUBLICA Sensor Centro-001 | buffer 2/3

[Analizador 1] PROCESA Sensor Norte-001: NORMAL | buffer 1/3

[Supervisor SIGET] MONITOREO producidas=5, procesadas=3, en_buffer=2
```

Los mensajes pueden aparecer en diferentes órdenes entre ejecuciones debido a la naturaleza concurrente del programa.

---

## Significado de los mensajes

### `PUBLICA`

Un productor generó una lectura y la introdujo en el búfer.

### `PROCESA`

Un consumidor retiró una lectura y realizó su clasificación.

### `MONITOREO`

El supervisor informa el estado general de la simulación.

### `buffer 3/3`

El búfer alcanzó su capacidad máxima.

Los productores deberán esperar hasta que un consumidor libere un espacio.

---

# Resultado final

Al terminar se presenta un resumen similar a:

```text
RESULTADO: producidas=36, procesadas=36

Esperas observadas: productores=X, consumidores=X

VERIFICACION DE INTEGRIDAD: APROBADA
```

El resultado permite comprobar el correcto funcionamiento de los mecanismos de sincronización.

---

# Pruebas automáticas

El proyecto incluye pruebas unitarias.

Para ejecutarlas:

```powershell
python -m unittest -v
```

Las pruebas verifican aspectos como:

* Clasificación correcta de las lecturas.
* Validación de capacidades incorrectas.
* Conservación de información durante la concurrencia.
* Funcionamiento general de la simulación.

Una ejecución correcta debe finalizar con:

```text
Ran 4 tests

OK
```

---

# Conceptos de Sistemas Operativos aplicados

Este proyecto permite observar de manera práctica diferentes conceptos estudiados en Sistemas Operativos.

### Concurrencia

Diferentes tareas progresan durante un mismo periodo de tiempo mediante múltiples hilos.

### Productor-consumidor

Los sensores producen información mientras los analizadores la consumen.

### Sección crítica

Corresponde a las operaciones donde se modifica información compartida.

### Exclusión mutua

Se utiliza un mutex para evitar modificaciones simultáneas incorrectas.

### Semáforos

Controlan la disponibilidad de espacios y elementos dentro del búfer.

### Sincronización

Los hilos coordinan su ejecución mediante eventos, semáforos y bloqueos.

### Prevención de condiciones de carrera

El acceso a las estructuras compartidas está protegido para mantener la consistencia de los datos.

### Prevención de bloqueos durante el cierre

Los marcadores `FIN` permiten finalizar correctamente los consumidores una vez terminan los productores.

---

# Conclusión

La implementación demuestra cómo los mecanismos de concurrencia de un sistema operativo pueden aplicarse a un escenario relacionado con la gestión inteligente del tráfico.

Mediante el patrón productor-consumidor, los sensores pueden generar información independientemente mientras diferentes módulos realizan su procesamiento.

El uso de **semáforos, mutex, eventos y un búfer acotado** permite coordinar los hilos, proteger los recursos compartidos y evitar problemas como condiciones de carrera, pérdida de información y bloqueos durante la finalización del sistema.

Finalmente, la verificación de integridad permite comprobar que todas las lecturas generadas fueron procesadas correctamente.

---

## Autor

Sebastián Zapata Alvarez
Emanuel Taborda Lopez
Juan Alejandro Salazar Acosta

Tecnología en Desarrollo de Software
Sistemas Operativos
2026
