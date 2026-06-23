import { Save } from "lucide-react";

type SettingsPanelProps = {
  value: number;
  onChange: (value: number) => void;
  onSave: () => void;
  saving: boolean;
};

const intervals = [
  { label: "5s", value: 5 },
  { label: "10s", value: 10 },
  { label: "30s", value: 30 },
  { label: "1min", value: 60 },
  { label: "5min", value: 300 },
  { label: "15min", value: 900 }
];

export default function SettingsPanel({ value, onChange, onSave, saving }: SettingsPanelProps) {
  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-zinc-100">Intervalo de coleta</h2>
          <p className="mt-1 text-sm text-zinc-400">Valor aplicado pelo backend sem reiniciar o container.</p>
        </div>
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          title="Salvar intervalo"
          className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-teal-300 px-4 text-sm font-semibold text-zinc-950 hover:bg-teal-200 disabled:opacity-60"
        >
          <Save size={18} />
          Salvar
        </button>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {intervals.map((interval) => (
          <button
            key={interval.value}
            type="button"
            onClick={() => onChange(interval.value)}
            className={`h-10 rounded-lg border px-4 text-sm font-medium ${
              value === interval.value
                ? "border-teal-300 bg-teal-300 text-zinc-950"
                : "border-zinc-700 bg-zinc-900 text-zinc-200 hover:border-zinc-500"
            }`}
          >
            {interval.label}
          </button>
        ))}
      </div>
    </section>
  );
}
