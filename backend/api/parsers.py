"""Leer como máximo 64 KiB antes de decodificar JSON."""

from io import BytesIO

from django.conf import settings
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser, JSONParser

from backend.api.exceptions import PayloadTooLarge


class BoundedJSONParser(BaseParser):
    media_type = 'application/json'

    def parse(self, stream, media_type=None, parser_context=None):
        limit = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
        request = (parser_context or {}).get('request')
        try:
            declared_length = int(request.META.get('CONTENT_LENGTH') or 0) if request else 0
        except (ValueError, TypeError):
            raise ParseError('Longitud de contenido inválida.') from None
        if declared_length > limit:
            raise PayloadTooLarge()
        encoding = (parser_context or {}).get('encoding', 'utf-8')
        if encoding.lower().replace('_', '-') not in {'utf-8', 'utf8'}:
            raise ParseError('Se requiere codificación UTF-8.')
        content = stream.read(limit + 1)
        if len(content) > limit:
            raise PayloadTooLarge()
        try:
            return JSONParser().parse(BytesIO(content), media_type, parser_context)
        except RecursionError:
            raise ParseError('El JSON tiene demasiados niveles de anidación.') from None
