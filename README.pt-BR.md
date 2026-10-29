# codex-field-harness

**Eu faço meu setup de Codex falhar antes de confiar nele.**

Eu tinha mais de mil sessões de Codex, sete perfis, plugins, skills e AGENTS.md espalhados por dezenas de repositórios. Mesmo assim, não sabia responder uma pergunta simples: o setup está melhor ou só parece melhor?

Este repositório é a minha resposta: um harness que roda casos congelados no meu Codex CLI, com gates que decidem por código, controles negativos que provam que o gate consegue reprovar, e recibo de cada execução. Nada é promovido sem evidência.

**Sendo direto sobre o que tem aqui:** construí isso em um dia (25/09/2026), dentro das minhas próprias sessões de Codex. Até agora são 11 execuções reais de modelo. Os testes verificam o próprio harness (roteamento, recibos, gates), não a qualidade do Codex. É um instrumento de medição com um achado documentado, ainda não um benchmark.

## O achado

Num caso de pesquisa com fontes (E03), uma execução devolveu uma resposta bem escrita, citando cinco fontes, e consumiu 156.342 tokens de entrada. Isso dá de 4 a 5 vezes mais que qualquer outra execução.

O gate reprovou. O trace não mostrava cinco aberturas de fonte. O modelo disse que leu, e o registro não confirmava.

Depois disso:
1. Toda alegação de fonte aberta passou a exigir um recibo por URL.
2. A execução reprovada virou controle negativo permanente.
3. A release não foi promovida, e as sete rotas continuaram no baseline.

Se o time não consegue separar "o agente fez" de "o agente disse que fez", qualquer discussão sobre adoção está em cima de areia.

## Como uso

1. `python -m pytest -q harness/tests`: o harness se testa primeiro.
2. Rodo um caso no setup atual (`codex exec -p <perfil> ...`) e confiro com `check_cases.py` / `static_gate.py`.
3. Mudo **uma** coisa (AGENTS.md, perfil, esforço, skill) e rodo o mesmo caso de novo.
4. Gero o recibo. Só promovo se o gate aprovar.

Os oito casos, as notas de produto e a tabela com todas as execuções estão no [README em inglês](README.md). O desenho de um workshop de 60 minutos está em [`workshop/`](workshop/), ainda não testado com um time externo.

João Lozano · AIdeas Lab · São Paulo · licença MIT
