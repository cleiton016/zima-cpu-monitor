import { Info } from "lucide-react";
import { useState } from "react";

import { getHardwareInfo, type HardwareInfo } from "../api/client";
import HardwareInfoModal from "./HardwareInfoModal";

export default function HardwareInfoButton() {
  const [open, setOpen] = useState(false);
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function openModal() {
    setOpen(true);
    setLoading(true);
    setError(null);
    try {
      const data = await getHardwareInfo();
      setHardware(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar hardware.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => void openModal()}
        className="inline-flex h-10 items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-sm font-medium text-zinc-100 transition hover:border-teal-300 hover:text-teal-200"
      >
        <Info size={16} />
        Info
      </button>
      <HardwareInfoModal
        open={open}
        loading={loading}
        error={error}
        hardware={hardware}
        onClose={() => setOpen(false)}
      />
    </>
  );
}
