import { sendCommand } from "../../api";
import type { DeviceState } from "../../types";
import { Btn } from "../common";

const UPMIXERS = ["auto", "native", "dolby", "dts", "auro3d", "legacy"];

export function TrinnovView({ device }: { device?: DeviceState }) {
  if (!device) return <div className="view-empty muted">Trinnov not configured.</div>;
  const e = device.extra ?? {};
  const volume = e.volume as number | undefined;
  const muted = e.mute as boolean | undefined;
  const dim = e.dim as boolean | undefined;
  const bypass = e.bypass as boolean | undefined;
  const upmixer = e.upmixer as string | undefined;
  const sources = (e.sources as Record<string, number>) ?? {};
  const current = device.input;
  const presets = (e.presets as Record<string, string>) ?? {};
  const currentPreset = e.current_preset as number | undefined;
  const format = e.source_format as string | undefined;
  const srate = e.sample_rate as number | undefined;

  const cmd = (command: string, params?: Record<string, unknown>) =>
    sendCommand("trinnov", command, params).catch((err) => console.error(err));

  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Trinnov Altitude</h1>
        <span className={`pill ${device.reachable === "online" ? "pill-on" : "pill-off"}`}>
          {device.reachable}
        </span>
      </div>

      <section className="card">
        <div className="vol-big">{volume !== undefined ? `${volume} dB` : "—"}</div>
        <input
          className="vol-slider"
          type="range"
          min={-60}
          max={0}
          step={0.5}
          value={volume ?? -40}
          onChange={(ev) => cmd("volume_set", { db: Number(ev.target.value) })}
        />
        <div className="row btn-row">
          <Btn onClick={() => cmd("volume_adjust", { delta: -2 })}>−2 dB</Btn>
          <Btn onClick={() => cmd("volume_adjust", { delta: -0.5 })}>−0.5</Btn>
          <Btn onClick={() => cmd("volume_adjust", { delta: 0.5 })}>+0.5</Btn>
          <Btn onClick={() => cmd("volume_adjust", { delta: 2 })}>+2 dB</Btn>
          <Btn active={muted} onClick={() => cmd("mute", { state: muted ? "off" : "on" })}>
            {muted ? "Unmute" : "Mute"}
          </Btn>
          <Btn active={dim} onClick={() => cmd("dim", { state: dim ? "off" : "on" })}>
            Dim
          </Btn>
        </div>
      </section>

      <section className="card">
        <div className="card-label">Source</div>
        <div className="row btn-row wrap">
          {Object.keys(sources).map((name) => (
            <Btn key={name} active={current === name} onClick={() => cmd("source", { name })}>
              {name}
            </Btn>
          ))}
        </div>
      </section>

      {Object.keys(presets).length > 0 && (
        <section className="card">
          <div className="card-label">Preset</div>
          <div className="row btn-row wrap">
            {Object.entries(presets).map(([idx, name]) => (
              <Btn
                key={idx}
                active={currentPreset === Number(idx)}
                onClick={() => cmd("preset", { index: Number(idx) })}
              >
                {name}
              </Btn>
            ))}
          </div>
        </section>
      )}

      <section className="card">
        <div className="card-label">Upmixer</div>
        <div className="row btn-row wrap">
          {UPMIXERS.map((mode) => (
            <Btn key={mode} active={upmixer === mode} onClick={() => cmd("upmixer", { mode })}>
              {mode}
            </Btn>
          ))}
          <Btn active={bypass} onClick={() => cmd("bypass", { state: bypass ? "off" : "on" })}>
            Bypass
          </Btn>
        </div>
      </section>

      <section className="card">
        <div className="card-label">Signal</div>
        <div className="info-grid">
          <div><span className="muted">Format</span><strong>{format ?? "—"}</strong></div>
          <div><span className="muted">Sample rate</span><strong>{srate ? `${srate / 1000} kHz` : "—"}</strong></div>
          <div><span className="muted">Upmixer</span><strong>{upmixer ?? "—"}</strong></div>
        </div>
      </section>
    </div>
  );
}
