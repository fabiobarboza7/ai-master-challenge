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

## 15/09 16:10–16:18 — Auditorias dos dois datasets

**Dataset 1.** Cada alegação pública foi conferida com código, e todas se confirmaram:
- não há data de abertura; todas as respostas cabem em 27 h;
- 49,3% das resoluções vêm antes da primeira resposta;
- a nota de satisfação é uniforme e nada a explica;
- 100% das descrições têm o placeholder `{product_purchased}`.

Dois achados que as reviews públicas não citavam:
- **Tipo e assunto são sorteados independentes.** O assunto "Refund request" tem o tipo "Refund request" em 20,7% dos casos, o esperado por acaso.
- **O texto do Dataset 1 não prevê nem tipo nem assunto.**

A revisão da própria saída pegou dois erros estatísticos (E3, E4).

**Dataset 2.** 12,3% dos tickets têm quase-duplicado. O maior grupo são 976 pedidos de compra idênticos. Pares quase iguais com rótulos diferentes mostram que a taxonomia se sobrepõe. **Antes de treinar**, o critério de escolha do modelo foi fixado no Adendo 1 da pré-registração.

## 15/09 16:20–16:35 — Classificador e mudança de domínio

- **Primeira rodada:** os cortes caíram no piso arbitrário da grade (E6).
- **Grade corrigida:** apareceu o problema maior (E7). A regra "precisão média ≥ 90%", que a própria IA tinha pré-registrado, aceitava tickets de 0–52% de acerto local. A regra virou "acerto ≥ 90% por ticket" (regressão isotônica); o desvio foi documentado e o teste avaliado para as duas regras.
- **Resultado:** regressão logística com 20 mil termos. No teste, 61,4% automáticos com 96,4% certos. A divisão aleatória superestimaria a acurácia em 1,8 ponto.
- **Aplicado ao Dataset 1:** o modelo manda 88% para Hardware, e 28,6% passariam na fila automática. Uma trava de vocabulário foi criada. Ela chegou a ser reportada barrando 95%; o número real, depois de alinhar a tokenização com o app, é 41% (E9).
- **Curva de aprendizado:** 5 mil tickets rotulados dão ~40% de fila automática.

## 15/09 16:42 — Checkpoint 2: decisões de negócio do Fabio

Com os resultados em mãos, o Fabio escolheu:
- 90% de precisão por ticket;
- a regra por ticket, e não a média;
- acesso e RH: a IA só roteia;
- R$ 35/h.

As três primeiras seguiram a recomendação da IA; o custo/hora foi escolha própria. Respostas literais em [`decisoes.md`](decisoes.md) (D8–D11).

## 15/09 16:44–16:52 — ROI

- **Base:** função paramétrica com a origem de cada insumo; 34,7 h/mês na base do brief.
- **Erro E10:** o Revisor-IA pediu para conferir penalidade dupla, e ela existia. O empate real é 75%, não 80%.
- **Erro E13:** o cenário otimista usava R$ 50/h, contrariando a decisão do Fabio.
- **Testes:** 10 testes Python cobrem os bugs E7, E9 e E10.

## 15/09 17:00–19:15 — Protótipo

- **Base:** o scaffold Next.js + shadcn que o Fabio já tinha criado, com os componentes shadcn não usados removidos.
- **Exportação e paridade:** modelo exportado com 3 casas decimais (filas 100% iguais ao modelo completo). 245 casos de paridade Python ↔ TypeScript e backtest com contagens idênticas: 258 testes.
- **Verificação visual** com capturas em desktop, celular e modo escuro:
  - a página tinha 6.942 px de largura no celular (E11);
  - o gráfico escondia os erros que existia para mostrar (E12).
- **Ferramental:** o ESLint do template quebrava por incompatibilidade entre ESLint 10 e `eslint-plugin-react`; resolvido fixando a versão do React na configuração.

## 15/09 19:15–19:30 — Reprodutibilidade e documentação

- **`run_all.sh`:** uma leitura antes de rodar achou uma pasta inexistente em clone limpo (E14). Depois, num clone novo do branch, o script rodou tudo em 2 min 36 s, com saídas idênticas byte a byte, exceto o ECE do SVM na 9ª casa decimal.
- **Documentação:** diagnóstico, proposta de automação com piloto, ficha do modelo e README no template.
