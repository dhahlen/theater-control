import { Btn } from "../common";
import { MuteIcon, SourceMark, sourceLabel } from "../icons";
import { SOURCES, ZONES, type PoolHouseState } from "./state";

// Room overview: Room On / Room Off scenes, source picker, and a control card per
// device that mirrors the theater dashboard (volume buttons, lighting sliders).
// The device tabs carry the fuller option menus.
export function OverviewTab({ s }: { s: PoolHouseState }) {
  return (
    <>
      <section className="scenebar ph-scenebar">
        <div className="scene-primary">
          <button className="scene-btn scene-on" onClick={() => s.setPower(true)} disabled={s.power}>
            <span className="scene-title">Room On</span>
            <span className="scene-sub">{s.power ? "on" : `source: ${sourceLabel(s.source)}`}</span>
          </button>
        </div>
        <div className="scene-source">
          <div className="source-list ph-source-list">
            {SOURCES.map((src) => (
              <button
                key={src}
                className={`source-chip ${src === s.source ? "chip-active" : ""}`}
                onClick={() => s.setSource(src)}
                title={sourceLabel(src)}
              >
                <SourceMark name={src} />
              </button>
            ))}
          </div>
        </div>
        <div className="scene-primary">
          <button className="scene-btn scene-off" onClick={() => s.setPower(false)} disabled={!s.power}>
            <span className="scene-title">Room Off</span>
            <span className="scene-sub">standby</span>
          </button>
        </div>
      </section>

      <div className="ph-grid">
        {/* LG G5 display */}
        <section className="card">
          <div className="card-head">
            <h2>LG G5 84&quot;</h2>
            <span className={`pill ${s.power ? "pill-on" : "pill-off"}`}>{s.power ? "on" : "standby"}</span>
          </div>
          <div className="info-grid">
            <div><span className="muted">Input</span><strong>{s.lgInput}</strong></div>
            <div><span className="muted">Source</span><strong>{sourceLabel(s.source)}</strong></div>
            <div><span className="muted">Picture</span><strong>{s.picture}</strong></div>
          </div>
          <div className="subhead">Power</div>
          <div className="row btn-row">
            <Btn active={s.power} onClick={() => s.setPower(true)}>On</Btn>
            <Btn active={!s.power} onClick={() => s.setPower(false)}>Off</Btn>
          </div>
        </section>

        {/* Trinnov Altitude 16 — volume controls, matching the theater card */}
        <section className="card">
          <div className="card-head">
            <h2>Trinnov Altitude 16</h2>
            <span className="pill pill-on">online</span>
          </div>
          <div className="row">
            <div className="stat">
              <span className="stat-label">Volume</span>
              <span className="stat-value">{s.muted ? "Muted" : `${s.volume} dB`}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Source</span>
              <span className="stat-value">{sourceLabel(s.source)}</span>
            </div>
          </div>
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
          </div>
        </section>

        {/* Lighting — a brightness slider per zone */}
        <section className="card">
          <div className="card-head">
            <h2>Lighting</h2>
            <span className="pill pill-on">online</span>
          </div>
          <div className="light-rows">
            {ZONES.map((z) => (
              <div className="light-row" key={z.key}>
                <span className="light-name">{z.label}</span>
                <input
                  className="vol-slider light-slider"
                  type="range"
                  min={0}
                  max={254}
                  value={s.bri[z.key] ?? 128}
                  onChange={(e) => s.setBri((b) => ({ ...b, [z.key]: Number(e.target.value) }))}
                />
              </div>
            ))}
          </div>
        </section>

        {/* Plex (shared with the theater) */}
        <section className="card">
          <div className="card-head">
            <h2>Plex</h2>
            <span className="pill pill-on">online</span>
          </div>
          <div className="info-grid">
            <div><span className="muted">Player</span><strong>Pool House SHIELD</strong></div>
            <div><span className="muted">Now playing</span><strong>—</strong></div>
          </div>
        </section>
      </div>
    </>
  );
}
