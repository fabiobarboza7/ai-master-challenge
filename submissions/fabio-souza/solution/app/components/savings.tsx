"use client"

import { useMemo, useState } from "react"

import { TableToggle, Tooltip, useWidth, type TooltipState } from "./charts"
import { num, pct, useData } from "./data"
import { monthlySavings, type RoiValues } from "@/lib/roi"
import { summarize } from "@/lib/triage/backtest"
import type { Thresholds } from "@/lib/triage/policy"

type Editable = {
  key: keyof RoiValues
  label: string
  unit: "min" | "x" | "tickets" | "%" | "R$"
  step: number
}

const EDITABLE: Editable[] = [
  { key: "tickets_por_mes", label: "Tickets por mês", unit: "tickets", step: 100 },
  { key: "fracao_reembolso_cancelamento", label: "Tickets de reembolso ou cancelamento", unit: "%", step: 1 },
  { key: "min_triagem_manual", label: "Tempo de uma triagem manual", unit: "min", step: 0.5 },
  { key: "multiplo_custo_erro", label: "Custo de um ticket na fila errada, em triagens", unit: "x", step: 1 },
  { key: "min_confirmacao_assistida", label: "Tempo para o atendente confirmar a sugestão", unit: "min", step: 0.25 },
  { key: "custo_hora_brl", label: "Custo por hora de atendente", unit: "R$", step: 5 },
]

const ORIGIN_LABEL: Record<string, string> = {
  BRIEF: "do brief",
  PREMISSA: "premissa",
  "PREMISSA (D5)": "premissa",
  "DATASET 1 (sintético)": "Dataset 1, sintético",
  "FABIO (D11)": "decisão do Fabio",
  MEDIDO: "medido no teste",
}

