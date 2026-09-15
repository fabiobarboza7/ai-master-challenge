import { tokens } from "./text"

// Formato de public/data/model.json, gerado por solution/analysis/07_exportar_app.py.
export type ModelFile = {
  classes: string[]
  rotulos_pt: Record<string, string>
  vocabulario: string[]
  idf: number[]
  coef: number[][]
  intercepto: number[]
  politica: {
    tau_auto: number
    tau_assist: number
    precisao_alvo_por_ticket: number
    categorias_elegiveis: string[]
    corte_palavras_conhecidas: number
    padrao_reembolso_cancelamento: string
    tipos_reembolso_cancelamento: string[]
    execucao_sempre_humana: string[]
    presets: Preset[]
  }
}

export type Preset = {
  alvo: number
  tau_auto: number
  tau_assist: number
  categorias_elegiveis: string[]
}

export type Model = ModelFile & {
  index: ReadonlyMap<string, number>
}

export type Prediction = {
  probabilities: number[]
  // termo e peso dele a favor da categoria prevista, do maior para o menor
  evidence: { term: string; weight: number }[]
}

export function prepareModel(file: ModelFile): Model {
  return {
    ...file,
    index: new Map(file.vocabulario.map((term, i) => [term, i])),
  }
}

// TF-IDF (tf sublinear, normalização L2) + softmax da regressão logística, como no scikit-learn.
export function predict(model: Model, normalized: string): Prediction {
  const toks = tokens(normalized)
  const grams = [...toks]
  for (let i = 0; i < toks.length - 1; i++) grams.push(`${toks[i]} ${toks[i + 1]}`)

  const counts = new Map<number, number>()
  for (const gram of grams) {
    const j = model.index.get(gram)
    if (j !== undefined) counts.set(j, (counts.get(j) ?? 0) + 1)
  }

  const features = [...counts].map(([j, c]) => ({
    j,
    value: (1 + Math.log(c)) * model.idf[j],
  }))
  const norm = Math.sqrt(features.reduce((s, f) => s + f.value * f.value, 0))
  if (norm > 0) for (const f of features) f.value /= norm

  const z = model.intercepto.map(
    (b, k) => b + features.reduce((s, f) => s + model.coef[k][f.j] * f.value, 0)
  )
  const max = Math.max(...z)
  const exp = z.map((v) => Math.exp(v - max))
  const total = exp.reduce((s, v) => s + v, 0)
  const probabilities = exp.map((v) => v / total)

  const top = probabilities.indexOf(Math.max(...probabilities))
  const evidence = features
    .map((f) => ({ term: model.vocabulario[f.j], weight: model.coef[top][f.j] * f.value }))
    .filter((e) => e.weight > 0)
    .sort((a, b) => b.weight - a.weight)

  return { probabilities, evidence }
}
