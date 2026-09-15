# Submissão — Fabio Souza — Challenge 002

## Sobre mim

- **Nome:** Fabio Souza
- **LinkedIn:** {{LINKEDIN}}
- **Challenge escolhido:** 002 — Redesign de Suporte

---

## Executive Summary

**Os dados operacionais não permitem dizer onde o suporte perde tempo nem o que derruba a satisfação.** O Dataset 1 não registra a abertura do ticket; em 49% dos fechados a resolução vem antes da primeira resposta; e nenhuma das 9 variáveis testadas explica a nota, com poder estatístico para detectar efeitos pequenos.

**A automação, por outro lado, tem evidência real.** Um classificador treinado em 47.837 tickets reais (Dataset 2) foi testado em 7.026 que nunca viu:

- **61%** vão direto para a fila certa, com **96% de acerto**;
- **26%** vão para o atendente confirmar entre 2 sugestões;
- **12%** seguem para triagem humana;
- **reembolso e cancelamento vão sempre para uma pessoa.**

Um protótipo roda essa política no navegador. Na base do brief, a triagem devolve **34,7 h/mês** (R$ 1,2 mil), numa faixa de 5 a 170 h que depende sobretudo do tempo de triagem manual, mensurável em uma semana.

**Recomendação principal:** registrar cinco eventos por ticket e rodar um piloto de 6 semanas em modo sombra, com o modelo treinado nos tickets da própria operação. O modelo atual não transfere para suporte ao consumidor.

---

## Solução

| Entregável | Onde |
|---|---|
| Diagnóstico operacional | [`docs/diagnostico.md`](docs/diagnostico.md) |
| Proposta de automação: fluxo, o que não automatizar, piloto | [`docs/proposta-de-automacao.md`](docs/proposta-de-automacao.md) |
| Ficha do modelo | [`docs/modelo.md`](docs/modelo.md) |
| Protótipo (Next.js, roda no navegador) | [`solution/app`](solution/app) |
| Análise reproduzível (Python, 7 scripts, testes) | [`solution/analysis`](solution/analysis) |

