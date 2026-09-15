# Ficha do modelo de triagem

## Uso pretendido

Classificar o texto de tickets de TI em 8 categorias e decidir entre fila automática, assistida e humana.

- **Não usar em outro domínio** sem re-treinar (seção "Mudança de domínio").
- **Não usar para decidir reembolso, cancelamento, acesso ou RH.**

## Dados e divisão

- **Treino:** Dataset 2 (IT Service Ticket Classification), 47.837 tickets reais, já em minúsculas e sem dígitos. Categorias: Hardware 28,5%, HR Support 22,8%, Access 14,9%, Miscellaneous 14,8%, Storage 5,8%, Purchase 5,2%, Internal Project 4,4%, Administrative rights 3,7%.
- **Divisão:** 70/15/15 (32.889 / 7.922 / 7.026), estratificada e **por grupos de quase-duplicados** (cosseno ≥ 0,8), para que textos quase iguais não fiquem de lados diferentes.
  - Com divisão aleatória, a acurácia seria **86,8%** e não 84,9%; a cobertura automática, 58,7% e não 54,7%, recalculando os cortes em cada conjunto.
- **Seleção:** modelo e cortes escolhidos só na validação.

## Candidatos comparados na validação

"Cobertura automática" é a fração de tickets com acerto local ≥ 90%: o critério usado na escolha.

Os dez candidatos, na ordem em que o script os avalia:

| Modelo | Acurácia | F1 macro | Cobertura automática |
|---|---|---|---|
| Classe majoritária | 25,8% | 0,05 | 0% |
| Vizinho mais próximo (cosseno) | 71,8% | 0,68 | 20,5% |
| TF-IDF 5 mil termos + regressão logística (C = 2) | 86,0% | 0,85 | 62,7% |
| TF-IDF 5 mil termos + regressão logística (C = 8) | 85,1% | 0,84 | 61,2% |
| **TF-IDF 20 mil termos + regressão logística (C = 2)** | **86,1%** | **0,84** | **64,6%** |
| TF-IDF 20 mil termos + regressão logística (C = 8) | 85,8% | 0,85 | 59,1% |
| TF-IDF 50 mil termos + regressão logística (C = 2) | 85,9% | 0,84 | 63,2% |
| TF-IDF 50 mil termos + regressão logística (C = 8) | 86,2% | 0,85 | 61,7% |
| TF-IDF 50 mil termos + SVM linear calibrado | 86,3% | 0,85 | 60,2% |
| TF-IDF 50 mil termos + Naive Bayes complementar | 81,5% | 0,79 | 43,0% |

O escolhido **não é o melhor em acurácia nem em F1** — é o melhor no critério pré-registrado. A diferença de acurácia para o primeiro colocado (SVM, 86,3%) é de 0,2 ponto; a de cobertura automática, 4,4 pontos a favor da regressão logística.

Pela regra pré-registrada de precisão **média** da fila, o SVM "venceria" com 81% de cobertura. Mas no corte dessa regra os tickets acertavam só 52%, e por isso a regra foi trocada (erro E7).

## Desempenho no teste (7.026 tickets, avaliação única)

- **Acurácia geral:** 84,9%.
- **Fila automática (confiança ≥ 0,78):** 61,4% dos tickets, 96,4% certos (IC 95%: 95,8%–96,9%). Todas as 8 categorias passaram no critério de ≥ 85% por categoria.
- **Fila assistida (0,485 ≤ confiança < 0,78):** 26,4% dos tickets, a certa entre as 2 sugestões em 94,0%.
- **Fila humana:** 12,2% dos tickets; o modelo acerta 49% nessa faixa.
- **Sensibilidade** (cortes escolhidos na validação para cada meta):

  | Meta | Cobertura automática | Certos |
  |---|---|---|
  | 85% | 65,3% | 95,8% |
  | 90% | 61,4% | 96,4% |
  | 95% | 42,8% | 98,4% |

- **Confusões mais comuns:** HR Support → Hardware (7,8% do RH), Miscellaneous → Hardware (10,2%), Access → Hardware (8,1%). Hardware funciona como categoria "ímã".
- **Otimismo do corte:** no corte de 0,78, o acerto local foi 90,5% na validação e ~88% no teste.

## Mudança de domínio (Dataset 1, suporte ao consumidor)

- **O modelo não transfere.** Nos 8.469 textos do Dataset 1, **88% vão para Hardware** e 28,6% passariam no corte automático.
- **Nenhuma trava simples resolve** (mesmo critério de corte, com perda máxima de ~1% do próprio domínio):

  | Trava | Barra do Dataset 1 |
  |---|---|
  | Fração de palavras conhecidas (adotada) | 40,8% |
  | Similaridade com o ticket mais próximo do treino | 18,6% |
  | Similaridade com o centroide da categoria | 0% |

- **Consequência:** o modelo precisa ser treinado com tickets da operação onde vai rodar, e a taxa de correção humana precisa ser monitorada.
- **Curva de aprendizado** (teste, média de 3 amostras):

  | Tickets rotulados | Fila automática | Certos |
  |---|---|---|
  | 500 | 15% | 94,3% |
  | 1 mil | 25% | 95,2% |
  | 2 mil | 34% | 95,8% |
  | 5 mil | 40% | 97,3% |
  | 10 mil | 47% | 97,3% |
  | 20 mil | 57% | 96,6% |
  | 33 mil | 61% | 96,4% |

## Exportação para o protótipo

- **Pesos:** arredondados a 3 casas decimais. Nos 7.026 tickets de teste, filas e categorias ficam 100% iguais às do modelo em precisão total (maior diferença de probabilidade: 0,0005).
- **Paridade:** o TypeScript reproduz o Python em 245 casos (probabilidades com diferença < 1e-9, mesma fila e motivo) e as contagens exatas do backtest (`solution/app/tests`).

## Como re-treinar

1. Trocar `solution/data/raw/all_tickets_processed_improved_v3.csv` pelos tickets da operação, com colunas `Document` (texto) e `Topic_group` (fila final).
2. Rodar `solution/run_all.sh`.

Os cortes são recalculados na validação e o protótipo recebe o novo `model.json`.
