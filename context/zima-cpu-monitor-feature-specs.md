# Zima CPU Monitor — Specs de Novas Features

## Contexto

Este documento define as especificações técnicas para evoluir o app **Zima CPU Monitor** para um painel completo de monitoramento de hardware do ZimaOS.

O app atual já possui backend com coletor, frontend com dashboard, Docker Compose funcionando no ZimaOS e persistência em banco local.

---

# 1. Feature: Modal de Informações de Hardware

## Objetivo

Adicionar no header do frontend um botão de informações técnicas. Ao clicar, abrir um modal exibindo os principais dados do hardware do ZimaOS.

## Interface

No header, adicionar botão com ícone de informação:

```txt
ℹ️ Info
```

Ao clicar:
- Abrir modal centralizado.
- Exibir loading enquanto busca os dados.
- Exibir erro amigável se a API falhar.
- Mostrar `Não disponível` quando algum dado não existir.

## Dados exibidos

### Processador

Campos:
- Modelo.
- Fabricante/vendor.
- Arquitetura.
- Núcleos físicos.
- Threads.
- Frequência atual.
- Frequência base, se disponível.
- Cache, se disponível.

Fontes Linux:
- `/proc/cpuinfo`
- `/sys/devices/system/cpu`
- `lscpu`, se disponível.

### Placa-mãe

Campos:
- Fabricante.
- Modelo.
- Versão.
- Serial, se disponível.
- BIOS vendor.
- BIOS version.
- BIOS date.

Fontes Linux:
- `/sys/class/dmi/id/board_vendor`
- `/sys/class/dmi/id/board_name`
- `/sys/class/dmi/id/board_version`
- `/sys/class/dmi/id/bios_vendor`
- `/sys/class/dmi/id/bios_version`
- `/sys/class/dmi/id/bios_date`

### GPU

Campos:
- Detectada: sim/não.
- Fabricante.
- Modelo.
- Driver.
- Memória dedicada, se disponível.
- Temperatura, se disponível.
- Uso atual, se disponível.

Fontes Linux:
- `/sys/class/drm`
- `lspci`, se disponível.
- `nvidia-smi`, se disponível.
- `intel_gpu_top`, se disponível.
- `/sys/class/hwmon`

### HDs / SSDs

Campos por disco:
- Nome do dispositivo.
- Modelo.
- Serial, se disponível.
- Tipo: HDD, SSD, NVMe ou desconhecido.
- Capacidade total.
- Espaço usado.
- Espaço livre.
- Percentual de uso.
- Temperatura, se disponível.
- Status SMART, se disponível.

Fontes Linux:
- `/sys/block`
- `/proc/mounts`
- `df`
- `lsblk`
- `smartctl`, se disponível.

### Memória RAM

Campos:
- Total instalado.
- Em uso.
- Disponível.
- Livre.
- Swap total.
- Swap em uso.
- Velocidade/módulos, se disponível.
- Temperatura, se disponível.

Fontes Linux:
- `/proc/meminfo`
- `dmidecode`, se disponível.
- `/sys/class/hwmon`, se houver sensor.

## Endpoint

```http
GET /api/hardware/info
```

Resposta esperada:

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
    "driver": null,
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

## Frontend

Criar componentes:

```txt
HardwareInfoButton
HardwareInfoModal
```

## Critérios de aceite

- O botão aparece no header.
- Ao clicar, abre modal.
- O modal exibe CPU, placa-mãe, GPU, HDs e RAM.
- Campos indisponíveis aparecem como `Não disponível`.
- O app não quebra quando GPU ou sensores não existem.

---

# 2. Feature: Cards Big Number

## Objetivo

Adicionar cards de resumo no topo do dashboard com os principais picos do dia.

## Cards obrigatórios

### Pico mais alto de CPU do dia

Exibir:
- Valor máximo de uso da CPU no dia.
- Hora em que ocorreu em `text-sm`.

### Temperatura mais alta do dia

Exibir:
- Temperatura máxima registrada no dia.
- Hora em que ocorreu em `text-sm`.

### Pico mais alto de RAM do dia

Exibir:
- Maior percentual de uso de RAM no dia.
- Hora em que ocorreu em `text-sm`.

