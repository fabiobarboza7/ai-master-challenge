import { Prototype } from "@/components/prototype"

const LIMITS = [
  "O modelo foi treinado com tickets de TI interna (Dataset 2). Aplicado ao suporte ao consumidor (Dataset 1), ele manda 88% dos tickets para Hardware. Antes de usar, é preciso treinar com tickets rotulados da própria operação.",
  "A trava de vocabulário barra só 41% do texto de outro domínio. No piloto, a proteção de verdade é acompanhar quantos tickets da fila automática um atendente precisa corrigir.",
  "Os tempos e o custo de erro são premissas. Nenhum dado do challenge mede tempo de forma confiável: o Dataset 1 não tem data de abertura e 49% das resoluções vêm antes da primeira resposta.",
  "Por isso não há painel de gargalos: com esses dados, qualquer ranking de canal ou prioridade seria ruído.",
  "É uma demonstração da política de filas, sem integração com help desk, login ou histórico.",
]

export default function Page() {
  return (
    <>
      <header className="border-b border-rule">
        <nav className="mx-auto flex max-w-6xl flex-wrap items-baseline justify-between gap-x-8 gap-y-2 px-4 py-4 sm:px-6">
          <p className="font-heading text-xl font-semibold">Triagem assistida</p>
          <ul className="flex flex-wrap gap-x-6 gap-y-1 text-ink-2">
            <li><a className="hover:text-ink" href="#rotear">Rotear um ticket</a></li>
            <li><a className="hover:text-ink" href="#teste">Resultado no teste</a></li>
            <li><a className="hover:text-ink" href="#economia">Economia</a></li>
            <li><a className="hover:text-ink" href="#limites">Limites</a></li>
          </ul>
        </nav>
      </header>
      <main>
        <Prototype />
        <section id="limites" className="border-t border-rule bg-surface">
          <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
            <h2 className="font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
              O que este protótipo não faz
            </h2>
            <ul className="mt-8 grid max-w-3xl gap-4">
              {LIMITS.map((l) => (
                <li key={l} className="border-l-4 border-rule pl-4 text-ink-2">{l}</li>
              ))}
            </ul>
          </div>
        </section>
      </main>
      <footer className="border-t border-rule">
        <p className="mx-auto max-w-6xl px-4 py-8 text-sm text-ink-3 sm:px-6">
          Dados: Customer Support Ticket Dataset e IT Service Ticket Classification Dataset (Kaggle).
          Análise, modelo e decisões documentados em submissions/fabio-souza.
        </p>
      </footer>
    </>
  )
}
