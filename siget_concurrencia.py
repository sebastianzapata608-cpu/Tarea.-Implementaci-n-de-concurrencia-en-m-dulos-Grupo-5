"""Simulacion concurrente productor-consumidor para el SIGET.

Tres sensores de trafico publican lecturas en un buffer acotado y dos modulos
de analisis las consumen. El buffer implementa explicitamente los semaforos
``espacios`` y ``elementos`` y un mutex para proteger la seccion critica.

Ejecutar:
    python siget_concurrencia.py
    python siget_concurrencia.py --lecturas 12 --capacidad 4 --rapido
"""

from __future__ import annotations

import argparse
import random
import threading
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class LecturaTrafico:
    """Dato inmutable enviado por un sensor del SIGET."""

    identificador: str
    sensor: str
    interseccion: str
    velocidad_kmh: float
    ocupacion_pct: float
    vehiculos_min: int
    instante: float


FIN: Final = object()


class RegistroSeguro:
    """Evita que las lineas de salida de varios hilos se mezclen."""

    def __init__(self) -> None:
        self._mutex = threading.Lock()
        self._inicio = time.monotonic()

    def escribir(self, actor: str, mensaje: str) -> None:
        transcurrido = time.monotonic() - self._inicio
        with self._mutex:
            print(f"[{transcurrido:6.2f}s] [{actor:<18}] {mensaje}", flush=True)


class BufferAcotado:
    """Buffer FIFO sincronizado mediante semaforos y exclusion mutua."""

    def __init__(self, capacidad: int) -> None:
        if capacidad <= 0:
            raise ValueError("La capacidad debe ser mayor que cero")
        self.capacidad = capacidad
        self._datos: deque[object] = deque()
        self._espacios = threading.Semaphore(capacidad)
        self._elementos = threading.Semaphore(0)
        self._mutex = threading.Lock()
        self.esperas_productores = 0
        self.esperas_consumidores = 0

    def publicar(self, dato: object) -> int:
        """Espera por un espacio, inserta atomicamente y devuelve la ocupacion."""
        if not self._espacios.acquire(timeout=0.05):
            with self._mutex:
                self.esperas_productores += 1
            self._espacios.acquire()
        with self._mutex:
            self._datos.append(dato)
            ocupacion = len(self._datos)
            assert ocupacion <= self.capacidad
        self._elementos.release()
        return ocupacion

    def retirar(self) -> tuple[object, int]:
        """Espera por un elemento, lo retira atomicamente y libera un espacio."""
        if not self._elementos.acquire(timeout=0.05):
            with self._mutex:
                self.esperas_consumidores += 1
            self._elementos.acquire()
        with self._mutex:
            dato = self._datos.popleft()
            ocupacion = len(self._datos)
            assert ocupacion >= 0
        self._espacios.release()
        return dato, ocupacion

    def ocupacion(self) -> int:
        with self._mutex:
            return len(self._datos)


class Metricas:
    """Estado compartido protegido para verificacion y reporte."""

    def __init__(self) -> None:
        self._mutex = threading.Lock()
        self.producidas: list[str] = []
        self.procesadas: list[str] = []
        self.estados: Counter[str] = Counter()

    def registrar_produccion(self, identificador: str) -> None:
        with self._mutex:
            self.producidas.append(identificador)

    def registrar_proceso(self, identificador: str, estado: str) -> None:
        with self._mutex:
            self.procesadas.append(identificador)
            self.estados[estado] += 1

    def resumen(self) -> tuple[int, int, Counter[str]]:
        with self._mutex:
            return len(self.producidas), len(self.procesadas), self.estados.copy()


def clasificar(lectura: LecturaTrafico) -> str:
    """Clasifica una lectura con reglas sencillas de operacion vial."""
    if lectura.ocupacion_pct >= 82 or lectura.vehiculos_min >= 48:
        return "CONGESTION"
    if lectura.velocidad_kmh >= 78:
        return "EXCESO_VELOCIDAD"
    return "NORMAL"


def sensor(
    nombre: str,
    interseccion: str,
    cantidad: int,
    semilla: int,
    buffer: BufferAcotado,
    metricas: Metricas,
    inicio: threading.Event,
    registro: RegistroSeguro,
    demora: tuple[float, float],
) -> None:
    rng = random.Random(semilla)
    inicio.wait()
    for secuencia in range(1, cantidad + 1):
        time.sleep(rng.uniform(*demora))
        lectura = LecturaTrafico(
            identificador=f"{nombre}-{secuencia:03d}",
            sensor=nombre,
            interseccion=interseccion,
            velocidad_kmh=round(rng.uniform(18, 92), 1),
            ocupacion_pct=round(rng.uniform(25, 96), 1),
            vehiculos_min=rng.randint(8, 60),
            instante=time.time(),
        )
        ocupacion = buffer.publicar(lectura)
        metricas.registrar_produccion(lectura.identificador)
        registro.escribir(
            nombre,
            f"PUBLICA {lectura.identificador} en {lectura.interseccion} "
            f"| buffer {ocupacion}/{buffer.capacidad}",
        )
    registro.escribir(nombre, "Finalizo la captura programada")


