import type { ReactNode } from "react";

type MetricCardProps = {
  title: string;
  value: string;
  detail?: string;
  tone?: "normal" | "warning" | "critical" | "muted";
  icon?: ReactNode;
};

const toneClasses = {
  normal: "border-emerald-400/30 bg-zinc-900",
  warning: "border-amber-400/40 bg-zinc-900",
  critical: "border-red-400/50 bg-zinc-900",
  muted: "border-zinc-700 bg-zinc-900"
};

export default function MetricCard({ title, value, detail, tone = "normal", icon }: MetricCardProps) {
  return (
    <section className={`rounded-lg border p-4 ${toneClasses[tone]}`}>
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-zinc-400">{title}</p>
        {icon ? <div className="text-zinc-400">{icon}</div> : null}
      </div>
      <p className="mt-3 text-2xl font-semibold text-zinc-50">{value}</p>
      {detail ? <p className="mt-2 text-sm text-zinc-400">{detail}</p> : null}
    </section>
  );
}
