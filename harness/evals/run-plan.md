# Plano de avaliação congelado

E01–E08 estão em `cases/`, com oráculos em `oracles/` e hashes em `fixture-manifest.json`. O executor recebe apenas o caso. E01, E02, E05, E06 e E07 têm gates determinísticos; E03, E04 e E08 também exigem julgamento factual e, quando aplicável, revisão humana real. Um modelo não fornece aprovação humana.

Microamostra baseline E02: uma execução Sol/high no CLI PATH 0.153.4, antes da orientação global. Lotes pareados ampliados dependem de teto explícito de consumo. Repetições determinísticas são testes locais, não chamadas de modelo.
