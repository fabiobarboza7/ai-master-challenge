#!/usr/bin/env bash
# Baixa os dois datasets públicos do challenge direto do Kaggle (não exige credencial)
# e confere o SHA-256 dos CSVs usados em toda a análise.
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p raw

fetch() {
  local slug="$1" zip="raw/$(echo "$1" | tr '/' '_').zip"
  if [[ ! -f "$zip" ]]; then
    echo "baixando $slug ..."
    curl -fsSL -o "$zip" "https://www.kaggle.com/api/v1/datasets/download/$slug"
  fi
  unzip -o -q "$zip" -d raw
}

fetch suraj520/customer-support-ticket-dataset
fetch adisongoh/it-service-ticket-classification-dataset

sha256sum_portable() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi; }

check() {
  local file="$1" expected="$2" actual
  actual="$(sha256sum_portable "raw/$file" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "ATENÇÃO: $file difere da versão analisada (sha256 $actual)." >&2
    echo "Os números do relatório foram gerados com sha256 $expected." >&2
    exit 1
  fi
  echo "ok  $file"
}

check customer_support_tickets.csv b06a9cde84da65db388bd964d75f88ee1eed96607cf75d0c35f09c3f11bf8bea
check all_tickets_processed_improved_v3.csv 044fdace33fa564e1e60453f2941dafc95539c99878b0d32746950394b9dd4d4
