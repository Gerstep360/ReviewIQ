"""Modelos de persistencia con restricciones de unicidad para ReviewIQ."""

import uuid
from django.db import models


class Entidad(models.Model):
    TIPOS_ENTIDAD = [
        ('app', 'Aplicación Móvil'),
        ('fisico', 'Negocio / Establecimiento Físico'),
    ]

    CATEGORIAS = [
        ('delivery', 'Delivery y Pedidos'),
        ('banca_finanzas', 'Banca y Billeteras Móviles'),
        ('transporte', 'Transporte y Movilidad'),
        ('telecom', 'Telecomunicaciones'),
        ('restaurantes', 'Restaurantes y Gastronomía'),
        ('supermercados', 'Supermercados y Retail'),
        ('salud', 'Salud y Farmacias'),
        ('servicios_publicos', 'Servicios Públicos y Trámites'),
    ]

    FUENTES = [
        ('play_store', 'Google Play Store'),
        ('google_maps', 'Google Maps'),
        ('manual', 'Ingreso Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150, db_index=True)
    tipo_entidad = models.CharField(max_length=20, choices=TIPOS_ENTIDAD, default='app')
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, db_index=True)
    tipo_fuente = models.CharField(max_length=30, choices=FUENTES, default='play_store')
    identificador_externo = models.CharField(
        max_length=255,
        help_text='ID único en origen: package_id (Play Store) o place_id (Maps)'
    )
    icono_url = models.URLField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entidad'
        verbose_name_plural = 'Entidades'
        # Evita duplicar la misma entidad en la misma plataforma
        constraints = [
            models.UniqueConstraint(
                fields=['tipo_fuente', 'identificador_externo'],
                name='unique_entidad_por_fuente'
            )
        ]

    def __str__(self):
        return f'{self.nombre} ({self.get_categoria_display()})'


class ComentarioCrudo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entidad = models.ForeignKey(Entidad, on_delete=models.CASCADE, related_name='comentarios')
    texto = models.TextField()
    estrellas_origen = models.IntegerField(help_text='Estrellas de 1 a 5 reportadas en la plataforma origen')
    fecha_publicacion = models.DateTimeField(blank=True, null=True)
    fecha_captura = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comentario Crudo'
        verbose_name_plural = 'Comentarios Crudos'

    def __str__(self):
        return f'Reseña de {self.entidad.nombre} ({self.estrellas_origen}★)'


class DiagnosticoIQ(models.Model):
    SENTIMIENTOS = [
        ('positivo', 'Positivo'),
        ('neutro', 'Neutro'),
        ('negativo', 'Negativo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # OneToOne garantiza que NUNCA habrá dos diagnósticos para el mismo comentario
    comentario = models.OneToOneField(ComentarioCrudo, on_delete=models.CASCADE, related_name='diagnostico')

    # Predicción generada por ReviewIQ
    estrellas_predichas = models.IntegerField(help_text='Estrellas inferidas por ReviewIQ (1 a 5)')
    probabilidad_mayor = models.FloatField(help_text='Confianza de la predicción (0.0 a 1.0)')
    sentimiento_global = models.CharField(max_length=20, choices=SENTIMIENTOS)

    # Las 5 dimensiones del Semáforo (-1.0=Negativo, 0.0=No aplica, 1.0=Positivo)
    atencion_cliente_score = models.FloatField(default=0.0)
    envio_logistica_score = models.FloatField(default=0.0)
    calidad_producto_score = models.FloatField(default=0.0)
    precio_valor_score = models.FloatField(default=0.0)
    ux_bugs_score = models.FloatField(default=0.0)

    fecha_analisis = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Diagnóstico IQ'
        verbose_name_plural = 'Diagnósticos IQ'

    def __str__(self):
        return f'Diagnóstico de {self.comentario.entidad.nombre} - {self.estrellas_predichas}★'