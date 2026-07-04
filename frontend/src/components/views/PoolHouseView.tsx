import { useState } from "react";
import { Btn } from "../common";
import { MuteIcon, SourceMark, sourceLabel } from "../icons";

// Phase 2 preview. The Pool House room is specified in docs/usecases/pool-house.md
// but its backend adapters (LG G5 display, the second Trinnov Altitude 16, and
// the Office Hue bridge) are not built yet. This view is a self-contained mockup
// driven by local state so the layout, sources, and scenes can be reviewed on the
// iPad before the hardware integration lands. Nothing here talks to a device.

const SOURCES = ["shield", "gaming_pc", "switch2", "switch1", "node"];
const SCENES = ["Movie", "Party", "Chill", "Off"];

export function PoolHouseView() {
  const [power, setPower] = useState(false);
  const [source, setSource] = useState("shield");
  const [volume, setVolume] = useState(-22);
  const [muted, setMuted] = useState(false);
  const [bri, setBri] = useState(140);
  const [scene, setScene] = useState("Chill");

  const nudge = (d: number) => setVolume((v) => Math.max(-60, Math.min(0, Math.round((v + d) * 2) / 2)));

  return (
    <div className="devview poolhouse">
      <div className="preview-banner">
        Phase 2 preview — layout mockup, not yet connected to hardware.
      </div>

      <section className="scenebar ph-scenebar">
        <div className="scene-primary">
          <button
            className="scene-btn scene-on"
            onClick={() => setPower(true)}
            disabled={power}
          >
            <span className="scene-title">Room On</span>
            <span className="scene-sub">{power ? "on" : `source: ${sourceLabel(source)}`}</span>
          </button>
        </div>

        <div className="scene-source">
          <div className="source-list ph-source-list">
            {SOURCES.map((s) => (
              <button
                key={s}
                className={`source-chip ${s === source ? "chip-active" : ""}`}
                onClick={() => setSource(s)}
                title={sourceLabel(s)}
              >
                <SourceMark name={s} />
              </button>
            ))}
          </div>
        </div>

        <div className="scene-primary">
          <button
            className="scene-btn scene-off"
            onClick={() => setPower(false)}
            disabled={!power}
          >
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
            <span className={`pill ${power ? "pill-on" : "pill-off"}`}>{power ? "on" : "standby"}</span>
          </div>
          <div className="info-grid">
            <div><span className="muted">Input</span><strong>HDMI 1</strong></div>
            <div><span className="muted">Source</span><strong>{sourceLabel(source)}</strong></div>
            <div><span className="muted">Picture</span><strong>Filmmaker</strong></div>
          </div>
          <div className="subhead">Power</div>
          <div className="row btn-row">
            <Btn active={power} onClick={() => setPower(true)}>On</Btn>
            <Btn active={!power} onClick={() => setPower(false)}>Off</Btn>
          </div>
        </section>

        {/* Trinnov Altitude 16 */}
        <section className="card">
          <div className="card-head">
            <h2>Trinnov Altitude 16</h2>
            <span className="pill pill-on">online</span>
          </div>
          <div className="vol-big">{muted ? "Muted" : `${volume} dB`}</div>
          <input
            className="vol-slider"
            type="range"
            min={-60}
            max={0}
            step={0.5}
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
          />
          <div className="row btn-row">
            <Btn onClick={() => nudge(-2)}>−2</Btn>
            <Btn onClick={() => nudge(-0.5)}>−0.5</Btn>
            <Btn onClick={() => nudge(0.5)}>+0.5</Btn>
            <Btn onClick={() => nudge(2)}>+2</Btn>
            <button
              className={`btn icon-btn ${muted ? "btn-active" : ""}`}
              aria-label={muted ? "Unmute" : "Mute"}
              onClick={() => setMuted((m) => !m)}
            >
              <MuteIcon muted={muted} />
            </button>
          </div>
        </section>

        {/* Office Hue lighting */}
        <section className="card">
          <div className="card-head">
            <h2>Pool House Lighting</h2>
            <span className="pill pill-on">online</span>
          </div>
          <div className="card-label">Brightness</div>
          <input
            className="vol-slider"
            type="range"
            min={0}
            max={254}
            value={bri}
            onChange={(e) => setBri(Number(e.target.value))}
          />
          <div className="subhead">Scene</div>
          <div className="row btn-row wrap">
            {SCENES.map((s) => (
              <Btn key={s} active={scene === s} onClick={() => setScene(s)}>
                {s}
              </Btn>
            ))}
          </div>
        </section>

        {/* Plex (shared with the theater) */}
        <section className="card">
          <div className="card-head">
            <h2>Plex</h2>
            <span className="pill pill-on">online</span>
          </div>
          <div className="ph-plex muted">
            Shared Plex Media Server. Browse and play on the Pool House Shield.
          </div>
          <div className="info-grid">
            <div><span className="muted">Player</span><strong>Pool House Shield</strong></div>
            <div><span className="muted">Now playing</span><strong>—</strong></div>
          </div>
        </section>
      </div>
    </div>
  );
}
