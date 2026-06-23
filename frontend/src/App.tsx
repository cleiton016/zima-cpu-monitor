import { Activity, Cpu, Gauge, Thermometer, Zap } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getCurrentMetric,
  getDailySummary,
  getEnergyHistory,
  getEnergyMonthly,
  getEnergySettings,
  getGpuCurrent,
  getGpuHistory,
  getHistory,
  getRamHistory,
  getSettings,
  getSummary,
  getStorageHistory,
  updateSettings,
  updateEnergySettings,
  type DailySummary,
  type EnergyMetric,
  type EnergyMonthly,
  type EnergySettings,
  type GpuCurrent,
  type GpuMetric,
  type Metric,
  type RamMetric,
  type StorageMetric,
  type Summary
} from "./api/client";
import MetricCard from "./components/MetricCard";
import DailyBigNumbers from "./components/DailyBigNumbers";
import EnergySettingsCard from "./components/EnergySettingsCard";
import HardwareInfoButton from "./components/HardwareInfoButton";
import MetricsTabs from "./components/MetricsTabs";
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

function buildCategoryQuery(range: RangeOption) {
  const now = new Date();
  const from = new Date(now);
  if (range === "1h") {
    from.setHours(now.getHours() - 1);
  } else if (range === "6h") {
    from.setHours(now.getHours() - 6);
  } else if (range === "24h") {
    from.setDate(now.getDate() - 1);
  } else if (range === "7d") {
    from.setDate(now.getDate() - 7);
  } else {
    from.setDate(now.getDate() - 30);
  }
  const bucket = range === "1h" || range === "6h" || range === "24h" ? "minute" : "hour";
  return `from=${encodeURIComponent(from.toISOString())}&to=${encodeURIComponent(now.toISOString())}&bucket=${bucket}`;
}

export default function App() {
  const [current, setCurrent] = useState<Metric | null>(null);
  const [history, setHistory] = useState<Metric[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
  const [ramHistory, setRamHistory] = useState<RamMetric[]>([]);
  const [storageHistory, setStorageHistory] = useState<StorageMetric[]>([]);
  const [gpuCurrent, setGpuCurrent] = useState<GpuCurrent | null>(null);
  const [gpuHistory, setGpuHistory] = useState<GpuMetric[]>([]);
  const [energyHistory, setEnergyHistory] = useState<EnergyMetric[]>([]);
  const [energyMonthly, setEnergyMonthly] = useState<EnergyMonthly | null>(null);
  const [energySettings, setEnergySettings] = useState<EnergySettings | null>(null);
  const [range, setRange] = useState<RangeOption>("24h");
  const [collectInterval, setCollectInterval] = useState(30);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingEnergy, setSavingEnergy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useMemo(() => `range=${range}`, [range]);
  const categoryQuery = useMemo(() => buildCategoryQuery(range), [range]);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        currentMetric,
        historyData,
        summaryData,
        dailySummaryData,
        ramHistoryData,
        storageHistoryData,
        gpuCurrentData,
        gpuHistoryData,
        energyHistoryData,
        energyMonthlyData,
        energySettingsData,
        settings
      ] = await Promise.all([
        getCurrentMetric(),
        getHistory(query),
        getSummary(query),
        getDailySummary(),
        getRamHistory(categoryQuery),
        getStorageHistory(categoryQuery),
        getGpuCurrent(),
        getGpuHistory(categoryQuery),
        getEnergyHistory(categoryQuery),
        getEnergyMonthly(),
        getEnergySettings(),
        getSettings()
      ]);
      setCurrent(currentMetric);
      setHistory(historyData);
      setSummary(summaryData);
      setDailySummary(dailySummaryData);
      setRamHistory(ramHistoryData);
      setStorageHistory(storageHistoryData);
      setGpuCurrent(gpuCurrentData);
      setGpuHistory(gpuHistoryData);
      setEnergyHistory(energyHistoryData);
      setEnergyMonthly(energyMonthlyData);
      setEnergySettings(energySettingsData);
      setCollectInterval(settings.collect_interval_seconds);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar métricas.");
    } finally {
      setLoading(false);
    }
  }, [categoryQuery, query]);

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

  async function saveEnergySettings(settings: EnergySettings) {
    setSavingEnergy(true);
    setError(null);
    try {
      const updated = await updateEnergySettings(settings);
      setEnergySettings(updated);
      const monthly = await getEnergyMonthly();
      setEnergyMonthly(monthly);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar energia.");
    } finally {
      setSavingEnergy(false);
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
          <div className="flex flex-col gap-2 sm:items-end">
            <p className="text-sm text-zinc-400">
            Última leitura: {current ? new Date(current.timestamp).toLocaleString("pt-BR") : "aguardando"}
            </p>
            <HardwareInfoButton />
          </div>
        </header>

        {error ? (
          <section className="rounded-lg border border-red-400/50 bg-red-950/40 p-4 text-sm text-red-100">
            {error}
          </section>
        ) : null}

        <DailyBigNumbers summary={dailySummary} loading={loading} />

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

        <EnergySettingsCard settings={energySettings} saving={savingEnergy} onSave={saveEnergySettings} />

        <MetricsTabs
          cpuHistory={history}
          ramHistory={ramHistory}
          storageHistory={storageHistory}
          gpuCurrent={gpuCurrent}
          gpuHistory={gpuHistory}
          energyHistory={energyHistory}
          energyMonthly={energyMonthly}
        />

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