**Como rodar tudo do zero** (~3 min; requer [uv](https://docs.astral.sh/uv/) ou Python 3.12, Node 20+ e pnpm):

```bash
cd submissions/fabio-souza/solution
bash run_all.sh        # baixa os dados (sem credencial), roda a análise, 268 testes e o build
cd app && pnpm dev     # http://localhost:3000
```

Só o protótipo, sem Python: `cd solution/app && pnpm install && pnpm dev`. Os dados do modelo já estão exportados.

A reprodução foi verificada num clone limpo do branch. Todas as saídas saíram idênticas byte a byte, exceto o ECE do SVM calibrado, que diverge na 9ª casa decimal por ruído numérico.

### Abordagem

1. **Entender como o desafio é avaliado.** A IA leu as regras e as ~200 reviews públicas do avaliador nos PRs de outros candidatos, para saber o que reprova: log de processo não auditável, higiene de repositório, entrega que não reproduz. Nenhum código ou texto de outro candidato foi usado; os problemas de dados citados nessas reviews foram tratados como alegações a verificar.
2. **Decidir os limites antes de olhar os dados.** O Fabio definiu que reembolso e cancelamento nunca são automatizados. As hipóteses e as regras de decisão foram pré-registradas por escrito antes da análise ([`process-log/hipoteses-pre-registradas.md`](process-log/hipoteses-pre-registradas.md)).
3. **Auditar os dois datasets antes de calcular qualquer indicador.** Testes corrigidos para múltiplas comparações, tamanho de efeito e poder estatístico.
4. **Escolher o modelo pela métrica que vira hora economizada**: a cobertura da fila automática com acerto ≥ 90% por ticket, e não a acurácia. A divisão treino/teste é por grupos de quase-duplicados, para não inflar o resultado.
5. **Testar o que acontece fora do domínio de treino**, aplicando o modelo ao texto do Dataset 1.
6. **Calcular o ROI como fórmula**, com a origem de cada insumo: medido, premissa, brief ou decisão do Fabio.
7. **Construir o protótipo com paridade testada contra o Python.** Levar as decisões de negócio ao Fabio com os números na mão (checkpoint 2).

### Resultados

| Pergunta | Achado | Evidência |
|---|---|---|
| Onde o fluxo trava? | **Não calculável.** Não há data de abertura; todas as respostas e resoluções cabem em 27 horas; nenhum canal, prioridade ou tipo difere dos outros | [`diagnostico.md` §1](docs/diagnostico.md) |
| O que impacta a satisfação? | **Nada no dado atual.** 9 testes, zero efeitos após Holm; o único p < 0,05 some com a correção | [`diagnostico.md` §2](docs/diagnostico.md) |
| Quanto desperdiçamos? | **Função, não número.** 34,7 h/mês na base do brief (5,3 a 169,6 h). A maior incerteza é o tempo de triagem manual | [`06_roi.json`](solution/analysis/outputs/06_roi.json) |
| O que automatizar? | Triagem em 3 filas: **61,4% automáticos com 96,4% de acerto** (IC 95%: 95,8–96,9%), 26,4% assistidos (certa entre 2 sugestões em 94%), 12,2% humanos | [`modelo.md`](docs/modelo.md) |
| E fora da IA? | **Formulário para pedidos de compra**: 976 tickets idênticos, 40% da categoria. **Resposta sugerida por ticket gêmeo**: 12,3% têm um quase idêntico | [`02_auditoria_ds2.json`](solution/analysis/outputs/02_auditoria_ds2.json) |
| O modelo serve para suporte ao consumidor? | **Não.** Manda 88% para Hardware, e 28,6% passariam como "confiantes". Travas simples barram no máximo 41% | [`04_transferencia_ds1.json`](solution/analysis/outputs/04_transferencia_ds1.json) |
| Quantos dados próprios são necessários? | 1 mil tickets rotulados dão 25% de fila automática; 5 mil dão 40%; 33 mil dão 61% | [`05_curva_de_aprendizado.json`](solution/analysis/outputs/05_curva_de_aprendizado.json) |

![Tickets de teste por confiança: os erros (vermelho) se concentram abaixo do corte automático](process-log/screenshots/05-teste-7026-tickets-precisao-90.png)

![Ticket com pedido de reembolso vai para uma pessoa, qualquer que seja a confiança do modelo](process-log/screenshots/02-regra-reembolso-vai-para-humano.png)

### Recomendações

1. **Semana 0: registrar cinco eventos por ticket** (abertura, mudanças de fila, interações, resolução, satisfação ligada ao ticket). Sem isso, "onde perdemos tempo" continua sem resposta.
2. **Criar o formulário estruturado para pedidos de compra.** É a automação de maior retorno por esforço, e não usa IA.
3. **Pilotar a triagem em três filas por 6 semanas.** Duas em modo sombra com tickets rotulados da própria operação (meta: 5 mil), depois fila automática com critérios explícitos de continuar ou voltar ([`proposta-de-automacao.md`](docs/proposta-de-automacao.md)).
4. **Sugerir ao atendente a resposta do ticket gêmeo.** Nunca fechar como duplicado sem uma pessoa.
5. **Manter com pessoas:** reembolso e cancelamento; concessão de acesso e RH, que a IA pode rotear mas nunca executar; tickets de baixa confiança; texto fora do domínio.

### Limitações

- **Dataset 1:** é sintético (distribuições uniformes, e-mails `example.com`, templates com placeholder), então nenhuma conclusão sobre uma operação real sai dele.
- **Modelo:** treinado em tickets de TI interna, não transfere para suporte ao consumidor. A trava de domínio é parcial (barra 41%).
- **Tempos e custos:** são premissas explícitas; o ROI é uma fórmula para a operação preencher.
- **Corte da fila automática:** levemente otimista. O acerto no corte foi 90,5% na validação e ~88% no teste; por isso o piloto recalibra e monitora a taxa de correção.
- **Regra por palavra-chave:** tem falsos positivos ("cancel meeting" em TI, 0,7% dos tickets), aceitos por serem conservadores.
- **Protótipo:** demonstra a política de filas, sem integração com help desk, login ou geração de respostas por IA.

---

## Process Log — Como usei IA

> Detalhes em [`process-log/`](process-log): diário, decisões com respostas literais, erros da IA, hipóteses pré-registradas, {{CHAT_EXPORT_LINE}} e capturas de tela.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Claude Opus 5) | Agente principal: leitura das regras e das reviews públicas, análise estatística, modelo, protótipo, testes e documentação |
| Revisor-IA (segundo modelo, ferramenta *advisor* do Claude Code) | Auditoria do raciocínio antes de cada etapa grande. Pegou o erro de denominador na escolha do desafio (E1) e o erro contado duas vezes no ROI (E10) |
| GitHub CLI e API | Coleta dos 124 PRs e das reviews do avaliador |
| Playwright com Chrome | Capturas do protótipo e verificação visual em celular e modo escuro; achou a página com 6.942 px de largura (E11) |
| Validador de paleta (skill de visualização) | Cores dos gráficos acessíveis a daltônicos e com contraste adequado |

### Workflow

1. **15:30** — Escolha do desafio: leitura das regras e das reviews públicas; estatística de aprovação por desafio.
2. **16:05** — Checkpoint 1: o Fabio define a política de risco; hipóteses delegadas e pré-registradas.
3. **16:10–16:52** — Auditorias, classificador, mudança de domínio, curva de aprendizado e ROI, em 9 commits.
4. **16:42** — Checkpoint 2: decisões de negócio do Fabio (precisão, regra, acesso/RH, custo/hora).
5. **17:00–19:15** — Protótipo, paridade Python ↔ TypeScript, verificação visual, reprodução num clone limpo e documentação.

### Onde a IA errou e como foi corrigido

Catorze erros reais, todos documentados com evidência em [`process-log/erros-da-ia.md`](process-log/erros-da-ia.md). Os mais relevantes:

- **E7 — a regra que a própria IA pré-registrou era falha.** "Precisão média ≥ 90%" aceitava tickets que acertam 0–52%, escondidos na média. Foi trocada por uma regra por ticket; o desvio está documentado e as duas regras aparecem nos resultados.
- **E9 — número inflado.** A trava de domínio foi reportada barrando 95% do texto estranho, inclusive numa mensagem de commit. O certo era 41%; a correção está num commit explícito.
- **E10 — ROI com erro contado duas vezes.** O ponto de empate real é 75%, não 80%.
- **E3/E4 — testes estatísticos mal aplicados.** KS em variável discreta e V de Cramér enviesado teriam gerado falsos achados.
- **E11 — protótipo quebrado no celular.** A página tinha 6.942 px de largura; foi pego pela verificação visual antes do commit.

### O que eu adicionei que a IA sozinha não faria

{{CONTRIBUICAO_HUMANA}}

---

## Evidências

- [x] Capturas de tela do protótipo rodando: 9, em [`process-log/screenshots`](process-log/screenshots)
- [{{CHAT_EXPORT_CHECK}}] Export da sessão com a IA
- [x] Histórico do git: commits incrementais com mensagens explicando o que mudou e o que foi corrigido
- [x] Outro: hipóteses pré-registradas, registro de decisões com respostas literais, 268 testes automatizados (10 Python + 258 TypeScript) e script que reproduz tudo do zero

---

_Submissão enviada em: 15/09/2026_
