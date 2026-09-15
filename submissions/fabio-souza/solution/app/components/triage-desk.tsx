"use client"

import { CircleArrowDown, CircleCheck, CircleMinus, UserRound } from "lucide-react"
import { useDeferredValue, useMemo, useState } from "react"

import { LANE_NAMES, pct, useData, type Example } from "./data"
import { route, type Decision, type Thresholds } from "@/lib/triage/policy"

const TICKET_TYPES = [
  { value: "", label: "Não informado" },
  { value: "Refund request", label: "Reembolso" },
  { value: "Cancellation request", label: "Cancelamento" },
  { value: "Technical issue", label: "Problema técnico" },
  { value: "Billing inquiry", label: "Dúvida de cobrança" },
  { value: "Product inquiry", label: "Dúvida sobre produto" },
]

// Escritos para exercitar as regras de risco; não fazem parte dos datasets.
const WRITTEN: Example[] = [
  {
    origem: "Escrito para testar a regra de reembolso",
    texto: "laptop screen broken need replacement asap, and please refund the delivery fee",
    tipo: null,
    categoria_real: null,
    sorteado_na_fila: null,
  },
  {
    origem: "Escrito para testar texto fora do domínio",
    texto: "Não consigo acessar minha conta desde ontem, já tentei trocar a senha",
    tipo: null,
    categoria_real: null,
    sorteado_na_fila: null,
  },
]

