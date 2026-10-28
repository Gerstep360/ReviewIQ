"""Motor léxico de análisis de tópicos y cálculo del Semáforo de Experiencia."""

import re
from ml.nlp.normalize import normalize_text

# Diccionario léxico curado en español para el mercado boliviano / hispanohablante
DIMENSION_KEYWORDS = {
    'atencion_cliente': [
        'atencion', 'atención', 'atender', 'atendieron', 'amable', 'amables',
        'grosero', 'grosera', 'pesima atencion', 'cajero', 'cajera', 'mesero',
        'personal', 'empleado', 'empleada', 'trato', 'espera', 'fila', 'cola',
        'soporte', 'reclamo', 'queja', 'respuesta', 'ayuda', 'sin respuesta'
    ],
    'envio_logistica': [
        'envio', 'envío', 'entrega', 'tardo', 'tardó', 'demoro', 'demoró',
        'llego', 'llegó', 'paquete', 'repartidor', 'delivery', 'pedido',
        'direccion', 'dirección', 'tardaron', 'a tiempo', 'retraso', 'tiempo de entrega'
    ],
    'calidad_producto': [
         'calidad', 'comida', 'roto', 'rota', 'dañado', 'dañada', 'frio', 'frío',
        'fria', 'fría', 'caliente', 'fresco', 'fresca', 'sabor', 'rico', 'rica',
        'delicioso', 'deliciosa', 'feo', 'fea', 'quemado', 'quemada', 'original',
        'falso', 'duradero', 'defectuoso', 'mala calidad', 'excelente calidad',
        'sirve', 'no sirve', 'vencido', 'vencida'
    ],
    'precio_valor': [
        'precio', 'caro', 'cara', 'barato', 'barata', 'costoso', 'costosa',
        'economico', 'económico', 'cobro', 'cobraron', 'estafa', 'robo',
        'descuento', 'promocion', 'promoción', 'oferta', 'vale la pena', 'tarifa'
    ],
    'ux_bugs': [
        'app', 'aplicacion', 'aplicación', 'bug', 'error', 'crashea', 'cierra',
        'traba', 'lenta', 'lento', 'actualizacion', 'actualización', 'login',
        'clave', 'contraseña', 'cuenta', 'cae', 'sistema', 'no abre', 'pantalla'
    ]
}


def detectar_dimensiones(texto_limpio: str) -> list[str]:
    """Retorna la lista de dimensiones presentes en el texto."""
    texto_norm = normalize_text(texto_limpio, preserve_accents=False).lower()
    detectadas = []
    
    for dimension, palabras in DIMENSION_KEYWORDS.items():
        for palabra in palabras:
            palabra_norm = normalize_text(palabra, preserve_accents=False).lower()
            patron = rf'\b{re.escape(palabra_norm)}\b'
            if re.search(patron, texto_norm):
                detectadas.append(dimension)
                break
                
    return detectadas


def puntuar_dimensiones(texto: str, estrellas: int, probabilidades: dict) -> dict:
    """Calcula el impacto (-1.0 a 1.0) en cada una de las 5 dimensiones.
    
    Usa las estrellas y probabilidades de ReviewIQ:
    - 1-2 estrellas: Negativo (-1.0 ponderado por la confianza en estrellas bajas)
    - 3 estrellas: Neutro (0.0)
    - 4-5 estrellas: Positivo (+1.0 ponderado por la confianza en estrellas altas)
    """
    dimensiones_presentes = detectar_dimensiones(texto)
    
    p_baja = float(probabilidades.get('1', 0.0)) + float(probabilidades.get('2', 0.0))
    p_alta = float(probabilidades.get('4', 0.0)) + float(probabilidades.get('5', 0.0))
    
    if estrellas in (1, 2):
        sentimiento = 'negativo'
        impacto = -1.0 * (p_baja if p_baja > 0 else 0.8)
    elif estrellas == 3:
        sentimiento = 'neutro'
        impacto = 0.0
    else:
        sentimiento = 'positivo'
        impacto = +1.0 * (p_alta if p_alta > 0 else 0.8)
        
    scores = {
        'sentimiento_global': sentimiento,
        'atencion_cliente_score': impacto if 'atencion_cliente' in dimensiones_presentes else 0.0,
        'envio_logistica_score': impacto if 'envio_logistica' in dimensiones_presentes else 0.0,
        'calidad_producto_score': impacto if 'calidad_producto' in dimensiones_presentes else 0.0,
        'precio_valor_score': impacto if 'precio_valor' in dimensiones_presentes else 0.0,
        'ux_bugs_score': impacto if 'ux_bugs' in dimensiones_presentes else 0.0,
        'dimensiones_detectadas': dimensiones_presentes,
    }
    return scores


def calcular_semaforo_entidad(diagnosticos) -> dict:
    """Toma los diagnósticos de una entidad y calcula el Semáforo 0-100% por dimensión."""
    dimensiones = [
        'atencion_cliente',
        'envio_logistica',
        'calidad_producto',
        'precio_valor',
        'ux_bugs'
    ]
    
    conteos = {d: {'suma': 0.0, 'menciones': 0} for d in dimensiones}
    
    for diag in diagnosticos:
        for d in dimensiones:
            val = getattr(diag, f'{d}_score', 0.0)
            if val != 0.0:
                conteos[d]['suma'] += val
                conteos[d]['menciones'] += 1
                
    semaforo = {}
    for d in dimensiones:
        menciones = conteos[d]['menciones']
        if menciones == 0:
            score_pct = 50.0
            badge = 'amarillo'
        else:
            promedio = conteos[d]['suma'] / menciones  # Entre -1.0 y +1.0
            score_pct = round(((promedio + 1.0) / 2.0) * 100.0, 1)  # Escala 0 a 100%
            
            if score_pct >= 75.0:
                badge = 'verde'
            elif score_pct >= 45.0:
                badge = 'amarillo'
            else:
                badge = 'rojo'
                
        semaforo[d] = {
            'score': score_pct,
            'badge': badge,
            'menciones': menciones
        }
        
    return semaforo