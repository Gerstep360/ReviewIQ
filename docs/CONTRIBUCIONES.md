# CONTRIBUCIONES — ReviewIQ (plantilla para completar con evidencias reales)

**Advertencia:** documento por rellenar después de trabajar. El PDF exige que **coincida** con los autores reales y el `git log`. No inventar cuentas, fechas, revisiones ni contribuciones.

## Identidad y autorización

- Modalidad: [grupo real de 3–4 / modalidad individual AUTORIZADA por docente el día X].
- Repo: [URL pública o privada que el profesor pueda leer].
- Profesor agregado como colaborador: [confirmación real, fecha].

## Responsabilidades realmente ejecutadas

| Persona real + usuario Git | Módulo | Cambio concreto y por qué | Commits (SHA reales) | PR/revisor real | Evidencia de prueba |
|---|---|---|---|---|---|
| [completar] | [ej. NLP] | [descripción] | [hash] | [link + persona] | [test/reporte] |

Si **solo tú** desarrollas, escribe **una sola fila de autoría auténtica** por persona con tantos módulos como corresponda (o varias filas para tu propia cuenta, siempre el mismo autor). No subdividirte en integrantes ficticios.

## Aportes de ML/NLP por integrante (si hay grupo)

- [Nombre real]: [commit que modifica técnicamente NLP/ML]; [cómo se comprueba].

## Trabajo asistido por IA

- Herramientas y alcance: [declaración real].
- Validación humana: [pruebas y revisiones hechas realmente].

## Evidencia consultable por el ingeniero

```bash
git shortlog -sne
git log --format='%h %ad %an %s' --date=short --reverse
git show <hash-real>
```

No incluir registros inventados. Solo marcar completado luego de comprobar cada commit y PR.