### Consumo de energia total do dia

Exibir:
- Total acumulado estimado ou medido em kWh.
- Custo estimado do dia, se o valor do kWh estiver configurado.

## Endpoint

```http
GET /api/metrics/daily-summary
```

Parâmetro opcional:

```http
?date=2026-06-23
```

Resposta:

```json
{
  "date": "2026-06-23",
  "cpuPeak": {
    "valuePercent": 92.4,
    "timestamp": "2026-06-23T14:32:00-03:00"
  },
  "temperaturePeak": {
    "valueCelsius": 78.2,
    "timestamp": "2026-06-23T13:48:00-03:00"
  },
  "ramPeak": {
    "valuePercent": 81.1,
    "timestamp": "2026-06-23T15:10:00-03:00"
  },
  "energyTotal": {
    "kwh": 1.84,
    "estimatedCost": 1.75,
    "currency": "BRL"
  }
}
```

## Frontend

Criar componente:

```txt
DailyBigNumbers
```

Layout:
- 4 cards em desktop.
- 2 por linha em tablet.
- 1 por linha em mobile.

## Critérios de aceite

- Mostra os 4 cards no topo.
- Mostra dados do dia atual.
- Mostra a hora do pico.
- Se não houver dados, exibe `Sem dados hoje`.

---

# 3. Feature: Separação de Gráficos por Categoria

## Objetivo

Organizar os gráficos em categorias.

## Categorias

- CPU
- RAM
- HDs
- GPU, se disponível.
- Energia

## Interface recomendada

Tabs:

```txt
[CPU] [RAM] [HDs] [GPU] [Energia]
```

## Regras

- GPU só aparece se for detectada ou se houver histórico.
- HDs deve permitir selecionar disco quando houver mais de um.
- Todas as categorias devem manter filtro de período.

Períodos mínimos:
- Última hora.
- Hoje.
- 7 dias.
- 30 dias.

## Endpoints

```http
GET /api/metrics/cpu
GET /api/metrics/ram
GET /api/metrics/storage
GET /api/metrics/gpu
GET /api/metrics/energy
```

Parâmetros:

```http
?from=2026-06-23T00:00:00&to=2026-06-23T23:59:59&bucket=minute
```

Buckets:
- raw
- minute
- hour
- day

## Frontend

Criar componentes:

```txt
MetricsTabs
CpuCharts
RamCharts
StorageCharts
GpuCharts
EnergyCharts
PeriodFilter
```

## Critérios de aceite

- Gráficos ficam separados por categoria.
- CPU, RAM, HDs e Energia aparecem sempre.
- GPU aparece apenas se disponível.
- Trocar de aba não quebra filtros.

---

# 4. Feature: Energia — kWh, Custo e Gráficos

## Objetivo

Expandir a seção de energia para permitir análise de consumo e custo.

## Requisitos

### Gráfico de linha

Manter gráfico de linha para energia.

Séries possíveis:
- Potência instantânea em watts.
- Consumo acumulado do dia em kWh.
- Custo acumulado estimado.

### Input de valor do kWh

Adicionar input:

```txt
Valor do kWh: R$ [____]
```

Regras:
- Aceitar `0,95`, `1,05`, `1.05`.
- Salvar no banco.
- Usar BRL como moeda padrão.
- Persistir após reload.
- Validar valor maior que zero.

### Gráfico de barra mensal

Mostrar:
- Consumo mensal em kWh.
- Valor calculado em reais.

## Observação técnica

Energia pode ser medida ou estimada.

Fontes possíveis:
- `/sys/class/powercap/intel-rapl`
- sensores hwmon
- estimativa baseada em TDP e uso da CPU
- futura integração com smart plug

## Endpoints

```http
GET /api/settings/energy
PUT /api/settings/energy
GET /api/metrics/energy
GET /api/metrics/energy/monthly
```

Payload do PUT:

```json
{
  "kwhPrice": 0.95,
  "currency": "BRL"
}
```

Resposta mensal:

```json
{
  "year": 2026,
  "currency": "BRL",
  "kwhPrice": 0.95,
  "months": [
    {
      "month": 1,
      "label": "Jan",
      "kwh": 42.3,
      "cost": 40.18
    }
  ]
}
```

