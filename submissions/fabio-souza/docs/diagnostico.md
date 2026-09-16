# Diagnóstico operacional

Respostas às três perguntas do Diretor de Operações. Cada número vem de `solution/analysis/outputs/01_auditoria_ds1.json` e pode ser refeito com `solution/run_all.sh`.

## Resposta curta

**Com os dados atuais, não dá para dizer onde a operação perde tempo, nem o que derruba a satisfação.** Não é falta de análise: os registros não sustentam essas respostas, e qualquer ranking de canal ou prioridade feito sobre eles seria ruído. O que dá para fazer já:

1. **Instrumentar cinco eventos por ticket** (lista no fim deste documento). Em 4 a 6 semanas, as perguntas passam a ter resposta.
2. **Automatizar a triagem**, onde há dado de texto real e o ganho é medido (ver `proposta-de-automacao.md`).

## 1. Onde o fluxo trava?

**Não é calculável: o sistema não registra quando o ticket foi aberto.** As únicas colunas de tempo são `Date of Purchase`, `First Response Time` e `Time to Resolution`, e as duas últimas são horários, não durações.

- **Janela impossível:** todas as primeiras respostas e resoluções dos 8.469 tickets cabem numa janela de **27 horas** (31/05/2023 21:53 a 02/06/2023 00:55). Uma operação de ~30 mil tickets/ano (número do brief) não resolve um ano de tickets em um dia.
- **Ordem invertida:** em **49,3%** dos 2.769 tickets fechados, a resolução acontece **antes** da primeira resposta. As diferenças vão de −23,2 h a +23,5 h, com mediana de +0,2 h: o padrão de dois horários sorteados no mesmo dia.
- **Nada varia entre segmentos:** tickets não fechados são 66–70% em todos os canais, prioridades e tipos (teste χ², nenhuma associação após correção de Holm). Tickets **Critical** ficam sem primeira resposta com a mesma frequência que os **Low** (32,5% vs. 33,7%).
- **Nem entre combinações.** A pergunta do Diretor é sobre *combinações*, então as **80 células** de canal × prioridade × tipo foram testadas uma a uma contra o resto. A pior delas parece alarmante — **Phone | Low | Cancellation request, com 80,6% sem fechar** contra 67,3% na base — e some na correção para 80 comparações (p de Holm = 0,25). O intervalo entre a melhor e a pior célula vai de 56,6% a 80,6%, a dispersão que se espera de células de ~100 tickets sorteadas.

> **Esta é a armadilha principal do Dataset 1.** Rankear as 80 combinações sem corrigir para múltiplas comparações produz um "gargalo" com nome, número e aparência de achado — e a recomendação que sai dele manda a operação reorganizar o atendimento telefônico de cancelamento de baixa prioridade por causa de ruído.
- **Volume:** o arquivo tem 8.469 tickets, **28%** dos ~30 mil/ano do brief. Pela janela de 27 horas, ele não serve para medir volume.

## 2. O que impacta a satisfação?

**Nenhuma variável disponível explica a nota de satisfação.**

- **Quem tem nota:** só os tickets fechados (2.769). As notas de 1 a 5 aparecem 543 a 580 vezes cada, compatível com sorteio uniforme (p = 0,80).
- **Nove testes, nenhum efeito:** foram testados canal, prioridade, tipo, assunto, produto, gênero, idade, momento da resposta e intervalo resposta→resolução. Após a correção de Holm, **nenhum** tem efeito. O maior efeito explica 0,1% da variação.
- **A ausência de efeito é informativa:** com 2.769 notas, o teste detectaria correlações a partir de 0,05 e diferenças entre grupos a partir de f = 0,06, abaixo do que se considera efeito pequeno (0,10).
- **Armadilha evitada:** sem a correção para múltiplos testes, "responder mais tarde reduz a satisfação" (p = 0,046) pareceria achado. Corrigido para 9 testes, p = 0,42.

## 3. Quanto estamos desperdiçando?

**Em horas medidas, não dá para responder**, pelos motivos do item 1. O que dá para entregar é a conta com os insumos que a operação consegue medir em uma semana (`solution/analysis/06_roi.py` e a tela "Economia" do protótipo).

- **Na base do brief** (2.500 tickets/mês, triagem de 2 min, R$ 35/h), a triagem automática devolve **34,7 h/mês (R$ 1.216/mês)**.
- **Faixa:** entre 5,3 e 169,6 h/mês conforme as premissas. A que mais pesa é o tempo de triagem manual: 15,8 h com 1 min, 72,7 h com 4 min. **Cronometrar 50 triagens resolve essa incerteza.**
- **Duas alavancas medidas pelo volume**, fora da triagem:
  - **Formulário para pedidos de compra, sem IA (~5,4 h/mês):** 976 tickets de TI (40% da categoria Compras) são o mesmo pedido de alocação, escrito à mão.
  - **Resposta sugerida a partir do ticket gêmeo (~7,7 h/mês):** 12,3% dos tickets têm um quase idêntico no histórico.

## Sinais de que o Dataset 1 é sintético

Registro para quem for reusar a base: não são problemas da operação, são limites do dado.

| Sinal | Evidência |
|---|---|
| E-mails de clientes | 100% em `example.com`, `example.org` ou `example.net` |
| Descrições | 100% contêm o placeholder `{product_purchased}` sem substituição; 37% começam pela mesma frase |
| Tipo × assunto | Tickets com assunto "Refund request" têm tipo "Refund request" em 20,7% dos casos, o esperado por sorteio entre 5 tipos |
| Texto informa o tipo? | Um classificador treinado na descrição acerta 19,7% dos tipos; o acaso é 20,7% |
| Texto da resolução | Frases aleatórias ("West decision evidence bit.") que não predizem o tipo do ticket |
| Distribuições | Canal, prioridade, status, tipo, produto, idade e nota compatíveis com distribuição uniforme |

## O que registrar a partir de amanhã

Cinco eventos por ticket respondem às três perguntas:

1. **Abertura:** data e hora, canal e categoria escolhida pelo cliente.
2. **Cada mudança de fila:** quem mudou e de onde para onde. Mede re-roteamento e erro de triagem.
3. **Cada interação:** autor (cliente ou atendente) e horário. Mede tempo de espera de cada lado.
4. **Resolução:** horário e código de resolução, de uma lista fechada.
5. **Pesquisa de satisfação ligada ao ticket**, com a data de envio. Mede viés de quem responde.
