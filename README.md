# Zima CPU Monitor

Dashboard leve para ZimaOS que coleta estatisticas de CPU, temperatura, RAM, discos, GPU e energia quando o hardware expoe esses sensores. O backend usa FastAPI, `psutil` e SQLite. O frontend usa React, Vite, Tailwind e Recharts.

## Requisitos

- Docker e Docker Compose.
- ZimaOS ou Linux com acesso de leitura a `/sys` e `/proc`.
- Arquitetura `amd64`.

## Instalacao no ZimaOS

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

## Endpoints principais

Leitura atual legada de CPU/temperatura/energia:

```txt
GET /api/metrics/current
```

Novos endpoints de hardware e categorias:

```txt
GET /api/hardware/info
GET /api/metrics/daily-summary
GET /api/metrics/ram/current
GET /api/metrics/ram
GET /api/metrics/ram/processes
GET /api/metrics/storage/current
GET /api/metrics/storage
GET /api/metrics/gpu/current
GET /api/metrics/gpu
GET /api/metrics/energy
GET /api/metrics/energy/monthly
GET /api/settings/energy
PUT /api/settings/energy
```

Endpoints para limpar historico por categoria:

```txt
DELETE /api/metrics/cpu/history
DELETE /api/metrics/ram/history
DELETE /api/metrics/storage/history
DELETE /api/metrics/gpu/history
DELETE /api/metrics/energy/history
```

Payload de configuracao de energia:

```json
{
  "kwhPrice": 0.95,
  "currency": "BRL"
}
```

Exemplo resumido de `/api/hardware/info`:

```json
{
  "cpu": {
    "model": "Intel(R) Celeron(R) N3450",
    "vendor": "GenuineIntel",
    "architecture": "x86_64",
    "physicalCores": 4,
    "threads": 4,
    "baseFrequencyMHz": null,
    "currentFrequencyMHz": 2200,
    "cache": null
  },
  "motherboard": {
    "vendor": "IceWhale",
    "model": "ZimaBoard",
    "version": null,
    "serial": null,
    "biosVendor": null,
    "biosVersion": null,
    "biosDate": null
  },
  "gpu": {
    "available": true,
    "vendor": "Intel",
    "model": "Intel HD Graphics",
    "driver": "i915",
    "memoryTotalBytes": null,
    "temperatureCelsius": null,
    "usagePercent": null
  },
  "storage": [],
  "memory": {
    "totalBytes": 8589934592,
    "usedBytes": 4294967296,
    "availableBytes": 4294967296,
    "freeBytes": 1000000000,
    "swapTotalBytes": 2147483648,
    "swapUsedBytes": 0,
    "temperatureCelsius": null
  }
}
```

Quando sensores ou ferramentas como `smartctl`, `lspci` ou drivers de GPU nao estiverem disponiveis, os campos retornam `null` ou listas vazias.

## CI/CD

O GitHub Actions usa `.github/workflows/ci-release.yml`.

Crie um Environment chamado `docker` em GitHub `Settings > Environments`.

Variables necessarias no Environment `docker`:

```txt
DOCKERHUB_USERNAME
```

Secrets necessarios no Environment `docker`:

```txt
DOCKERHUB_TOKEN
```

Fluxo:

- Pull request para `main`: instala dependencias, roda testes do backend, testes do frontend, build do frontend e valida build Docker das duas imagens.
- Push ou merge em `main`: repete a validacao, incrementa automaticamente o patch em `backend/VERSION` e `frontend/package.json`, cria commit `chore: release X.Y.Z`, cria tag `vX.Y.Z` e publica imagens no Docker Hub.

Imagens publicadas:

```txt
cleiton016/zima-cpu-monitor-api:X.Y.Z
cleiton016/zima-cpu-monitor-api:latest
cleiton016/zima-cpu-monitor-web:X.Y.Z
cleiton016/zima-cpu-monitor-web:latest
```

## Rodando localmente

Modo dev com live reload:

```bash
docker compose -f docker-compose.dev.yml up --build
```

URLs locais:

```txt
Frontend: http://localhost:5173
Backend: http://localhost:8008/health
```

Nesse modo:

- Alteracoes em `backend/app` reiniciam o FastAPI via `uvicorn --reload`.
- Alteracoes em `frontend/src` atualizam o navegador via Vite HMR.
- O SQLite local fica em `./data/metrics.db`.
- O proxy do Vite encaminha `/api` e `/health` para o container da API.

Modo similar ao deploy do ZimaOS:

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

## Persistencia

O SQLite e salvo em:

```txt
/DATA/AppData/zima-cpu-monitor/data/metrics.db
```

No compose, esse diretorio e montado em `/data` no container do backend. O historico e mantido indefinidamente no MVP.

## Portas

As portas padrao sao:

- Frontend: `8090:80`
- Backend: `8008:8000`

Para alterar, edite `docker-compose.yml` nos blocos `ports`.

## Sensores

Temperatura e lida primeiro via `psutil.sensors_temperatures()`. Se nao existir, o backend tenta:

```txt
/sys/class/thermal/thermal_zone*/temp
/sys/class/hwmon/hwmon*/temp*_input
```

Energia e lida via Intel RAPL quando disponivel:

```txt
/sys/class/powercap/intel-rapl:*/energy_uj
```

Nem todo hardware expoe temperatura, GPU detalhada, SMART ou energia. Quando nao existir leitura, o app continua funcionando e retorna `null` ou listas vazias.

## Exportacao CSV

Use o botao de exportacao no dashboard ou acesse:

```txt
http://IP_DO_ZIMA:8090/api/export/csv?range=24h
```

Ranges aceitos:

```txt
1h, 6h, 24h, 7d, 30d
```

Tambem e possivel usar `from` e `to` em formato ISO:

```txt
/api/export/csv?from=2026-06-22T00:00:00Z&to=2026-06-23T00:00:00Z
```

## Configuracao do intervalo

O intervalo de coleta pode ser alterado no dashboard. Valores aceitos:

```txt
5, 10, 30, 60, 300, 900 segundos
```

A configuracao e persistida no SQLite e aplicada pelo coletor sem reiniciar o container.

## Seguranca

O MVP nao exige autenticacao e deve ficar restrito a rede local. Se for expor para a internet, coloque o app atras de um reverse proxy com autenticacao e TLS.

Os volumes `/sys`, `/proc`, `/dev` e `/run/udev` sao montados para leitura de informacoes do host. O compose usa `privileged: true` para maximizar compatibilidade com sensores no ZimaOS. Caso queira reduzir privilegios, valide antes se CPU, RAM, discos, GPU e energia continuam visiveis para o container.

## Remocao

Para parar e remover containers:

```bash
docker compose down
```

Para remover tambem o banco local:

```bash
rm -rf /DATA/AppData/zima-cpu-monitor/data
```
