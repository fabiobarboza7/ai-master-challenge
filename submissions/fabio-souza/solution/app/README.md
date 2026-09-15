# Triagem assistida: protótipo

Aplicação 100% no navegador. Recebe um ticket e decide entre três filas:

- **automática:** segue direto para a fila certa;
- **atendente confirma:** o atendente escolhe entre 2 sugestões;
- **triagem humana.**

Para cada decisão, mostra a regra que decidiu. Também mostra o mesmo critério aplicado aos 7.026 tickets de teste e simula a economia de tempo.

## Como rodar

Requer Node 20+ e pnpm. Os dados do modelo já estão em `public/data/`; não é preciso rodar o Python.

```bash
pnpm install
pnpm dev          # http://localhost:3000
pnpm test         # 258 testes: paridade com o Python, regras de risco, backtest e ROI
pnpm typecheck
pnpm build        # exportação estática em out/ (sirva com qualquer servidor de arquivos)
```

As fontes vêm do Google Fonts durante o build. Sem internet, o Next usa a fonte do sistema.

## Como funciona

| Arquivo | O que faz |
|---|---|
| `lib/triage/text.ts` | Normalização e tokenização. Espelho de `analysis/texto.py` |
| `lib/triage/model.ts` | TF-IDF (1–2 gramas, tf sublinear, L2) + softmax da regressão logística, com os pesos de `public/data/model.json` |
| `lib/triage/policy.ts` | Aplica as regras em ordem: (1) reembolso/cancelamento → humano; (2) texto fora do domínio → humano; (3) confiança ≥ corte automático → fila automática; (4) confiança ≥ corte assistido → atendente confirma; (5) o resto → humano |
| `lib/triage/backtest.ts` | Recalcula as filas dos 7.026 tickets de teste para cada precisão escolhida |
| `lib/roi.ts` | Economia mensal. Espelho de `analysis/roi.py` |
| `components/` | Telas: mesa de triagem, resultado no teste, economia |

Todos os arquivos de `public/data/` são gerados por `solution/analysis/07_exportar_app.py`.

- **Pesos arredondados a 3 casas:** no teste, 100% das filas e categorias são iguais às do modelo em precisão total.
- **Paridade (`tests/triage.test.ts`):** 245 tickets calculados no Python, cada um com mesmo texto normalizado, mesma fração de palavras conhecidas, probabilidades com diferença menor que 1e-9, e a mesma fila e motivo.
- **Backtest:** o TypeScript reproduz exatamente as contagens de fila do Python (4.260 / 1.817 / 949).

## Limites

- **Modelo de outro domínio.** Foi treinado com tickets de TI interna. Para suporte ao consumidor, é preciso treinar com tickets rotulados da própria operação.
- **Sem integração.** Não há ligação com help desk, autenticação nem registro das decisões: é uma demonstração da política de filas.
