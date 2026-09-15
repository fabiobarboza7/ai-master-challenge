# Process log

Como a IA foi usada, quem decidiu o quê e onde ela errou. Tudo aqui foi escrito durante o trabalho.

| Arquivo | O que tem |
|---|---|
| [`diario.md`](diario.md) | Linha do tempo com horários, do pedido inicial à verificação final |
| [`decisoes.md`](decisoes.md) | Cada decisão com **quem decidiu** (Fabio, IA por delegação, IA, Revisor-IA) e as respostas literais do Fabio nos dois checkpoints |
| [`hipoteses-pre-registradas.md`](hipoteses-pre-registradas.md) | Hipóteses e regras de decisão escritas **antes** da análise, mais o adendo escrito antes de treinar |
| [`erros-da-ia.md`](erros-da-ia.md) | 15 erros reais da IA: como foram detectados, a correção e o impacto se tivessem passado |
| [`screenshots/`](screenshots) | 9 capturas do protótipo rodando: regras de risco, teste com 7.026 tickets, economia, celular, modo escuro |

## Como auditar

- **Números:** rode `bash solution/run_all.sh`. Os scripts regeram cada JSON citado.
- **Paridade entre análise e protótipo:** `cd solution/app && pnpm test`.
- **Ordem dos acontecimentos:** `git log --reverse -- submissions/fabio-souza`. As hipóteses e o critério do modelo aparecem em commits anteriores aos resultados que eles governam.

## Divisão de trabalho, sem enfeite

- **IA:** executou a leitura das regras e das reviews públicas, a análise, o código, os testes e a documentação.
- **Fabio:**
  - pediu a recomendação de desafio e decidiu seguir com o 002;
  - definiu antes dos dados que reembolso e cancelamento nunca são automatizados;
  - delegou explicitamente as hipóteses ("Descubra!") e a meta inicial de precisão ("Decida por mim");
  - no checkpoint 2, escolheu a precisão por ticket, a regra de corte, o limite para acesso e RH, e o custo por hora.
- **Revisor-IA:** um segundo modelo auditou o raciocínio em pontos de decisão e pegou dois erros (E1, E10).
