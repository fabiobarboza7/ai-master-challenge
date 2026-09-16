# Registro de decisões

Cada decisão relevante registra **quem decidiu**, com base em quê e quando.

Categorias de "quem decidiu":
- **Fabio** — decisão do candidato.
- **IA (delegada)** — o Fabio pediu explicitamente que a IA decidisse.
- **IA** — decisão técnica tomada pela IA durante a execução.
- **Revisor-IA** — correção feita a partir da auditoria de um segundo modelo.

| # | Data | Decisão | Quem decidiu | Base |
|---|------|---------|--------------|------|
| D1 | 15/09 | Fazer o desafio 002, e não o 001 que já tinha sido iniciado | Fabio, a partir da recomendação da IA | É o único que pede protótipo funcional, onde um perfil de dev rende mais; e o que mais se aproxima da descrição da vaga |
| D2 | 15/09 | Não versionar dados brutos: script de download com SHA-256 | IA | Reviews públicas criticam dados commitados; os dois datasets baixam sem credencial |
| D3 | 15/09 | **Reembolso e cancelamento nunca são resolvidos pela IA sem aprovação humana** | **Fabio** | Pergunta feita antes de abrir os dados. Resposta: "Reembolso/cancelamento" |
| D4 | 15/09 | Hipóteses de trabalho | IA (delegada) | Resposta do Fabio: "Descubra!". Hipóteses pré-registradas antes da análise |
| D5 | 15/09 | Precisão mínima da fila automática: 90% | IA (delegada) | Resposta do Fabio: "Decida por mim". Modelo de custo: rotear errado custa ~4× a triagem, o que dá empate em 80%; mais 10 pontos de margem para mudança de domínio. Fixado antes de treinar |
| D6 | 15/09 | Trocar a regra de corte de "precisão média da fila ≥ 90%" para "acerto **local** ≥ 90% para cada ticket da fila" | IA (delegada) | Erro E7: a regra média põe na fila automática tickets que acertam 0–52%. Decidido olhando só a validação; o teste foi avaliado para as duas regras. **Levado ao Fabio para confirmação no checkpoint 2** |
| D7 | 15/09 | Modelo: TF-IDF (1–2 gramas, 20 mil termos) + regressão logística (C = 2) | IA | Maior cobertura pela regra marginal na validação (64,6%). SVM e Naive Bayes perdem; o modelo cabe no navegador (~20 mil termos) |
| D8 | 15/09 16:41 | Precisão mínima **por ticket** da fila automática: **90%** | **Fabio** (aceitou a recomendação da IA) | Opções mostradas com o resultado no teste: 85% → 65% automático; 90% → 61%; 95% → 43% |
| D9 | 15/09 16:41 | Regra de corte **por ticket (marginal)** no lugar da média da fila | **Fabio** (aceitou a recomendação da IA) | Explicação dada: a regra média aceitava tickets que acertam ~45%, escondidos na média |
| D10 | 15/09 16:41 | **Acesso/permissões e RH: a IA só roteia; conceder acesso e tratar dado pessoal é sempre humano** | **Fabio** (aceitou a recomendação da IA) | Alternativas mostradas: executar casos simples, como reset de senha; executar tudo |
| D11 | 15/09 16:41 | Custo por hora de atendente para o ROI: **R$ 35/h** | **Fabio** (escolha própria; não havia recomendação) | Opções: R$ 35/h (júnior), R$ 50/h (pleno), só horas. Escolheu a mais conservadora |
| D12 | 15/09 19:54 | Múltiplo do custo do erro no ROI: **4×** a triagem manual | IA (delegada) | Levado ao Fabio com o efeito de cada opção (2× → empate em 50% e 36,9 h/mês; 4× → 75% e 34,7 h; 8× → 87,5% e 30,5 h). Resposta: *"escolha o que faz mais sentido"*. Mantido 4×: é o único valor cujo empate (75%) fica abaixo da precisão medida (96,4%) com folga, sem tornar o ganho otimista |
| D13 | 15/09 19:54 | Critério para manter a fila automática ligada no piloto: **acerto ≥ 95% por 2 semanas e correções humanas ≤ 5%** | **Fabio** (confirmou a proposta da IA, vendo as alternativas) | Alternativas mostradas: mais duro (≥ 97% / ≤ 3%, que provavelmente restringe o piloto a poucas categorias) e mais frouxo (≥ 93% / ≤ 7%, que cobre mais desde a semana 3) |
| D14 | 15/09 19:54 | **Aceitar os falsos positivos da regra por palavra-chave** (0,7% dos tickets de TI vão para humano à toa, tipo "cancel meeting") | **Fabio** | Alternativas mostradas: usar só o campo de tipo (zera o falso positivo, mas quem erra o tipo tem o reembolso roteado pela IA) ou aplicar a palavra-chave só em confiança baixa. Escolheu errar para o lado seguro, coerente com D3 |
| D15 | 15/09 19:54 | Ordem de execução: **formulário de compras → triagem → resposta gêmea** | **Fabio** (confirmou a proposta da IA, vendo as alternativas) | Alternativas mostradas: triagem primeiro (maior ganho isolado, 34,7 h/mês, e é o que o brief pede) ou só instrumentar por 6 semanas antes de automatizar qualquer coisa |
| D16 | 15/09 20:40 | Publicar o protótipo na Vercel e pôr o link no README | **Fabio** | Pedido dele depois de ver o PR aberto. O enunciado pede "não quero só um PowerPoint, quero ver algo rodando": o link dispensa o avaliador de rodar qualquer coisa. Exportação estática, sem back-end nem dado pessoal |

