import { percent } from '../lib/format'
import { STAR_VALUES } from '../types/reviewiq'
import type { Probabilities, Stars } from '../types/reviewiq'

export function ProbabilityBars({
  probabilities,
  selected,
}: {
  probabilities: Probabilities
  selected: Stars
}) {
  return (
    <div className="probability-chart" role="group" aria-label="Probabilidades por estrellas">
      {STAR_VALUES.map((stars) => (
        <div key={stars} className={`probability-row ${stars === selected ? 'selected' : ''}`}>
          <span className="probability-label">
            {stars}
            <span aria-hidden="true"> ★</span>
            <span className="sr-only"> estrellas</span>
          </span>
          <span className="probability-track" aria-hidden="true">
            <span
              className="probability-fill"
              style={{ width: `${probabilities[stars] * 100}%` }}
            />
          </span>
          <span className="probability-value">{percent(probabilities[stars])}</span>
        </div>
      ))}
    </div>
  )
}