## Banco de dados

```sql
CREATE TABLE IF NOT EXISTS app_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

```sql
CREATE TABLE IF NOT EXISTS energy_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  power_watts REAL,
  energy_kwh REAL,
  source TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Cálculo estimado

```txt
kWh = (watts * intervalo_em_horas) / 1000
```

## Frontend

Criar componentes:

```txt
EnergySettingsCard
EnergyLineChart
EnergyMonthlyBarChart
```

## Critérios de aceite

- Usuário consegue salvar valor do kWh.
- Valor fica salvo após reload.
- Gráfico de linha mostra energia.
- Gráfico mensal mostra kWh e custo.
- Se não houver sensor real, indicar que é estimado.

---

# 5. Feature: Estatísticas de Memória RAM

## Objetivo

Adicionar monitoramento avançado de RAM.

## Métricas obrigatórias

- Total de RAM.
- RAM usada.
- RAM disponível.
- RAM livre.
- Percentual de uso.
- Swap total.
- Swap usado.
- Swap livre.
- Percentual de swap.
- Temperatura da RAM, se possível.
- Uso por serviço/processo, se possível.
- Gráfico de pizza: em uso vs disponível.

## Métricas úteis adicionais

- Cache/buffers.
- Memória compartilhada.
- Top processos por uso de memória.
- Tendência de crescimento da memória.
- Alerta de possível memory leak.
- Pico do dia.
- Média do dia.

## Fontes Linux

- `/proc/meminfo`
- `/proc/[pid]/status`
- `/proc/[pid]/cmdline`
- `/sys/class/hwmon`
- `ps`, se disponível.

## Endpoints

```http
GET /api/metrics/ram/current
GET /api/metrics/ram
GET /api/metrics/ram/processes
```

Resposta current:

```json
{
  "timestamp": "2026-06-23T18:00:00-03:00",
  "totalBytes": 8589934592,
  "usedBytes": 4294967296,
  "availableBytes": 4294967296,
  "freeBytes": 1000000000,
  "usagePercent": 50.0,
  "buffersBytes": 200000000,
  "cachedBytes": 900000000,
  "sharedBytes": 100000000,
  "swapTotalBytes": 2147483648,
  "swapUsedBytes": 0,
  "swapUsagePercent": 0,
  "temperatureCelsius": null
}
```

Resposta processes:

```json
{
  "timestamp": "2026-06-23T18:00:00-03:00",
  "processes": [
    {
      "pid": 1234,
      "name": "python",
      "command": "python app/main.py",
      "memoryBytes": 250000000,
      "memoryPercent": 2.9
    }
  ]
}
```

## Banco de dados

```sql
CREATE TABLE IF NOT EXISTS ram_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  total_bytes INTEGER NOT NULL,
  used_bytes INTEGER NOT NULL,
  available_bytes INTEGER NOT NULL,
  free_bytes INTEGER,
  usage_percent REAL NOT NULL,
  buffers_bytes INTEGER,
  cached_bytes INTEGER,
  shared_bytes INTEGER,
  swap_total_bytes INTEGER,
  swap_used_bytes INTEGER,
  swap_usage_percent REAL,
  temperature_celsius REAL,
  created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE IF NOT EXISTS process_memory_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  pid INTEGER NOT NULL,
  name TEXT,
  command TEXT,
  memory_bytes INTEGER,
  memory_percent REAL,
  created_at TEXT NOT NULL
);
```

Armazenar somente top 10 processos por coleta.

## Frontend

Aba RAM:
- Card uso atual.
- Card RAM disponível.
- Card swap.
- Card temperatura, se disponível.
- Gráfico linha uso RAM.
- Gráfico linha swap.
- Gráfico pizza em uso vs disponível.
- Tabela top processos.

## Critérios de aceite

- RAM aparece em categoria própria.
- Mostra uso atual e histórico.
- Mostra gráfico de pizza.
- Mostra top processos quando possível.
- Temperatura aparece apenas se disponível.

---

# 6. Feature: Estatísticas de GPU

## Objetivo

Adicionar monitoramento da GPU quando disponível.

