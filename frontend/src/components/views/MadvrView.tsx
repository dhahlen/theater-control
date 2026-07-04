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

export function MadvrView({ device }: { device?: DeviceState }) {
  if (!device) return <div className="view-empty muted">MadVR not configured.</div>;
  const e = device.extra ?? {};
  const signal = (e.signal as Record<string, string>) ?? {};
  const temps = (e.temperatures as Record<string, number>) ?? {};

  const cmd = (command: string, params?: Record<string, unknown>) =>
    sendCommand("madvr", command, params).catch((err) => console.error(err));
  const key = (button: string) => cmd("key_press", { button });

  return (
    <div className="devview">
      <div className="devview-head">
        <h1>MadVR Envy</h1>
        <span className={`pill ${device.reachable === "online" ? "pill-on" : "pill-off"}`}>
          {device.reachable}
        </span>
      </div>

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
        <div className="card-label">Remote</div>
        <div className="dpad">
          <div />
          <Btn onClick={() => key("UP")}>▲</Btn>
          <div />
          <Btn onClick={() => key("LEFT")}>◀</Btn>
          <Btn onClick={() => key("OK")}>OK</Btn>
          <Btn onClick={() => key("RIGHT")}>▶</Btn>
          <div />
          <Btn onClick={() => key("DOWN")}>▼</Btn>
          <div />
        </div>
        <div className="row btn-row">
          <Btn onClick={() => key("MENU")}>Menu</Btn>
          <Btn onClick={() => key("SETTINGS")}>Settings</Btn>
          <Btn onClick={() => key("INFO")}>Info</Btn>
          <Btn onClick={() => key("BACK")}>Back</Btn>
        </div>
        <div className="row btn-row">
          <Btn onClick={() => key("RED")}>Red</Btn>
          <Btn onClick={() => key("GREEN")}>Green</Btn>
          <Btn onClick={() => key("BLUE")}>Blue</Btn>
          <Btn onClick={() => key("YELLOW")}>Yellow</Btn>
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
  );
}
