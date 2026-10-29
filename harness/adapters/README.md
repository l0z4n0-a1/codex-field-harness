# Adaptador externo

`dispatch.py` aceita argv literal, stdin, diretório novo por run, JSON com run_id e watchdog. O único provider liberado é `fake`. Providers reais levantam erro até que acesso, contenção de hooks/fan-out, dados e consumo sejam verificados. `fake_provider.py` é fixture local E07; não chama serviços externos.
