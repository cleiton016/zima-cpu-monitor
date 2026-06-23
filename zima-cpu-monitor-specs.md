# Zima CPU Monitor - Especificação para implementação via Codex

## 1. Objetivo

Criar um app para ZimaOS capaz de monitorar estatísticas da CPU e sensores disponíveis do sistema, salvando histórico em logs persistentes e exibindo gráficos em uma interface web.

O app deve ser leve, simples de instalar via Docker Compose no ZimaOS e funcionar mesmo em hardware limitado.

## 2. Decisão técnica recomendada

Para este tipo de aplicação, priorizar:

- Backend em **Python com FastAPI**.
- Coletor usando **psutil** e leitura direta de arquivos do Linux em `/sys` e `/proc`.
- Banco local em **SQLite**.
- Frontend em **React + Vite + Recharts**.
- Empacotamento com **Docker Compose**.
- Servir frontend via **Nginx**.

Motivo da escolha:

- Python possui ótima integração com métricas do sistema.
- `psutil` facilita coleta de CPU, frequência, carga, memória e sensores.
- SQLite é suficiente para histórico local e reduz complexidade.
- React + Vite gera frontend leve e rápido.
- Recharts simplifica criação dos gráficos.
- Docker Compose facilita instalação como app customizado no ZimaOS.

Codificação:
- Use clean code
- Use API REST
- Comente blocos de codigo explicando oque faz
- Comente trechos e metodos complexos informando oque ele faz

## 3. Nome do app

Nome interno:

```txt
zima-cpu-monitor
```

Nome exibido:

```txt
Zima CPU Monitor
```

## 4. Funcionalidades principais

### 4.1 Coleta de métricas

O backend deve coletar periodicamente:

- Uso geral da CPU em porcentagem.
- Uso por núcleo.
- Frequência atual da CPU, se disponível.
- Frequência mínima e máxima, se disponível.
- Load average de 1, 5 e 15 minutos.
- Temperatura da CPU, se disponível.
- Temperatura por sensor, quando disponível.
- Pico de temperatura registrado.
- Média de temperatura por período.
- Consumo de energia, se disponível.
- Energia acumulada via Intel RAPL, se disponível.
- Estimativa de potência em watts, quando possível calcular.
- Uptime do sistema.
- Timestamp da coleta.

### 4.2 Intervalo configurável

O usuário deve conseguir definir o intervalo de coleta.

Valores permitidos:

- 5 segundos
- 10 segundos
- 30 segundos
- 1 minuto
- 5 minutos
- 15 minutos

Valor padrão:

```txt
30 segundos
```

A alteração deve ser persistida no banco e aplicada sem reiniciar o container.

### 4.3 Histórico

O app deve salvar todas as coletas em SQLite.

Deve ser possível consultar histórico por:

- Última hora.
- Últimas 6 horas.
- Últimas 24 horas.
- Últimos 7 dias.
- Últimos 30 dias.
- Intervalo customizado por data inicial e final.

### 4.4 Dashboard web

A interface web deve conter:

- Card com uso atual da CPU.
- Card com temperatura atual.
- Card com pico de temperatura.
- Card com load average.
- Card com frequência atual.
- Card com consumo atual em watts, se disponível.
- Aviso quando temperatura ou energia não estiverem disponíveis.
- Gráfico de uso da CPU ao longo do tempo.
- Gráfico de temperatura ao longo do tempo.
- Gráfico de load average.
- Gráfico de consumo de energia, se disponível.
- Filtro de período.
- Botão para atualizar.
- Configuração do intervalo de coleta.
- Botão para exportar CSV.

### 4.5 Alertas visuais

Criar níveis de alerta:

- Normal: temperatura abaixo de 70°C.
- Atenção: temperatura entre 70°C e 80°C.
- Crítico: temperatura acima de 80°C.

A temperatura limite deve ser configurável no futuro, mas no MVP pode ser fixa.

### 4.6 Exportação

Permitir exportar dados históricos em CSV.

O endpoint deve aceitar filtros:

- `from`
- `to`
- `range`

## 5. Limitações esperadas

Nem todo hardware expõe temperatura ou consumo de energia.

O app deve tratar isso de forma amigável:

- Se temperatura não estiver disponível, mostrar: `Sensor de temperatura não disponível neste hardware. Dica: { Adicione uma dica doque o usuario deve fazer para conseguir obter a informação }`.
- Se consumo não estiver disponível, mostrar: `Medição de energia não disponível neste hardware. Dica: { Adicione uma dica doque o usuario deve fazer para conseguir obter a informação }`.
- O app não deve quebrar caso algum sensor não exista.

## 6. Fontes de dados no Linux

### 6.1 CPU

Usar `psutil`:

