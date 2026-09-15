"use client"

import { createContext, useContext, useEffect, useState } from "react"

import type { BacktestFile } from "@/lib/triage/backtest"
import { prepareModel, type Model, type ModelFile } from "@/lib/triage/model"

export type Example = {
  origem: string
  texto: string
  tipo: string | null
  categoria_real: string | null
  sorteado_na_fila: string | null
}

type Param = { valor: number; faixa?: [number, number]; origem: string; nota: string }

export type Report = {
  roi: {
    parametros: Record<string, Param>
    base: { horas_mes: number }
    alavancas_adicionais: Record<string, { horas_mes: number; nota: string; origem_volume: string }>
  }
  curva_de_aprendizado: {
    tickets_rotulados: number
    cobertura_auto_media: number
    precisao_auto_media: number
  }[]
  transferencia: {
    trava_de_dominio: {
      dataset1_barrados: number
      dataset1_fila_auto_com_trava: number
    }
    dataset1_descricoes: { fila_auto: number }
  }
}

export type AppData = {
  model: Model
  backtest: BacktestFile
  examples: Example[]
  report: Report
}

const DataContext = createContext<AppData | null>(null)

async function load<T>(name: string): Promise<T> {
  const res = await fetch(`data/${name}`)
  if (!res.ok) throw new Error(`Não foi possível carregar data/${name} (HTTP ${res.status}).`)
  return res.json() as Promise<T>
}

export function DataProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<AppData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      load<ModelFile>("model.json"),
      load<BacktestFile>("backtest.json"),
      load<Example[]>("exemplos.json"),
      load<Report>("relatorio.json"),
    ])
      .then(([model, backtest, examples, report]) =>
        setData({ model: prepareModel(model), backtest, examples, report })
      )
      .catch((e: Error) => setError(e.message))
  }, [])

  if (error) {
    return (
      <p role="alert" className="mx-auto max-w-3xl px-4 py-16 text-ink">
        {error} Rode <code>python 07_exportar_app.py</code> em <code>solution/analysis</code> para
        gerar os arquivos de dados.
      </p>
    )
  }
  if (!data) {
    return (
      <p className="mx-auto max-w-3xl px-4 py-16 text-ink-2" aria-live="polite">
        Carregando o modelo (1,5 MB)…
      </p>
    )
  }
  return <DataContext.Provider value={data}>{children}</DataContext.Provider>
}

export function useData(): AppData {
  const data = useContext(DataContext)
  if (!data) throw new Error("useData precisa estar dentro de DataProvider")
  return data
}

export const pct = (x: number, digits = 1) =>
  new Intl.NumberFormat("pt-BR", {
    style: "percent",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(x)

export const num = (x: number, digits = 0) =>
  new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(x)

export const LANE_NAMES = {
  automatica: "Fila automática",
  assistida: "Atendente confirma",
  humana: "Triagem humana",
} as const
