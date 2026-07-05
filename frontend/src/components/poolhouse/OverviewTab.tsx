import { Btn } from "../common";
import { MuteIcon, SourceMark, sourceLabel } from "../icons";
import { PlexNowPlaying } from "../MediaPanel";
import type { PoolHouse } from "./live";

// Room overview: a single-pane dashboard mirroring the theater layout — Room
// On/Off and the source picker on top, then Media (Plex) as the tall column with
// the display, audio, and lighting cards beside it. No scrolling on this tab.
export function OverviewTab({ s }: { s: PoolHouse }) {
  const sourceNames = Object.keys(s.sources);
  const np = s.plex?.extra?.now_playing as Record<string, unknown> | undefined;
  const plexReach = s.plex?.reachable ?? "—";

  return (
    <>
      <section className="scenebar ph-scenebar">
        <div className="scene-primary">
          <button className="scene-btn scene-on" onClick={s.roomOn}>
            <span className="scene-title">Room On</span>
            <span className="scene-sub">
              {s.power ? "on" : `source: ${s.source ? sourceLabel(s.source) : "—"}`}
            </span>
          </button>
        </div>
        <div className="scene-source">
          <div className="source-list ph-source-list">
            {sourceNames.map((name) => (
              <button
                key={name}
                className={`source-chip ${name === s.source ? "chip-active" : ""}`}
                onClick={() => s.setSource(name)}
                title={sourceLabel(name)}
              >
                <SourceMark name={name} />
              </button>
            ))}
          </div>
        </div>
        <div className="scene-primary">
          <button className="scene-btn scene-off" onClick={s.roomOff}>
            <span className="scene-title">Room Off</span>
            <span className="scene-sub">standby</span>
          </button>
        </div>
      </section>

      <div className="grid">
        {/* Media (Plex) — tall column */}
        <section className="panel panel-wide">
          <header className="panel-head media-head">
            <h2>Plex</h2>
            <span className={`pill ${plexReach === "online" ? "pill-on" : "pill-off"}`}>{plexReach}</span>
          </header>
          <div className="panel-body">
            {np ? (
              <PlexNowPlaying np={np} deviceId="ph_plex" />
            ) : (
              <div className="np-idle">
                <div className="np-idle-title">Nothing playing</div>
                <div className="muted">Start something on the Pool House SHIELD and it will show here.</div>
              </div>
            )}
          </div>
        </section>

        {/* Display + audio */}
        <div className="grid-col">
          <section className="card">
            <div className="card-head">
              <h2>LG G5 84&quot;</h2>
              <span className={`pill ${s.power ? "pill-on" : "pill-off"}`}>
                {s.lgOnline ? (s.power ? "on" : "standby") : "offline"}
              </span>
            </div>
            <div className="info-grid">
              <div><span className="muted">Input</span><strong>HDMI 1</strong></div>
              <div><span className="muted">Source</span><strong>{s.source ? sourceLabel(s.source) : "—"}</strong></div>
            </div>
            <div className="row btn-row">
              <Btn active={s.power} onClick={() => s.lgPower(true)}>On</Btn>
              <Btn active={s.lgOnline && !s.power} onClick={() => s.lgPower(false)}>Off</Btn>
            </div>
          </section>

          <section className="card">
            <div className="card-head">
              <h2>Trinnov Altitude 16</h2>
              <span className={`pill ${s.trinnovOnline ? "pill-on" : "pill-off"}`}>
                {s.trinnovOnline ? "online" : "offline"}
              </span>
            </div>
            <div className="row">
              <div className="stat">
                <span className="stat-label">Volume</span>
                <span className="stat-value">
                  {s.muted ? "Muted" : s.volume !== undefined ? `${s.volume} dB` : "—"}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Source</span>
                <span className="stat-value">{s.source ? sourceLabel(s.source) : "—"}</span>
              </div>
            </div>
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
            </div>
          </section>
        </div>

        {/* Lighting */}
        <div className="grid-col">
          <section className="card">
            <div className="card-head">
              <h2>Lighting</h2>
              <span className="pill pill-on">online</span>
            </div>
            <div className="light-rows">
              {s.zones.map((z) => (
                <div className="light-row" key={z.key}>
                  <span className="light-name">{z.label}</span>
                  <input
                    className="vol-slider light-slider"
                    type="range"
                    min={0}
                    max={254}
                    value={z.bri}
                    disabled={!z.online}
                    onChange={(e) => s.zoneLevel(z.id, Number(e.target.value))}
                  />
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
