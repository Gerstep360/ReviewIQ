import { useRef, useState } from 'react'
import { characterCount, number, reviewProblem } from '../lib/format'
import { Icon } from './Icon'

const examples = [
  { name: 'Positiva', text: 'Excelente calidad, funciona muy bien y llegó a tiempo.' },
  {
    name: 'Con contraste',
    text: 'El producto funciona bien, pero la batería dura muy poco y el envío fue lento.',
  },
  {
    name: 'Negativa',
    text: 'No funciona, llegó roto y no ofrecen garantía. Una mala experiencia.',
  },
]

interface Props {
  text: string
  onChange: (text: string) => void
  onSubmit: () => void
  pending: boolean
  laboratory?: boolean
}

export function ReviewForm({ text, onChange, onSubmit, pending, laboratory = false }: Props) {
  const textarea = useRef<HTMLTextAreaElement>(null)
  const [example, setExample] = useState(false)
  const count = characterCount(text)
  const problem = reviewProblem(text)
  const visibleProblem = text.length > 0 && problem
  return (
    <form
      className="review-form"
      onSubmit={(event) => {
        event.preventDefault()
        if (!problem && !pending) onSubmit()
      }}
      aria-busy={pending}
    >
      <div className="section-heading">
        <label htmlFor="review-text">Tu reseña</label>
        <span className="eyebrow">ESPAÑOL</span>
      </div>
      <p className="field-description" id="review-help">
        Escribe sobre un producto y tu experiencia de compra.
      </p>
      <textarea
        ref={textarea}
        id="review-text"
        value={text}
        disabled={pending}
        placeholder="¿Qué te pareció el producto? ¿Funcionó como esperabas?"
        aria-describedby={`review-help review-count${visibleProblem ? ' review-error' : ''}`}
        aria-invalid={Boolean(visibleProblem)}
        onChange={(event) => {
          setExample(false)
          onChange(event.target.value)
        }}
      />
      <div className="field-footer">
        <span className={example ? 'example-label' : 'muted'}>
          {example
            ? 'Ejemplo sintético · puedes editarlo'
            : 'No se guarda un historial de reseñas.'}
        </span>
        <span id="review-count" className={count > 3000 ? 'text-error' : 'muted'}>
          {number(count)} / 3.000
        </span>
      </div>
      {visibleProblem && (
        <p id="review-error" className="field-error" role="alert">
          {visibleProblem}
        </p>
      )}
      <div className="example-picker">
        <span>Prueba con un ejemplo sintético</span>
        <div>
          {examples.map((item) => (
            <button
              key={item.name}
              type="button"
              className="example-button"
              disabled={pending}
              onClick={() => {
                onChange(item.text)
                setExample(true)
                textarea.current?.focus()
              }}
            >
              {item.name}
            </button>
          ))}
        </div>
      </div>
      <div className="form-actions">
        <button className="button primary" type="submit" disabled={pending || Boolean(problem)}>
          {pending ? (
            <span className="spinner small" aria-hidden="true" />
          ) : (
            <Icon name={laboratory ? 'nlp' : 'analyze'} />
          )}
          {pending ? 'Analizando…' : laboratory ? 'Ver procesamiento NLP' : 'Analizar reseña'}
        </button>
        <button
          className="text-button"
          type="button"
          disabled={pending || !text}
          onClick={() => {
            setExample(false)
            onChange('')
            textarea.current?.focus()
          }}
        >
          Limpiar
        </button>
      </div>
    </form>
  )
}