```python
psutil.cpu_percent(interval=None)
psutil.cpu_percent(interval=None, percpu=True)
psutil.cpu_freq()
psutil.getloadavg()
psutil.boot_time()
```

### 6.2 Temperatura

Tentar primeiro:

```python
psutil.sensors_temperatures()
```

Fallbacks:

```txt
/sys/class/thermal/thermal_zone*/temp
/sys/class/hwmon/hwmon*/temp*_input
```

Converter valores quando necessário:

- Se valor > 1000, dividir por 1000.
- Exemplo: `55000` vira `55.0°C`.

### 6.3 Consumo de energia

Tentar ler Intel RAPL:

```txt
/sys/class/powercap/intel-rapl:*/energy_uj
/sys/class/powercap/intel-rapl:*/name
```

Calcular watts aproximados:

```txt
watts = delta_energy_joules / delta_time_seconds
```

Onde:

```txt
energy_joules = energy_uj / 1_000_000
```

Se RAPL não existir, retornar `null`.

## 7. Arquitetura

```txt
zima-cpu-monitor/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── collector.py
│   │   ├── metrics_reader.py
│   │   ├── routes/
│   │   │   ├── metrics.py
│   │   │   ├── settings.py
│   │   │   └── export.py
│   │   └── services/
│   │       ├── metrics_service.py
│   │       └── settings_service.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── MetricCard.tsx
│   │   │   ├── CpuUsageChart.tsx
│   │   │   ├── TemperatureChart.tsx
│   │   │   ├── PowerChart.tsx
│   │   │   ├── PeriodFilter.tsx
│   │   │   └── SettingsPanel.tsx
│   │   └── styles.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── README.md
└── zimaos-app.yml
```

## 8. Banco de dados

Usar SQLite.

Arquivo persistente:

```txt
/data/metrics.db
```

### 8.1 Tabela `metrics`

```sql
CREATE TABLE IF NOT EXISTS metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  cpu_percent REAL,
  cpu_per_core_json TEXT,
  cpu_freq_current REAL,
  cpu_freq_min REAL,
  cpu_freq_max REAL,
  load_1 REAL,
  load_5 REAL,
  load_15 REAL,
  temperature_current REAL,
  temperature_max REAL,
  temperature_sensors_json TEXT,
  power_watts REAL,
  energy_joules REAL,
  uptime_seconds INTEGER,
  created_at TEXT NOT NULL
);
```

### 8.2 Tabela `settings`

```sql
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

Configuração inicial:

```txt
collect_interval_seconds = 30
```

## 9. API REST

Base URL interna:

```txt
http://zima-cpu-monitor-api:8000
```

Base URL pelo navegador:

```txt
/api
```

O Nginx do frontend deve fazer proxy de `/api` para o backend.

### 9.1 Health check

```http
GET /health
```

Resposta:

```json
{
  "status": "ok"
}
```

### 9.2 Métrica atual

```http
GET /api/metrics/current
```

Resposta:

```json
{
  "timestamp": "2026-06-23T10:00:00Z",
  "cpu_percent": 23.5,
  "cpu_per_core": [15.2, 30.1, 22.0, 26.7],
  "cpu_freq": {
    "current": 1800,
    "min": 800,
    "max": 3200
  },
  "load": {
    "1": 0.52,
    "5": 0.44,
    "15": 0.31
  },
  "temperature": {
    "current": 55.2,
    "max": 67.1,
    "available": true,
    "sensors": []
  },
  "power": {
    "watts": 8.5,
    "energy_joules": 123456.7,
    "available": true
  },
  "uptime_seconds": 99999
}
```

### 9.3 Histórico

```http
GET /api/metrics/history?range=24h
```

Ranges válidos:

```txt
1h, 6h, 24h, 7d, 30d
```

Também aceitar:

```http
GET /api/metrics/history?from=2026-06-22T00:00:00Z&to=2026-06-23T00:00:00Z
```

### 9.4 Estatísticas resumidas

```http
GET /api/metrics/summary?range=24h
```

Resposta:

```json
{
  "cpu_percent": {
    "min": 5.1,
    "avg": 21.8,
    "max": 92.4
  },
  "temperature": {
    "min": 42.0,
    "avg": 56.3,
    "max": 81.2,
    "available": true
  },
  "power": {
    "min": 3.2,
    "avg": 7.9,
    "max": 18.1,
    "available": true
  }
}
```

### 9.5 Configurações

```http
GET /api/settings
```

Resposta:

```json
{
  "collect_interval_seconds": 30
}
```

```http
PUT /api/settings
Content-Type: application/json

