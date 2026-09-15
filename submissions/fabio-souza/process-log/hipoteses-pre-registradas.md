# Hipóteses pré-registradas

**Escrito em 15/09 ~16:10, antes de rodar qualquer análise.** Até aqui só foram vistos o cabeçalho e as primeiras linhas de cada CSV, mais a contagem de linhas feita no download.

- **Autoria:** o Fabio delegou a formulação das hipóteses à IA ("Descubra!", ver `decisoes.md`, D4). As hipóteses abaixo são da IA.
- **Por que pré-registrar:** fixar por escrito o que será testado e as regras de decisão impede escolher a métrica ou o corte depois de ver o resultado.

## A. Alegações públicas a verificar (não são premissas)

Reviews públicas de PRs aprovados neste desafio afirmam:

- **A1.** A satisfação (CSAT) do Dataset 1 não depende de nenhuma variável, como se tivesse sido sorteada.
- **A2.** Em boa parte dos tickets, `Time to Resolution` vem *antes* de `First Response Time`.
- **A3.** O Dataset 1 não tem data de abertura do ticket, então o tempo de resolução não é calculável.
- **A4.** As descrições do Dataset 1 são templates com o placeholder `{product_purchased}`.

Cada uma será confirmada ou refutada com código. Se não se sustentarem, serão descartadas.

## B. Hipóteses de trabalho

| # | Hipótese | Como será testada | Refutada se |
|---|----------|-------------------|-------------|
| H1 | O Dataset 1 representa o volume do brief (~30 mil tickets/ano) | Contagem de linhas e janela de datas | Volume ou janela incompatíveis. *Observação já feita no download: o arquivo tem 8.469 linhas* |
| H2 | Tickets travam em `Open` / `Pending Customer Response`, e isso varia por canal, prioridade e tipo | Proporção de backlog por segmento; teste χ² com correção de Holm | Nenhuma associação significativa **e** efeito desprezível (V de Cramér < 0,05) |
| H3 | A prioridade não acelera o atendimento (fila não priorizada de fato) | Tempo até 1ª resposta e desfecho por prioridade (Kruskal-Wallis, χ²) | Prioridades altas com atendimento significativamente melhor |
| H4 | A satisfação é explicada por tempo de resposta/resolução e por tipo de problema | Correlação de Spearman e testes por grupo (Holm); poder estatístico do teste | Nenhum efeito significativo, com poder suficiente para detectar efeitos pequenos |
| H5 | Dá para calcular horas gastas por ticket com os campos de tempo | Semântica dos campos: existe carimbo de abertura? durações são consistentes? | Sem carimbo de abertura ou com durações negativas frequentes |
| H6 | O texto carrega sinal para classificar a categoria com alta precisão em boa parte dos tickets (Dataset 2) | Classificador validado em conjunto separado; curva cobertura × precisão | Nenhum corte atinge a precisão mínima com cobertura útil (≥ 30%) |
| H7 | Parte relevante dos tickets é quase duplicada: oportunidade de automação **e** risco de vazamento treino→teste | Similaridade de cosseno TF-IDF entre tickets | Menos de 1% de quase-duplicados |
| H8 | Um classificador treinado no Dataset 2 (TI interna) não transfere para o Dataset 1 (suporte ao consumidor) | Confiança e cobertura do mesmo modelo nos textos do Dataset 1 | Cobertura no Dataset 1 próxima à do Dataset 2 |
| H9 | A descrição do Dataset 1 é informativa sobre tipo e assunto do ticket | Validação cruzada texto→tipo comparada ao acaso; independência tipo × assunto | Acurácia significativamente acima do acaso |

## C. Regras de decisão fixadas agora

1. **Significância:** α = 0,05 com correção de Holm dentro de cada família de testes. Sempre reportar tamanho de efeito, não só p-valor.
2. **Divisão dos dados do classificador:** tickets quase idênticos ficam no mesmo lado da divisão, para evitar vazamento. Divisão estratificada 70/15/15, semente 42. Modelo e corte são escolhidos **só na validação**. O teste é usado **uma vez**, no final.
3. **Precisão mínima da fila automática (decisão delegada, D5):** **90%** na validação.
   - Modelo de custo: rotear errado custa cerca de 4 vezes a triagem manual. O agente errado lê o ticket, devolve e o cliente espera. Com essa razão, a automação empata em 80% de precisão (4/(1+4)).
   - Os 10 pontos acima do empate são margem para a mudança de domínio: texto de produção ≠ texto de treino.
   - Uma categoria só entra na fila automática se tiver **≥ 85% de precisão** acima do corte na validação.
   - Sensibilidade a 85% e 95% será reportada.
4. **Política de risco (Fabio, D3):** qualquer ticket de **reembolso ou cancelamento** vai para humano, independentemente da confiança do modelo.
