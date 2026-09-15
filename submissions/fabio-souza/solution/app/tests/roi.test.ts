import { readFileSync } from "node:fs"
import { join } from "node:path"

import { describe, expect, it } from "vitest"

import { monthlySavings, type RoiResult, type RoiValues } from "@/lib/roi"

type Param = { valor: number }
const report = JSON.parse(
  readFileSync(join(__dirname, "..", "public", "data", "relatorio.json"), "utf8")
)
const roi = report.roi as {
  parametros: Record<keyof RoiValues, Param>
  base: RoiResult
  cenarios: Record<"pessimista" | "otimista", RoiResult & { parametros: RoiValues }>
}

const values = Object.fromEntries(
  Object.entries(roi.parametros).map(([k, p]) => [k, p.valor])
) as RoiValues

function expectSame(actual: RoiResult, expected: RoiResult) {
  for (const key of Object.keys(actual) as (keyof RoiResult)[]) {
    expect(actual[key]).toBeCloseTo(expected[key], 9)
  }
}

describe("ROI igual ao do Python (06_roi.py)", () => {
  it("cenário base", () => expectSame(monthlySavings(values), roi.base))

  it.each(["pessimista", "otimista"] as const)("cenário %s", (name) =>
    expectSame(monthlySavings(roi.cenarios[name].parametros), roi.cenarios[name])
  )

  it("com k = 4, a fila automática empata em 75% de precisão (erro E10)", () => {
    const r = monthlySavings({ ...values, precisao_auto: 0.75, multiplo_custo_erro: 4 })
    expect(r.min_liquidos_por_ticket_auto).toBeCloseTo(0, 12)
  })
})
