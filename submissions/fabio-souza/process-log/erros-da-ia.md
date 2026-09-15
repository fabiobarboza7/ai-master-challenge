# Onde a IA errou e como foi corrigido

Só erros reais desta sessão, na ordem em que aconteceram, cada um com a evidência de como foi pego.
A sessão completa do Claude Code está em `chat-exports/`.

| # | Etapa | Erro | Como foi detectado | Correção | Impacto se passasse |
|---|-------|------|--------------------|----------|---------------------|
| E1 | Escolha do desafio | A taxa de aprovação por desafio contava "PR parado aguardando ajuste" como reprovação: 001 aparecia com 38% | Revisor-IA (segundo modelo auditando o raciocínio) | Métrica trocada para "aprovado na 1ª review" (001 = 29%, 002 = 68%), com a ressalva sobre candidatos que não voltaram após o feedback | Recomendação certa pelo motivo errado |
| E2 | Setup do repositório | Filtro de stage com `git ls-files --exclude-from=.gitignore` não listava **nenhum** arquivo | Teste negativo com um `node_modules` e um `.env` falsos, antes do primeiro commit | Script que percorre a pasta com lista de exclusão explícita, mais uma trava que aborta o commit com arquivo proibido, arquivo acima de 3 MB ou alteração fora da pasta | Commit vazio, ou, no remendo óbvio (`git add -f .`), `node_modules` no PR: motivo de reprovação de 4 candidatos |
| E3 | Auditoria do Dataset 1 | Teste de Kolmogorov-Smirnov aplicado à idade, que é inteira (18–70). KS pressupõe variável contínua; os empates geraram p = 0,001 ("idade não uniforme") | Revisão da saída pela IA: o p destoava de todas as outras distribuições | Qui-quadrado de aderência por idade: p = 0,55, compatível com uniforme | Um falso "achado" que contradiz a conclusão correta |
| E4 | Auditoria do Dataset 1 | V de Cramér sem correção de viés. Com 42 produtos × 16 assuntos, o V fica em ~0,07 **mesmo com campos sorteados**, e o relatório compararia isso com um "V mínimo detectável" de 0,027 | Revisão da saída pela IA: V = 0,070 com p = 1,0 é contraditório | V com correção de viés de Bergsma (2013): todos os pares ficaram entre 0,000 e 0,016 | Associações inexistentes entre produto e assunto apresentadas como fracas porém reais |
