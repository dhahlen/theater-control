import { sendCommand } from "../../api";
import type { DeviceState } from "../../types";
import { Btn } from "../common";

const TEMP_MAX = 90; // deg C, for the bar scale

function TempBar({ label, value }: { label: string; value?: number }) {
  const pct = value ? Math.min(100, (value / TEMP_MAX) * 100) : 0;
  const hot = (value ?? 0) >= 70;
  return (
    <div className="temp-row">
      <span className="temp-label">{label}</span>
      <div className="temp-track">
        <div className={`temp-fill ${hot ? "temp-hot" : ""}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="temp-val">{value !== undefined ? `${value}°C` : "—"}</span>
    </div>
  );
}

// Styled remote mirroring the madVR Envy remote layout, buttons wired to
// KeyPress. Sits in the right column so the page does not scroll.
function EnvyRemote({ press }: { press: (button: string) => void }) {
  const colors = ["RED", "GREEN", "BLUE", "YELLOW", "MAGENTA", "CYAN"];
  return (
    <div className="remote">
      <div className="remote-row">
        <button className="rbtn rbtn-power" onClick={() => press("POWER")} aria-label="Power">⏻</button>
        <button className="rbtn" onClick={() => press("INFO")} aria-label="Info">ⓘ</button>
      </div>
      <div className="remote-row">
        <button className="rbtn" onClick={() => press("MENU")} aria-label="Menu">☰</button>
        <button className="rbtn" onClick={() => press("SETTINGS")} aria-label="Settings">⚙</button>
      </div>
      <div className="remote-dpad">
        <button className="rbtn rbtn-up" onClick={() => press("UP")}>▲</button>
        <button className="rbtn rbtn-left" onClick={() => press("LEFT")}>◀</button>
        <button className="rbtn rbtn-ok" onClick={() => press("OK")}>OK</button>
        <button className="rbtn rbtn-right" onClick={() => press("RIGHT")}>▶</button>
        <button className="rbtn rbtn-down" onClick={() => press("DOWN")}>▼</button>
      </div>
      <div className="remote-row">
        <button className="rbtn" onClick={() => press("INPUT")} aria-label="Input">▢</button>
        <button className="rbtn" onClick={() => press("BACK")} aria-label="Back">↩</button>
      </div>
      <div className="remote-colors">
        {colors.map((c) => (
          <button
            key={c}
            className="rbtn rbtn-color"
            style={{ color: `var(--c-${c.toLowerCase()})` }}
            onClick={() => press(c)}
            aria-label={c}
          >
            ◉
          </button>
        ))}
      </div>
    </div>
  );
}

export function MadvrView({ device }: { device?: DeviceState }) {
  if (!device) return <div className="view-empty muted">MadVR not configured.</div>;
  const e = device.extra ?? {};
  const signal = (e.signal as Record<string, string>) ?? {};
  const temps = (e.temperatures as Record<string, number>) ?? {};

  const cmd = (command: string, params?: Record<string, unknown>) =>
    sendCommand("madvr", command, params).catch((err) => console.error(err));
  const press = (button: string) => cmd("key_press", { button });

  return (
    <div className="devview">
      <div className="devview-head">
        <h1>MadVR Envy</h1>
        <span className={`pill ${device.reachable === "online" ? "pill-on" : "pill-off"}`}>
          {device.reachable}
        </span>
      </div>

      <div className="madvr-layout">
        <div className="madvr-main">
          <section className="card">
            <div className="card-label">Signal</div>
            <div className="info-grid">
              <div><span className="muted">Incoming</span><strong>{signal.IncomingSignalInfo ?? "—"}</strong></div>
              <div><span className="muted">Outgoing</span><strong>{signal.OutgoingSignalInfo ?? "—"}</strong></div>
              <div><span className="muted">Aspect</span><strong>{signal.AspectRatio ?? "—"}</strong></div>
            </div>
          </section>

          <section className="card">
            <div className="card-label">Temperatures</div>
            <TempBar label="GPU" value={temps.gpu} />
            <TempBar label="HDMI" value={temps.hdmi} />
            <TempBar label="CPU" value={temps.cpu} />
            <TempBar label="Mainboard" value={temps.mainboard} />
          </section>

          <section className="card">
            <div className="card-label">Aspect ratio &amp; profile</div>
            <div className="row btn-row wrap">
              <Btn onClick={() => cmd("set_aspect_ratio_mode", { mode: "Auto" })}>Auto</Btn>
              <Btn onClick={() => cmd("set_aspect_ratio_mode", { mode: "2.40:1" })}>2.40:1</Btn>
              <Btn onClick={() => cmd("set_aspect_ratio_mode", { mode: "1.85:1" })}>1.85:1</Btn>
              <Btn onClick={() => cmd("set_aspect_ratio_mode", { mode: "16:9" })}>16:9</Btn>
              <Btn onClick={() => cmd("profile_cycle")}>Profile ⟳</Btn>
            </div>
          </section>

          <section className="card">
            <div className="card-label">Power</div>
            <div className="row btn-row">
              <Btn onClick={() => cmd("wake")}>Wake</Btn>
              <Btn onClick={() => cmd("standby")}>Standby</Btn>
              <Btn onClick={() => cmd("power_off")}>Power Off</Btn>
              <Btn onClick={() => cmd("restart")}>Restart</Btn>
            </div>
          </section>
        </div>

        <section className="card madvr-remote">
          <div className="card-label">Remote</div>
          <EnvyRemote press={press} />
        </section>
      </div>
    </div>
  );
}
