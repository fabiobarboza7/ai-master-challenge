# Registro de decisões

Cada decisão relevante registra **quem decidiu**, com base em quê e quando.

Categorias de "quem decidiu":
- **Fabio** — decisão do candidato.
- **IA (delegada)** — o Fabio pediu explicitamente que a IA decidisse.
- **IA** — decisão técnica tomada pela IA durante a execução.
- **Revisor-IA** — correção feita a partir da auditoria de um segundo modelo.

| # | Data | Decisão | Quem decidiu | Base |
|---|------|---------|--------------|------|
| D1 | 15/09 | Fazer o desafio 002, e não o 001 que já tinha sido iniciado | Fabio, a partir da recomendação da IA | Taxas de aprovação calculadas a partir das reviews públicas; aderência ao perfil de dev |
| D2 | 15/09 | Não versionar dados brutos: script de download com SHA-256 | IA | Reviews públicas criticam dados commitados; os dois datasets baixam sem credencial |
| D3 | 15/09 | **Reembolso e cancelamento nunca são resolvidos pela IA sem aprovação humana** | **Fabio** | Pergunta feita antes de abrir os dados. Resposta: "Reembolso/cancelamento" |
| D4 | 15/09 | Hipóteses de trabalho | IA (delegada) | Resposta do Fabio: "Descubra!". Hipóteses pré-registradas antes da análise |
| D5 | 15/09 | Precisão mínima da fila automática | IA (delegada) | Resposta do Fabio: "Decida por mim". A regra de escolha será fixada **antes** de olhar o conjunto de teste |

## Respostas literais do Fabio às perguntas iniciais (15/09, ~16:05)

As opções de múltipla escolha foram sugeridas pela IA; o Fabio podia marcar ou escrever outra resposta.

1. *"Antes de eu abrir os dados: onde VOCÊ acha que essa operação de suporte mais perde tempo?"* → **"Descubra!"**
2. *"O que a IA NUNCA deve resolver sozinha, sem um humano aprovar?"* → **"Reembolso/cancelamento"**
3. *"Na fila que a IA roteia sozinha, qual a precisão mínima aceitável?"* → **"Decida por mim"**
4. *"Você já está inscrito na vaga no site de vagas da G4?"* → **"Sim, já estou"**