export function TriageDesk({ thresholds, target }: { thresholds: Thresholds; target: number }) {
  const { model, examples } = useData()
  const [picked, setPicked] = useState<Example>(examples[0])
  const [text, setText] = useState(examples[0].texto)
  const [ticketType, setTicketType] = useState("")
  const deferredText = useDeferredValue(text)

  const decision = useMemo(
    () => route(model, deferredText, ticketType || null, thresholds),
    [model, deferredText, ticketType, thresholds]
  )
  const truth = picked.texto === text ? picked.categoria_real : null

  const choose = (e: Example) => {
    setPicked(e)
    setText(e.texto)
    setTicketType(e.tipo ?? "")
  }

  const fromTest = examples.filter((e) => e.origem.startsWith("Dataset 2"))
  const fromDs1 = examples.filter((e) => e.origem === "Dataset 1")

  return (
    <section id="rotear" className="mx-auto max-w-6xl px-4 pt-10 pb-20 sm:px-6">
      <h1 className="max-w-3xl font-heading text-4xl leading-[1.05] font-semibold tracking-tight sm:text-5xl">
        Para onde vai este ticket?
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-ink-2">
        Cole um ticket de suporte. O modelo decide se ele segue direto para a fila certa, se um
        atendente confirma a sugestão ou se precisa de triagem humana, e mostra o motivo.
      </p>

      <div className="mt-10 grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <div>
          <label htmlFor="ticket" className="block font-medium">
            Texto do ticket
          </label>
          <textarea
            id="ticket"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={7}
            className="mt-2 w-full resize-y rounded-md border border-axis bg-surface p-3 leading-relaxed text-ink"
          />
          <label htmlFor="tipo" className="mt-4 block font-medium">
            Tipo informado pelo cliente
          </label>
          <select
            id="tipo"
            value={ticketType}
            onChange={(e) => setTicketType(e.target.value)}
            className="mt-2 w-full rounded-md border border-axis bg-surface p-2.5 text-ink sm:w-72"
          >
            {TICKET_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>

          <ExamplePicker title="Sorteados do teste (tickets reais de TI)" items={fromTest} onPick={choose} active={picked} />
          <ExamplePicker title="Sorteados do Dataset 1 (suporte ao consumidor)" items={fromDs1} onPick={choose} active={picked} />
          <ExamplePicker title="Para testar as regras" items={WRITTEN} onPick={choose} active={picked} />
        </div>

        <RoutingSlip decision={decision} thresholds={thresholds} target={target} truth={truth} />
      </div>
    </section>
  )
}

function ExamplePicker({
  title,
  items,
  onPick,
  active,
}: {
  title: string
  items: Example[]
  onPick: (e: Example) => void
  active: Example
}) {
  return (
    <div className="mt-6">
      <p className="text-sm text-ink-2">{title}</p>
      <ul className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
        {items.map((e) => (
          <li key={e.texto}>
            <button
              type="button"
              onClick={() => onPick(e)}
              aria-pressed={active === e}
              className="w-full truncate rounded-full border border-axis px-3 py-1 text-left text-sm text-ink hover:border-accent aria-pressed:border-accent aria-pressed:bg-surface"
            >
              {e.texto || "(vazio)"}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

const LANE_BAR = {
  automatica: "bg-lane-automatica",
  assistida: "bg-lane-assistida",
  humana: "bg-lane-humana",
} as const

type Step = { state: "passou" | "decidiu" | "nao_avaliado"; text: string }

function steps(d: Decision, t: Thresholds, cut: number, labels: Record<string, string>): Step[] {
  const top = d.ranking[0]
  const conf = pct(top.probability, 0)
  const risk = d.reason === "reembolso_cancelamento"
  const outside = d.reason === "fora_do_dominio"
  const auto = d.lane === "automatica"
  const why = d.riskByType ? "pelo tipo informado" : "por uma palavra no texto"
  return [
    risk
      ? { state: "decidiu", text: `Fala de reembolso ou cancelamento (${why}). Vai para uma pessoa, qualquer que seja a confiança.` }
      : { state: "passou", text: "Não fala de reembolso nem de cancelamento." },
    risk
      ? { state: "nao_avaliado", text: "Vocabulário conhecido pelo modelo." }
      : outside
        ? { state: "decidiu", text: `O modelo conhece só ${pct(d.knownShare, 0)} das palavras (mínimo ${pct(cut, 0)}). O texto está fora do que ele aprendeu.` }
        : { state: "passou", text: `O modelo conhece ${pct(d.knownShare, 0)} das palavras (mínimo ${pct(cut, 0)}).` },
    risk || outside
      ? { state: "nao_avaliado", text: "Confiança para seguir sozinho." }
      : auto
        ? { state: "decidiu", text: `Confiança de ${conf} em ${labels[top.category]}, acima do corte de ${pct(t.tauAuto, 0)}.` }
        : { state: "passou", text: `Confiança de ${conf}, abaixo do corte de ${pct(t.tauAuto, 0)} para seguir sozinho.` },
    risk || outside || auto
      ? { state: "nao_avaliado", text: "Confiança para sugerir ao atendente." }
      : d.lane === "assistida"
        ? { state: "decidiu", text: `Acima de ${pct(t.tauAssist, 0)}: o atendente escolhe entre as 2 categorias mais prováveis.` }
        : { state: "decidiu", text: `Abaixo de ${pct(t.tauAssist, 0)}: as sugestões não são confiáveis, a triagem é manual.` },
  ]
}

function RoutingSlip({
  decision: d,
  thresholds,
  target,
  truth,
}: {
  decision: Decision
  thresholds: Thresholds
  target: number
  truth: string | null
}) {
  const { model } = useData()
  const labels = model.rotulos_pt
  const top = d.ranking[0]
  const list = steps(d, thresholds, model.politica.corte_palavras_conhecidas, labels)
  const decidedByModel = d.reason.startsWith("confianca")

  return (
    <article aria-live="polite" className="relative self-start overflow-hidden rounded-md border border-rule bg-surface lg:sticky lg:top-6">
      <div className={`absolute inset-y-0 left-0 w-1.5 ${LANE_BAR[d.lane]}`} aria-hidden />
      <div className="p-6 pl-8">
        <p className="text-sm text-ink-2">Decisão com precisão mínima de {pct(target, 0)} por ticket</p>
        <h2 className="mt-1 font-heading text-3xl font-semibold">{LANE_NAMES[d.lane]}</h2>
        {decidedByModel && (
          <p className="mt-1 text-lg">
            {d.lane === "assistida"
              ? `${labels[d.ranking[0].category]} ou ${labels[d.ranking[1].category]}`
              : labels[top.category]}
            <span className="text-ink-2">, confiança de {pct(top.probability, 0)}</span>
          </p>
        )}
        {truth && decidedByModel && (
          <p className="mt-2 text-sm text-ink-2">
            O dataset registra {labels[truth]}:{" "}
            {top.category === truth
              ? "a categoria mais provável está certa."
              : d.ranking[1].category === truth
                ? "a certa é a segunda sugestão."
                : "o modelo errou."}
          </p>
        )}

        <h3 className="mt-6 font-medium">Por que esta fila</h3>
        <ol className="mt-2 space-y-2">
          {list.map((s, i) => (
            <li key={i} className={`flex gap-3 ${s.state === "nao_avaliado" ? "text-ink-3" : ""}`}>
              <span className="tabular w-4 shrink-0 text-ink-3">{i + 1}</span>
              <StepIcon state={s.state} />
              <span>{s.text}</span>
            </li>
          ))}
        </ol>

        {d.evidence.length > 0 && decidedByModel && (
          <>
            <h3 className="mt-6 font-medium">Palavras que mais pesaram para {labels[top.category]}</h3>
            <p className="mt-1 text-ink-2">{d.evidence.slice(0, 6).map((e) => e.term).join(", ")}</p>
          </>
        )}

        {d.executionAlwaysHuman && decidedByModel && (
          <p className="mt-6 flex gap-2 border-t border-rule pt-4 text-sm text-ink-2">
            <UserRound className="size-4 shrink-0 translate-y-0.5" aria-hidden />
            A IA só encaminha. Conceder acesso ou tratar dado de RH continua com uma pessoa.
          </p>
        )}
      </div>
    </article>
  )
}

function StepIcon({ state }: { state: Step["state"] }) {
  if (state === "decidiu") return <CircleCheck className="size-5 shrink-0 text-accent" aria-label="decidiu a fila" />
  if (state === "passou") return <CircleArrowDown className="size-5 shrink-0 text-ink-3" aria-label="não decide, segue para a próxima regra" />
  return <CircleMinus className="size-5 shrink-0 text-ink-3" aria-label="não avaliado" />
}
