import { Download, RefreshCw } from "lucide-react";
import { csvExportUrl } from "../api/client";

export type RangeOption = "1h" | "6h" | "24h" | "7d" | "30d";

type PeriodFilterProps = {
  range: RangeOption;
  onRangeChange: (range: RangeOption) => void;
  onRefresh: () => void;
  query: string;
  loading: boolean;
};

const options: Array<{ label: string; value: RangeOption }> = [
  { label: "1h", value: "1h" },
  { label: "6h", value: "6h" },
  { label: "24h", value: "24h" },
  { label: "7d", value: "7d" },
  { label: "30d", value: "30d" }
];

export default function PeriodFilter({ range, onRangeChange, onRefresh, query, loading }: PeriodFilterProps) {
  return (
    <section className="border-y border-zinc-800 py-4">
      <div className="mb-3">
        <h2 className="text-base font-semibold text-zinc-100">Periodo de analise</h2>
        <p className="mt-1 text-sm text-zinc-400">Escolha a janela de tempo usada nos cards, graficos e exportacao CSV.</p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => onRangeChange(option.value)}
              className={`h-10 rounded-lg border px-4 text-sm font-medium transition ${
                range === option.value
                  ? "border-teal-300 bg-teal-300 text-zinc-950"
                  : "border-zinc-700 bg-zinc-900 text-zinc-200 hover:border-zinc-500"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            title="Atualizar"
            className="inline-flex h-10 items-center justify-center rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-zinc-100 hover:border-zinc-500 disabled:opacity-60"
          >
            <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
          </button>
          <a
            href={csvExportUrl(query)}
            title="Exportar CSV"
            className="inline-flex h-10 items-center justify-center rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-zinc-100 hover:border-zinc-500"
          >
            <Download size={18} />
          </a>
        </div>
      </div>
    </section>
  );
}