## Métricas obrigatórias

- GPU detectada ou não.
- Modelo.
- Uso percentual, se disponível.
- Temperatura, se disponível.
- Memória total, se disponível.
- Memória usada, se disponível.
- Driver, se disponível.

## Métricas adicionais

- Frequência da GPU.
- Frequência da memória.
- Consumo de energia da GPU, se disponível.
- Fan speed, se disponível.
- Encoder/decoder usage, se disponível.

## Fontes possíveis

Intel:
- `/sys/class/drm`
- `/sys/kernel/debug/dri`
- `intel_gpu_top`, se instalado.

NVIDIA:
- `nvidia-smi`

AMD:
- `/sys/class/drm/card*/device`
- `/sys/class/hwmon`
- `rocm-smi`, se instalado.

Genérico:
- `lspci`
- `/sys/class/hwmon`

## Endpoints

```http
GET /api/metrics/gpu/current
GET /api/metrics/gpu
```

Resposta current:

```json
{
  "available": true,
  "timestamp": "2026-06-23T18:00:00-03:00",
  "devices": [
    {
      "id": "card0",
      "vendor": "Intel",
      "model": "Intel HD Graphics",
      "driver": "i915",
      "usagePercent": null,
      "temperatureCelsius": null,
      "memoryTotalBytes": null,
      "memoryUsedBytes": null,
      "memoryUsagePercent": null,
      "powerWatts": null
    }
  ]
}
```

## Banco de dados

```sql
CREATE TABLE IF NOT EXISTS gpu_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  gpu_id TEXT NOT NULL,
  vendor TEXT,
  model TEXT,
  usage_percent REAL,
  temperature_celsius REAL,
  memory_total_bytes INTEGER,
  memory_used_bytes INTEGER,
  memory_usage_percent REAL,
  power_watts REAL,
  source TEXT,
  created_at TEXT NOT NULL
);
```

## Frontend

Aba GPU:
- Estado `GPU não detectada`.
- Card modelo.
- Card uso.
- Card temperatura.
- Card memória da GPU.
- Gráfico uso.
- Gráfico temperatura.
- Gráfico memória usada.
- Se múltiplas GPUs existirem, permitir seleção.

## Critérios de aceite

- GPU aparece apenas se disponível.
- Sem GPU, app não quebra.
- Intel iGPU sem métricas detalhadas mostra modelo e limitação.
- Histórico é salvo quando houver dados.

---

# 7. Feature: Estatísticas dos HDs / SSDs

## Objetivo

Adicionar monitoramento detalhado dos discos.

## Métricas obrigatórias

Por disco:
- Nome.
- Modelo.
- Tipo: HDD, SSD, NVMe ou desconhecido.
- Capacidade total.
- Espaço usado.
- Espaço livre.
- Percentual de uso.
- Temperatura, se disponível.
- Leituras por segundo.
- Escritas por segundo.
- Bytes lidos.
- Bytes escritos.
- Status SMART, se disponível.

Por mount:
- Caminho montado.
- Total.
- Usado.
- Livre.
- Percentual.

## Fontes Linux

- `/sys/block`
- `/proc/diskstats`
- `/proc/mounts`
- `df`
- `lsblk`
- `smartctl`, se disponível.

## Endpoints

```http
GET /api/metrics/storage/current
GET /api/metrics/storage
```

Parâmetros:

```http
?device=sda&from=...&to=...
```

Resposta current:

```json
{
  "timestamp": "2026-06-23T18:00:00-03:00",
  "devices": [
    {
      "name": "sda",
      "model": "Samsung SSD",
      "type": "SSD",
      "sizeBytes": 256000000000,
      "temperatureCelsius": 38,
      "smartStatus": "PASSED",
      "readBytesTotal": 120000000000,
      "writeBytesTotal": 80000000000,
      "readBytesPerSecond": 102400,
      "writeBytesPerSecond": 204800
    }
  ],
  "mounts": [
    {
      "device": "/dev/sda1",
      "mountPoint": "/DATA",
      "filesystem": "ext4",
      "totalBytes": 256000000000,
      "usedBytes": 120000000000,
      "freeBytes": 136000000000,
      "usagePercent": 46.8
    }
  ]
}
```

