import { Btn } from "../common";
import { MuteIcon, SourceMark, sourceLabel } from "../icons";
import { UPMIXERS, type PoolHouse } from "./live";

export function TrinnovTab({ s }: { s: PoolHouse }) {
  const sourceNames = Object.keys(s.sources);
  const presets = Object.entries(s.presets);

  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Trinnov Altitude 16</h1>
        <span className={`pill ${s.trinnovOnline ? "pill-on" : "pill-off"}`}>
          {s.trinnovOnline ? "online" : "offline"}
        </span>
      </div>

      <section className="card">
        <div className="vol-big">
          {s.muted ? "Muted" : s.volume !== undefined ? `${s.volume} dB` : "—"}
        </div>
        <input
          className="vol-slider"
          type="range"
          min={-60}
          max={0}
          step={0.5}
          value={s.volume ?? -40}
          onChange={(e) => s.volumeSet(Number(e.target.value))}
        />
        <div className="row btn-row">
          <Btn onClick={() => s.volumeAdjust(-2)}>−2</Btn>
          <Btn onClick={() => s.volumeAdjust(-0.5)}>−0.5</Btn>
          <Btn onClick={() => s.volumeAdjust(0.5)}>+0.5</Btn>
          <Btn onClick={() => s.volumeAdjust(2)}>+2</Btn>
          <button
            className={`btn icon-btn ${s.muted ? "btn-active" : ""}`}
            aria-label={s.muted ? "Unmute" : "Mute"}
            onClick={() => s.setMute(!s.muted)}
          >
            <MuteIcon muted={s.muted} />
          </button>
          <Btn active={s.dim} onClick={() => s.setDim(!s.dim)}>Dim</Btn>
        </div>
      </section>

      <section className="card">
        <div className="card-label">Source</div>
        <div className="source-grid">
          {sourceNames.map((name) => (
            <button
              key={name}
              className={`source-card ${s.source === name ? "source-card-active" : ""}`}
              onClick={() => s.setSource(name)}
              title={sourceLabel(name)}
            >
              <SourceMark name={name} />
            </button>
          ))}
        </div>
      </section>

      {presets.length > 0 && (
        <section className="card">
          <div className="card-label">Preset</div>
          <div className="row btn-row wrap">
            {presets.map(([idx, name]) => (
              <Btn
                key={idx}
                active={s.currentPreset === Number(idx)}
                onClick={() => s.setPreset(Number(idx))}
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
          {UPMIXERS.map((m) => (
            <Btn key={m} active={s.upmixer === m} onClick={() => s.setUpmixer(m)}>{m}</Btn>
          ))}
          <Btn active={s.bypass} onClick={() => s.setBypass(!s.bypass)}>Bypass</Btn>
        </div>
      </section>

      <section className="card">
        <div className="card-label">Signal</div>
        <div className="info-grid">
          <div><span className="muted">Format</span><strong>{s.sourceFormat ?? "—"}</strong></div>
          <div><span className="muted">Sample rate</span><strong>{s.sampleRate ? `${s.sampleRate / 1000} kHz` : "—"}</strong></div>
          <div><span className="muted">Upmixer</span><strong>{s.upmixer ?? "—"}</strong></div>
        </div>
      </section>
    </div>
  );
}