## Checkpoint 3 — respostas literais do Fabio (15/09 19:54), sobre as decisões de operação

Com a submissão pronta, a IA listou o que ainda estava decidido por ela e que era decisão de negócio, e devolveu cada uma com o efeito numérico de cada alternativa.

1. *"Quanto custa um ticket roteado para a fila errada, em relação ao custo de triar um ticket à mão?"* → **"escolha o que faz mais sentido"** (delegado de volta à IA; ver D12)
2. *"No piloto de 6 semanas, qual critério para manter a fila automática ligada?"* → **"Manter: ≥95% e ≤5% de correção"**
3. *"A regra de reembolso/cancelamento também olha palavra-chave no texto, e isso manda 0,7% dos tickets de TI para humano à toa. Aceita esse custo?"* → **"Aceitar — errar para o lado seguro"**
4. *"Em que ordem a operação deve executar?"* → **"Manter: formulário primeiro"**

## Checkpoint 2 — respostas literais do Fabio (15/09 16:41), depois de ver os resultados

Antes das perguntas, a IA mostrou o resumo: o Dataset 1 não permite diagnosticar gargalos; o classificador roteia 61% com 96% de precisão; o modelo fica "confiante" em texto de outro domínio.

1. *"Qual precisão mínima POR TICKET a fila automática deve exigir?"* → **"90% (Recommended)"**
2. *"A regra que eu mesmo tinha pré-registrado ('precisão MÉDIA da fila ≥ 90%') aceitava tickets que acertam só ~45%, escondidos na média. Qual regra usar?"* → **"Por ticket (Recommended)"**
3. *"Tickets de Acesso/Permissões e de RH (dados pessoais): a IA pode só ROTEAR ou também EXECUTAR a solução?"* → **"Só rotear (Recommended)"**
4. *"Para converter horas economizadas em reais: qual custo por hora de um atendente usar como premissa?"* → **"R$ 35/h"**

## Respostas literais do Fabio às perguntas iniciais (15/09 16:06)

As opções de múltipla escolha foram sugeridas pela IA; o Fabio podia marcar ou escrever outra resposta.

1. *"Antes de eu abrir os dados: onde VOCÊ acha que essa operação de suporte mais perde tempo?"* → **"Descubra!"**
2. *"O que a IA NUNCA deve resolver sozinha, sem um humano aprovar?"* → **"Reembolso/cancelamento"**
3. *"Na fila que a IA roteia sozinha, qual a precisão mínima aceitável?"* → **"Decida por mim"**
4. *"Você já está inscrito na vaga no site de vagas da G4?"* → **"Sim, já estou"**
