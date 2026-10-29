# Recuperação seletiva

Busque nomes e descrições antes de abrir corpos de skills ou ferramentas. Comece com até oito candidatos. Expanda quando a cobertura for insuficiente. Para arquivos, liste caminhos e seções, leia os trechos necessários e preserve o caminho da fonte integral. `retrieval.py --read-lines PATH START END` lê só um intervalo exato após a busca; `complete_range=false` indica fim de arquivo antes de END. A opção `retrieval.py --expand` recupera todos os hits e o conteúdo integral de cada linha, inclusive quando o primeiro recorte truncou uma linha longa. Confira `missing_paths`; não trate fonte ausente como cobertura completa.

Resuma logs grandes com contagens, erros e caminhos. Mantenha o bruto local sanitizado para revisão. Leia o corpo inteiro quando a ordem, cláusulas cruzadas, layout ou critérios de aceite exigirem contexto completo; registre o motivo. Não reduza evidência necessária apenas para caber em um orçamento. Reporte contagem de caracteres como caracteres, nunca como tokens faturados.

Revalide descoberta após mudança de versão, falha de busca ou alteração da tarefa. Nenhuma economia de tokens é presumida sem recibos comparáveis do H04.
