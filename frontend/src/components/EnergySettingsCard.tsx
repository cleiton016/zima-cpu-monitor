import { Save, Zap } from "lucide-react";
import { useEffect, useState } from "react";

import type { EnergySettings } from "../api/client";

type EnergySettingsCardProps = {
  settings: EnergySettings | null;
  saving: boolean;
  onSave: (settings: EnergySettings) => Promise<void>;
};

function formatDraft(value: number | null | undefined) {
  return value === null || value === undefined ? "" : String(value).replace(".", ",");
}

export default function EnergySettingsCard({ settings, saving, onSave }: EnergySettingsCardProps) {
  const [draft, setDraft] = useState(formatDraft(settings?.kwhPrice));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraft(formatDraft(settings?.kwhPrice));
  }, [settings?.kwhPrice]);

  async function save() {
    const normalized = draft.trim().replace(",", ".");
    const value = Number(normalized);
    if (!Number.isFinite(value) || value <= 0) {
      setError("Informe um valor maior que zero.");
      return;
    }
    setError(null);
    await onSave({
      kwhPrice: value,
      currency: settings?.currency || "BRL"
    });
  }

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm font-medium text-zinc-400">
            <Zap size={16} />
            Energia
          </div>
          <label className="mt-3 block text-sm text-zinc-300" htmlFor="kwh-price">
            Valor do kWh
          </label>
          <div className="mt-2 flex h-11 max-w-xs items-center rounded-lg border border-zinc-700 bg-zinc-950 px-3 focus-within:border-teal-300">
            <span className="text-sm text-zinc-500">R$</span>
            <input
              id="kwh-price"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              inputMode="decimal"
              className="h-full min-w-0 flex-1 bg-transparent px-2 text-base text-zinc-100 outline-none"
              placeholder="0,95"
            />
          </div>
          {error ? <p className="mt-2 text-sm text-red-300">{error}</p> : null}
        </div>
        <button
          type="button"
          onClick={() => void save()}
          disabled={saving}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-lg border border-teal-300 bg-teal-300 px-4 text-sm font-semibold text-zinc-950 transition hover:bg-teal-200 disabled:opacity-60"
        >
          <Save size={16} />
          {saving ? "Salvando" : "Salvar"}
        </button>
      </div>
    </section>
  );
}
