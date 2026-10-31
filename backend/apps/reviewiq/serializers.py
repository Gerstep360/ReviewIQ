"""
Serializadores para el módulo de Diagnóstico y Reputación (ReviewIQ).
"""
from django.contrib.auth.models import User
from django.db.models import Avg
from rest_framework import serializers

from .models import Entidad, ComentarioCrudo, DiagnosticoIQ


class EntidadSerializer(serializers.ModelSerializer):
    """Serializador para listar o detallar empresas / aplicaciones."""
    total_resenas = serializers.SerializerMethodField()
    calificacion_promedio = serializers.SerializerMethodField()

    class Meta:
        model = Entidad
        fields = [
            'id',
            'nombre',
            'tipo_entidad',
            'categoria',
            'tipo_fuente',
            'identificador_externo',
            'icono_url',
            'total_resenas',
            'calificacion_promedio',
            'fecha_creacion',
        ]

    def get_total_resenas(self, obj):
        return obj.comentarios.count()

    def get_calificacion_promedio(self, obj):
        avg = obj.comentarios.aggregate(Avg('estrellas_origen'))['estrellas_origen__avg']
        return round(float(avg), 1) if avg is not None else 0.0


class DiagnosticoIQSerializer(serializers.ModelSerializer):
    """Serializador del diagnóstico generado por ReviewIQ para una reseña."""
    class Meta:
        model = DiagnosticoIQ
        fields = [
            'estrellas_predichas',
            'probabilidad_mayor',
            'sentimiento_global',
            'atencion_cliente_score',
            'envio_logistica_score',
            'calidad_producto_score',
            'precio_valor_score',
            'ux_bugs_score',
            'fecha_analisis',
        ]


class ComentarioCrudoSerializer(serializers.ModelSerializer):
    """Serializador para mostrar reseñas junto a su diagnóstico de IA."""
    diagnostico = DiagnosticoIQSerializer(read_only=True)

    class Meta:
        model = ComentarioCrudo
        fields = [
            'id',
            'texto',
            'estrellas_origen',
            'fecha_publicacion',
            'fecha_captura',
            'diagnostico',
        ]


class CrearComentarioSerializer(serializers.Serializer):
    """Valida los datos enviados por un usuario cuando deja su opinión en la web."""
    texto = serializers.CharField(
        min_length=5,
        max_length=2000,
        required=True,
        help_text="Texto de la opinión escrita por el usuario"
    )
    estrellas = serializers.IntegerField(
        min_value=1,
        max_value=5,
        default=5,
        help_text="Calificación de 1 a 5 estrellas dada por el usuario"
    )


class LoginSerializer(serializers.Serializer):
    """Valida credenciales de acceso para Usuario o Administrador."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class RegisterSerializer(serializers.Serializer):
    """Valida el registro de un nuevo usuario."""
    username = serializers.CharField(min_length=3, max_length=150, required=True)
    password = serializers.CharField(min_length=4, max_length=128, write_only=True, required=True)
    nombre = serializers.CharField(max_length=150, required=False, allow_blank=True)


class SyncPlayStoreRequestSerializer(serializers.Serializer):
    """Valida los datos recibidos cuando el administrador pide sincronizar una app."""
    app_id = serializers.CharField(
        max_length=255,
        required=True,
        help_text="ID del paquete de Google Play Store (ej. com.pedidosya)"
    )
    nombre = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        help_text="Nombre amigable de la entidad"
    )
    categoria = serializers.CharField(
        max_length=50,
        default='delivery',
        help_text="Categoría (delivery, banca_finanzas, transporte, etc.)"
    )
    pais = serializers.CharField(
        max_length=5,
        default='bo',
        help_text="Código del país en Play Store (ej. bo, ar, es)"
    )
    cantidad = serializers.IntegerField(
        default=20,
        min_value=5,
        max_value=100,
        help_text="Cantidad de reseñas a descargar y procesar"
    )