import type { Lane } from "./policy"

// Formato de public/data/backtest.json: um item por ticket do teste do Dataset 2.
export type BacktestFile = {
  classes: string[]
  confianca: number[]
  prevista: number[]
  real: number[]
  top2_certo: (0 | 1)[]
  palavras_conhecidas: number[]
  palavra_chave_reembolso_cancelamento: (0 | 1)[]
  referencia_python: { filas: Record<Lane, number>; tau_auto: number; tau_assist: number }
}

export type LaneOptions = {
  tauAuto: number
  tauAssist: number
  eligible: ReadonlySet<string>
  knownCut: number
  // O ROI trata reembolso/cancelamento à parte (fração do volume), então desliga a regra por palavra-chave.
  keywordRule?: boolean
}

export type LaneSummary = {
  total: number
  counts: Record<Lane, number>
  autoWrong: number
  assistTop2Right: number
  blockedByRules: number
}

export function laneOf(bt: BacktestFile, i: number, o: LaneOptions): Lane {
  if ((o.keywordRule ?? true) && bt.palavra_chave_reembolso_cancelamento[i]) return "humana"
  if (bt.palavras_conhecidas[i] < o.knownCut) return "humana"
  const conf = bt.confianca[i]
  if (conf >= o.tauAuto && o.eligible.has(bt.classes[bt.prevista[i]])) return "automatica"
  if (conf >= o.tauAssist) return "assistida"
  return "humana"
}

export function summarize(bt: BacktestFile, o: LaneOptions): LaneSummary {
  const counts: Record<Lane, number> = { automatica: 0, assistida: 0, humana: 0 }
  let autoWrong = 0
  let assistTop2Right = 0
  let blockedByRules = 0
  for (let i = 0; i < bt.confianca.length; i++) {
    const lane = laneOf(bt, i, o)
    counts[lane]++
    if (lane === "automatica" && bt.prevista[i] !== bt.real[i]) autoWrong++
    if (lane === "assistida" && bt.top2_certo[i]) assistTop2Right++
    const keyword = (o.keywordRule ?? true) && bt.palavra_chave_reembolso_cancelamento[i]
    if (keyword || bt.palavras_conhecidas[i] < o.knownCut) blockedByRules++
  }
  return { total: bt.confianca.length, counts, autoWrong, assistTop2Right, blockedByRules }
}

export type Bin = { from: number; to: number; right: number; wrong: number }

// Tickets que passam pelas regras, agrupados pela confiança do modelo.
export function histogram(bt: BacktestFile, knownCut: number, width = 0.02): Bin[] {
  const start = 0.1
  const bins: Bin[] = []
  for (let from = start; from < 1 - 1e-9; from += width) {
    bins.push({ from: round(from), to: round(Math.min(1, from + width)), right: 0, wrong: 0 })
  }
  for (let i = 0; i < bt.confianca.length; i++) {
    if (bt.palavra_chave_reembolso_cancelamento[i] || bt.palavras_conhecidas[i] < knownCut) continue
    const k = Math.min(bins.length - 1, Math.max(0, Math.floor((bt.confianca[i] - start) / width)))
    if (bt.prevista[i] === bt.real[i]) bins[k].right++
    else bins[k].wrong++
  }
  return bins
}

function round(x: number) {
  return Math.round(x * 1000) / 1000
}