{
  "collect_interval_seconds": 60
}
```

Validar apenas valores permitidos:

```txt
5, 10, 30, 60, 300, 900
```

### 9.6 Exportação CSV

```http
GET /api/export/csv?range=24h
```

Retornar arquivo CSV com colunas:

```txt
timestamp,cpu_percent,temperature_current,temperature_max,power_watts,load_1,load_5,load_15,cpu_freq_current,uptime_seconds
```

## 10. Coletor em background

Implementar tarefa assíncrona no FastAPI usando `asyncio`.

Requisitos:

- Iniciar coletor no startup da aplicação.
- Ler intervalo atual no banco antes de cada ciclo.
- Coletar métricas.
- Salvar no SQLite.
- Não travar a API se uma leitura falhar.
- Registrar erros no log do container.
- Manter última métrica em memória para endpoint `/current`.

Pseudocódigo:

```python
async def collector_loop():
    while True:
        try:
            interval = settings_service.get_collect_interval()
            metric = metrics_reader.read_all()
            metrics_service.save(metric)
            cache.set_current(metric)
        except Exception:
            logger.exception("Failed to collect metrics")
        await asyncio.sleep(interval)
```

## 11. Frontend

### 11.1 Páginas

A aplicação terá uma única página:

```txt
Dashboard
```

### 11.2 Componentes

Criar:

- `MetricCard`
- `CpuUsageChart`
- `TemperatureChart`
- `PowerChart`
- `LoadAverageChart`
- `PeriodFilter`
- `SettingsPanel`
- `UnavailableMetricWarning`

### 11.3 Layout

Desktop:

```txt
Header
Cards de resumo
Filtros
Gráficos
Configurações
```

Mobile:

```txt
Header
Cards em coluna
Filtros
Gráficos em coluna
Configurações
```

### 11.4 Estilo

Usar Tailwind.

Cores sugeridas:

- Fundo: `#0f172a`
- Cards: `#111827`
- Texto principal: `#f9fafb`
- Texto secundário: `#9ca3af`
- Alerta atenção: `#f59e0b`
- Alerta crítico: `#ef4444`

## 12. Docker

### 12.1 Backend Dockerfile

Criar imagem leve com Python.

Base recomendada:

```txt
python:3.12-slim
```

Instalar dependências:

```txt
fastapi
uvicorn[standard]
psutil
pydantic
```

Expor porta:

```txt
8000
```

### 12.2 Frontend Dockerfile

Multi-stage:

- Build com `node:22-alpine`.
- Servir build com `nginx:alpine`.

Expor porta:

```txt
80
```

### 12.3 Docker Compose

Criar `docker-compose.yml`:

```yaml
services:
  zima-cpu-monitor-api:
    build: ./backend
    container_name: zima-cpu-monitor-api
    restart: unless-stopped
    privileged: true
    volumes:
      - /DATA/AppData/zima-cpu-monitor/data:/data
      - /sys:/host/sys:ro
      - /proc:/host/proc:ro
    environment:
      - DATABASE_PATH=/data/metrics.db
      - HOST_SYS_PATH=/host/sys
      - HOST_PROC_PATH=/host/proc
    ports:
      - "8008:8000"

  zima-cpu-monitor-web:
    build: ./frontend
    container_name: zima-cpu-monitor-web
    restart: unless-stopped
    ports:
      - "8090:80"
    depends_on:
      - zima-cpu-monitor-api
```

## 13. Nginx do frontend

Criar proxy para API:

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://zima-cpu-monitor-api:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://zima-cpu-monitor-api:8000/health;
    }
}
```

## 14. Integração com ZimaOS

Criar arquivo `zimaos-app.yml` ou incluir metadados `x-casaos` no compose.

Exemplo:

```yaml
x-casaos:
  architectures:
    - amd64
  main: zima-cpu-monitor-web
  author: Cleiton Luiz
  category: Utilities
  description:
    en_us: Lightweight CPU monitoring dashboard for ZimaOS.
    pt_br: Dashboard leve para monitoramento de CPU no ZimaOS.
  developer: Cleiton Luiz
  hostname: ""
  icon: "https://raw.githubusercontent.com/IceWhaleTech/CasaOS-AppStore/main/Apps/CasaOS/icon.png"
  index: /
  is_uncontrolled: false
  port_map: "8090"
  scheme: http
  title:
    en_us: Zima CPU Monitor
    pt_br: Zima CPU Monitor
