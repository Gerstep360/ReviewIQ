export type Stars = 1 | 2 | 3 | 4 | 5
export const STAR_VALUES: Stars[] = [1, 2, 3, 4, 5]
export type Probabilities = Record<Stars, number>

export interface Health {
  status: 'ok'
  model_loaded: true
  model_id: string
  mode: 'full' | 'quick'
}

export interface Prediction {
  stars: Stars
  label: number
  probabilities: Probabilities
  model_id: string
  inference_ms: number
  experimental: boolean
}

export interface PerClass {
  label: number
  stars: Stars
  precision: number
  recall: number
  f1: number
  support: number
}

export interface MetricValues {
  rows: number
  macro_f1: number
  accuracy: number
  mae_stars: number
  per_class: PerClass[]
  confusion_matrix: number[][]
}

export interface ComparisonModel {
  model: string
  morphology: string
  ngram_range: number[]
  best_params: Record<string, number>
  train_rows: number
  metrics: MetricValues
}

export interface ModelConfiguration {
  preprocessing: { morphology: string; preserve_accents: boolean; protect_negations: boolean }
  tfidf: {
    ngram_range: number[]
    max_features: number
    min_df: number
    max_df: number
    sublinear_tf: boolean
  }
  classifier: { name: string; parameters: Record<string, string | number | boolean | null> }
  feature_count: number
  seed: number
}

export interface Metrics {
  model_id: string
  mode: 'full' | 'quick'
  split: 'test' | 'validation'
  experimental: boolean
  evaluated_at_utc: string | null
  packaged_at_utc: string
  dataset: { repository: string; revision: string }
  configuration: ModelConfiguration
  metrics: MetricValues
  comparison: {
    model_id: string
    split: 'validation'
    generated_at_utc: string
    models: ComparisonModel[]
  } | null
  probability_notice: string
}

export interface NlpTrace {
  model_id: string
  original: string
  normalized: string
  tokens: string[]
  removed_stopwords: string[]
  tokens_after_stopwords: string[]
  processed_tokens: string[]
  processed_text: string
  method: 'stemming' | 'lemmatization'
  policy_version: string
  stopwords_version: string
  stopwords_sha256: string
  ngram_range: number[]
  ngrams: string[]
  known_ngrams: string[]
  unknown_ngrams: string[]
  truncated: boolean
  limits: { items_per_list: number; characters_per_string: number }
  original_counts: Record<string, number>
}
