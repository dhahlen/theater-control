import { sendCommand } from "../../api";
import type { DeviceState } from "../../types";
import { Btn } from "../common";

const PICTURE_MODES = [
  "frame_adapt_hdr", "frame_adapt_hdr2", "frame_adapt_hdr3", "hdr_plus", "hdr",
  "hlg", "pana_pq", "filmmaker", "film", "cinema", "natural", "thx",
  "user1", "user2", "user3", "user4", "user5", "user6",
];

export function JvcView({ device }: { device?: DeviceState }) {
  if (!device) return <div className="view-empty muted">JVC not configured.</div>;
  const e = device.extra ?? {};
  const lowLatency = e.low_latency as string | undefined;
  const signal = e.source_status as string | undefined;
  const power = device.power;

  const cmd = (command: string, params?: Record<string, unknown>) =>
    sendCommand("jvc", command, params).catch((err) => console.error(err));

  return (
    <div className="devview">
      <div className="devview-head">
        <h1>JVC DLA-NZ900</h1>
        <span className={`pill ${device.reachable === "online" ? "pill-on" : "pill-off"}`}>
          {device.reachable}
        </span>
      </div>

      <section className="card">
        <div className="info-grid">
          <div><span className="muted">Power</span><strong>{power ?? "—"}</strong></div>
          <div><span className="muted">Input</span><strong>{device.input ?? "—"}</strong></div>
          <div><span className="muted">Low latency</span><strong>{lowLatency ?? "—"}</strong></div>
          <div><span className="muted">Signal</span><strong>{signal ?? "—"}</strong></div>
        </div>
      </section>

      <section className="card">
        <div className="card-label">Power</div>
        <div className="row btn-row">
          <Btn active={power === "on"} onClick={() => cmd("power", { state: "on" })}>On</Btn>
          <Btn active={power === "standby"} onClick={() => cmd("power", { state: "off" })}>Off</Btn>
        </div>
      </section>

      <section className="card">
        <div className="card-label">Input</div>
        <div className="row btn-row">
          <Btn active={device.input === "hdmi1"} onClick={() => cmd("input_mode", { input: "hdmi1" })}>HDMI 1</Btn>
          <Btn active={device.input === "hdmi2"} onClick={() => cmd("input_mode", { input: "hdmi2" })}>HDMI 2</Btn>
        </div>
      </section>

      <section className="card">
        <div className="card-label">Low latency</div>
        <div className="row btn-row">
          <Btn active={lowLatency === "on"} onClick={() => cmd("low_latency", { state: "on" })}>On</Btn>
          <Btn active={lowLatency === "off"} onClick={() => cmd("low_latency", { state: "off" })}>Off</Btn>
        </div>
      </section>

      <section className="card">
        <div className="card-label">Picture mode</div>
        <div className="mode-grid">
          {PICTURE_MODES.map((mode) => (
            <button key={mode} className="btn mode-btn" onClick={() => cmd("picture_mode", { mode })}>
              {mode.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
