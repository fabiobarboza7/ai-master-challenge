#!/usr/bin/env bash
# Reproduz a solução do zero: dados -> análise -> exportação -> testes -> build do protótipo.
# Requer: uv (ou Python 3.12 com pip), Node 20+ e pnpm. Leva ~3 minutos numa máquina comum.
set -euo pipefail
cd "$(dirname "$0")"

echo "== 1/5 dados (Kaggle, sem credencial, com SHA-256)"
bash data/download.sh

echo "== 2/5 ambiente Python"
cd analysis
if command -v uv >/dev/null; then
  uv venv --python 3.12 .venv -q
  uv pip install -q --python .venv/bin/python -r requirements.txt
else
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
PY=.venv/bin/python
mkdir -p outputs/cache

echo "== 3/5 análise (01-07)"
for script in 01_auditoria_ds1.py 02_auditoria_ds2.py 03_classificador.py 04_transferencia_ds1.py \
              05_curva_de_aprendizado.py 06_roi.py 07_exportar_app.py; do
  echo "-- $script"
  $PY "$script" > "outputs/cache/${script%.py}.log" 2>&1 || { cat "outputs/cache/${script%.py}.log"; exit 1; }
done
$PY -m pytest -q tests

echo "== 4/5 protótipo: dependências e testes"
cd ../app
pnpm install --frozen-lockfile
pnpm test
pnpm typecheck

echo "== 5/5 build estático (out/)"
pnpm build
echo "Pronto. Rode 'pnpm dev' em solution/app ou sirva solution/app/out."
