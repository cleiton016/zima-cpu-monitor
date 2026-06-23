import { X } from "lucide-react";
import type { ReactNode } from "react";

import type { HardwareInfo } from "../api/client";

type HardwareInfoModalProps = {
  open: boolean;
  loading: boolean;
  error: string | null;
  hardware: HardwareInfo | null;
  onClose: () => void;
};

function valueOrUnavailable(value: string | number | null | undefined, suffix = "") {
  if (value === null || value === undefined || value === "") {
    return "Nao disponivel";
  }
  return `${value}${suffix}`;
}

function formatBytes(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "Nao disponivel";
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

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <p className="text-xs font-medium uppercase text-zinc-500">{label}</p>
      <p className="mt-1 break-words text-sm text-zinc-100">{value}</p>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-zinc-800 pt-4">
      <h3 className="text-sm font-semibold text-zinc-200">{title}</h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{children}</div>
    </section>
  );
}

export default function HardwareInfoModal({ open, loading, error, hardware, onClose }: HardwareInfoModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-lg border border-zinc-700 bg-zinc-950 p-5 shadow-2xl">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-teal-300">Hardware</p>
            <h2 className="text-xl font-semibold text-zinc-50">Informacoes tecnicas</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            title="Fechar"
            className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-700 bg-zinc-900 text-zinc-200 hover:border-zinc-500"
          >
            <X size={18} />
          </button>
        </div>

        {loading ? <p className="mt-6 text-sm text-zinc-400">Carregando informacoes...</p> : null}
        {error ? (
          <section className="mt-6 rounded-lg border border-red-400/50 bg-red-950/40 p-4 text-sm text-red-100">
            {error}
          </section>
        ) : null}

        {!loading && !error && hardware ? (
          <div className="mt-6 flex flex-col gap-5">
            <Section title="Processador">
              <Field label="Modelo" value={valueOrUnavailable(hardware.cpu.model)} />
              <Field label="Fabricante" value={valueOrUnavailable(hardware.cpu.vendor)} />
              <Field label="Arquitetura" value={valueOrUnavailable(hardware.cpu.architecture)} />
              <Field label="Nucleos fisicos" value={valueOrUnavailable(hardware.cpu.physicalCores)} />
              <Field label="Threads" value={valueOrUnavailable(hardware.cpu.threads)} />
              <Field label="Frequencia atual" value={valueOrUnavailable(hardware.cpu.currentFrequencyMHz, " MHz")} />
              <Field label="Frequencia base" value={valueOrUnavailable(hardware.cpu.baseFrequencyMHz, " MHz")} />
              <Field label="Cache" value={valueOrUnavailable(hardware.cpu.cache)} />
            </Section>

            <Section title="Placa-mae">
              <Field label="Fabricante" value={valueOrUnavailable(hardware.motherboard.vendor)} />
              <Field label="Modelo" value={valueOrUnavailable(hardware.motherboard.model)} />
              <Field label="Versao" value={valueOrUnavailable(hardware.motherboard.version)} />
              <Field label="Serial" value={valueOrUnavailable(hardware.motherboard.serial)} />
              <Field label="BIOS vendor" value={valueOrUnavailable(hardware.motherboard.biosVendor)} />
              <Field label="BIOS version" value={valueOrUnavailable(hardware.motherboard.biosVersion)} />
              <Field label="BIOS date" value={valueOrUnavailable(hardware.motherboard.biosDate)} />
            </Section>

            <Section title="GPU">
              <Field label="Detectada" value={hardware.gpu.available ? "Sim" : "Nao"} />
              <Field label="Fabricante" value={valueOrUnavailable(hardware.gpu.vendor)} />
              <Field label="Modelo" value={valueOrUnavailable(hardware.gpu.model)} />
              <Field label="Driver" value={valueOrUnavailable(hardware.gpu.driver)} />
              <Field label="Memoria dedicada" value={formatBytes(hardware.gpu.memoryTotalBytes)} />
              <Field label="Temperatura" value={valueOrUnavailable(hardware.gpu.temperatureCelsius, " C")} />
              <Field label="Uso atual" value={valueOrUnavailable(hardware.gpu.usagePercent, "%")} />
            </Section>

            <Section title="Memoria RAM">
              <Field label="Total" value={formatBytes(hardware.memory.totalBytes)} />
              <Field label="Em uso" value={formatBytes(hardware.memory.usedBytes)} />
              <Field label="Disponivel" value={formatBytes(hardware.memory.availableBytes)} />
              <Field label="Livre" value={formatBytes(hardware.memory.freeBytes)} />
              <Field label="Swap total" value={formatBytes(hardware.memory.swapTotalBytes)} />
              <Field label="Swap em uso" value={formatBytes(hardware.memory.swapUsedBytes)} />
              <Field label="Temperatura" value={valueOrUnavailable(hardware.memory.temperatureCelsius, " C")} />
            </Section>

            <section className="border-t border-zinc-800 pt-4">
              <h3 className="text-sm font-semibold text-zinc-200">HDs / SSDs</h3>
              {hardware.storage.length ? (
                <div className="mt-3 grid gap-3 lg:grid-cols-2">
                  {hardware.storage.map((disk) => (
                    <div key={disk.name} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
                      <p className="text-sm font-semibold text-zinc-100">{disk.name}</p>
                      <div className="mt-3 grid gap-3 sm:grid-cols-2">
                        <Field label="Modelo" value={valueOrUnavailable(disk.model)} />
                        <Field label="Serial" value={valueOrUnavailable(disk.serial)} />
                        <Field label="Tipo" value={valueOrUnavailable(disk.type)} />
                        <Field label="Capacidade" value={formatBytes(disk.sizeBytes)} />
                        <Field label="Usado" value={formatBytes(disk.usedBytes)} />
                        <Field label="Livre" value={formatBytes(disk.freeBytes)} />
                        <Field label="Uso" value={valueOrUnavailable(disk.usagePercent, "%")} />
                        <Field label="Temperatura" value={valueOrUnavailable(disk.temperatureCelsius, " C")} />
                        <Field label="SMART" value={valueOrUnavailable(disk.smartStatus)} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-zinc-400">Nao disponivel</p>
              )}
            </section>
          </div>
        ) : null}
      </div>
    </div>
  );
}