```

## 15. Logs

O app deve gerar logs no stdout do container.

Eventos mínimos:

- Inicialização do backend.
- Inicialização do coletor.
- Intervalo atual de coleta.
- Erro ao ler sensores.
- Erro ao salvar métrica.
- Alteração de configuração.

Não gravar logs infinitos em arquivo por padrão.

O histórico deve ficar no SQLite.

## 16. Retenção de dados

MVP:

- Manter dados indefinidamente.

Adicionar configuração futura:

- 7 dias.
- 30 dias.
- 90 dias.
- 1 ano.

## 17. Testes mínimos

### 17.1 Backend

Criar testes para:

- Leitura de CPU.
- Conversão de temperatura.
- Cálculo de watts via RAPL.
- Inserção de métrica no banco.
- Consulta de histórico.
- Validação de intervalo permitido.

### 17.2 Frontend

Criar testes básicos para:

- Renderização dos cards.
- Renderização dos gráficos sem dados.
- Mensagem quando temperatura não disponível.
- Mensagem quando energia não disponível.

## 18. Critérios de aceite

O projeto será considerado concluído quando:

1. Rodar com `docker compose up -d`.
2. Abrir dashboard em `http://IP_DO_ZIMA:8090`.
3. Backend responder em `http://IP_DO_ZIMA:8008/health`.
4. Coletar métricas automaticamente.
5. Salvar histórico no SQLite em `/DATA/AppData/zima-cpu-monitor/data`.
6. Exibir gráfico de uso de CPU.
7. Exibir gráfico de temperatura quando sensor existir.
8. Exibir aviso amigável quando temperatura não existir.
9. Exibir gráfico de energia quando Intel RAPL existir.
10. Exibir aviso amigável quando energia não existir.
11. Permitir alterar intervalo de coleta.
12. Permitir exportar CSV.
13. Não quebrar caso `/sys/class/powercap` não exista.
14. Não quebrar caso `/sys/class/thermal` não exista.

## 19. Roadmap pós-MVP

Depois do MVP, adicionar:

- Alertas via Telegram.
- Alertas via webhook.
- Integração com Grafana.
- Retenção automática de dados.
- Monitoramento de disco.
- Monitoramento de memória.
- Monitoramento de rede.
- Monitoramento de containers Docker.
- Página de diagnóstico dos sensores disponíveis.
- Instalação com um clique no formato App Store do ZimaOS.

## 20. Prompt principal para Codex

Use este prompt para iniciar a implementação:

```txt
Implemente o projeto Zima CPU Monitor seguindo integralmente a especificação deste arquivo.

Crie uma aplicação Docker Compose com backend em Python FastAPI, banco SQLite, coletor periódico de métricas do sistema Linux e frontend React + Vite + Recharts.

O app deve funcionar no ZimaOS, lendo métricas de CPU via psutil e tentando obter temperatura e energia pelos caminhos montados de /sys e /proc do host.

Priorize robustez: se sensores de temperatura ou energia não existirem, a aplicação deve continuar funcionando e exibir mensagens amigáveis no frontend.

Entregue todos os arquivos necessários: backend, frontend, Dockerfiles, docker-compose.yml, nginx.conf, README.md e metadados para ZimaOS/CasaOS.

Inclua testes mínimos para backend e frontend quando viável.
```

## 21. Ordem de execução recomendada para o Codex

1. Criar estrutura de pastas.
2. Implementar backend FastAPI.
3. Implementar banco SQLite e migrations simples no startup.
4. Implementar leitor de métricas.
5. Implementar loop de coleta.
6. Implementar endpoints REST.
7. Implementar frontend React.
8. Criar gráficos com Recharts.
9. Criar tela de configurações.
10. Criar exportação CSV.
11. Criar Dockerfiles.
12. Criar Docker Compose.
13. Criar README.
14. Criar testes básicos.
15. Validar execução local.

## 22. Comandos esperados

Rodar local:

```bash
docker compose up -d --build
```

Ver logs:

```bash
docker logs -f zima-cpu-monitor-api
```

Acessar dashboard:

```txt
http://localhost:8090
```

Health check:

```txt
http://localhost:8008/health
```

## 23. README mínimo esperado

O README deve conter:

- O que é o app.
- Requisitos.
- Como instalar no ZimaOS.
- Como rodar com Docker Compose.
- Como acessar a interface.
- Como alterar portas.
- Como os dados são persistidos.
- Limitações sobre sensores de temperatura e energia.
- Como exportar CSV.
- Como remover o app.

## 24. Segurança

- Não expor nenhuma API sensível além da rede local.
- Não exigir autenticação no MVP.
- Documentar que, caso o usuário exponha o app para internet, deve colocar autenticação/reverse proxy.
- Montar `/sys` e `/proc` como somente leitura.
- Usar `privileged: true` apenas se necessário. Primeiro tentar sem `privileged`; se sensores não forem acessíveis, documentar o uso.

## 25. Resultado esperado

Ao final, o repositório deve permitir que o usuário copie a pasta para o ZimaOS e execute:

```bash
docker compose up -d --build
```

Depois disso, o dashboard deve estar acessível em:

```txt
http://IP_DO_ZIMA:8090
```
