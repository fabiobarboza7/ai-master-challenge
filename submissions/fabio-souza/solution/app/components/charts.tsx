"use client"

import { useEffect, useRef, useState } from "react"

// Largura do contêiner, para os gráficos SVG ocuparem o espaço disponível sem distorcer texto.
export function useWidth<T extends HTMLElement>(fallback = 720) {
  const ref = useRef<T>(null)
  const [width, setWidth] = useState(fallback)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    observer.observe(el)
    return () => observer.disconnect()
  }, [])
  return [ref, width] as const
}

export function niceTicks(max: number, count = 4): number[] {
  if (max <= 0) return [0]
  const raw = max / count
  const magnitude = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= raw) ?? raw
  const ticks = []
  for (let v = 0; v <= max + 1e-9; v += step) ticks.push(Math.round(v * 1e6) / 1e6)
  return ticks
}

export type TooltipState = { x: number; y: number; lines: { value: string; label: string }[] } | null

// Valor primeiro, rótulo depois: quem passa o mouse já sabe a série e quer o número.
export function Tooltip({ state }: { state: TooltipState }) {
  if (!state) return null
  return (
    <div
      role="status"
      className="pointer-events-none absolute z-10 min-w-40 rounded-md border border-rule bg-surface px-3 py-2 text-sm shadow-sm"
      style={{ left: state.x, top: state.y, transform: "translate(-50%, calc(-100% - 10px))" }}
    >
      {state.lines.map((line, i) => (
        <div key={i} className="flex items-baseline justify-between gap-4">
          <span className="font-semibold text-ink tabular">{line.value}</span>
          <span className="text-ink-2">{line.label}</span>
        </div>
      ))}
    </div>
  )
}

export function TableToggle({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <details className="mt-4 text-sm">
      <summary className="cursor-pointer text-accent underline-offset-4 hover:underline">{label}</summary>
      <div className="mt-3 overflow-x-auto">{children}</div>
    </details>
  )
}
