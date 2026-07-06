import { useEffect, useRef, useState } from "react";
import { sendCommand } from "../../api";
import type { DeviceState } from "../../types";
import { Btn } from "../common";
import { MuteIcon } from "../icons";

// MiniDSP SHD driving the Crowson tactile transducers. Master level is the
// overall transducer gain; each output row (front, rear) has its own gain and an
// on/off (mute) toggle so a row can be turned down or off independently. The
// daemon does not report per-output gain, so the row sliders track optimistically
// and commit on release.

function label(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function RowControl({
  name,
  index,
  gain,
  muted,
  min,
  max,
  cmd,
}: {
  name: string;
  index: number;
  gain: number | null;
  muted: boolean;
  min: number;
  max: number;
  cmd: (command: string, params?: Record<string, unknown>) => void;
}) {
  const initial = gain ?? max;
  const [val, setVal] = useState(initial);
  const dragging = useRef(false);
  const latest = useRef(initial);

  useEffect(() => {
    if (!dragging.current && gain !== null) {
      setVal(gain);
      latest.current = gain;
    }
  }, [gain]);

  const commit = () => {
    if (!dragging.current) return;
    dragging.current = false;
    cmd("output_gain", { index, db: latest.current });
  };

  return (
    <section className="card">
      <div className="card-head">
        <h2>{label(name)}</h2>
        <button
          className={`btn ${muted ? "" : "btn-active"}`}
          onClick={() => cmd("output_mute", { index, state: muted ? "off" : "on" })}
        >
          {muted ? "Off" : "On"}
        </button>
      </div>
      <div className="row light-with-pct">
        <input
          className={`vol-slider ${muted ? "slider-off" : ""}`}
          type="range"
          min={min}
          max={max}
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
          onKeyUp={() => cmd("output_gain", { index, db: latest.current })}
        />
        <span className="light-pct">{val.toFixed(1)} dB</span>
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
  const outputs = (e.outputs as Record<string, number>) ?? {};
  const gains = (e.output_gain as Record<string, number | null>) ?? {};
  const mutes = (e.output_mute as Record<string, boolean>) ?? {};
  const masterMin = (e.master_min as number) ?? -80;
  const outMin = (e.output_min as number) ?? -40;
  const outMax = (e.output_max as number) ?? 0;

  const cmd = (command: string, params?: Record<string, unknown>) =>
    sendCommand("minidsp", command, params).catch((err) => console.error(err));

  const rows = Object.entries(outputs).sort((a, b) => a[1] - b[1]);

  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Crowson</h1>
        <span className={`pill ${online ? "pill-on" : "pill-off"}`}>{device.reachable}</span>
      </div>

      <section className="card">
        <div className="card-label">Master level</div>
        <div className="vol-big">{volume !== undefined ? `${volume} dB` : "—"}</div>
        <input
          className="vol-slider"
          type="range"
          min={masterMin}
          max={0}
          step={0.5}
          value={volume ?? masterMin / 2}
          onChange={(ev) => cmd("volume_set", { db: Number(ev.target.value) })}
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

      {rows.length === 0 ? (
        <div className="muted ph-note">No output rows configured (set minidsp.outputs).</div>
      ) : (
        rows.map(([name, index]) => (
          <RowControl
            key={name}
            name={name}
            index={index}
            gain={gains[name] ?? null}
            muted={Boolean(mutes[name])}
            min={outMin}
            max={outMax}
            cmd={cmd}
          />
        ))
      )}
    </div>
  );
}
