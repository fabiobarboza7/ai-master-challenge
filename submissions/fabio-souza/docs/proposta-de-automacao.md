# Proposta de automação com IA

- **Números:** vêm de `solution/analysis/outputs/` (03 a 06) e são reproduzíveis com `solution/run_all.sh`.
- **Decisões de risco:** marcadas com "(decisão do Fabio)"; o registro completo está em `process-log/decisoes.md`.

## Como um ticket passa pelo fluxo

As regras rodam nesta ordem; a primeira que decide encerra o fluxo.

1. **Entrada.** O ticket chega por qualquer canal com o texto e o **tipo escolhido pelo cliente num campo obrigatório**. O campo é necessário: no Dataset 1, a descrição não indica o tipo (um classificador treinado nela acerta 19,7%; o acaso é 20,7%).
2. **Regra de risco, antes da IA.** Reembolso ou cancelamento vai para a fila humana especializada, identificado pelo tipo informado ou por palavra-chave no texto (*decisão do Fabio*).
3. **Trava de domínio.** Se o modelo conhece menos de 85% das palavras, o ticket vai para uma pessoa. Isso cobre outro idioma ou assunto que ele nunca viu.
4. **Classificador.** Devolve categoria e confiança.
5. **Fila automática.** Confiança ≥ 78% roteia sem toque humano.
   - Nesse corte, tickets com a mesma confiança acertam ≥ 90% (*precisão por ticket, decisão do Fabio*).
   - Teste: **61,4% dos tickets, 96,4% na categoria certa** (IC 95%: 95,8% a 96,9%).
6. **Fila assistida.** Confiança entre 48,5% e 78% mostra as 2 categorias mais prováveis e o atendente escolhe com um clique.
   - Teste: **26,4%** dos tickets; a certa está entre as duas em **94,0%**.
7. **Triagem humana.** O restante, **12,2%**. Nessa faixa o modelo acerta só 49%, então sugerir atrapalharia.
8. **Execução.** Tickets de Acesso, Permissões administrativas e RH podem ser roteados pela IA, mas **conceder acesso e tratar dado pessoal é sempre humano** (*decisão do Fabio*).
9. **Aprendizado.** Toda correção de fila feita por um atendente vira rótulo para o treino do mês seguinte. A **taxa de correção na fila automática** é o alarme principal.

## O que automatizar, em ordem

| # | Automação | Evidência nos dados | Ganho estimado | Risco |
|---|---|---|---|---|
| 1 | **Formulário estruturado para pedidos de compra**, sem IA | 976 tickets de TI são o mesmo pedido de alocação: 40% da categoria Compras | ~5,4 h/mês (tempo por ticket é premissa) | Baixo |
| 2 | **Triagem em três filas** (fluxo acima) | Teste com 7.026 tickets nunca vistos: 61% automáticos com 96% certos | 34,7 h/mês na base do brief; faixa de 5,3 a 169,6 | Médio, contido pelos cortes, pela trava e pela regra de risco |
| 3 | **Resposta sugerida a partir do ticket gêmeo** | 12,3% dos tickets têm um quase idêntico (cosseno ≥ 0,9); 95% desses pares têm a mesma categoria | ~7,7 h/mês (premissa de 3 min poupados e 50% de adoção) | Baixo: o atendente decide |

A ordem acima é **decisão do Fabio** (D15): primeiro o que não usa IA, depois a triagem. As alternativas consideradas foram começar pela triagem, que é o maior ganho isolado e o que o brief pede, ou não automatizar nada antes de 6 semanas de instrumentação.

A de maior retorno por esforço não usa IA. Os ganhos são modestos na base do brief: a triagem sozinha devolve cerca de 0,22 pessoa em tempo integral. **O ganho grande só vai aparecer depois de medir onde o tempo vai** (`diagnostico.md`).

## O que não automatizar

| Não automatizar | Por quê | Evidência |
|---|---|---|
| **Reembolso e cancelamento** (*decisão do Fabio*) | Dinheiro, direito do consumidor e risco de perder o cliente | 40,7% dos tickets do Dataset 1. O tipo só é detectável pelo campo estruturado; a palavra-chave na descrição aparece em 2,3% dos tickets, na mesma proporção entre os tipos |
| **Conceder acesso, permissões e atender RH** (*decisão do Fabio*) | Erro vira incidente de segurança ou exposição de dado pessoal (LGPD) | A taxonomia se sobrepõe: há textos quase idênticos rotulados ora "Access", ora "Administrative rights" |
| **Tickets de baixa confiança** (< 48,5%) | Metade das sugestões estaria errada | O modelo acerta 49% nessa faixa |
| **Texto fora do domínio do modelo** | O modelo fica "confiante" mesmo errando | Aplicado ao Dataset 1, manda 88% para Hardware e 28,6% passariam no corte automático |
| **Fechar ticket como duplicado** | Pares quase idênticos às vezes são pedidos diferentes | 5% dos pares com cosseno ≥ 0,9 têm categorias diferentes |
| **Resposta final ao cliente escrita por IA sem revisão** | Não há base para medir a qualidade dessas respostas | As resoluções do Dataset 1 são frases aleatórias; não existem respostas reais para comparar |

**Como o reembolso é detectado, e o que isso custa** (*decisão do Fabio*, D14). A regra olha o campo de tipo **e** a palavra-chave no texto, porque um cliente que escolhe o tipo errado no formulário teria o pedido roteado pela IA. O preço disso é 0,7% dos tickets de TI indo para uma pessoa à toa — "cancel meeting" dispara a regra. Duas alternativas foram descartadas: usar só o campo de tipo (zera o falso positivo e abre o buraco) e aplicar a palavra-chave só quando o modelo está inseguro (deixa passar o pedido de reembolso que o modelo classifica com confiança alta).

## Piloto de 6 semanas

Os critérios de continuar ou voltar são **decisão do Fabio** (D13), escolhidos entre três níveis de rigor; o resto do desenho é proposta da IA, para validar com a operação.

**Semana 0: preparação**
- Registrar os cinco eventos do diagnóstico.
- Cronometrar 50 triagens.
- Exportar os tickets históricos com a fila final: são os rótulos de treino.

**Semanas 1–2: modo sombra**
- Treinar com os tickets da própria operação. Pela curva de aprendizado, 5 mil tickets rotulados dão ~40% de fila automática com 97% de precisão; 1 mil dão ~25%.
- O modelo sugere, mas nenhum ticket é roteado sozinho. Medir o acerto real por faixa de confiança e recalibrar os cortes.

**Semanas 3–6: fila automática ligada** para as categorias com acerto ≥ 90% no modo sombra.

| Decisão | Critério |
|---|---|
| **Continuar** | Acerto da fila automática ≥ 95% por 2 semanas seguidas **e** correções humanas nessa fila ≤ 5% **e** o tempo até a primeira resposta não piora |
| **Voltar ao modo sombra** | Acerto < 90% em qualquer semana, **ou** a fração barrada pela trava de domínio sobe mais de 5 pontos (sinal de assunto ou produto novo) |
| **Acompanhar toda semana** | Acerto por categoria, taxa de correção, fração de tickets por fila, fração barrada pela trava |

Por que monitorar e não confiar só nos cortes: na validação, o corte de 78% entregava acerto local de 90,5%. No teste, o mesmo corte ficou em ~88%. Cortes escolhidos em um conjunto perdem um pouco quando os dados mudam, e em produção os dados mudam.
