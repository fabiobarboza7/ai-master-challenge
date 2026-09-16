# Process log

Como a IA foi usada, quem decidiu o quê e onde ela errou. Escrito durante o trabalho.

| Arquivo | O que tem |
|---|---|
| [`decisoes.md`](decisoes.md) | As 16 decisões, cada uma com **quem decidiu**, e as respostas literais do Fabio nos três checkpoints |
| [`diario.md`](diario.md) | A linha do tempo, das 15:30 às 20:40 |
| [`hipoteses-pre-registradas.md`](hipoteses-pre-registradas.md) | Hipóteses e regras de decisão escritas **antes** da análise |
| [`erros-da-ia.md`](erros-da-ia.md) | 17 erros da IA: 9 que mudaram uma conclusão, 8 pegos antes de virarem problema |
| [`screenshots/`](screenshots) | 9 capturas do protótipo rodando |

## Como auditar em 3 comandos

```bash
bash solution/run_all.sh          # refaz todos os números do zero (~3 min)
cd solution/app && pnpm test      # paridade entre a análise e o protótipo
git log --reverse -- submissions/fabio-souza
```

O `git log` é a parte que não dá para forjar: as hipóteses e o critério de escolha do modelo estão em commits **anteriores** aos resultados que eles governam.

## Divisão de trabalho

**Fabio** decidiu onde a IA não manda, e quando. Fixou o limite de risco antes de qualquer coluna ser lida (D3), delegou de propósito as hipóteses e a precisão inicial para não ancorar a análise (D4, D5), escolheu as premissas de negócio com os números na mão (D8–D11) e, no fim, as regras de operação: critério do piloto, custo aceito de falso positivo e ordem de execução (D13–D15).

**A IA** executou: leitura das regras e das reviews públicas, análise estatística, modelo, protótipo, testes e documentação. As decisões técnicas dela estão marcadas como dela.

**O Revisor-IA** auditou o raciocínio em pontos de decisão e pegou três erros que já tinham passado (E1, E10, E16).
