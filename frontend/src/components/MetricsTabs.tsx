import { Cpu, Database, HardDrive, MemoryStick, Trash2, Zap } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import type {
  EnergyMetric,
  EnergyMonthly,
  GpuCurrent,
  GpuMetric,
  Metric,
  MetricCategory,
  RamMetric,
  StorageCurrent,
  StorageMetric
} from "../api/client";
import { CpuUsageChart, LoadAverageChart, PowerChart, TemperatureChart } from "./Charts";

type MetricsTabsProps = {
  cpuHistory: Metric[];
  ramHistory: RamMetric[];
  storageCurrent: StorageCurrent | null;
  storageHistory: StorageMetric[];
  gpuCurrent: GpuCurrent | null;
  gpuHistory: GpuMetric[];
  energyHistory: EnergyMetric[];
  energyMonthly: EnergyMonthly | null;
  clearingHistory: MetricCategory | null;
  onClearHistory: (category: MetricCategory) => Promise<void>;
};

type TabId = "cpu" | "ram" | "storage" | "gpu" | "energy";

function formatTime(timestamp: string) {
  return new Date(timestamp).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit"
  });
}

function EmptyState({ label }: { label: string }) {
  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-sm text-zinc-400">
      {label}
    </section>
  );
}

function formatBytes(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "N/D";
  }
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = value;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function ChartFrame({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
      <h2 className="text-base font-semibold text-zinc-100">{title}</h2>
      <div className="mt-4 h-72">{children}</div>
    </section>
  );
}

