"use client"

import { useMemo, useState } from "react"

import { DataProvider, useData } from "./data"
import { Savings } from "./savings"
import { SortingBoard } from "./sorting-board"
import { TriageDesk } from "./triage-desk"
import type { Preset } from "@/lib/triage/model"
import type { Thresholds } from "@/lib/triage/policy"

export function Prototype() {
  return (
    <DataProvider>
      <Sections />
    </DataProvider>
  )
}

function Sections() {
  const { model } = useData()
  const presets = model.politica.presets
  const [target, setTarget] = useState(model.politica.precisao_alvo_por_ticket)
  const preset = presets.find((p) => p.alvo === target) ?? presets[0]
  const thresholds = useMemo(() => toThresholds(preset), [preset])

  return (
    <>
      <TriageDesk thresholds={thresholds} target={target} />
      <SortingBoard presets={presets} target={target} onTarget={setTarget} thresholds={thresholds} />
      <Savings thresholds={thresholds} target={target} />
    </>
  )
}

function toThresholds(p: Preset): Thresholds {
  return { tauAuto: p.tau_auto, tauAssist: p.tau_assist, eligible: new Set(p.categorias_elegiveis) }
}
