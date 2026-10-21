"""Contrato JSON de entrada y salida, independiente de modelos de base de datos."""

import math

from django.conf import settings
from rest_framework import serializers


class StrictObjectSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({'non_field_errors': ['Se requiere un objeto JSON.']})
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: ['Campo no permitido.'] for key in sorted(unknown)})
        return super().to_internal_value(data)


class ReviewTextField(serializers.CharField):
    default_error_messages = {
        'invalid': 'La reseña debe ser una cadena de texto.',
        'blank': 'La reseña no puede estar vacía ni contener solo espacios.',
        'null': 'La reseña no puede ser null.',
        'required': 'El campo text es obligatorio.',
        'max_length': 'La reseña no puede superar {max_length} caracteres.',
        'encoding': 'La reseña debe contener Unicode válido y no puede incluir caracteres nulos.',
    }

    def run_validation(self, data=serializers.empty):
        if data is not serializers.empty and data is not None:
            if not isinstance(data, str):
                self.fail('invalid')
            if not data.strip():
                self.fail('blank')
            try:
                data.encode('utf-8')
            except UnicodeEncodeError:
                self.fail('encoding')
            if '\0' in data:
                self.fail('encoding')
        return super().run_validation(data)


class ReviewRequestSerializer(StrictObjectSerializer):
    text = ReviewTextField(max_length=settings.REVIEWIQ_MAX_TEXT_LENGTH, trim_whitespace=False)


class ProbabilitiesSerializer(StrictObjectSerializer):
    def get_fields(self):
        return {str(stars): serializers.FloatField(min_value=0, max_value=1) for stars in range(1, 6)}

    def validate(self, values):
        if not all(math.isfinite(value) for value in values.values()) or not math.isclose(sum(values.values()), 1.0, abs_tol=1e-5):
            raise serializers.ValidationError('Las probabilidades deben ser finitas y sumar uno.')
        return values


class PredictionSerializer(StrictObjectSerializer):
    stars = serializers.IntegerField(min_value=1, max_value=5)
    label = serializers.IntegerField(min_value=0, max_value=4)
    probabilities = ProbabilitiesSerializer()
    model_id = serializers.CharField()
    inference_ms = serializers.FloatField(min_value=0)
    experimental = serializers.BooleanField()

    def validate(self, values):
        most_likely = int(max(values['probabilities'], key=values['probabilities'].get))
        if values['stars'] != most_likely or values['stars'] != values['label'] + 1 or not math.isfinite(values['inference_ms']):
            raise serializers.ValidationError('La salida no corresponde a las clases del modelo.')
        return values


class HealthSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['ok'])
    model_loaded = serializers.BooleanField()
    model_id = serializers.CharField()
    mode = serializers.ChoiceField(choices=['quick', 'full'])


class ErrorDetailSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    fields = serializers.DictField(required=False)


class ErrorSerializer(serializers.Serializer):
    error = ErrorDetailSerializer()


class UnavailableHealthSerializer(ErrorSerializer):
    status = serializers.ChoiceField(choices=['unavailable'])
    model_loaded = serializers.BooleanField()
    model_id = serializers.CharField(allow_null=True)


class PerClassSerializer(serializers.Serializer):
    label = serializers.IntegerField(min_value=0, max_value=4)
    stars = serializers.IntegerField(min_value=1, max_value=5)
    precision = serializers.FloatField(min_value=0, max_value=1)
    recall = serializers.FloatField(min_value=0, max_value=1)
    f1 = serializers.FloatField(min_value=0, max_value=1)
    support = serializers.IntegerField(min_value=0)


class MetricValuesSerializer(serializers.Serializer):
    rows = serializers.IntegerField(min_value=1)
    macro_f1 = serializers.FloatField(min_value=0, max_value=1)
    accuracy = serializers.FloatField(min_value=0, max_value=1)
    mae_stars = serializers.FloatField(min_value=0, max_value=4)
    per_class = PerClassSerializer(many=True, min_length=5, max_length=5)
    confusion_matrix = serializers.ListField(child=serializers.ListField(child=serializers.IntegerField(min_value=0), min_length=5, max_length=5), min_length=5, max_length=5)
    ordinal_error_counts = serializers.DictField(child=serializers.IntegerField(min_value=0), required=False)
    probabilities_sum_to_one = serializers.BooleanField(required=False)

    def validate(self, values):
        if [item['stars'] for item in values['per_class']] != list(range(1, 6)):
            raise serializers.ValidationError('Se requiere el orden de clases 1–5.')
        if sum(sum(row) for row in values['confusion_matrix']) != values['rows']:
            raise serializers.ValidationError('La matriz no corresponde al número de filas.')
        return values


class ComparisonSerializer(serializers.Serializer):
    model_id = serializers.CharField()
    split = serializers.ChoiceField(choices=['validation'])
    generated_at_utc = serializers.CharField()
    models = serializers.ListField(child=serializers.JSONField())


class MetricsSerializer(serializers.Serializer):
    model_id = serializers.CharField()
    mode = serializers.ChoiceField(choices=['quick', 'full'])
    split = serializers.ChoiceField(choices=['test', 'validation'])
    experimental = serializers.BooleanField()
    evaluated_at_utc = serializers.CharField(allow_null=True)
    packaged_at_utc = serializers.CharField()
    dataset = serializers.DictField(child=serializers.CharField())
    configuration = serializers.JSONField()
    metrics = MetricValuesSerializer()
    comparison = ComparisonSerializer(allow_null=True)
    probability_notice = serializers.CharField()


class TraceSerializer(serializers.Serializer):
    model_id = serializers.CharField()
    original = serializers.CharField(trim_whitespace=False)
    normalized = serializers.CharField(allow_blank=True, trim_whitespace=False)
    tokens = serializers.ListField(child=serializers.CharField())
    removed_stopwords = serializers.ListField(child=serializers.CharField())
    tokens_after_stopwords = serializers.ListField(child=serializers.CharField())
    processed_tokens = serializers.ListField(child=serializers.CharField())
    processed_text = serializers.CharField(allow_blank=True, trim_whitespace=False)
    method = serializers.ChoiceField(choices=['stemming', 'lemmatization'])
    policy_version = serializers.CharField()
    stopwords_version = serializers.CharField()
    stopwords_sha256 = serializers.CharField()
    ngram_range = serializers.ListField(child=serializers.IntegerField(), min_length=2, max_length=2)
    ngrams = serializers.ListField(child=serializers.CharField())
    known_ngrams = serializers.ListField(child=serializers.CharField())
    unknown_ngrams = serializers.ListField(child=serializers.CharField())
    truncated = serializers.BooleanField()
    limits = serializers.DictField(child=serializers.IntegerField())
    original_counts = serializers.DictField(child=serializers.IntegerField())


def checked_output(serializer_class, data):
    serializer = serializer_class(data=data)
    if not serializer.is_valid():
        # Un error del modelo/contrato es un 500, no un fallo de entrada del usuario.
        raise RuntimeError('El resultado no cumple el contrato de salida.')
    return serializer.data
