import { MuteIcon, SourceMark, sourceLabel } from "../icons";
import { SOURCES, ZONES, type PoolHouseState } from "./state";

// Room overview: the Room On / Room Off scenes, source picker, and a compact
// summary card per device. The individual device tabs carry the full options.
export function OverviewTab({ s, onOpen }: { s: PoolHouseState; onOpen: (tab: string) => void }) {
  const litZones = ZONES.filter((z) => s.zoneOn[z.key]).map((z) => z.label);

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
        <button className="card card-link" onClick={() => onOpen("display")}>
          <div className="card-head">
            <h2>LG G5 84&quot;</h2>
            <span className={`pill ${s.power ? "pill-on" : "pill-off"}`}>{s.power ? "on" : "standby"}</span>
          </div>
          <div className="info-grid">
            <div><span className="muted">Input</span><strong>{s.lgInput}</strong></div>
            <div><span className="muted">Source</span><strong>{sourceLabel(s.source)}</strong></div>
            <div><span className="muted">Picture</span><strong>{s.picture}</strong></div>
          </div>
        </button>

        <button className="card card-link" onClick={() => onOpen("trinnov")}>
          <div className="card-head">
            <h2>Trinnov Altitude 16</h2>
            <span className="pill pill-on">online</span>
          </div>
          <div className="vol-big">{s.muted ? "Muted" : `${s.volume} dB`}</div>
          <div className="row btn-row center">
            <span className="muted">{sourceLabel(s.source)} · {s.upmixer}</span>
            {s.muted && <MuteIcon muted size={18} />}
          </div>
        </button>

        <button className="card card-link" onClick={() => onOpen("lighting")}>
          <div className="card-head">
            <h2>Lighting</h2>
            <span className="pill pill-on">online</span>
          </div>
          <div className="info-grid">
            <div><span className="muted">On</span><strong>{litZones.length ? litZones.join(", ") : "all off"}</strong></div>
          </div>
        </button>

        <button className="card card-link" onClick={() => onOpen("media")}>
          <div className="card-head">
            <h2>Plex</h2>
            <span className="pill pill-on">online</span>
          </div>
          <div className="info-grid">
            <div><span className="muted">Player</span><strong>Pool House SHIELD</strong></div>
            <div><span className="muted">Now playing</span><strong>—</strong></div>
          </div>
        </button>
      </div>
    </>
  );
}
