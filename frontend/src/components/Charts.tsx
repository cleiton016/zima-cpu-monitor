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
import { Info } from "lucide-react";
import { useState, type ReactNode } from "react";
import type { Metric } from "../api/client";

type ChartProps = {
  data: Metric[];
};

function formatTime(timestamp: string) {
  return new Date(timestamp).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit"
  });
}

function ChartFrame({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  const [showDescription, setShowDescription] = useState(false);

  return (
    <section className="relative rounded-lg border border-zinc-800 bg-zinc-950 p-4">
      <div className="flex items-center justify-between gap-3 pr-10">
        <h2 className="text-base font-semibold text-zinc-100">{title}</h2>
      </div>
      <button
        type="button"
        onClick={() => setShowDescription((current) => !current)}
        aria-expanded={showDescription}
        aria-label={`Mostrar descricao do grafico ${title}`}
        title="Informacoes do grafico"
        className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full border border-zinc-700 bg-zinc-900 text-zinc-300 transition hover:border-teal-300 hover:text-teal-200"
      >
        <Info size={16} />
      </button>
      {showDescription ? (
        <div className="mt-3 rounded-lg border border-teal-300/30 bg-teal-950/30 p-3 text-sm leading-6 text-zinc-200">
          {description}
        </div>
      ) : null}
      <div className="mt-4 h-72">{children}</div>
    </section>
  );
}

export function CpuUsageChart({ data }: ChartProps) {
  const chartData = data.map((item) => ({
    time: formatTime(item.timestamp),
    cpu: item.cpu_percent
  }));

  return (
    <ChartFrame title="Uso da CPU" description="Mostra a porcentagem de uso total da CPU ao longo do periodo selecionado. Valores altos por muito tempo indicam maior carga de processamento.">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
          <YAxis stroke="#a1a1aa" unit="%" />
          <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
          <Line type="monotone" dataKey="cpu" name="CPU" stroke="#2dd4bf" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

export function TemperatureChart({ data }: ChartProps) {
  const chartData = data.map((item) => ({
    time: formatTime(item.timestamp),
    current: item.temperature.current,
    max: item.temperature.max
  }));

  return (
    <ChartFrame title="Temperatura" description="Mostra a temperatura atual lida pelos sensores disponiveis e o pico registrado no periodo. Leituras acima de 70°C pedem atencao; acima de 80°C indicam estado critico.">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
          <YAxis stroke="#a1a1aa" unit="°C" />
          <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
          <Legend />
          <Line type="monotone" dataKey="current" name="Atual" stroke="#f59e0b" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="max" name="Pico" stroke="#ef4444" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

export function LoadAverageChart({ data }: ChartProps) {
  const chartData = data.map((item) => ({
    time: formatTime(item.timestamp),
    "1 min": item.load["1"],
    "5 min": item.load["5"],
    "15 min": item.load["15"]
  }));

  return (
    <ChartFrame title="Load average" description="Mostra a media de carga do sistema em 1, 5 e 15 minutos. Quanto maior o valor, mais processos estao competindo por CPU; comparar as tres linhas ajuda a identificar picos recentes ou carga sustentada.">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#a1a1aa" minTickGap={24} />
          <YAxis stroke="#a1a1aa" />
          <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" }} />
          <Legend />
          <Line type="monotone" dataKey="1 min" stroke="#38bdf8" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="5 min" stroke="#a78bfa" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="15 min" stroke="#fb7185" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

export function PowerChart({ data }: ChartProps) {
  const chartData = data.map((item) => ({
    time: formatTime(item.timestamp),
    watts: item.power.watts
  }));

  return (
    <ChartFrame title="Consumo de energia" description="Mostra a potencia estimada em watts a partir da variacao de energia acumulada pelo Intel RAPL. O grafico aparece quando o hardware expoe essa medicao em /sys/class/powercap.">
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
  );
}
