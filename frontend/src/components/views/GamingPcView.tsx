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

function Meter({
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
  return (
    <div className="temp-row">
      <span className="temp-label">{label}</span>
      <div className="temp-track">
        <div className={`temp-fill ${hot ? "temp-hot" : ""}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="temp-val">{value !== undefined ? `${Math.round(value)}${unit}` : "—"}</span>
    </div>
  );
}

function DeviceCard({
  title,
  name,
  temp,
  load,
  power,
}: {
  title: string;
  name?: string;
  temp?: number;
  load?: number;
  power?: number;
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
      </div>
      <Meter label="Temp" value={temp} unit="°C" max={TEMP_MAX} hot={(temp ?? 0) >= 80} />
      <Meter label="Load" value={load} unit="%" max={100} hot={(load ?? 0) >= 90} />
      <Meter label="Power" value={power} unit="W" max={400} />
    </section>
  );
}

export function GamingPcView({ device }: { device?: DeviceState }) {
  if (!device) return <div className="view-empty muted">Gaming PC not configured.</div>;
  const online = device.reachable === "online";
  const e = device.extra ?? {};
  const groups = (e.groups as Group[]) ?? [];

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
            />
            <section className="card gpc-card">
              <div className="gpc-card-head">
                <span className="gpc-title">Memory</span>
              </div>
              <div className="gpc-hero">
                <span className="gpc-temp">
                  {num(e, "memory_load") !== undefined ? Math.round(num(e, "memory_load")!) : "—"}
                </span>
                <span className="gpc-unit">%</span>
              </div>
              <Meter label="Used" value={num(e, "memory_load")} unit="%" max={100} hot={(num(e, "memory_load") ?? 0) >= 90} />
            </section>
          </div>

          <div className="gpc-groups">
            {groups.map((g) => (
              <section className="card gpc-group" key={g.hardware}>
                <div className="card-label">{g.hardware}</div>
                <div className="gpc-sensor-list">
                  {g.sensors.map((srow, i) => (
                    <div className="gpc-sensor" key={`${srow.category}-${srow.name}-${i}`}>
                      <span className="gpc-sensor-name">{srow.name}</span>
                      <span className="gpc-sensor-val">
                        {Number.isInteger(srow.value) ? srow.value : srow.value.toFixed(1)}
                        {srow.unit ? ` ${srow.unit}` : ""}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
