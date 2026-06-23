export type Metric = {
  timestamp: string;
  cpu_percent: number | null;
  cpu_per_core: number[];
  cpu_freq: {
    current: number | null;
    min: number | null;
    max: number | null;
  };
  load: {
    "1": number | null;
    "5": number | null;
    "15": number | null;
  };
  temperature: {
    current: number | null;
    max: number | null;
    available: boolean;
    sensors: Array<{ source: string; chip: string; label: string; value: number }>;
  };
  power: {
    watts: number | null;
    energy_joules: number | null;
    available: boolean;
  };
  uptime_seconds: number | null;
};

export type Summary = {
  cpu_percent: Stats;
  temperature: Stats & { available: boolean };
  power: Stats & { available: boolean };
};

export type Stats = {
  min: number | null;
  avg: number | null;
  max: number | null;
};

export type Settings = {
  collect_interval_seconds: number;
};

export type DailySummary = {
  date: string;
  cpuPeak: {
    valuePercent: number | null;
    timestamp: string | null;
  };
  temperaturePeak: {
    valueCelsius: number | null;
    timestamp: string | null;
  };
  ramPeak: {
    valuePercent: number | null;
    timestamp: string | null;
  };
  energyTotal: {
    kwh: number | null;
    estimatedCost: number | null;
    currency: string;
  };
};

const API_BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getCurrentMetric() {
  return request<Metric>("/metrics/current");
}

export function getHistory(query: string) {
  return request<Metric[]>(`/metrics/history?${query}`);
}

export function getSummary(query: string) {
  return request<Summary>(`/metrics/summary?${query}`);
}

export function getDailySummary() {
  return request<DailySummary>("/metrics/daily-summary");
}

export function getSettings() {
  return request<Settings>("/settings");
}

export function updateSettings(settings: Settings) {
  return request<Settings>("/settings", {
    method: "PUT",
    body: JSON.stringify(settings)
  });
}

export function csvExportUrl(query: string) {
  return `${API_BASE}/export/csv?${query}`;
}
