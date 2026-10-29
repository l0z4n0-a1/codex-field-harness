# codex-field-harness

**Antes de confiar no meu setup de Codex, eu faço ele falhar.**

Este repositório é o harness de avaliação que uso no meu próprio Codex CLI. Ele tem casos de teste congelados, gates determinísticos, controles negativos, recibos de execução e uma regra de promoção: nenhuma rota de modelo, perfil ou instrução é promovida sem evidência.

Tudo começou com uma pergunta. Eu tinha mais de 1.000 sessões de Codex, 7 perfis, plugins, skills e AGENTS.md espalhados por dezenas de repositórios, e nenhuma resposta honesta para "esse setup é melhor mesmo, ou só parece melhor?"

## O caso que mudou tudo

Rodei um canário de uma chamada no **E03**, uma pesquisa com fontes. A resposta citava cinco fontes, estava bem escrita e consumiu **156.342 tokens de entrada**.

O gate reprovou. No trace não havia cinco aberturas de fonte identificáveis. O modelo *disse* que leu cinco fontes, e o registro observável não sustentava isso.

O que mudou:
1. O gate H05 passou a exigir **recibo observável por URL** para qualquer alegação de fonte aberta.
2. O canário salvo passou a falhar também no gate estrutural e ficou como controle negativo permanente.
3. A candidata **não foi promovida**. As sete rotas continuaram no baseline.

**Eloquência não é evidência.** Se o time não consegue separar "o agente fez" de "o agente disse que fez", o problema não é adoção. É medição.

## Estado atual, sem maquiagem

- 27 testes passam. Os gates E01, E02 e E05 passam. 18 controles negativos estruturais são detectados.
- 7 releases candidatas com hash. O rollback foi ensaiado em cópia isolada.
- Ainda pendente: revisão humana de E03, E04 e E08, e uma janela de 10 tarefas reais. **Nada disso é validação de produção**, e cada release diz isso.

A versão completa, com os oito casos, as lições e as notas de produto, está no [README em inglês](README.md). O kit de workshop de 60 minutos está em [`workshop/`](workshop/).

João Lozano · AIdeas Lab · São Paulo · Licença MIT
