# Diário de bordo

Escrito durante o trabalho, não reconstruído no fim. Horários em BRT (UTC−3), lidos do log local do Claude Code.

**Quem é quem:** **Fabio**, o candidato · **IA**, o Claude Code (Opus 5) que executou a análise e o código · **Revisor-IA**, um segundo modelo chamado pela IA para auditar o próprio raciocínio.

---

**15:30 — Escolha do desafio.** Pedido do Fabio: *"me diga qual projeto temos maior chances?"* A IA leu as regras e o template, e notou que o avaliador comenta nos PRs à vista de todos. Dessas reviews saíram três exigências que o enunciado não diz: process log auditável, repositório limpo e entrega que reproduza. A primeira leitura desse material teve um erro de método, corrigido depois (E1). Recomendação: **002**, o único que pede protótipo — onde um perfil de dev rende mais. Decisão do Fabio: seguir com o 002.

> Ler as reviews mostrou problemas de dados que outros candidatos já tinham levantado. Aqui eles são **alegações a verificar**, nunca fatos: todo número deste repositório foi recalculado dos CSVs originais. Nenhum código ou texto de outro candidato foi usado, e este log não publica resultado de ninguém além do meu.

**15:53 — Começo.** Branch criada, datasets baixando do endpoint público do Kaggle com conferência de SHA-256. Armadilha: o `.gitignore` do repositório ignora `submissions/`, então é preciso `git add -f` — e o `-f` desliga *todos* os ignores, `node_modules` inclusive. Resolvido com um script de stage que bloqueia o commit se algo proibido aparecer (E2).

**16:01–16:06 — Checkpoint 1: o Fabio decide antes dos dados.** Quatro perguntas, e a IA parou até as respostas. Ele fixou que **reembolso e cancelamento nunca são resolvidos sem uma pessoa** (D3) e delegou explicitamente duas coisas: as hipóteses (*"Descubra!"*) e a precisão mínima (*"Decida por mim"*). Com a delegação por escrito, a IA **pré-registrou** as hipóteses antes de rodar qualquer análise. Nesse momento os arquivos estavam baixados, mas nenhuma coluna tinha sido lida: a primeira inspeção de conteúdo é das 16:07.

**16:10–16:18 — Auditoria dos dois datasets.** Cada alegação pública sobre o Dataset 1 se confirmou: sem data de abertura, tudo cabendo em 27 h, 49,3% das resoluções antes da primeira resposta, nota de satisfação uniforme. Dois achados que as reviews não citavam: **tipo e assunto são sorteados independentes**, e **o texto não prevê nem tipo nem assunto**. No Dataset 2, 12,3% dos tickets têm quase-duplicado — o maior grupo são 976 pedidos de compra idênticos. **Antes de treinar**, o critério de escolha do modelo foi fixado por escrito. Dois erros estatísticos pegos aqui (E3, E4).

**16:20–16:35 — Classificador e mudança de domínio.** O problema sério apareceu na segunda rodada: a regra que a própria IA tinha pré-registrado aceitava tickets que acertam 0–52% (E7). Trocada por acerto **por ticket**, com o desvio documentado. Resultado no teste: **61,4% automáticos com 96,4% certos**. Aplicado ao Dataset 1, o modelo manda 88% para Hardware — a trava de vocabulário barra 41% disso, não os 95% reportados a princípio (E9).

**16:36–16:41 — Checkpoint 2: o Fabio decide com os números na mão.** Precisão de 90% por ticket, regra por ticket em vez da média, IA só roteia em acesso e RH, R$ 35/h. As três primeiras seguiram a recomendação da IA; o custo/hora foi escolha dele, e a mais conservadora das três opções (D8–D11).

**16:44–16:52 — ROI.** Função paramétrica com a origem declarada de cada insumo: 34,7 h/mês na base do brief. O Revisor-IA pediu para conferir penalidade dupla e ela existia (E10): o empate real é 75%, não 80%.

**17:00–19:15 — Protótipo.** Construído sobre o scaffold Next.js do Fabio. Modelo exportado com 3 casas decimais, com filas 100% iguais às do modelo completo, e **258 testes** de paridade Python ↔ TypeScript. A verificação visual em celular e modo escuro achou dois defeitos sérios: a página com 6.942 px de largura (E11) e o gráfico escondendo justamente os erros que ele existe para mostrar (E12).

**19:15–19:50 — Reprodução e conferência.** Num clone novo, `run_all.sh` rodou em 2 min 36 s com saídas idênticas byte a byte, exceto o ECE do SVM na 9ª casa decimal. Depois, cada número dos documentos foi conferido contra o JSON que ele cita: dois não batiam (E15).

**19:54 — Checkpoint 3: as decisões de operação voltam para o Fabio.** A IA listou o que ainda estava decidido por ela e que, por ser decisão de negócio, cabia a ele. Ele decidiu o critério do piloto (D13), aceitou o custo dos falsos positivos da regra de risco (D14) e fixou a ordem de execução, formulário antes da triagem (D15). O múltiplo do custo do erro ele devolveu para a IA, que manteve 4× e registrou o porquê (D12). O Revisor-IA leu a versão final e achou uma afirmação invertida na seção do candidato (E16).

**20:10 — Auditoria contra o enunciado.** Pergunta do Fabio: *"o que fizemos está de acordo com o enunciado, as regras e dicas? Estamos mostrando algo em que não deveríamos?"* Cada item pedido foi conferido contra o que a entrega respondia, e apareceram duas coisas.

- **Uma pergunta do enunciado estava sem resposta** (E17). O Diretor pergunta quais *combinações* de canal, prioridade e tipo geram os piores tempos; a análise testava as três variáveis isoladas. As 80 células passaram a ser testadas com Holm — e o resultado virou o achado mais forte do diagnóstico.
- **O log publicava resultado de outras pessoas.** A versão anterior trazia taxa de aprovação por desafio e contagem de reprovados, tirados das reviews públicas. É informação pública, mas é resultado de outros candidatos, num PR que eles leem. Saiu da entrega. O que ficou é o que diz respeito a este trabalho: quais exigências foram aprendidas ali e como elas mudaram a submissão.
- **Varredura de dados pessoais:** nenhum nome, e-mail, idade ou gênero foi exportado para o protótipo; só o texto do ticket. Dados brutos não vão no repositório.
