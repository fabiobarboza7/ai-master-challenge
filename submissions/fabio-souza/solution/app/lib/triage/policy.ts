import { predict, type Model } from "./model"
import { knownShare, normalize } from "./text"

export type Lane = "automatica" | "assistida" | "humana"

export type Reason =
  | "reembolso_cancelamento"
  | "fora_do_dominio"
  | "confianca_alta"
  | "confianca_media"
  | "confianca_baixa"

export type Thresholds = {
  tauAuto: number
  tauAssist: number
  eligible: ReadonlySet<string>
}

export type Decision = {
  lane: Lane
  reason: Reason
  normalized: string
  knownShare: number
  probabilities: number[]
  ranking: { category: string; probability: number }[]
  evidence: { term: string; weight: number }[]
  riskByType: boolean
  riskByText: boolean
  executionAlwaysHuman: boolean
}

export function defaultThresholds(model: Model): Thresholds {
  return {
    tauAuto: model.politica.tau_auto,
    tauAssist: model.politica.tau_assist,
    eligible: new Set(model.politica.categorias_elegiveis),
  }
}

// Ordem das regras (espelho de lane() em 07_exportar_app.py):
// 1. reembolso/cancelamento vai para humano, qualquer que seja a confiança (decisão D3 do Fabio);
// 2. texto que o modelo não conhece vai para humano (trava de domínio);
// 3. confiança >= corte automático e categoria elegível: fila automática;
// 4. confiança >= corte assistido: atendente confirma 1 de 2 sugestões;
// 5. o resto vai para triagem humana.
export function route(
  model: Model,
  rawText: string,
  ticketType: string | null,
  thresholds: Thresholds = defaultThresholds(model)
): Decision {
  const normalized = normalize(rawText)
  const { probabilities, evidence } = predict(model, normalized)
  const share = knownShare(normalized, model.index)
  const ranking = probabilities
    .map((probability, k) => ({ category: model.classes[k], probability }))
    .sort((a, b) => b.probability - a.probability)
  const top = ranking[0]

  const riskByType =
    ticketType !== null && model.politica.tipos_reembolso_cancelamento.includes(ticketType)
  const riskByText = new RegExp(model.politica.padrao_reembolso_cancelamento, "i").test(rawText)

  let lane: Lane
  let reason: Reason
  if (riskByType || riskByText) {
    lane = "humana"
    reason = "reembolso_cancelamento"
  } else if (share < model.politica.corte_palavras_conhecidas) {
    lane = "humana"
    reason = "fora_do_dominio"
  } else if (top.probability >= thresholds.tauAuto && thresholds.eligible.has(top.category)) {
    lane = "automatica"
    reason = "confianca_alta"
  } else if (top.probability >= thresholds.tauAssist) {
    lane = "assistida"
    reason = "confianca_media"
  } else {
    lane = "humana"
    reason = "confianca_baixa"
  }

  return {
    lane,
    reason,
    normalized,
    knownShare: share,
    probabilities,
    ranking,
    evidence,
    riskByType,
    riskByText,
    executionAlwaysHuman: model.politica.execucao_sempre_humana.includes(top.category),
  }
}
