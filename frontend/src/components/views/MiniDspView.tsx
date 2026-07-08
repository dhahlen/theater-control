import { useEffect, useRef, useState } from "react";
import { sendCommand } from "../../api";
import type { DeviceState } from "../../types";
import { Btn } from "../common";
import { MuteIcon } from "../icons";

// MiniDSP SHD driving the Crowson tactile transducers. The tab exposes the
// master level, the device's config presets (each a gain/crossover profile), and
// an on/off toggle per output row (front = out 1, rear = out 2). Per-output gain
// is set on the device presets, not from here. The SHD does not report per-output
// mute over the CLI, so the row On/Off is tracked optimistically; the master level
// and active preset are read back from the device.

function label(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// Master level slider: drags smoothly and commits on release, ignoring the poll
// while dragging so it never snaps back mid-drag.
function MasterLevel({
  volume,
  min,
  muted,
  cmd,
}: {
  volume?: number;
  min: number;
  muted: boolean;
  cmd: (command: string, params?: Record<string, unknown>) => void;
}) {
  const initial = volume ?? min / 2;
  const [val, setVal] = useState(initial);
  const dragging = useRef(false);
  const latest = useRef(initial);

  useEffect(() => {
    if (!dragging.current && volume !== undefined) {
      setVal(volume);
      latest.current = volume;
    }
  }, [volume]);

  const commit = () => {
    if (!dragging.current) return;
    dragging.current = false;
    cmd("volume_set", { db: latest.current });
  };

  return (
    <section className="card">
      <div className="card-label">Master level</div>
      <div className="vol-big">{volume !== undefined ? `${val} dB` : "—"}</div>
      <input
        className="vol-slider"
        type="range"
        min={min}
        max={0}
        step={0.5}
        value={val}
        onChange={(e) => {
          const v = Number(e.currentTarget.value);
          latest.current = v;
          setVal(v);
        }}
        onPointerDown={() => (dragging.current = true)}
        onPointerUp={commit}
        onPointerCancel={commit}
        onKeyUp={() => cmd("volume_set", { db: latest.current })}
      />
      <div className="row btn-row">
        <Btn onClick={() => cmd("volume_adjust", { delta: -2 })}>−2</Btn>
        <Btn onClick={() => cmd("volume_adjust", { delta: -0.5 })}>−0.5</Btn>
        <Btn onClick={() => cmd("volume_adjust", { delta: 0.5 })}>+0.5</Btn>
        <Btn onClick={() => cmd("volume_adjust", { delta: 2 })}>+2</Btn>
        <button
          className={`btn icon-btn ${muted ? "btn-active" : ""}`}
          aria-label={muted ? "Unmute" : "Mute"}
          onClick={() => cmd("mute", { state: muted ? "off" : "on" })}
        >
          <MuteIcon muted={muted} />
        </button>
      </div>
    </section>
  );
}

export function MiniDspView({ device }: { device?: DeviceState }) {
  if (!device) return <div className="view-empty muted">MiniDSP not configured.</div>;
  const online = device.reachable === "online";
  const e = device.extra ?? {};
  const volume = e.volume as number | undefined;
  const muted = e.mute as boolean | undefined;
  const preset = e.preset as number | undefined;
  const presetLabels = (e.presets as string[]) ?? [];
  const outputs = (e.outputs as Record<string, number>) ?? {};
  const mutes = (e.output_mute as Record<string, boolean>) ?? {};
  const masterMin = (e.master_min as number) ?? -80;

  const cmd = (command: string, params?: Record<string, unknown>) =>
    sendCommand("minidsp", command, params).catch((err) => console.error(err));

  const rows = Object.entries(outputs).sort((a, b) => a[1] - b[1]);
  // Fall back to four generically-labelled presets if none are configured.
  const presets =
    presetLabels.length > 0
      ? presetLabels
      : ["Preset 1", "Preset 2", "Preset 3", "Preset 4"];

  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Crowson</h1>
        <span className={`pill ${online ? "pill-on" : "pill-off"}`}>{device.reachable}</span>
      </div>

      <MasterLevel volume={volume} min={masterMin} muted={Boolean(muted)} cmd={cmd} />

      <section className="card">
        <div className="card-label">Preset</div>
        <div className="mode-grid">
          {presets.map((name, index) => (
            <button
              key={index}
              className={`btn mode-btn ${preset === index ? "btn-active" : ""}`}
              onClick={() => cmd("preset", { index })}
            >
              {name}
            </button>
          ))}
        </div>
      </section>

      {rows.length > 0 && (
        <section className="card">
          <div className="card-label">Rows</div>
          {rows.map(([name, index]) => {
            const off = Boolean(mutes[name]);
            return (
              <div className="row btn-row row-toggle" key={name}>
                <span className="row-name">{label(name)}</span>
                <button
                  className={`btn ${off ? "" : "btn-active"}`}
                  onClick={() => cmd("output_mute", { index, state: off ? "off" : "on" })}
                >
                  {off ? "Off" : "On"}
                </button>
              </div>
            );
          })}
        </section>
      )}
    </div>
  );
}
