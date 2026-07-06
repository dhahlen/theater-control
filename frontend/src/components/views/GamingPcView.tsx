import type { DeviceState } from "../../types";

// Gaming PC telemetry, read from Libre Hardware Monitor via the backend adapter.
// Read-only: headline CPU/GPU meters up top, then every sensor grouped by
// hardware. This is a sub-tab, so it may scroll.

interface SensorRow {
  category: string;
  name: string;
  value: number;
  unit: string;
}
interface Group {
  hardware: string;
  kind: string;
  sensors: SensorRow[];
}

const TEMP_MAX = 100; // deg C, full-scale for the temperature bars

function num(e: Record<string, unknown>, key: string): number | undefined {
  const v = e[key];
  return typeof v === "number" ? v : undefined;
}

function str(e: Record<string, unknown>, key: string): string {
  const v = e[key];
  return typeof v === "string" ? v : "";
}

const toF = (c: number): number => (c * 9) / 5 + 32;

// Libre Hardware Monitor reports VRAM in MB; show GB once it is over a gigabyte.
function fmtSize(value: number, unit: string): string {
  if (unit === "MB" && value >= 1024) return `${(value / 1024).toFixed(1)} GB`;
  return `${Math.round(value)} ${unit}`;
}

function BarRow({
  label,
  pct,
  text,
  hot,
}: {
  label: string;
  pct: number;
  text: string;
  hot?: boolean;
}) {
  return (
    <div className="temp-row">
      <span className="temp-label">{label}</span>
      <div className="temp-track">
        <div className={`temp-fill ${hot ? "temp-hot" : ""}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="temp-val gpc-val">{text}</span>
    </div>
  );
}

function TempMeter({ label, value, hot }: { label: string; value?: number; hot?: boolean }) {
  const pct = value !== undefined ? Math.min(100, Math.max(0, (value / TEMP_MAX) * 100)) : 0;
  const text =
    value !== undefined ? `${Math.round(value)}°C · ${Math.round(toF(value))}°F` : "—";
  return <BarRow label={label} pct={pct} text={text} hot={hot} />;
}

function PlainMeter({
  label,
  value,
  unit,
  max,
  hot,
}: {
  label: string;
  value?: number;
  unit: string;
  max: number;
  hot?: boolean;
}) {
  const pct = value !== undefined ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  const text = value !== undefined ? `${Math.round(value)}${unit}` : "—";
  return <BarRow label={label} pct={pct} text={text} hot={hot} />;
}

interface Vram {
  load?: number;
  used?: number;
  usedUnit: string;
  total?: number;
  totalUnit: string;
}

function VramMeter({ vram }: { vram: Vram }) {
  const havePair = vram.used !== undefined && vram.total !== undefined && vram.total > 0;
  const pct =
    vram.load !== undefined
      ? Math.min(100, Math.max(0, vram.load))
      : havePair
        ? Math.min(100, (vram.used! / vram.total!) * 100)
        : 0;
  let text = "—";
  if (havePair) {
    text = `${fmtSize(vram.used!, vram.usedUnit)} / ${fmtSize(vram.total!, vram.totalUnit)}`;
  } else if (vram.used !== undefined) {
    text = fmtSize(vram.used, vram.usedUnit);
  } else if (vram.load !== undefined) {
    text = `${Math.round(vram.load)}%`;
  }
  const show = havePair || vram.used !== undefined || vram.load !== undefined;
  if (!show) return null;
  return <BarRow label="VRAM" pct={pct} text={text} hot={pct >= 90} />;
}

function DeviceCard({
  title,
  name,
  temp,
  load,
  power,
  vram,
}: {
  title: string;
  name?: string;
  temp?: number;
  load?: number;
  power?: number;
  vram?: Vram;
}) {
  return (
    <section className="card gpc-card">
      <div className="gpc-card-head">
        <span className="gpc-title">{title}</span>
        <span className="muted gpc-name">{name ?? "—"}</span>
      </div>
      <div className="gpc-hero">
        <span className="gpc-temp">{temp !== undefined ? Math.round(temp) : "—"}</span>
        <span className="gpc-unit">°C</span>
        {temp !== undefined && <span className="gpc-fahr">{Math.round(toF(temp))}°F</span>}
      </div>
      <TempMeter label="Temp" value={temp} hot={(temp ?? 0) >= 80} />
      <PlainMeter label="Load" value={load} unit="%" max={100} hot={(load ?? 0) >= 90} />
      <PlainMeter label="Power" value={power} unit="W" max={400} />
      {vram && <VramMeter vram={vram} />}
    </section>
  );
}

export function GamingPcView({ device }: { device?: DeviceState }) {
  if (!device) return <div className="view-empty muted">Gaming PC not configured.</div>;
  const online = device.reachable === "online";
  const e = device.extra ?? {};
  const groups = (e.groups as Group[]) ?? [];

  const memLoad = num(e, "memory_load");
  const vram: Vram = {
    load: num(e, "gpu_mem_load"),
    used: num(e, "gpu_mem_used"),
    usedUnit: str(e, "gpu_mem_used_unit"),
    total: num(e, "gpu_mem_total"),
    totalUnit: str(e, "gpu_mem_total_unit"),
  };

  return (
    <div className="devview devview-wide">
      <div className="devview-head">
        <h1>Gaming PC</h1>
        <span className={`pill ${online ? "pill-on" : "pill-off"}`}>
          {online ? "online" : "offline"}
        </span>
      </div>

      {!online ? (
        <div className="view-empty muted">
          No sensor data. The PC must be on with Libre Hardware Monitor running and its
          remote web server enabled.
        </div>
      ) : (
        <>
          <div className="gpc-heroes">
            <DeviceCard
              title="CPU"
              name={e.cpu_name as string | undefined}
              temp={num(e, "cpu_temp")}
              load={num(e, "cpu_load")}
              power={num(e, "cpu_power")}
            />
            <DeviceCard
              title="GPU"
              name={e.gpu_name as string | undefined}
              temp={num(e, "gpu_temp")}
              load={num(e, "gpu_load")}
              power={num(e, "gpu_power")}
              vram={vram}
            />
            <section className="card gpc-card">
              <div className="gpc-card-head">
                <span className="gpc-title">Memory</span>
              </div>
              <div className="gpc-hero">
                <span className="gpc-temp">{memLoad !== undefined ? Math.round(memLoad) : "—"}</span>
                <span className="gpc-unit">%</span>
              </div>
              <PlainMeter label="Used" value={memLoad} unit="%" max={100} hot={(memLoad ?? 0) >= 90} />
            </section>
          </div>

          <div className="gpc-groups">
            {groups.map((g) => (
              <section className="card gpc-group" key={g.hardware}>
                <div className="card-label">{g.hardware}</div>
                <div className="gpc-sensor-list">
                  {g.sensors.map((srow, i) => {
                    const val = Number.isInteger(srow.value) ? `${srow.value}` : srow.value.toFixed(1);
                    const isTemp = srow.unit === "°C";
                    return (
                      <div className="gpc-sensor" key={`${srow.category}-${srow.name}-${i}`}>
                        <span className="gpc-sensor-name">{srow.name}</span>
                        <span className="gpc-sensor-val">
                          {val}
                          {srow.unit ? ` ${srow.unit}` : ""}
                          {isTemp ? ` · ${Math.round(toF(srow.value))} °F` : ""}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </section>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
