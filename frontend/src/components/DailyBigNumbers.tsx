import { Cpu, MemoryStick, Thermometer, Zap } from "lucide-react";
import type { ReactNode } from "react";

import type { DailySummary } from "../api/client";

type DailyBigNumbersProps = {
  summary: DailySummary | null;
  loading: boolean;
};

function formatPercent(value: number | null | undefined) {
  return value === null || value === undefined ? "Sem dados hoje" : `${value.toFixed(1)}%`;
}

function formatTemperature(value: number | null | undefined) {
  return value === null || value === undefined ? "Sem dados hoje" : `${value.toFixed(1)} C`;
}

function formatEnergy(value: number | null | undefined) {
  return value === null || value === undefined || value === 0 ? "Sem dados hoje" : `${value.toFixed(3)} kWh`;
}

function formatTime(timestamp: string | null | undefined) {
  if (!timestamp) {
    return "";
  }
  return new Date(timestamp).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit"
  });
}

function formatCost(summary: DailySummary | null) {
  const energy = summary?.energyTotal;
  if (!energy?.estimatedCost) {
    return "";
  }
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: energy.currency || "BRL"
  }).format(energy.estimatedCost);
}

function BigNumberCard({
  title,
  value,
  detail,
  icon
}: {
  title: string;
  value: string;
  detail: string;
  icon: ReactNode;
}) {
  return (
    <section className="min-h-32 rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-zinc-400">{title}</p>
        <div className="text-zinc-500">{icon}</div>
      </div>
      <p className="mt-4 text-2xl font-semibold text-zinc-50">{value}</p>
      <p className="mt-2 min-h-5 text-sm text-zinc-400">{detail}</p>
    </section>
  );
}

export default function DailyBigNumbers({ summary, loading }: DailyBigNumbersProps) {
  const loadingText = loading ? "Carregando" : "Sem dados hoje";
  const cpuTime = formatTime(summary?.cpuPeak.timestamp);
  const temperatureTime = formatTime(summary?.temperaturePeak.timestamp);
  const ramTime = formatTime(summary?.ramPeak.timestamp);
  const cost = formatCost(summary);

  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <BigNumberCard
        title="Pico CPU hoje"
        value={loading ? loadingText : formatPercent(summary?.cpuPeak.valuePercent)}
        detail={cpuTime ? `Horario ${cpuTime}` : ""}
        icon={<Cpu size={18} />}
      />
      <BigNumberCard
        title="Maior temperatura"
        value={loading ? loadingText : formatTemperature(summary?.temperaturePeak.valueCelsius)}
        detail={temperatureTime ? `Horario ${temperatureTime}` : ""}
        icon={<Thermometer size={18} />}
      />
      <BigNumberCard
        title="Pico RAM hoje"
        value={loading ? loadingText : formatPercent(summary?.ramPeak.valuePercent)}
        detail={ramTime ? `Horario ${ramTime}` : ""}
        icon={<MemoryStick size={18} />}
      />
      <BigNumberCard
        title="Energia hoje"
        value={loading ? loadingText : formatEnergy(summary?.energyTotal.kwh)}
        detail={cost || ""}
        icon={<Zap size={18} />}
      />
    </section>
  );
}
