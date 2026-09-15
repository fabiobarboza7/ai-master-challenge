"use client"

import { useMemo, useState } from "react"

import { niceTicks, TableToggle, Tooltip, useWidth, type TooltipState } from "./charts"
import { LANE_NAMES, num, pct, useData } from "./data"
import { laneOf, summarize, type LaneOptions } from "@/lib/triage/backtest"
import type { Preset } from "@/lib/triage/model"
import type { Lane, Thresholds } from "@/lib/triage/policy"

const BIN = 0.02
const START = 0.1
const LANES: Lane[] = ["humana", "assistida", "automatica"]
const FILL: Record<Lane | "errado", string> = {
  humana: "var(--lane-humana)",
  assistida: "var(--lane-assistida)",
  automatica: "var(--lane-automatica)",
  errado: "var(--wrong)",
}

type Column = { from: number; to: number; right: Record<Lane, number>; wrong: number; total: number }

export function SortingBoard({
  presets,
  target,
  onTarget,
  thresholds,
}: {
  presets: Preset[]
  target: number
  onTarget: (t: number) => void
  thresholds: Thresholds
}) {
  const { model, backtest: bt } = useData()
  const options: LaneOptions = { ...thresholds, knownCut: model.politica.corte_palavras_conhecidas }
  const summary = summarize(bt, options)

  const columns = useMemo(() => {
    const cols: Column[] = []
    for (let k = 0; START + k * BIN < 1 - 1e-9; k++) {
      const from = Math.round((START + k * BIN) * 100) / 100
      cols.push({ from, to: Math.round((from + BIN) * 100) / 100, right: { humana: 0, assistida: 0, automatica: 0 }, wrong: 0, total: 0 })
    }
    for (let i = 0; i < bt.confianca.length; i++) {
      const keyword = bt.palavra_chave_reembolso_cancelamento[i]
      if (keyword || bt.palavras_conhecidas[i] < options.knownCut) continue
      const k = Math.min(cols.length - 1, Math.floor((bt.confianca[i] - START) / BIN + 1e-9))
      const col = cols[k]
      col.total++
      if (bt.prevista[i] !== bt.real[i]) col.wrong++
      else col.right[laneOf(bt, i, options)]++
    }
    return cols
    // options muda junto com thresholds
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bt, thresholds])

  return (
    <section id="teste" className="border-t border-rule bg-surface">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <h2 className="max-w-3xl font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
          O mesmo critério em {num(summary.total)} tickets reais que o modelo nunca viu
        </h2>
        <p className="mt-4 max-w-2xl text-ink-2">
          Cada coluna junta os tickets pela confiança do modelo. A cor mostra a fila em que cada um
          cai; em vermelho, os que ele classificaria na categoria errada. Os cortes de cada opção
          foram escolhidos na validação, sem olhar este teste.
        </p>

        <fieldset className="mt-8">
          <legend className="font-medium">Precisão mínima exigida de cada ticket da fila automática</legend>
          <div className="mt-3 inline-flex rounded-md border border-axis p-1">
            {presets.map((p) => (
              <label
                key={p.alvo}
                className="cursor-pointer rounded px-4 py-1.5 has-checked:bg-ink has-checked:text-paper has-focus-visible:outline-2 has-focus-visible:outline-accent"
              >
                <input
                  type="radio"
                  name="alvo"
                  className="sr-only"
                  checked={p.alvo === target}
                  onChange={() => onTarget(p.alvo)}
                />
                {pct(p.alvo, 0)}
                {p.alvo === 0.9 ? " (recomendada)" : ""}
              </label>
            ))}
          </div>
        </fieldset>

        <LaneTiles summary={summary} />
        <Chart columns={columns} thresholds={thresholds} />
        <p className="mt-2 text-sm text-ink-2">
          Fora do gráfico: {num(summary.blockedByRules)} tickets foram direto para uma pessoa pelas
          regras de risco (texto fora do domínio ou palavra de reembolso/cancelamento), qualquer que
          fosse a confiança.
        </p>

        <TableToggle label="Ver o gráfico como tabela">
          <table className="w-full max-w-xl text-left tabular">
            <thead className="text-ink-2">
              <tr>
                <th className="py-1 pr-4 font-medium">Confiança</th>
                <th className="py-1 pr-4 font-medium">Classificados certo</th>
                <th className="py-1 pr-4 font-medium">Classificados errado</th>
              </tr>
            </thead>
            <tbody>
              {columns.filter((c) => c.total > 0).map((c) => (
                <tr key={c.from} className="border-t border-rule">
                  <td className="py-1 pr-4">{pct(c.from, 0)} a {pct(c.to, 0)}</td>
                  <td className="py-1 pr-4">{num(c.total - c.wrong)}</td>
                  <td className="py-1 pr-4">{num(c.wrong)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableToggle>
      </div>
    </section>
  )
}

function LaneTiles({ summary: s }: { summary: ReturnType<typeof summarize> }) {
  const tiles: { lane: Lane; detail: string }[] = [
    {
      lane: "automatica",
      detail: `${pct(1 - s.autoWrong / Math.max(1, s.counts.automatica))} na categoria certa (${num(s.autoWrong)} erros)`,
    },
    {
      lane: "assistida",
      detail: `a categoria certa está entre as 2 sugestões em ${pct(s.assistTop2Right / Math.max(1, s.counts.assistida))}`,
    },
    { lane: "humana", detail: `inclui ${num(s.blockedByRules)} tickets barrados pelas regras de risco` },
  ]
  return (
    <dl className="mt-10 grid gap-6 sm:grid-cols-3">
      {tiles.map(({ lane, detail }) => (
        <div key={lane} className="border-l-4 pl-4" style={{ borderColor: FILL[lane] }}>
          <dt className="text-ink-2">{LANE_NAMES[lane]}</dt>
          <dd className="font-heading text-4xl font-semibold">{pct(s.counts[lane] / s.total, 0)}</dd>
          <dd className="text-sm text-ink-2">
            {num(s.counts[lane])} tickets; {detail}
          </dd>
        </div>
      ))}
    </dl>
  )
}

function Chart({ columns, thresholds }: { columns: Column[]; thresholds: Thresholds }) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const [tip, setTip] = useState<TooltipState>(null)
  const margin = { top: 46, right: 12, bottom: 44, left: 48 }
  const height = 300
  const plotW = Math.max(200, width - margin.left - margin.right)
  const plotH = height - margin.top - margin.bottom

  // A última faixa (98% a 100%) sozinha tem ~1.500 tickets e achataria o resto, onde estão os erros.
  // O eixo vai até a segunda coluna mais alta; a que passa do topo é cortada e ganha o total como rótulo.
  const totals = columns.map((c) => c.total).sort((a, b) => b - a)
  const ticks = niceTicks(totals[1] * 1.1)
  const yMax = ticks[ticks.length - 1]
  const x = (v: number) => margin.left + ((v - START) / (1 - START)) * plotW
  const y = (v: number) => margin.top + plotH - (Math.min(v, yMax) / yMax) * plotH
  const tallest = columns.reduce((a, b) => (b.total > a.total ? b : a))
  const narrow = width < 560
  const slot = plotW / columns.length
  const barW = Math.min(24, Math.max(2, slot - 2))

  return (
    <div ref={ref} className="relative mt-10">
      <svg width={width} height={height} role="img" aria-label="Tickets de teste por faixa de confiança, coloridos pela fila">
        {ticks.map((t) => (
          <g key={t}>
            <line x1={margin.left} x2={margin.left + plotW} y1={y(t)} y2={y(t)} stroke="var(--rule)" />
            <text x={margin.left - 8} y={y(t)} dy="0.32em" textAnchor="end" className="fill-ink-3 text-xs tabular">
              {num(t)}
            </text>
          </g>
        ))}
        {[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1].map((t) => (
          <text key={t} x={x(t)} y={margin.top + plotH + 18} textAnchor="middle" className="fill-ink-3 text-xs tabular">
            {pct(t, 0)}
          </text>
        ))}
        <text x={margin.left + plotW / 2} y={height - 4} textAnchor="middle" className="fill-ink-2 text-sm">
          Confiança do modelo na categoria mais provável
        </text>

        {columns.map((c) => {
          const cx = x(c.from) + (slot - barW) / 2
          // Os erros ficam na base: alinhados na mesma linha, dá para comparar entre colunas (e não somem nas cortadas).
          const segments: { key: string; value: number; fill: string }[] = [
            { key: "errado", value: c.wrong, fill: FILL.errado },
            ...LANES.map((l) => ({ key: l, value: c.right[l], fill: FILL[l] })),
          ].filter((s) => s.value > 0)
          let acc = 0
          return (
            <g key={c.from}>
              {segments.map((s, i) => {
                const y0 = y(acc)
                acc += s.value
                const y1 = y(acc)
                const gap = i < segments.length - 1 ? 2 : 0
                const h = Math.max(0, y0 - y1 - gap)
                const isTop = i === segments.length - 1
                return (
                  <path
                    key={s.key}
                    d={isTop ? roundedTop(cx, y1, barW, h, Math.min(4, h)) : `M${cx},${y1 + gap}h${barW}v${h}h${-barW}z`}
                    fill={s.fill}
                  />
                )
              })}
              {c === tallest && c.total > yMax && (
                <>
                  <line x1={cx - 2} x2={cx + barW + 2} y1={margin.top + 14} y2={margin.top + 8} stroke="var(--surface)" strokeWidth={3} />
                  <text x={cx - 6} y={margin.top + 12} textAnchor="end" className="fill-ink-2 text-xs tabular">
                    {num(c.total)}{narrow ? "" : " tickets"}
                  </text>
                </>
              )}
              <rect
                x={x(c.from)}
                y={margin.top}
                width={slot}
                height={plotH}
                fill="transparent"
                onPointerMove={() =>
                  setTip({
                    x: x(c.from) + slot / 2,
                    y: margin.top + 8,
                    lines: [
                      { value: `${pct(c.from, 0)} a ${pct(c.to, 0)}`, label: "confiança" },
                      { value: num(c.total - c.wrong), label: "classificados certo" },
                      { value: num(c.wrong), label: "classificados errado" },
                    ],
                  })
                }
                onPointerLeave={() => setTip(null)}
              />
            </g>
          )
        })}

        {[
          { v: thresholds.tauAssist, label: `${narrow ? "confirma" : "atendente confirma a partir de"} ${pct(thresholds.tauAssist, 0)}` },
          { v: thresholds.tauAuto, label: `${narrow ? "automática" : "automática a partir de"} ${pct(thresholds.tauAuto, 0)}` },
        ].map((t, i) => (
          <g key={t.label} pointerEvents="none">
            <line x1={x(t.v)} x2={x(t.v)} y1={margin.top - (i === 1 ? 6 : 22)} y2={margin.top + plotH} stroke="var(--ink)" strokeWidth={2} />
            <text
              x={x(t.v) + (i === 1 ? -6 : 6)}
              y={margin.top - (i === 1 ? 12 : 28)}
              textAnchor={i === 1 ? "end" : "start"}
              className="fill-ink text-xs"
            >
              {t.label}
            </text>
          </g>
        ))}
        <line x1={margin.left} x2={margin.left + plotW} y1={margin.top + plotH} y2={margin.top + plotH} stroke="var(--axis)" />
      </svg>
      <Tooltip state={tip} />

      <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-2">
        {LANES.map((l) => (
          <li key={l} className="flex items-center gap-2">
            <span className="inline-block size-3 rounded-sm" style={{ background: FILL[l] }} aria-hidden />
            {LANE_NAMES[l]}, classificado certo
          </li>
        ))}
        <li className="flex items-center gap-2">
          <span className="inline-block size-3 rounded-sm" style={{ background: FILL.errado }} aria-hidden />
          Classificado na categoria errada
        </li>
      </ul>
    </div>
  )
}

function roundedTop(x: number, y: number, w: number, h: number, r: number) {
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}z`
}
