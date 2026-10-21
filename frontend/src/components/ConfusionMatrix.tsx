import { number } from '../lib/format'
import { STAR_VALUES } from '../types/reviewiq'

export function ConfusionMatrix({ matrix }: { matrix: number[][] }) {
  const maximum = Math.max(1, ...matrix.flat())
  return (
    <div className="matrix-wrapper">
      <table className="confusion-matrix">
        <caption>
          <span className="sr-only">Matriz de confusión. </span>Filas: estrellas reales · Columnas:
          predicción
        </caption>
        <thead>
          <tr>
            <th scope="col">Real ↓</th>
            {STAR_VALUES.map((stars) => (
              <th scope="col" key={stars}>
                {stars} ★
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, rowIndex) => (
            <tr key={rowIndex}>
              <th scope="row">{rowIndex + 1} ★</th>
              {row.map((count, columnIndex) => {
                const intensity = count / maximum
                const alpha = 0.04 + intensity * 0.91
                const channels = [28, 85, 71].map(
                  (channel) => (channel * alpha + 255 * (1 - alpha)) / 255,
                )
                const linear = channels.map((channel) =>
                  channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4,
                )
                const luminance = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
                return (
                  <td
                    key={columnIndex}
                    style={{
                      backgroundColor: `rgba(28, 85, 71, ${alpha})`,
                      color: luminance > 0.179 ? '#000' : '#fff',
                    }}
                    title={`Real: ${rowIndex + 1} estrellas. Predicción: ${columnIndex + 1} estrellas. ${number(count)} reseñas.`}
                  >
                    {number(count)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="chart-note">
        <span className="heat-scale" aria-hidden="true" />
        Mayor intensidad, más reseñas. La diagonal indica aciertos.
      </p>
    </div>
  )
}