def analizador(
    nombre: str,
    buffer: BufferAcotado,
    metricas: Metricas,
    inicio: threading.Event,
    registro: RegistroSeguro,
    demora: tuple[float, float],
    semilla: int,
) -> None:
    rng = random.Random(semilla)
    inicio.wait()
    while True:
        dato, ocupacion = buffer.retirar()
        if dato is FIN:
            registro.escribir(nombre, "Recibe senal de cierre y termina ordenadamente")
            return
        assert isinstance(dato, LecturaTrafico)
        time.sleep(rng.uniform(*demora))
        estado = clasificar(dato)
        metricas.registrar_proceso(dato.identificador, estado)
        registro.escribir(
            nombre,
            f"PROCESA {dato.identificador}: {estado:<17} "
            f"| buffer {ocupacion}/{buffer.capacidad}",
        )


def supervisor(
    buffer: BufferAcotado,
    metricas: Metricas,
    inicio: threading.Event,
    detener: threading.Event,
    registro: RegistroSeguro,
    intervalo: float,
) -> None:
    inicio.wait()
    while not detener.wait(intervalo):
        producidas, procesadas, _ = metricas.resumen()
        registro.escribir(
            "Supervisor SIGET",
            f"MONITOREO producidas={producidas}, procesadas={procesadas}, "
            f"en_buffer={buffer.ocupacion()}",
        )
    registro.escribir("Supervisor SIGET", "Monitoreo finalizado")


def ejecutar_simulacion(
    lecturas_por_sensor: int = 8,
    capacidad: int = 5,
    rapido: bool = False,
) -> bool:
    if lecturas_por_sensor <= 0:
        raise ValueError("Las lecturas por sensor deben ser mayores que cero")

    demora_productor = (0.01, 0.04) if rapido else (0.08, 0.24)
    demora_consumidor = (0.02, 0.06) if rapido else (0.13, 0.30)
    intervalo_supervision = 0.08 if rapido else 0.35

    buffer = BufferAcotado(capacidad)
    metricas = Metricas()
    registro = RegistroSeguro()
    inicio = threading.Event()
    detener_supervisor = threading.Event()

    configuracion_sensores = [
        ("Sensor Norte", "Av. 10 con Calle 26", 101),
        ("Sensor Centro", "Carrera 7 con Calle 19", 202),
        ("Sensor Sur", "Av. 1 de Mayo con Cra. 30", 303),
    ]
    productores = [
        threading.Thread(
            target=sensor,
            name=nombre,
            args=(
                nombre,
                interseccion,
                lecturas_por_sensor,
                semilla,
                buffer,
                metricas,
                inicio,
                registro,
                demora_productor,
            ),
        )
        for nombre, interseccion, semilla in configuracion_sensores
    ]
    consumidores = [
        threading.Thread(
            target=analizador,
            name=f"Analizador {numero}",
            args=(
                f"Analizador {numero}",
                buffer,
                metricas,
                inicio,
                registro,
                demora_consumidor,
                400 + numero,
            ),
        )
        for numero in (1, 2)
    ]
    hilo_supervisor = threading.Thread(
        target=supervisor,
        name="Supervisor SIGET",
        args=(
            buffer,
            metricas,
            inicio,
            detener_supervisor,
            registro,
            intervalo_supervision,
        ),
    )

    registro.escribir(
        "Principal",
        f"Inicia 3 productores, 2 consumidores y 1 supervisor; "
        f"buffer acotado={capacidad}",
    )
    for hilo in productores + consumidores + [hilo_supervisor]:
        hilo.start()
    inicio.set()

    for hilo in productores:
        hilo.join()

    # Un marcador por consumidor garantiza que ambos puedan salir sin quedar
    # bloqueados, pero solo despues de que todos los productores terminaron.
    for _ in consumidores:
        buffer.publicar(FIN)

    for hilo in consumidores:
        hilo.join()
    detener_supervisor.set()
    hilo_supervisor.join()

    producidas, procesadas, estados = metricas.resumen()
    ids_producidos = Counter(metricas.producidas)
    ids_procesados = Counter(metricas.procesadas)
    integridad = (
        producidas == 3 * lecturas_por_sensor
        and producidas == procesadas
        and ids_producidos == ids_procesados
        and all(repeticiones == 1 for repeticiones in ids_procesados.values())
        and buffer.ocupacion() == 0
    )

    registro.escribir("Principal", "=" * 64)
    registro.escribir(
        "Principal",
        f"RESULTADO: producidas={producidas}, procesadas={procesadas}, "
        f"estados={dict(estados)}",
    )
    registro.escribir(
        "Principal",
        f"Esperas observadas: productores={buffer.esperas_productores}, "
        f"consumidores={buffer.esperas_consumidores}",
    )
    registro.escribir(
        "Principal",
        "VERIFICACION DE INTEGRIDAD: " + ("APROBADA" if integridad else "FALLIDA"),
    )
    return integridad


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulacion productor-consumidor del SIGET con semaforos"
    )
    parser.add_argument(
        "--lecturas",
        type=int,
        default=8,
        help="lecturas que genera cada uno de los tres sensores (predeterminado: 8)",
    )
    parser.add_argument(
        "--capacidad",
        type=int,
        default=5,
        help="capacidad del buffer compartido (predeterminado: 5)",
    )
    parser.add_argument(
        "--rapido",
        action="store_true",
        help="reduce las pausas para pruebas automaticas",
    )
    return parser.parse_args()


def main() -> int:
    opciones = argumentos()
    try:
        correcto = ejecutar_simulacion(
            lecturas_por_sensor=opciones.lecturas,
            capacidad=opciones.capacidad,
            rapido=opciones.rapido,
        )
    except ValueError as error:
        print(f"Error de configuracion: {error}")
        return 2
    return 0 if correcto else 1


if __name__ == "__main__":
    raise SystemExit(main())
