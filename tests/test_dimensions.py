"""Pruebas unitarias para el motor de dimensiones y cálculo del Semáforo."""

import unittest
from backend.apps.reviewiq.dimensions import (
    detectar_dimensiones,
    puntuar_dimensiones,
    calcular_semaforo_entidad
)


class MockDiagnostico:
    """Objeto simulado para probar el cálculo del Semáforo sin tocar la base de datos."""
    def __init__(self, atencion=0.0, envio=0.0, calidad=0.0, precio=0.0, ux=0.0):
        self.atencion_cliente_score = atencion
        self.envio_logistica_score = envio
        self.calidad_producto_score = calidad
        self.precio_valor_score = precio
        self.ux_bugs_score = ux


class DimensionsTests(unittest.TestCase):
    def test_deteccion_de_dimensiones_por_palabras_clave(self):
        # 1. Atención al cliente
        d1 = detectar_dimensiones("Pésima atención del cajero, fue muy grosero")
        self.assertIn("atencion_cliente", d1)

        # 2. Envío y logística
        d2 = detectar_dimensiones("El delivery tardó más de dos horas y el pedido no llegó")
        self.assertIn("envio_logistica", d2)

        # 3. Calidad y Precio juntos
        d3 = detectar_dimensiones("La comida fría pero el precio es muy barato")
        self.assertIn("calidad_producto", d3)
        self.assertIn("precio_valor", d3)

        # 4. Fallos de la App (UX)
        d4 = detectar_dimensiones("La app se traba y crashea al poner mi contraseña")
        self.assertIn("ux_bugs", d4)

        # 5. Texto sin palabras clave del catálogo
        d5 = detectar_dimensiones("Hoy es un día soleado en Santa Cruz")
        self.assertEqual(d5, [])

    def test_puntuacion_positiva_y_negativa_segun_estrellas(self):
        # Reseña negativa de 1 estrella
        negativo = puntuar_dimensiones(
            texto="El delivery tardó demasiado",
            estrellas=1,
            probabilidades={"1": 0.85, "2": 0.10, "3": 0.03, "4": 0.01, "5": 0.01}
        )
        self.assertEqual(negativo["sentimiento_global"], "negativo")
        self.assertLess(negativo["envio_logistica_score"], 0.0)
        self.assertEqual(negativo["calidad_producto_score"], 0.0)  # No se mencionó

        # Reseña positiva de 5 estrellas
        positivo = puntuar_dimensiones(
            texto="Excelente calidad de los productos, muy rico todo",
            estrellas=5,
            probabilidades={"1": 0.01, "2": 0.01, "3": 0.03, "4": 0.10, "5": 0.85}
        )
        self.assertEqual(positivo["sentimiento_global"], "positivo")
        self.assertGreater(positivo["calidad_producto_score"], 0.0)

    def test_calculo_del_semaforo_de_experiencia(self):
        # Simulamos 3 comentarios para un restaurante:
        # - 2 quejas graves de entrega (envio=-0.9)
        # - 2 felicitaciones de comida rica (calidad=+0.9)
        diagnosticos = [
            MockDiagnostico(envio=-0.9, calidad=0.9),
            MockDiagnostico(envio=-0.8, calidad=0.8),
            MockDiagnostico(calidad=0.9),
        ]

        semaforo = calcular_semaforo_entidad(diagnosticos)

        # Envío debe estar en ROJO (porque las quejas son negativas)
        self.assertEqual(semaforo["envio_logistica"]["badge"], "rojo")
        self.assertLess(semaforo["envio_logistica"]["score"], 45.0)

        # Calidad debe estar en VERDE (porque las opiniones son excelentes)
        self.assertEqual(semaforo["calidad_producto"]["badge"], "verde")
        self.assertGreaterEqual(semaforo["calidad_producto"]["score"], 75.0)

        # UX / Bugs no tuvo menciones ➔ debe estar en estado neutro (AMARILLO 50%)
        self.assertEqual(semaforo["ux_bugs"]["badge"], "amarillo")
        self.assertEqual(semaforo["ux_bugs"]["score"], 50.0)


if __name__ == "__main__":
    unittest.main()