function RamCharts({ data }: { data: RamMetric[] }) {
  if (!data.length) {
    return <EmptyState label="Sem dados de RAM no periodo selecionado." />;
  }

  const chartData = data.map((item) => ({
    time: formatTime(item.timestamp),
    ram: item.usagePercent,
    swap: item.swapUsagePercent
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <ChartFrame title="Uso de RAM">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
            <YAxis stroke="#a1a1aa" unit="%" />
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
            <Line type="monotone" dataKey="ram" name="RAM" stroke="#38bdf8" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartFrame>
      <ChartFrame title="Uso de swap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
            <YAxis stroke="#a1a1aa" unit="%" />
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
            <Line type="monotone" dataKey="swap" name="Swap" stroke="#a78bfa" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartFrame>
    </div>
  );
}

function StorageCharts({ current, data }: { current: StorageCurrent | null; data: StorageMetric[] }) {
  const disks = useMemo(() => {
    const currentDisks = current?.devices ?? [];
    if (currentDisks.length) {
      return currentDisks;
    }
    const byName = new Map<string, StorageCurrent["devices"][number]>();
    data.forEach((item) => {
      if (!byName.has(item.name)) {
        byName.set(item.name, {
          name: item.name,
          model: item.model,
          type: item.type,
          sizeBytes: item.sizeBytes,
          temperatureCelsius: item.temperatureCelsius,
          smartStatus: item.smartStatus,
          readBytesTotal: item.readBytesTotal,
          writeBytesTotal: item.writeBytesTotal,
          readBytesPerSecond: item.readBytesPerSecond,
          writeBytesPerSecond: item.writeBytesPerSecond
        });
      }
    });
    return Array.from(byName.values());
  }, [current?.devices, data]);
  const [selectedDisk, setSelectedDisk] = useState("");
  const activeDisk = disks.some((disk) => disk.name === selectedDisk) ? selectedDisk : disks[0]?.name ?? "";
  const selectedDiskInfo = disks.find((disk) => disk.name === activeDisk);
  const selectedHistory = activeDisk ? data.filter((item) => item.name === activeDisk) : [];

  if (!disks.length) {
    return <EmptyState label="Nenhum disco fisico detectado." />;
  }

  const chartData = selectedHistory.map((item) => ({
    time: formatTime(item.timestamp),
    usage: item.usagePercent,
    readMb: item.readBytesTotal === null ? null : item.readBytesTotal / 1024 / 1024,
    writeMb: item.writeBytesTotal === null ? null : item.writeBytesTotal / 1024 / 1024
  }));

  return (
    <div className="flex flex-col gap-4">
      <section className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
        <h2 className="text-base font-semibold text-zinc-100">Discos detectados</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {disks.map((disk) => (
            <button
              key={disk.name}
              type="button"
              onClick={() => setSelectedDisk(disk.name)}
              className={`min-h-28 rounded-lg border p-4 text-left transition ${
                activeDisk === disk.name
                  ? "border-teal-300 bg-teal-300 text-zinc-950"
                  : "border-zinc-800 bg-zinc-900 text-zinc-100 hover:border-zinc-600"
              }`}
            >
              <p className="text-base font-semibold">{disk.name}</p>
              <p className={`mt-2 text-sm ${activeDisk === disk.name ? "text-zinc-800" : "text-zinc-400"}`}>
                {disk.model || "Modelo N/D"}
              </p>
              <p className={`mt-1 text-sm ${activeDisk === disk.name ? "text-zinc-800" : "text-zinc-400"}`}>
                {[disk.type || "Tipo N/D", formatBytes(disk.sizeBytes)].join(" | ")}
              </p>
            </button>
          ))}
        </div>
      </section>

      {selectedDiskInfo ? (
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <p className="text-sm text-zinc-400">Disco</p>
            <p className="mt-2 text-xl font-semibold text-zinc-50">{selectedDiskInfo.name}</p>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <p className="text-sm text-zinc-400">Capacidade</p>
            <p className="mt-2 text-xl font-semibold text-zinc-50">{formatBytes(selectedDiskInfo.sizeBytes)}</p>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <p className="text-sm text-zinc-400">Temperatura</p>
            <p className="mt-2 text-xl font-semibold text-zinc-50">
              {selectedDiskInfo.temperatureCelsius === null || selectedDiskInfo.temperatureCelsius === undefined
                ? "N/D"
                : `${selectedDiskInfo.temperatureCelsius.toFixed(1)} C`}
            </p>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <p className="text-sm text-zinc-400">SMART</p>
            <p className="mt-2 text-xl font-semibold text-zinc-50">{selectedDiskInfo.smartStatus || "N/D"}</p>
          </div>
        </section>
      ) : null}

      {!selectedHistory.length ? <EmptyState label="Sem historico para o disco selecionado no periodo." /> : null}

      <div className="grid gap-4 lg:grid-cols-2">
      <ChartFrame title="Uso do disco">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
            <YAxis stroke="#a1a1aa" unit="%" />
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
            <Line type="monotone" dataKey="usage" name="Uso" stroke="#2dd4bf" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartFrame>
      <ChartFrame title="Leitura e escrita total">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
            <YAxis stroke="#a1a1aa" unit=" MB" />
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
            <Legend />
            <Line type="monotone" dataKey="readMb" name="Lido" stroke="#38bdf8" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="writeMb" name="Escrito" stroke="#f59e0b" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartFrame>
      </div>
    </div>
  );
}

function GpuCharts({ current, data }: { current: GpuCurrent | null; data: GpuMetric[] }) {
  if (!current?.available && !data.length) {
    return <EmptyState label="GPU nao detectada ou sem historico disponivel." />;
  }

  const chartData = data.map((item) => ({
    time: formatTime(item.timestamp),
    usage: item.usagePercent,
    temperature: item.temperatureCelsius,
    memory: item.memoryUsagePercent
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <ChartFrame title="Uso da GPU">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
            <YAxis stroke="#a1a1aa" unit="%" />
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
            <Line type="monotone" dataKey="usage" name="Uso" stroke="#a78bfa" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartFrame>
      <ChartFrame title="Temperatura e memoria GPU">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
            <YAxis stroke="#a1a1aa" />
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
            <Legend />
            <Line type="monotone" dataKey="temperature" name="Temp C" stroke="#f59e0b" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="memory" name="Memoria %" stroke="#38bdf8" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartFrame>
    </div>
  );
}

function EnergyCharts({ data, monthly }: { data: EnergyMetric[]; monthly: EnergyMonthly | null }) {
  if (!data.length) {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <EmptyState label="Sem dados de energia no periodo selecionado." />
        <EnergyMonthlyBarChart monthly={monthly} />
      </div>
    );
  }

  const chartData = data.map((item) => ({
    time: formatTime(item.timestamp),
    watts: item.powerWatts,
    kwh: item.energyKwh
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <ChartFrame title="Potencia instantanea">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
            <YAxis stroke="#a1a1aa" unit=" W" />
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
            <Line type="monotone" dataKey="watts" name="Watts" stroke="#84cc16" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartFrame>
      <ChartFrame title="Consumo por amostra">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
            <YAxis stroke="#a1a1aa" unit=" kWh" />
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
            <Line type="monotone" dataKey="kwh" name="kWh" stroke="#f59e0b" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartFrame>
      <EnergyMonthlyBarChart monthly={monthly} />
    </div>
  );
}

function EnergyMonthlyBarChart({ monthly }: { monthly: EnergyMonthly | null }) {
  if (!monthly) {
    return <EmptyState label="Sem dados mensais de energia." />;
  }

  return (
    <ChartFrame title="Consumo mensal">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={monthly.months}>
          <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
          <XAxis dataKey="label" stroke="#a1a1aa" />
          <YAxis stroke="#a1a1aa" />
          <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
          <Legend />
          <Bar dataKey="kwh" name="kWh" fill="#84cc16" radius={[4, 4, 0, 0]} />
          <Bar dataKey="cost" name={monthly.currency} fill="#38bdf8" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

export default function MetricsTabs({
  cpuHistory,
  ramHistory,
  storageCurrent,
  storageHistory,
  gpuCurrent,
  gpuHistory,
  energyHistory,
  energyMonthly,
  clearingHistory,
  onClearHistory
}: MetricsTabsProps) {
  const tabs = useMemo(() => {
    const baseTabs: Array<{ id: TabId; label: string; icon: ReactNode }> = [
      { id: "cpu", label: "CPU", icon: <Cpu size={16} /> },
      { id: "ram", label: "RAM", icon: <MemoryStick size={16} /> },
      { id: "storage", label: "HDs", icon: <HardDrive size={16} /> },
      { id: "energy", label: "Energia", icon: <Zap size={16} /> }
    ];
    if (gpuCurrent?.available || gpuHistory.length > 0) {
      baseTabs.splice(3, 0, { id: "gpu", label: "GPU", icon: <Database size={16} /> });
    }
    return baseTabs;
  }, [gpuCurrent?.available, gpuHistory.length]);
  const [activeTab, setActiveTab] = useState<TabId>("cpu");
  const visibleTab = tabs.some((tab) => tab.id === activeTab) ? activeTab : "cpu";
  const activeLabel = tabs.find((tab) => tab.id === visibleTab)?.label ?? "historico";
  const isClearingActive = clearingHistory === visibleTab;

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 border-b border-zinc-800 pb-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex h-10 items-center gap-2 rounded-lg border px-4 text-sm font-medium transition ${
                visibleTab === tab.id
                  ? "border-teal-300 bg-teal-300 text-zinc-950"
                  : "border-zinc-700 bg-zinc-900 text-zinc-200 hover:border-zinc-500"
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={() => void onClearHistory(visibleTab)}
          disabled={clearingHistory !== null}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-red-400/50 bg-red-950/40 px-4 text-sm font-medium text-red-100 transition hover:border-red-300 hover:bg-red-900/60 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Trash2 size={16} />
          {isClearingActive ? "Limpando" : `Limpar historico ${activeLabel}`}
        </button>
      </div>

      {visibleTab === "cpu" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <CpuUsageChart data={cpuHistory} />
          <TemperatureChart data={cpuHistory} />
          <LoadAverageChart data={cpuHistory} />
          <PowerChart data={cpuHistory} />
        </div>
      ) : null}
      {visibleTab === "ram" ? <RamCharts data={ramHistory} /> : null}
      {visibleTab === "storage" ? <StorageCharts current={storageCurrent} data={storageHistory} /> : null}
      {visibleTab === "gpu" ? <GpuCharts current={gpuCurrent} data={gpuHistory} /> : null}
      {visibleTab === "energy" ? <EnergyCharts data={energyHistory} monthly={energyMonthly} /> : null}
    </section>
  );
}
