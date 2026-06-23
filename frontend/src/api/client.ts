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

export type RamMetric = {
  timestamp: string;
  totalBytes: number;
  usedBytes: number;
  availableBytes: number;
  freeBytes: number | null;
  usagePercent: number;
  buffersBytes: number | null;
  cachedBytes: number | null;
  sharedBytes: number | null;
  swapTotalBytes: number | null;
  swapUsedBytes: number | null;
  swapUsagePercent: number | null;
  temperatureCelsius: number | null;
};

export type StorageMetric = {
  timestamp: string;
  name: string;
  model: string | null;
  type: string | null;
  sizeBytes: number | null;
  usedBytes: number | null;
  freeBytes: number | null;
  usagePercent: number | null;
  temperatureCelsius: number | null;
  smartStatus: string | null;
  readBytesTotal: number | null;
  writeBytesTotal: number | null;
  readBytesPerSecond: number | null;
  writeBytesPerSecond: number | null;
};

export type GpuMetric = {
  timestamp: string;
  id: string;
  vendor: string | null;
  model: string | null;
  usagePercent: number | null;
  temperatureCelsius: number | null;
  memoryTotalBytes: number | null;
  memoryUsedBytes: number | null;
  memoryUsagePercent: number | null;
  powerWatts: number | null;
  source: string | null;
};

export type GpuCurrent = {
  available: boolean;
  timestamp: string;
  devices: Array<{
    id: string;
    vendor: string | null;
    model: string | null;
    driver: string | null;
    usagePercent: number | null;
    temperatureCelsius: number | null;
    memoryTotalBytes: number | null;
    memoryUsedBytes: number | null;
    memoryUsagePercent: number | null;
    powerWatts: number | null;
  }>;
};

export type EnergyMetric = {
  timestamp: string;
  powerWatts: number | null;
  energyKwh: number | null;
  source: string;
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

export function getRamHistory(query: string) {
  return request<RamMetric[]>(`/metrics/ram?${query}`);
}

export function getStorageHistory(query: string) {
  return request<StorageMetric[]>(`/metrics/storage?${query}`);
}

export function getGpuCurrent() {
  return request<GpuCurrent>("/metrics/gpu/current");
}

export function getGpuHistory(query: string) {
  return request<GpuMetric[]>(`/metrics/gpu?${query}`);
}

export function getEnergyHistory(query: string) {
  return request<EnergyMetric[]>(`/metrics/energy?${query}`);
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
