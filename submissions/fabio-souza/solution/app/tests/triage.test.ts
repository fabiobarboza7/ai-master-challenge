import { readFileSync } from "node:fs"
import { join } from "node:path"

import { describe, expect, it } from "vitest"

import { summarize, type BacktestFile } from "@/lib/triage/backtest"
import { prepareModel, type ModelFile } from "@/lib/triage/model"
import { defaultThresholds, route, type Lane, type Reason } from "@/lib/triage/policy"
import { knownShare, normalize, tokens } from "@/lib/triage/text"

const data = (name: string) =>
  JSON.parse(readFileSync(join(__dirname, "..", "public", "data", name), "utf8"))

const model = prepareModel(data("model.json") as ModelFile)

type ParityCase = {
  origem: string
  texto: string
  tipo: string | null
  normalizado: string
  palavras_conhecidas: number
  probabilidades: number[]
  fila: Lane
  motivo: Reason
}

describe("paridade com o Python (07_exportar_app.py)", () => {
  const cases = data("paridade.json") as ParityCase[]

  it("tem casos de todas as filas e de todos os motivos", () => {
    expect(new Set(cases.map((c) => c.fila))).toEqual(
      new Set(["automatica", "assistida", "humana"])
    )
    expect(new Set(cases.map((c) => c.motivo)).size).toBe(5)
  })

  it.each(cases.map((c, i) => [i, c.origem, c] as const))(
    "caso %i (%s): mesmo texto, mesmas probabilidades, mesma fila",
    (_, __, c) => {
      const decision = route(model, c.texto, c.tipo)
      expect(decision.normalized).toBe(c.normalizado)
      expect(decision.knownShare).toBe(c.palavras_conhecidas)
      const maxDiff = Math.max(
        ...decision.probabilities.map((p, k) => Math.abs(p - c.probabilidades[k]))
      )
      expect(maxDiff).toBeLessThan(1e-9)
      expect(decision.lane).toBe(c.fila)
      expect(decision.reason).toBe(c.motivo)
    }
  )
})

describe("regras de risco", () => {
  it("reembolso vai para humano mesmo com texto que o modelo classifica com confiança", () => {
    const text = "laptop screen broken need replacement asap"
    expect(route(model, text, null).lane).not.toBe("humana")
    expect(route(model, text, "Refund request")).toMatchObject({
      lane: "humana",
      reason: "reembolso_cancelamento",
    })
  })

  it("texto fora do domínio do modelo (português) vai para humano", () => {
    expect(route(model, "Não consigo acessar minha conta desde ontem", null).reason).toBe(
      "fora_do_dominio"
    )
  })

  it("acesso e RH podem ser roteados, mas a execução é sempre humana (decisão D10)", () => {
    const decision = route(model, "please grant access to shared folder for new employee", null)
    expect(model.politica.execucao_sempre_humana).toContain("Access")
    expect(decision.executionAlwaysHuman).toBe(
      model.politica.execucao_sempre_humana.includes(decision.ranking[0].category)
    )
  })
})

describe("texto (erro E9)", () => {
  it("descarta fragmentos de uma letra como o tokenizador do scikit-learn", () => {
    expect(tokens(normalize("I'm having an issue with the {product_purchased}."))).toEqual([
      "having",
      "an",
      "issue",
      "with",
      "the",
    ])
  })

  it("fração de palavras conhecidas de texto vazio é zero", () => {
    expect(knownShare("", model.index)).toBe(0)
  })
})

describe("backtest dos 7.026 tickets de teste", () => {
  const bt = data("backtest.json") as BacktestFile
  const thresholds = defaultThresholds(model)
  const summary = summarize(bt, {
    ...thresholds,
    knownCut: model.politica.corte_palavras_conhecidas,
  })

  it("reproduz exatamente as filas calculadas no Python", () => {
    expect(summary.total).toBe(7026)
    expect(summary.counts).toEqual(bt.referencia_python.filas)
  })

  it("sem a regra por palavra-chave, reproduz as filas medidas usadas no ROI do Python", () => {
    const roi = data("relatorio.json").roi.parametros
    const s = summarize(bt, {
      ...thresholds,
      knownCut: model.politica.corte_palavras_conhecidas,
      keywordRule: false,
    })
    expect(s.counts.automatica / s.total).toBeCloseTo(roi.fila_auto.valor, 12)
    expect(1 - s.autoWrong / s.counts.automatica).toBeCloseTo(roi.precisao_auto.valor, 12)
    expect(s.counts.assistida / s.total).toBeCloseTo(roi.fila_assistida.valor, 12)
    expect(s.assistTop2Right / s.counts.assistida).toBeCloseTo(roi.top2_assistida.valor, 12)
  })

  it("mantém a precisão da fila automática acima de 96%", () => {
    expect(1 - summary.autoWrong / summary.counts.automatica).toBeGreaterThan(0.96)
  })
})
