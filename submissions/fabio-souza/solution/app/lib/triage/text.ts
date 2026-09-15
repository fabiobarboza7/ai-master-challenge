// Espelho de solution/analysis/texto.py. Qualquer mudança aqui precisa ser feita lá (o teste de paridade garante).

export function normalize(text: string): string {
  return text
    .replaceAll("{product_purchased}", " ")
    .toLowerCase()
    .replace(/[^a-z]+/g, " ")
    .trim()
}

// Mesmo resultado do tokenizador padrão do scikit-learn ((?u)\b\w\w+\b) sobre texto já normalizado.
export function tokens(normalized: string): string[] {
  return normalized.split(" ").filter((t) => t.length >= 2)
}

export function knownShare(
  normalized: string,
  vocabulary: ReadonlyMap<string, number>
): number {
  const toks = tokens(normalized)
  if (toks.length === 0) return 0
  let known = 0
  for (const t of toks) if (vocabulary.has(t)) known++
  return known / toks.length
}
