import { Activity, Cpu, Gauge, Thermometer, Zap } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getCurrentMetric,
  getHistory,
  getSettings,
  getSummary,
  updateSettings,
  type Metric,
  type Summary
} from "./api/client";
import {
  CpuUsageChart,
  LoadAverageChart,
  PowerChart,
  TemperatureChart
} from "./components/Charts";
import MetricCard from "./components/MetricCard";
import PeriodFilter, { type RangeOption } from "./components/PeriodFilter";
import SettingsPanel from "./components/SettingsPanel";
import UnavailableMetricWarning from "./components/UnavailableMetricWarning";

function formatNumber(value: number | null | undefined, suffix = "") {
  if (value === null || value === undefined) {
    return "N/D";
  }
  return `${value.toFixed(1)}${suffix}`;
}

function formatUptime(seconds: number | null | undefined) {
  if (!seconds) {
    return "N/D";
  }
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  return days > 0 ? `${days}d ${hours}h` : `${hours}h`;
}

function temperatureTone(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "muted" as const;
  }
  if (value > 80) {
    return "critical" as const;
  }
  if (value >= 70) {
    return "warning" as const;
  }
  return "normal" as const;
}

export default function App() {
  const [current, setCurrent] = useState<Metric | null>(null);
  const [history, setHistory] = useState<Metric[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [range, setRange] = useState<RangeOption>("24h");
  const [collectInterval, setCollectInterval] = useState(30);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useMemo(() => `range=${range}`, [range]);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [currentMetric, historyData, summaryData, settings] = await Promise.all([
        getCurrentMetric(),
        getHistory(query),
        getSummary(query),
        getSettings()
      ]);
      setCurrent(currentMetric);
      setHistory(historyData);
      setSummary(summaryData);
      setCollectInterval(settings.collect_interval_seconds);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar métricas.");
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  async function saveSettings() {
    setSaving(true);
    setError(null);
    try {
      const settings = await updateSettings({ collect_interval_seconds: collectInterval });
      setCollectInterval(settings.collect_interval_seconds);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar configurações.");
    } finally {
      setSaving(false);
    }
  }

  const hasTemperature = Boolean(current?.temperature.available);
  const hasPower = Boolean(current?.power.available);

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-teal-300">ZimaOS</p>
            <h1 className="text-3xl font-semibold text-zinc-50">Zima CPU Monitor</h1>
          </div>
          <p className="text-sm text-zinc-400">
            Última leitura: {current ? new Date(current.timestamp).toLocaleString("pt-BR") : "aguardando"}
          </p>
        </header>

        {error ? (
          <section className="rounded-lg border border-red-400/50 bg-red-950/40 p-4 text-sm text-red-100">
            {error}
          </section>
        ) : null}

        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          <MetricCard
            title="CPU"
            value={formatNumber(current?.cpu_percent, "%")}
            detail={`${current?.cpu_per_core.length ?? 0} núcleos`}
            icon={<Cpu size={18} />}
          />
          <MetricCard
            title="Temperatura"
            value={formatNumber(current?.temperature.current, "°C")}
            detail={hasTemperature ? "Sensor ativo" : "Sem leitura"}
            tone={temperatureTone(current?.temperature.current)}
            icon={<Thermometer size={18} />}
          />
          <MetricCard
            title="Pico"
            value={formatNumber(summary?.temperature.max ?? current?.temperature.max, "°C")}
            detail="No período selecionado"
            tone={temperatureTone(summary?.temperature.max ?? current?.temperature.max)}
            icon={<Gauge size={18} />}
          />
          <MetricCard
            title="Load 1m"
            value={formatNumber(current?.load["1"])}
            detail={`5m ${formatNumber(current?.load["5"])} | 15m ${formatNumber(current?.load["15"])}`}
            icon={<Activity size={18} />}
          />
          <MetricCard
            title="Frequência"
            value={formatNumber(current?.cpu_freq.current, " MHz")}
            detail={`Uptime ${formatUptime(current?.uptime_seconds)}`}
            icon={<Cpu size={18} />}
          />
          <MetricCard
            title="Energia"
            value={formatNumber(current?.power.watts, " W")}
            detail={hasPower ? "Intel RAPL" : "Sem leitura"}
            tone={hasPower ? "normal" : "muted"}
            icon={<Zap size={18} />}
          />
        </section>

        <PeriodFilter
          range={range}
          onRangeChange={setRange}
          onRefresh={loadDashboard}
          query={query}
          loading={loading}
        />

        <div className="grid gap-4 lg:grid-cols-2">
          <CpuUsageChart data={history} />
          <TemperatureChart data={history} />
          <LoadAverageChart data={history} />
          <PowerChart data={history} />
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {!hasTemperature ? <UnavailableMetricWarning type="temperature" /> : null}
          {!hasPower ? <UnavailableMetricWarning type="power" /> : null}
        </div>

        <SettingsPanel
          value={collectInterval}
          onChange={setCollectInterval}
          onSave={saveSettings}
          saving={saving}
        />
      </div>
    </main>
  );
}
