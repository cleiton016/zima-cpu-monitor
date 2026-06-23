type Props = {
  type: "temperature" | "power";
};

export default function UnavailableMetricWarning({ type }: Props) {
  const content =
    type === "temperature"
      ? {
          title: "Sensor de temperatura não disponível neste hardware.",
          tip: "Verifique se os módulos de sensor estão habilitados no Linux e se /sys foi montado como leitura no container."
        }
      : {
          title: "Medição de energia não disponível neste hardware.",
          tip: "Intel RAPL precisa aparecer em /sys/class/powercap; em alguns CPUs essa leitura não é exposta."
        };

  return (
    <section className="rounded-lg border border-amber-400/40 bg-amber-950/30 p-4">
      <p className="text-sm font-semibold text-amber-200">{content.title}</p>
      <p className="mt-1 text-sm text-amber-100/80">Dica: {content.tip}</p>
    </section>
  );
}
