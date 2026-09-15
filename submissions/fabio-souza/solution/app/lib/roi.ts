// Espelho de solution/analysis/roi.py (o teste confere contra a saída do Python).

export type RoiValues = {
  tickets_por_mes: number
  fracao_reembolso_cancelamento: number
  fila_auto: number
  precisao_auto: number
  fila_assistida: number
  top2_assistida: number
  min_triagem_manual: number
  multiplo_custo_erro: number
  min_confirmacao_assistida: number
  custo_hora_brl: number
  horas_produtivas_por_fte_mes: number
}

export type RoiResult = {
  tickets_elegiveis_mes: number
  tickets_auto_mes: number
  tickets_assistidos_mes: number
  min_liquidos_por_ticket_auto: number
  min_liquidos_por_ticket_assistido: number
  horas_mes: number
  horas_mes_fila_auto: number
  horas_mes_fila_assistida: number
  fte: number
  brl_mes: number
  brl_ano: number
}

export function monthlySavings(v: RoiValues): RoiResult {
  const eligible = v.tickets_por_mes * (1 - v.fracao_reembolso_cancelamento)
  const t = v.min_triagem_manual
  // Todo ticket automático pula a triagem (ganha t); os errados custam k x t na fila errada.
  const netAuto = t - (1 - v.precisao_auto) * v.multiplo_custo_erro * t
  const netAssist =
    v.top2_assistida * (t - v.min_confirmacao_assistida) -
    (1 - v.top2_assistida) * v.min_confirmacao_assistida
  const minutesAuto = eligible * v.fila_auto * netAuto
  const minutesAssist = eligible * v.fila_assistida * netAssist
  const hours = (minutesAuto + minutesAssist) / 60
  return {
    tickets_elegiveis_mes: eligible,
    tickets_auto_mes: eligible * v.fila_auto,
    tickets_assistidos_mes: eligible * v.fila_assistida,
    min_liquidos_por_ticket_auto: netAuto,
    min_liquidos_por_ticket_assistido: netAssist,
    horas_mes: hours,
    horas_mes_fila_auto: minutesAuto / 60,
    horas_mes_fila_assistida: minutesAssist / 60,
    fte: hours / v.horas_produtivas_por_fte_mes,
    brl_mes: hours * v.custo_hora_brl,
    brl_ano: 12 * hours * v.custo_hora_brl,
  }
}
