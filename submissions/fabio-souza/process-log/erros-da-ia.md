# Onde a IA errou e como corrigi

Dezesseis erros reais desta sessão. Oito mudaram um número ou uma conclusão e estão detalhados;
oito foram pegos antes de virarem problema e estão resumidos no fim.

Os que geraram correção de código aparecem como commits `fix:` no `git log`.

## Os oito que mudaram uma conclusão

| # | Erro | Como foi pego | O que mudou |
|---|------|---------------|-------------|
| **E7** | **A regra de corte que a própria IA tinha pré-registrado era falha.** "Precisão média da fila ≥ 90%" deixa entrar ticket de baixa confiança, compensado na média pelos de confiança alta. O corte foi parar em 0,0, aceitando tickets que acertam 0–52% | Acerto por faixa de confiança na validação: tickets de 0,3–0,5 acertam 41–49% e todos entrariam na fila automática | Regra trocada para acerto **por ticket** (regressão isotônica). O desvio do pré-registro foi documentado e levado ao Fabio, que confirmou (D9). Sem isso, um cliente com confiança 0,35 teria ~60% de chance de ir para a fila errada, com o painel exibindo "precisão 90%" |
| **E10** | **ROI contava o erro duas vezes:** descontava o custo do ticket roteado errado, sem somar a triagem manual que esse mesmo ticket pulou | Revisor-IA pediu para conferir penalidade dupla | Ganho por ticket = t × (1 − (1 − precisão) × k). O ponto de empate real é **75%**, não 80%. Coberto por teste |
| **E9** | **Número inflado:** a trava de domínio foi reportada barrando **95%** do texto estranho, inclusive numa mensagem de commit. Contava fragmentos de 1 letra que o modelo descarta | Ao reescrever a regra em TypeScript, a tokenização foi unificada num módulo só e o número caiu | **40,8%**, e 17,6% do texto de outro domínio ainda passa. A conclusão virou "proteção parcial": o que resolve é treinar com dados da própria operação |
| **E1** | A taxa de aprovação por desafio contava "PR parado aguardando ajuste" como reprovação | Revisor-IA apontou o problema de denominador | Métrica trocada para "aprovado na 1ª review": 002 = 68%. A recomendação continuou a mesma, agora pelo motivo certo |
| **E3** | Kolmogorov-Smirnov aplicado à idade, que é inteira. Os empates geraram p = 0,001 ("idade não uniforme") | O p destoava de todas as outras distribuições | Qui-quadrado: p = 0,55. Sem a correção, um falso achado contradiria a conclusão certa |
| **E4** | V de Cramér sem correção de viés: com 42 produtos × 16 assuntos, dá ~0,07 **mesmo com campos sorteados** | V = 0,070 com p = 1,0 é contraditório | V de Bergsma (2013): todos os pares entre 0,000 e 0,016. Sem isso, associações inexistentes apareceriam como reais |
| **E15** | Dois números escritos à mão não batiam com o JSON que citam: "treinado em 47.837 tickets" e "testado em 7.026 que nunca viu" (os 7.026 **fazem parte** dos 47.837; o treino são 32.889), e F1 0,85 para o modelo escolhido, que tem 0,844 | Conferência final de cada número contra a sua fonte, relendo os JSON por script | Números corrigidos. A tabela de candidatos passou a mostrar os 10 comparados, e não 7, com a ressalva de que o escolhido não é o melhor em acurácia nem em F1 |
| **E16** | A seção "o que eu adicionei" dizia que o critério do piloto era **mais exigente** que o teste. Exigir ≥ 95% quando o teste mediu 96,4% é o contrário | Revisor-IA, lendo a seção já commitada | Texto trocado pelo que o log sustenta. Na mesma passada caiu o "antes de a IA abrir qualquer CSV": os arquivos já estavam baixados, e o certo é que nenhuma coluna tinha sido lida (primeira inspeção às 16:07, depois da resposta das 16:06) |

## Os oito pegos antes de virarem problema

- **E2 — filtro de stage vazio.** `git ls-files --exclude-from` não listava nenhum arquivo. Pego num teste com `node_modules` e `.env` falsos, antes do primeiro commit. Virou um script que bloqueia o commit com dependência, dado bruto, `.env`, arquivo acima de 3 MB ou alteração fora da pasta. O remendo óbvio (`git add -f .`) teria posto `node_modules` no PR — motivo de reprovação de 4 candidatos.
- **E5 — binário no commit.** Um `.npy` de 380 KB entrou. Pego na revisão do `--stat`, corrigido com `--amend` antes de qualquer push; a trava passou a barrar `.npy/.pkl/.parquet/.zip`.
- **E6 — grade de cortes começando em 0,30.** Com 8 categorias a confiança pode ser 0,125, então os dois cortes caíram no piso: era a grade decidindo, não a regra.
- **E8 — dois números para a mesma coisa.** 60,8% num script e 61,4% noutro. Causa: `fit_transform` difere de `fit` + `transform` em 2,8e-16 e o otimizador para em pontos diferentes. Unificado o caminho.
- **E11 — protótipo quebrado no celular.** A página tinha **6.942 px de largura**: a grade crescia até caber o texto dos botões. Pego na captura em 390 px.
- **E12 — o gráfico escondia o que existia para mostrar.** A coluna de 98–100% achatava as faixas baixas, justamente onde estão os erros. Eixo, corte e ancoragem refeitos.
- **E13 — cenário otimista com R$ 50/h,** contrariando a decisão do Fabio (D11). Custo fixado em todos os cenários.
- **E14 — `run_all.sh` não rodava em clone limpo:** gravava log numa pasta ignorada pelo git. Depois do `mkdir -p`, rodou em 2 min 36 s com saídas idênticas.