const brl = (x: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(x)

export function Savings({ thresholds, target }: { thresholds: Thresholds; target: number }) {
  const { model, backtest, report } = useData()
  const params = report.roi.parametros
  const [inputs, setInputs] = useState(() =>
    Object.fromEntries(EDITABLE.map((e) => [e.key, params[e.key].valor])) as Record<keyof RoiValues, number>
  )

  // Filas medidas no teste para a precisão escolhida; reembolso/cancelamento entra pela fração acima.
  const measured = useMemo(() => {
    const s = summarize(backtest, {
      ...thresholds,
      knownCut: model.politica.corte_palavras_conhecidas,
      keywordRule: false,
    })
    return {
      fila_auto: s.counts.automatica / s.total,
      precisao_auto: 1 - s.autoWrong / Math.max(1, s.counts.automatica),
      fila_assistida: s.counts.assistida / s.total,
      top2_assistida: s.assistTop2Right / Math.max(1, s.counts.assistida),
    }
  }, [backtest, model, thresholds])

  const values: RoiValues = {
    ...inputs,
    ...measured,
    horas_produtivas_por_fte_mes: params.horas_produtivas_por_fte_mes.valor,
  }
  const result = monthlySavings(values)

  const sensitivity = EDITABLE.filter((e) => params[e.key].faixa)
    .map((e) => {
      const [lo, hi] = params[e.key].faixa as [number, number]
      const hLo = monthlySavings({ ...values, [e.key]: lo }).horas_mes
      const hHi = monthlySavings({ ...values, [e.key]: hi }).horas_mes
      return { ...e, lo, hi, hLo, hHi }
    })
    .sort((a, b) => Math.abs(b.hHi - b.hLo) - Math.abs(a.hHi - a.hLo))

  const extreme = (pickMax: boolean) =>
    monthlySavings({
      ...values,
      ...Object.fromEntries(
        sensitivity.map((s) => [s.key, (s.hHi > s.hLo) === pickMax ? s.hi : s.lo])
      ),
    }).horas_mes

  return (
    <section id="economia" className="border-t border-rule">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <h2 className="max-w-3xl font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
          Quanto tempo isso devolve à operação
        </h2>
        <p className="mt-4 max-w-2xl text-ink-2">
          O tamanho e a precisão das filas vêm do teste. Os tempos são premissas até alguém cronometrar
          50 triagens: troque pelos números da sua operação.
        </p>

        <div className="mt-10 grid grid-cols-1 gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div>
            <p className="text-ink-2">Com precisão mínima de {pct(target, 0)} por ticket</p>
            <p className="font-heading text-6xl font-semibold">{num(result.horas_mes, 1)} h por mês</p>
            <p className="mt-2 text-lg">
              {brl(result.brl_mes)} por mês, ou {num(result.fte, 2)} pessoa em tempo integral
            </p>
            <p className="mt-2 text-ink-2">
              Entre {num(extreme(false), 1)} h e {num(extreme(true), 1)} h por mês, conforme as
              premissas ao lado.
            </p>
            <p className="mt-6 max-w-md border-l-4 border-rule pl-4 text-ink-2">
              A triagem automática sozinha não resolve a sobrecarga. Ela é um ganho seguro e rápido;
              os ganhos grandes dependem de medir onde o tempo vai, e hoje os dados não registram nem
              a abertura do ticket.
            </p>
          </div>

          <form className="grid gap-4" onSubmit={(e) => e.preventDefault()}>
            {EDITABLE.map((e) => {
              const p = params[e.key]
              const isPct = e.unit === "%"
              return (
                <div key={e.key} className="grid grid-cols-[minmax(0,1fr)_7.5rem] items-center gap-3">
                  <label htmlFor={e.key}>
                    {e.label}
                    <span className="block text-sm text-ink-3">{ORIGIN_LABEL[p.origem] ?? p.origem}</span>
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      id={e.key}
                      type="number"
                      min={0}
                      step={e.step}
                      value={isPct ? Math.round(inputs[e.key] * 1000) / 10 : inputs[e.key]}
                      onChange={(ev) => {
                        const v = Number(ev.target.value)
                        if (Number.isFinite(v)) setInputs({ ...inputs, [e.key]: isPct ? v / 100 : v })
                      }}
                      className="w-full rounded-md border border-axis bg-surface px-2 py-1.5 text-right tabular"
                    />
                    <span className="w-12 text-sm text-ink-2">{e.unit === "tickets" ? "" : e.unit}</span>
                  </div>
                </div>
              )
            })}
            <p className="text-sm text-ink-3">
              Medido no teste, sem a regra de reembolso (que entra pela fração acima):{" "}
              {pct(measured.fila_auto)} automáticos com {pct(measured.precisao_auto)} certos;{" "}
              {pct(measured.fila_assistida)} assistidos, com a certa entre 2 sugestões em{" "}
              {pct(measured.top2_assistida)}.
            </p>
          </form>
        </div>

        <h3 className="mt-16 font-heading text-2xl font-semibold">O que mais muda o resultado</h3>
        <p className="mt-2 max-w-2xl text-ink-2">
          Cada barra mostra as horas por mês com a premissa no mínimo e no máximo da faixa, mantendo as
          outras como estão. A linha marca o valor atual.
        </p>
        <Tornado rows={sensitivity} current={result.horas_mes} />

        <h3 className="mt-16 font-heading text-2xl font-semibold">Quantos tickets rotulados para chegar lá</h3>
        <p className="mt-2 max-w-2xl text-ink-2">
          O modelo foi treinado com tickets de TI de outra empresa e não serve para o seu suporte como
          está. Com os tickets da própria operação, a fila automática cresce assim:
        </p>
        <LearningCurve />

        <h3 className="mt-16 font-heading text-2xl font-semibold">Ganhos fora da triagem, medidos pelo volume</h3>
        <ul className="mt-4 grid max-w-3xl gap-4">
          <li className="border-l-4 border-rule pl-4">
            <p className="font-medium">
              Formulário para pedidos de compra: {num(report.roi.alavancas_adicionais.formulario_para_pedido_de_compra.horas_mes, 1)} h por mês, sem IA
            </p>
            <p className="text-ink-2">
              976 tickets do Dataset 2 são o mesmo pedido de alocação, 40% da categoria Compras. Um
              formulário integrado resolve na origem.
            </p>
          </li>
          <li className="border-l-4 border-rule pl-4">
            <p className="font-medium">
              Resposta sugerida a partir do ticket gêmeo: {num(report.roi.alavancas_adicionais.resposta_sugerida_por_ticket_gemeo.horas_mes, 1)} h por mês
            </p>
            <p className="text-ink-2">
              12,3% dos tickets têm um quase idêntico no histórico. Mostrar a resposta dada antes ajuda
              o atendente; fechar como duplicado continua sendo decisão humana.
            </p>
          </li>
        </ul>
      </div>
    </section>
  )
}

type TornadoRow = Editable & { lo: number; hi: number; hLo: number; hHi: number }

function Tornado({ rows, current }: { rows: TornadoRow[]; current: number }) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const rowH = 58
  const left = 40
  const right = 52
  const plotW = Math.max(120, width - left - right)
  const max = Math.max(current, ...rows.flatMap((r) => [r.hLo, r.hHi])) * 1.05
  const x = (v: number) => left + (Math.max(0, v) / max) * plotW
  const digits = (r: TornadoRow) => (r.unit === "min" ? 2 : 0)
  const fmtRange = (r: TornadoRow) =>
    r.unit === "%"
      ? `${pct(r.lo, 0)} a ${pct(r.hi, 0)}`
      : `${num(r.lo, digits(r))} a ${num(r.hi, digits(r))}${r.unit === "tickets" ? "" : ` ${r.unit}`}`

  return (
    <div ref={ref} className="mt-6 max-w-3xl">
      <svg width={width} height={rows.length * rowH} role="img" aria-label="Sensibilidade das horas economizadas a cada premissa">
        {rows.map((r, i) => {
          const y = i * rowH
          const a = Math.min(r.hLo, r.hHi)
          const b = Math.max(r.hLo, r.hHi)
          return (
            <g key={r.key}>
              {/* Nome da premissa numa linha própria: nunca disputa espaço com a barra, em qualquer largura. */}
              <text x={0} y={y + 16} className="fill-ink text-sm">
                {r.label} <tspan className="fill-ink-3">({fmtRange(r)})</tspan>
              </text>
              <rect x={x(a)} y={y + 28} width={Math.max(2, x(b) - x(a))} height={12} rx={4} fill="var(--lane-assistida)" />
              <text x={x(a) - 6} y={y + 38} textAnchor="end" className="fill-ink-2 text-xs tabular">{num(a, 1)}</text>
              <text x={x(b) + 6} y={y + 38} className="fill-ink-2 text-xs tabular">{num(b, 1)} h</text>
            </g>
          )
        })}
        <line x1={x(current)} x2={x(current)} y1={22} y2={rows.length * rowH - 12} stroke="var(--ink)" strokeWidth={2} />
      </svg>
      <TableToggle label="Ver como tabela">
        <table className="text-left tabular">
          <thead className="text-ink-2">
            <tr>
              <th className="py-1 pr-6 font-medium">Premissa</th>
              <th className="py-1 pr-6 font-medium">Faixa</th>
              <th className="py-1 pr-6 font-medium">Horas no mínimo</th>
              <th className="py-1 font-medium">Horas no máximo</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key} className="border-t border-rule">
                <td className="py-1 pr-6">{r.label}</td>
                <td className="py-1 pr-6">{fmtRange(r)}</td>
                <td className="py-1 pr-6">{num(r.hLo, 1)}</td>
                <td className="py-1">{num(r.hHi, 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableToggle>
    </div>
  )
}

function LearningCurve() {
  const { report } = useData()
  const points = report.curva_de_aprendizado
  const [ref, width] = useWidth<HTMLDivElement>()
  const [tip, setTip] = useState<TooltipState>(null)
  const margin = { top: 16, right: 48, bottom: 40, left: 44 }
  const height = 240
  const plotW = Math.max(200, width - margin.left - margin.right)
  const plotH = height - margin.top - margin.bottom
  const lx = (n: number) => Math.log10(n)
  const [x0, x1] = [lx(points[0].tickets_rotulados), lx(points[points.length - 1].tickets_rotulados)]
  const x = (n: number) => margin.left + ((lx(n) - x0) / (x1 - x0)) * plotW
  const y = (v: number) => margin.top + plotH - (v / 0.7) * plotH
  const path = points.map((p, i) => `${i ? "L" : "M"}${x(p.tickets_rotulados)},${y(p.cobertura_auto_media)}`).join("")
  const last = points[points.length - 1]
  // Rótulos do eixo só onde cabem: o último sempre, os outros a pelo menos 44 px de distância.
  const axisLabels = points.reduce<typeof points>((kept, p) => {
    const prev = kept[kept.length - 1]
    const fitsPrev = !prev || x(p.tickets_rotulados) - x(prev.tickets_rotulados) >= 44
    const fitsLast = p === last || x(last.tickets_rotulados) - x(p.tickets_rotulados) >= 44
    return fitsPrev && fitsLast ? [...kept, p] : kept
  }, [])

  return (
    <div ref={ref} className="relative mt-6">
      <svg width={width} height={height} role="img" aria-label="Fração automática por número de tickets rotulados">
        {[0, 0.2, 0.4, 0.6].map((t) => (
          <g key={t}>
            <line x1={margin.left} x2={margin.left + plotW} y1={y(t)} y2={y(t)} stroke="var(--rule)" />
            <text x={margin.left - 8} y={y(t)} dy="0.32em" textAnchor="end" className="fill-ink-3 text-xs tabular">{pct(t, 0)}</text>
          </g>
        ))}
        {axisLabels.map((p) => (
          <text key={p.tickets_rotulados} x={x(p.tickets_rotulados)} y={margin.top + plotH + 18} textAnchor="middle" className="fill-ink-3 text-xs tabular">
            {p.tickets_rotulados >= 1000 ? `${num(p.tickets_rotulados / 1000, 0)} mil` : num(p.tickets_rotulados)}
          </text>
        ))}
        <text x={margin.left + plotW / 2} y={height - 4} textAnchor="middle" className="fill-ink-2 text-sm">
          Tickets rotulados para treinar (escala logarítmica)
        </text>
        <path d={path} fill="none" stroke="var(--lane-automatica)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        {points.map((p) => (
          <g key={p.tickets_rotulados}>
            <circle cx={x(p.tickets_rotulados)} cy={y(p.cobertura_auto_media)} r={4} fill="var(--lane-automatica)" stroke="var(--paper)" strokeWidth={2} />
            <circle
              cx={x(p.tickets_rotulados)}
              cy={y(p.cobertura_auto_media)}
              r={14}
              fill="transparent"
              onPointerMove={() =>
                setTip({
                  x: x(p.tickets_rotulados),
                  y: y(p.cobertura_auto_media),
                  lines: [
                    { value: pct(p.cobertura_auto_media, 0), label: "na fila automática" },
                    { value: pct(p.precisao_auto_media), label: "certos" },
                    { value: num(p.tickets_rotulados), label: "tickets rotulados" },
                  ],
                })
              }
              onPointerLeave={() => setTip(null)}
            />
          </g>
        ))}
        <text x={x(last.tickets_rotulados) + 8} y={y(last.cobertura_auto_media)} dy="0.32em" className="fill-ink text-sm tabular">
          {pct(last.cobertura_auto_media, 0)}
        </text>
      </svg>
      <Tooltip state={tip} />
      <TableToggle label="Ver como tabela">
        <table className="text-left tabular">
          <thead className="text-ink-2">
            <tr>
              <th className="py-1 pr-6 font-medium">Tickets rotulados</th>
              <th className="py-1 pr-6 font-medium">Na fila automática</th>
              <th className="py-1 font-medium">Certos na fila automática</th>
            </tr>
          </thead>
          <tbody>
            {points.map((p) => (
              <tr key={p.tickets_rotulados} className="border-t border-rule">
                <td className="py-1 pr-6">{num(p.tickets_rotulados)}</td>
                <td className="py-1 pr-6">{pct(p.cobertura_auto_media)}</td>
                <td className="py-1">{pct(p.precisao_auto_media)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableToggle>
    </div>
  )
}
