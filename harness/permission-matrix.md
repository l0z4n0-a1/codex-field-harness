# Perfis de execução

| Situação | Seleção | Escrita shell | Rede shell | Observação |
|---|---|---|---|---|
| Inspeção | `codex exec -p harness-readonly` | Negada pela política de sandbox | Política do host | Conectores têm autorizações próprias. |
| Edição local | `codex exec -p harness-workspace` | Limitada ao workspace | Desligada no perfil | Roots adicionais exigem mudança explícita. |
| Default atual | Sem perfil | Full access configurado | Conforme host | Mantido como encontrado. |

Os perfis são arquivos `$CODEX_HOME/<nome>.config.toml` e podem ser sobrepostos por flags CLI ou configuração de projeto confiável. Um prompt não concede nem remove permissão. Teste de parsing e seleção de perfil não prova que a sandbox do sistema operacional bloqueou um comando. A regra genérica PowerShell em `rules/default.rules` merece revisão separada, com comandos concretos afetados; nenhuma regra existente foi removida nesta release.
