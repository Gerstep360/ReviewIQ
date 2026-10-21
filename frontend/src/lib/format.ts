export const number = (value: number, digits = 0) =>
  new Intl.NumberFormat('es-BO', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
export const percent = (value: number, digits = 1) => `${number(value * 100, digits)} %`
export const modelName = (name: string) =>
  ({ LogisticRegression: 'Regresión logística', MultinomialNB: 'Naive Bayes' })[name] || name
export const morphologyName = (method: string) =>
  method === 'lemmatization' ? 'Lematización' : method === 'stemming' ? 'Stemming' : method
export function dateLabel(value: string | null) {
  if (!value || !Number.isFinite(Date.parse(value))) return 'Fecha no registrada'
  return new Intl.DateTimeFormat('es-BO', { dateStyle: 'medium' }).format(new Date(value))
}
export const characterCount = (text: string) => Array.from(text).length
export function reviewProblem(text: string) {
  if (!text.trim()) return 'Escribe una reseña antes de analizar.'
  if (characterCount(text) > 3000) return 'La reseña no puede superar 3.000 caracteres.'
  if (text.includes('\0')) return 'La reseña no puede incluir caracteres nulos.'
  return null
}
