# Harness local

## 2026-09-25 — núcleo 1.0 candidato

- Baseline verificável e comentários corrigidos sem mudança de valores ativos.
- Orientação global curta, roteamento tipado, recibos, oito fixtures, busca seletiva, handoff, perfis opt-in, inventário de worktrees e adaptador externo desligado.
- Microamostra e um par E02 Sol/high–Sol/medium concluídos; nenhuma rota promovida. Plugins corrigidos instalados; validação E04/E08 no app e observação longitudinal permanecem pendentes.

## 2026-09-25 — candidato local de release

- 19 testes do harness e gates E01/E02/E05 passaram; 17 controles negativos estruturais E03/E04/E08 foram detectados. Revisão factual e humana permanece pendente.
- Recuperação seletiva H06 lê em fluxo, revela fontes ausentes e expande linhas longas. Default global e sete rotas permanecem no baseline.
- Registro em `releases/20260925T1420Z-core-candidate/receipt.json`; candidato não equivale a validação de produção.
- H04 corrigido para não declarar sucesso em JSONL truncado, zero em reset acumulado ou subcontagens impossíveis; cinco fluxos salvos foram reprocessados sem divergência.
- Canário E03 de uma chamada não aceito: alegação de cinco fontes abertas sem cinco aberturas identificáveis no trace CLI; 156.342 tokens de entrada. Gate de qualidade da candidata falhou, sem promoção.
- Gate H05 revisado: alegação de fonte aberta exige recibo observável por URL. O canário E03 salvo agora falha também no gate estrutural; 20 testes e 18 controles negativos passaram.

## 2026-09-25 — candidato local v2

- E03 com fontes atribuídas ao harness, E04 contrato v2 e E08 fixture v1.1 passaram canários limitados a texto/estado. Falhas iniciais permanecem em recibos históricos.
- 20 testes, 18 controles negativos, 11 recibos CLI e rollback com hashes; sete rotas continuam no baseline.
- Registro em `releases/20260925T1516Z-core-candidate-v2/receipt.json`. Observação de dez tarefas reais ou janela de duas semanas, revisão humana e exposição MUSE no app seguem pendentes; produção não validada.

## 2026-09-25 — candidata local v6 e verificações posteriores

- A candidata v6 ativou o observador H15 restrito à release; 26 testes passaram. Nenhuma tarefa real foi registrada, e validação de produção permanece pendente.
- O manifesto completo de 115 registros restaurou 73 hashes de baseline e reaplicou 73 hashes ativos em cópia isolada; os 26 testes passaram após a reaplicação. O processo do app e o estado externo dos plugins não foram revertidos nesse ensaio.
- Quatro referências staged históricas foram reparadas com backups posteriores de mesmo SHA-256; o manifesto não aponta mais para essas versões sobrescritas.
- H12 preservou os três worktrees. Referências NEXUS foram conferidas: `<workspace>/nexus` está ausente, `<workspace>/NEXUS OS\nexus` existe e seu `.codex\hooks.json` está ausente. Nenhuma referência foi apagada.
- A sonda local de skills achou caminhos explicitamente referenciados para 21/26 skills em argumentos de ferramentas. Isso não prova uso produtivo, desuso das demais nem economia de tokens; nenhuma skill foi desativada.
- Sete rotas permaneceram no baseline. H07/H13 não foram promovidos; H15 aguarda observação longitudinal de tarefas reais.

## 2026-09-25 — E07: argv literal verificado

- O provedor falso agora devolve os argumentos recebidos; o teste confirma round-trip exato de argumento com espaços, aspas, metacaracteres de shell e barra invertida, além do texto de stdin.
- 27 testes do harness passaram. O manifesto contém 118 registros de mudanças; o rollback foi ensaiado em cópia isolada. Nenhum provedor externo foi acionado.

## 2026-09-25 — candidata local v7

- Registro em `releases/20260925T1627Z-core-candidate-v7/receipt.json` após a correção E07. A suíte ativa passou 27 testes; sete rotas continuam no baseline.
- Observador H15 permanece restrito à release e sem tarefa real elegível; a janela longitudinal e a revisão de custo total seguem pendentes. Esta candidata não é validação de produção.