## Banco de dados

```sql
CREATE TABLE IF NOT EXISTS storage_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  device_name TEXT NOT NULL,
  model TEXT,
  type TEXT,
  size_bytes INTEGER,
  used_bytes INTEGER,
  free_bytes INTEGER,
  usage_percent REAL,
  temperature_celsius REAL,
  smart_status TEXT,
  read_bytes_total INTEGER,
  write_bytes_total INTEGER,
  read_bytes_per_second REAL,
  write_bytes_per_second REAL,
  created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE IF NOT EXISTS storage_mount_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  device TEXT,
  mount_point TEXT NOT NULL,
  filesystem TEXT,
  total_bytes INTEGER,
  used_bytes INTEGER,
  free_bytes INTEGER,
  usage_percent REAL,
  created_at TEXT NOT NULL
);
```

## Frontend

Aba HDs:
- Lista de discos.
- Seletor de disco.
- Cards: capacidade, uso, temperatura, SMART, leitura/s, escrita/s.
- Gráfico uso.
- Gráfico temperatura.
- Gráfico leitura/escrita por segundo.
- Tabela de partições/mount points.

## Critérios de aceite

- Suporta múltiplos discos.
- Suporta múltiplos mounts.
- Mostra `/DATA` claramente.
- Temperatura e SMART aparecem somente quando disponíveis.
- App não quebra se `smartctl` não existir.

---

# 8. Ajustes no Coletor de Métricas

## Objetivo

Expandir o coletor para suportar CPU, RAM, GPU, HDs e Energia.

## Requisitos

O coletor deve rodar em intervalo configurável e coletar:
- CPU.
- Temperatura da CPU.
- RAM.
- Storage.
- GPU, se disponível.
- Energia, se disponível ou estimada.

## Boas práticas

- Não travar se uma fonte falhar.
- Cada coletor deve ser isolado.
- Registrar logs claros.
- Evitar comandos pesados em intervalos muito curtos.
- Usar timeout em comandos externos.
- Salvar `null` quando informação não estiver disponível.
- Identificar origem da métrica com `source`.

## Estrutura recomendada

```txt
app/
  collectors/
    cpu_collector.py
    ram_collector.py
    storage_collector.py
    gpu_collector.py
    energy_collector.py
    hardware_info_collector.py
  services/
    metrics_service.py
    settings_service.py
  routes/
    cpu_routes.py
    ram_routes.py
    storage_routes.py
    gpu_routes.py
    energy_routes.py
    hardware_routes.py
```

## Critérios de aceite

- Falha no coletor GPU não impede CPU/RAM.
- Falha no sensor de energia não derruba backend.
- Coleta salva dados corretamente.
- Logs indicam sensores não encontrados sem erro crítico.

---

# 9. Ajustes no Docker Compose

## Objetivo

Garantir que a API tenha acesso às informações do host.

## Compose recomendado

```yaml
services:
  zima-cpu-monitor-api:
    image: cleiton016/zima-cpu-monitor-api:0.0.1
    container_name: zima-cpu-monitor-api
    restart: unless-stopped
    privileged: true
    environment:
      DATABASE_PATH: /data/metrics.db
      COLLECT_INTERVAL_SECONDS: 30
      TZ: America/Sao_Paulo
    volumes:
      - /DATA/AppData/zima-cpu-monitor/data:/data
      - /sys:/host/sys:ro
      - /proc:/host/proc:ro
      - /dev:/host/dev:ro
      - /run/udev:/run/udev:ro
    ports:
      - "8008:8000"
    networks:
      - zima-cpu-monitor

  zima-cpu-monitor-web:
    image: cleiton016/zima-cpu-monitor-web:0.0.1
    container_name: zima-cpu-monitor-web
    restart: unless-stopped
    ports:
      - "8088:80"
    depends_on:
      - zima-cpu-monitor-api
    networks:
      - zima-cpu-monitor

networks:
  zima-cpu-monitor:
    driver: bridge

x-casaos:
  architectures:
    - amd64
  main: zima-cpu-monitor-web
  author: Cleiton
  category: Utilities
  description:
    en_us: Hardware monitoring dashboard for ZimaOS
  developer: Cleiton
  icon: https://icon.casaos.io/main/all/cpu.png
  index: /
  port_map: "8088"
  scheme: http
  title:
    en_us: Zima Hardware Monitor
```

