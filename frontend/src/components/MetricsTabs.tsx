import { Cpu, Database, HardDrive, MemoryStick, Zap } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import type { EnergyMetric, GpuCurrent, GpuMetric, Metric, RamMetric, StorageMetric } from "../api/client";
import { CpuUsageChart, LoadAverageChart, PowerChart, TemperatureChart } from "./Charts";

type MetricsTabsProps = {
  cpuHistory: Metric[];
  ramHistory: RamMetric[];
  storageHistory: StorageMetric[];
  gpuCurrent: GpuCurrent | null;
  gpuHistory: GpuMetric[];
  energyHistory: EnergyMetric[];
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

function StorageCharts({ data }: { data: StorageMetric[] }) {
  if (!data.length) {
    return <EmptyState label="Sem dados de HDs/SSDs no periodo selecionado." />;
  }

  const chartData = data.map((item) => ({
    time: formatTime(item.timestamp),
    usage: item.usagePercent,
    readMb: item.readBytesTotal === null ? null : item.readBytesTotal / 1024 / 1024,
    writeMb: item.writeBytesTotal === null ? null : item.writeBytesTotal / 1024 / 1024
  }));

  return (
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

function EnergyCharts({ data }: { data: EnergyMetric[] }) {
  if (!data.length) {
    return <EmptyState label="Sem dados de energia no periodo selecionado." />;
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
    </div>
  );
}

export default function MetricsTabs({
  cpuHistory,
  ramHistory,
  storageHistory,
  gpuCurrent,
  gpuHistory,
  energyHistory
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

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2 border-b border-zinc-800 pb-3">
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

      {visibleTab === "cpu" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <CpuUsageChart data={cpuHistory} />
          <TemperatureChart data={cpuHistory} />
          <LoadAverageChart data={cpuHistory} />
          <PowerChart data={cpuHistory} />
        </div>
      ) : null}
      {visibleTab === "ram" ? <RamCharts data={ramHistory} /> : null}
      {visibleTab === "storage" ? <StorageCharts data={storageHistory} /> : null}
      {visibleTab === "gpu" ? <GpuCharts current={gpuCurrent} data={gpuHistory} /> : null}
      {visibleTab === "energy" ? <EnergyCharts data={energyHistory} /> : null}
    </section>
  );
}
