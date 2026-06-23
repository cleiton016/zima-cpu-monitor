# Zima CPU Monitor

Dashboard leve para ZimaOS que coleta estatísticas de CPU, temperatura e energia quando o hardware expõe esses sensores. O backend usa FastAPI, `psutil` e SQLite. O frontend usa React, Vite, Tailwind e Recharts.

## Requisitos

- Docker e Docker Compose.
- ZimaOS ou Linux com acesso de leitura a `/sys` e `/proc`.
- Arquitetura `amd64`.

## Instalação no ZimaOS

Copie a pasta do projeto para o ZimaOS e execute:

```bash
docker compose up -d --build
```

Depois acesse:

```txt
http://IP_DO_ZIMA:8090
```

O health check do backend fica em:

```txt
http://IP_DO_ZIMA:8008/health
```

## Rodando localmente

```bash
docker compose up -d --build
docker logs -f zima-cpu-monitor-api
```

Dashboard local:

```txt
http://localhost:8090
```

Backend local:

```txt
http://localhost:8008/health
```

## Persistência

O SQLite é salvo em:

```txt
/DATA/AppData/zima-cpu-monitor/data/metrics.db
```

No compose, esse diretório é montado em `/data` no container do backend. O histórico é mantido indefinidamente no MVP.

## Portas

As portas padrão são:

- Frontend: `8090:80`
- Backend: `8008:8000`

Para alterar, edite `docker-compose.yml` nos blocos `ports`.

## Sensores

Temperatura é lida primeiro via `psutil.sensors_temperatures()`. Se não existir, o backend tenta:

```txt
/sys/class/thermal/thermal_zone*/temp
/sys/class/hwmon/hwmon*/temp*_input
```

Energia é lida via Intel RAPL quando disponível:

```txt
/sys/class/powercap/intel-rapl:*/energy_uj
```

Nem todo hardware expõe temperatura ou energia. Quando não existir leitura, o app continua funcionando e mostra um aviso no dashboard.

## Exportação CSV

Use o botão de exportação no dashboard ou acesse:

```txt
http://IP_DO_ZIMA:8090/api/export/csv?range=24h
```

Ranges aceitos:

```txt
1h, 6h, 24h, 7d, 30d
```

Também é possível usar `from` e `to` em formato ISO:

```txt
/api/export/csv?from=2026-06-22T00:00:00Z&to=2026-06-23T00:00:00Z
```

## Configuração do intervalo

O intervalo de coleta pode ser alterado no dashboard. Valores aceitos:

```txt
5, 10, 30, 60, 300, 900 segundos
```

A configuração é persistida no SQLite e aplicada pelo coletor sem reiniciar o container.

## Segurança

O MVP não exige autenticação e deve ficar restrito à rede local. Se for expor para a internet, coloque o app atrás de um reverse proxy com autenticação e TLS.

Os volumes `/sys` e `/proc` são montados como somente leitura. O compose não usa `privileged: true` por padrão. Caso algum sensor necessário não apareça no seu hardware, teste permissões adicionais apenas depois de confirmar que os caminhos existem no host.

## Remoção

Para parar e remover containers:

```bash
docker compose down
```

Para remover também o banco local:

```bash
rm -rf /DATA/AppData/zima-cpu-monitor/data
```
