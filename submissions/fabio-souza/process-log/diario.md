# Diário de bordo

Registro cronológico, escrito durante o trabalho (não reconstruído no final).
Horários em BRT (UTC−3). A sessão completa do Claude Code está em `chat-exports/`.

**Quem é quem neste log**
- **Fabio** — candidato.
- **IA** — Claude Code rodando Claude Opus 5, o agente que executou a análise e o código.
- **Revisor-IA** — um segundo modelo, chamado pelo agente para auditar o próprio raciocínio em pontos de decisão.

---

## 15/09 15:30 — Escolha do desafio

Pedido do Fabio: *"leia atentamente os requisitos da vaga, as regras e etc, e me diga qual projeto temos maior chances?"*

- A IA leu o README, as regras, o guia de submissão, o template e os 4 desafios.
- Descobriu que os PRs de outros candidatos, e as reviews do avaliador, são públicos.
- Via GitHub API, baixou os 124 PRs e os ~200 comentários do avaliador para entender o critério real de aprovação.
- **Erro da IA:** a primeira taxa de aprovação por desafio contava "PR parado aguardando ajuste" como reprovação. O Revisor-IA apontou o problema de denominador. A IA trocou a métrica por "aprovado na 1ª review": 001 = 29%, 002 = 68%, 003 = 48%, 004 = 57%.
- Recomendação: **002**. Tem a maior aprovação com amostra razoável, pede protótipo (encaixa no perfil de dev) e é o desafio mais próximo da descrição da vaga.

**Transparência:** ler as reviews públicas mostrou problemas nos dados que outros candidatos já tinham levantado (CSAT aleatório, timestamps invertidos). Neste trabalho eles são tratados como **alegações a verificar**, nunca como fatos. Todo número deste repositório foi recalculado a partir dos CSVs originais pelos scripts em `solution/analysis/`. Nenhum código ou texto de outros candidatos foi usado.

## 15/09 15:53 — Início do desafio 002

Pedido do Fabio: *"Va em frente! O importante e atingir o objetivo de eu ser aprovado para a vaga de emprego. Faca o seu melhor!"*

- A IA clonou o repositório e criou a branch `submission/fabio-souza`.
- Os dois datasets baixam do endpoint público do Kaggle sem credencial. O script `solution/data/download.sh` confere o SHA-256.
- **Armadilha encontrada pela IA:** o `.gitignore` raiz do repositório ignora `submissions/`. Por isso é preciso `git add -f`, e o `-f` desliga *todos* os ignores, inclusive `node_modules`.
  - A primeira tentativa de filtro da IA (`git ls-files --exclude-from`) não listava nenhum arquivo. Foi detectado num teste com um `node_modules` falso antes de qualquer commit.
  - Solução final: um script de stage que percorre a pasta com uma lista de exclusão explícita e **bloqueia o commit** se houver dependências, dados brutos, `.env`, arquivo acima de 3 MB ou alteração fora da pasta.

## 15/09 ~16:05 — Decisões iniciais do Fabio (antes de abrir os dados)

A IA fez 4 perguntas antes de qualquer análise. Respostas literais em [`decisoes.md`](decisoes.md).

- Hipóteses sobre onde a operação perde tempo: *"Descubra!"*. O Fabio delegou a formulação à IA.
- O que nunca automatizar: **reembolso/cancelamento**.
- Precisão mínima da fila automática: *"Decida por mim"*. Também delegado.

Com essa delegação, a IA **pré-registrou** as hipóteses por escrito antes de rodar qualquer análise, em [`hipoteses-pre-registradas.md`](hipoteses-pre-registradas.md). Assim os resultados não podem ser ajustados para caber numa narrativa escolhida depois.