O backend deve ler caminhos do host usando prefixo `/host`:

```txt
/host/proc/meminfo
/host/sys/class/thermal
/host/sys/block
```

---

# 10. Ordem recomendada para Codex

## Etapa 1 — Banco e endpoints base

Implementar:
- `app_settings`.
- `ram_samples`.
- `storage_samples`.
- `storage_mount_samples`.
- `gpu_samples`.
- `energy_samples`.
- endpoints de settings.
- endpoint de hardware info.

## Etapa 2 — Coletor RAM e Storage

Implementar:
- RAM atual.
- RAM histórico.
- Storage atual.
- Storage histórico.
- Top processos por RAM.

## Etapa 3 — Big Numbers

Implementar:
- endpoint `daily-summary`.
- cards no frontend.

## Etapa 4 — Separação por categorias

Implementar:
- tabs no dashboard.
- filtros por período.
- componentes de categoria.

## Etapa 5 — Energia

Implementar:
- input kWh.
- persistência.
- gráfico mensal.
- cálculo de custo.

## Etapa 6 — GPU

Implementar:
- detecção de GPU.
- endpoint atual.
- histórico quando disponível.
- aba condicional.

## Etapa 7 — Modal de hardware

Implementar:
- botão no header.
- endpoint `/api/hardware/info`.
- modal responsivo.

---

# 11. Prompt para Codex

```txt
Você está trabalhando no projeto Zima CPU Monitor, um app Docker para ZimaOS com backend, frontend e banco local.

Implemente as novas features descritas neste documento, seguindo a ordem recomendada:

1. Criar/ajustar migrations ou inicialização do banco para app_settings, ram_samples, storage_samples, storage_mount_samples, gpu_samples e energy_samples.
2. Criar endpoints:
   - GET /api/hardware/info
   - GET /api/metrics/daily-summary
   - GET /api/settings/energy
   - PUT /api/settings/energy
   - GET /api/metrics/ram/current
   - GET /api/metrics/ram
   - GET /api/metrics/ram/processes
   - GET /api/metrics/storage/current
   - GET /api/metrics/storage
   - GET /api/metrics/gpu/current
   - GET /api/metrics/gpu
   - GET /api/metrics/energy
   - GET /api/metrics/energy/monthly
3. Expandir o coletor para CPU, RAM, Storage, GPU e Energia.
4. Garantir que sensores indisponíveis retornem null e nunca quebrem o backend.
5. Atualizar frontend:
   - Botão Info no header.
   - Modal de hardware.
   - Big number cards.
   - Tabs por categoria: CPU, RAM, HDs, GPU, Energia.
   - Seção Energia com input de kWh e gráfico mensal.
   - Seção RAM com pizza uso/disponível e top processos.
   - Seção GPU condicional.
   - Seção HDs com múltiplos discos e mounts.
6. Manter compatibilidade com Docker/ZimaOS.
7. Não usar dependências pesadas sem necessidade.
8. Garantir que o app continue funcionando mesmo sem GPU, sem sensores de RAM, sem sensores de energia e sem smartctl.

Ao terminar:
- Atualize README.
- Atualize docker-compose.yml se necessário.
- Adicione exemplos de resposta dos endpoints.
- Adicione tratamento de erro no frontend.
- Garanta layout responsivo.
```

---

# 12. Critérios finais de aceite

O projeto será considerado pronto quando:

- App abre pelo frontend no ZimaOS.
- API continua estável.
- Dashboard mostra big numbers do dia.
- Hardware info abre em modal.
- Gráficos ficam separados por categoria.
- RAM tem histórico, pizza e top processos.
- HDs mostram discos, mounts e uso.
- Energia permite configurar valor do kWh.
- Energia mostra consumo mensal e custo.
- GPU aparece somente quando disponível.
- Falta de sensores não derruba o app.
- Dados persistem em `/DATA/AppData/zima-cpu-monitor/data`.
- Compose continua compatível com Custom Install do ZimaOS.
