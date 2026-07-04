import { Btn } from "../common";
import { MuteIcon, SourceMark, sourceLabel } from "../icons";
import { PRESETS, SOURCES, UPMIXERS, type PoolHouseState } from "./state";

export function TrinnovTab({ s }: { s: PoolHouseState }) {
  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Trinnov Altitude 16</h1>
        <span className="pill pill-on">online</span>
      </div>

      <section className="card">
        <div className="vol-big">{s.muted ? "Muted" : `${s.volume} dB`}</div>
        <input
          className="vol-slider"
          type="range"
          min={-60}
          max={0}
          step={0.5}
          value={s.volume}
          onChange={(e) => s.setVolume(Number(e.target.value))}
        />
        <div className="row btn-row">
          <Btn onClick={() => s.nudge(-2)}>−2</Btn>
          <Btn onClick={() => s.nudge(-0.5)}>−0.5</Btn>
          <Btn onClick={() => s.nudge(0.5)}>+0.5</Btn>
          <Btn onClick={() => s.nudge(2)}>+2</Btn>
          <button
            className={`btn icon-btn ${s.muted ? "btn-active" : ""}`}
            aria-label={s.muted ? "Unmute" : "Mute"}
            onClick={() => s.setMuted((m) => !m)}
          >
            <MuteIcon muted={s.muted} />
          </button>
          <Btn active={s.dim} onClick={() => s.setDim((d) => !d)}>Dim</Btn>
        </div>
      </section>

      <section className="card">
        <div className="card-label">Source</div>
        <div className="source-grid">
          {SOURCES.map((name) => (
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

      <section className="card">
        <div className="card-label">Preset</div>
        <div className="row btn-row wrap">
          {PRESETS.map((p) => (
            <Btn key={p} active={s.preset === p} onClick={() => s.setPreset(p)}>{p}</Btn>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="card-label">Upmixer</div>
        <div className="row btn-row wrap">
          {UPMIXERS.map((m) => (
            <Btn key={m} active={s.upmixer === m} onClick={() => s.setUpmixer(m)}>{m}</Btn>
          ))}
          <Btn active={s.bypass} onClick={() => s.setBypass((b) => !b)}>Bypass</Btn>
        </div>
      </section>
    </div>
  );
}
