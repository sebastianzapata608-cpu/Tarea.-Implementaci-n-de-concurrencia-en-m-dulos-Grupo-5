"""Pruebas de integridad de la simulacion SIGET."""

import unittest

from siget_concurrencia import BufferAcotado, LecturaTrafico, clasificar, ejecutar_simulacion


class PruebasSIGET(unittest.TestCase):
    def test_clasificacion_congestion(self) -> None:
        lectura = LecturaTrafico("x", "s", "i", 30, 90, 20, 0)
        self.assertEqual(clasificar(lectura), "CONGESTION")

    def test_clasificacion_exceso_velocidad(self) -> None:
        lectura = LecturaTrafico("x", "s", "i", 85, 40, 20, 0)
        self.assertEqual(clasificar(lectura), "EXCESO_VELOCIDAD")

    def test_capacidad_invalida(self) -> None:
        with self.assertRaises(ValueError):
            BufferAcotado(0)

    def test_simulacion_preserva_todas_las_lecturas(self) -> None:
        self.assertTrue(ejecutar_simulacion(lecturas_por_sensor=3, capacidad=2, rapido=True))


if __name__ == "__main__":
    unittest.main()
