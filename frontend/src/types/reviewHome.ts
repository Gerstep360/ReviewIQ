export interface Entidad {
  id: string;
  nombre: string;
  tipo_entidad: string;
  categoria: string;
  tipo_fuente: string;
  identificador_externo: string;
  icono_url?: string | null;
  total_resenas: number;
  calificacion_promedio: number;
  fecha_creacion: string;
}

export interface DimensionSemaforo {
  etiqueta: string;
  porcentaje: number;
  color: 'verde' | 'amarillo' | 'rojo';
  menciones: number;
}

export interface SemaforoMap {
  atencion_cliente: DimensionSemaforo;
  envio_logistica: DimensionSemaforo;
  calidad_producto: DimensionSemaforo;
  precio_valor: DimensionSemaforo;
  ux_bugs: DimensionSemaforo;
}

export interface DiagnosticoResena {
  estrellas_predichas: number;
  probabilidad_mayor: number;
  sentimiento_global: string;
  atencion_cliente_score: number;
  envio_logistica_score: number;
  calidad_producto_score: number;
  precio_valor_score: number;
  ux_bugs_score: number;
  fecha_analisis: string;
}

export interface Resena {
  id: string;
  texto: string;
  estrellas_origen: number;
  fecha_publicacion?: string | null;
  fecha_captura: string;
  diagnostico?: DiagnosticoResena;
}

export interface UserSession {
  id: number;
  username: string;
  nombre: string;
  role: 'admin' | 'user';
}