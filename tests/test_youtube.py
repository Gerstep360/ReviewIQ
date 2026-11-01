"""Pruebas unitarias para el extractor de comentarios de YouTube y su integración con ReviewIQ."""

import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
os.environ.setdefault('USE_SQLITE', '1')

import django
django.setup()

import uuid
from django.test import TestCase

from backend.apps.reviewiq.youtube_scraper import (
    extraer_video_id,
    extraer_comentarios_youtube,
    sincronizar_app_youtube
)
from backend.apps.reviewiq.models import Entidad, ComentarioCrudo, DiagnosticoIQ


class YouTubeExtractorTests(TestCase):
    def test_extraer_video_id(self):
        # 1. URL estándar
        id1 = extraer_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(id1, "dQw4w9WgXcQ")

        # 2. URL corta youtu.be
        id2 = extraer_video_id("https://youtu.be/dQw4w9WgXcQ")
        self.assertEqual(id2, "dQw4w9WgXcQ")

        # 3. URL con parámetros extras
        id3 = extraer_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&feature=shared")
        self.assertEqual(id3, "dQw4w9WgXcQ")

        # 4. URL de shorts
        id4 = extraer_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        self.assertEqual(id4, "dQw4w9WgXcQ")

        # 5. ID directo de 11 caracteres
        id5 = extraer_video_id("dQw4w9WgXcQ")
        self.assertEqual(id5, "dQw4w9WgXcQ")

        # 6. Texto inválido
        id6 = extraer_video_id("https://otra-cosa.com/pagina")
        self.assertEqual(id6, "")

    def test_extraer_comentarios_estructura(self):
        comentarios = extraer_comentarios_youtube("https://www.youtube.com/watch?v=dQw4w9WgXcQ", cantidad=5)
        self.assertIsInstance(comentarios, list)
        self.assertGreater(len(comentarios), 0)
        primer = comentarios[0]
        self.assertIn("author", primer)
        self.assertIn("text", primer)
        self.assertIn("id", primer)
        self.assertIsInstance(primer["text"], str)

    def test_sincronizar_app_youtube_con_mock_predictor(self):
        # Crear entidad de prueba con ID único
        entidad = Entidad.objects.create(
            nombre="App YouTube Test",
            categoria="delivery",
            tipo_fuente="youtube",
            identificador_externo=f"test_yt_{uuid.uuid4().hex[:8]}"
        )

        resultado = sincronizar_app_youtube(
            package_id_o_entidad_id=str(entidad.id),
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            cantidad=3
        )

        self.assertEqual(resultado["status"], "success")
        self.assertGreater(resultado["total_procesadas"], 0)
        self.assertIn("semaforo", resultado)
        self.assertIn("calificacion_promedio", resultado)

        # Verificar que se crearon los comentarios con fuente 'youtube'
        comentarios = ComentarioCrudo.objects.filter(entidad=entidad)
        self.assertGreater(comentarios.count(), 0)
        for c in comentarios:
            self.assertEqual(c.fuente, "youtube")
            self.assertIsNotNone(c.diagnostico)
            self.assertGreaterEqual(c.diagnostico.estrellas_predichas, 1)
            self.assertLessEqual(c.diagnostico.estrellas_predichas, 5)


if __name__ == "__main__":
    unittest.main()
