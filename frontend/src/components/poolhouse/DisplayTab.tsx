import { useRef, useState } from "react";
import { Btn } from "../common";
import { sourceLabel } from "../icons";
import { PICTURE_MODES, type PoolHouse } from "./live";

// The LG is fed a single HDMI (HDMI 1) from the Altitude 16, so source switching
// happens on the Trinnov, not here. webOS does not report the current picture
// mode or picture settings, so the active preset and brightness are tracked
// optimistically from the last selection.
export function DisplayTab({ s }: { s: PoolHouse }) {
  const [picture, setPicture] = useState<string | null>(null);
  const [backlight, setBacklight] = useState(80);
  const dragging = useRef(false);

  const choose = (mode: string) => {
    setPicture(mode);
    s.setPicture(mode);
  };

  return (
    <div className="devview">
      <div className="devview-head">
        <h1>LG G5 84&quot;</h1>
        <span className={`pill ${s.power ? "pill-on" : "pill-off"}`}>
          {s.lgOnline ? (s.power ? "on" : "standby") : "offline"}
        </span>
      </div>

      <section className="card">
        <div className="info-grid">
          <div><span className="muted">Input</span><strong>HDMI 1</strong></div>
          <div><span className="muted">Source</span><strong>{s.source ? sourceLabel(s.source) : "—"}</strong></div>
          <div><span className="muted">Picture</span><strong>{picture ?? "—"}</strong></div>
        </div>
        <div className="subhead">Power</div>
        <div className="row btn-row">
          <Btn active={s.power} onClick={() => s.lgPower(true)}>On</Btn>
          <Btn active={s.lgOnline && !s.power} onClick={() => s.lgPower(false)}>Off</Btn>
        </div>
      </section>

      <section className="card">
        <div className="subhead">Picture mode</div>
        <div className="mode-grid">
          {PICTURE_MODES.map((m) => (
            <button
              key={m}
              className={`btn mode-btn ${picture === m ? "btn-active" : ""}`}
              onClick={() => choose(m)}
            >
              {m}
            </button>
          ))}
        </div>

        <div className="subhead">Brightness</div>
        <div className="row light-with-pct">
          <input
            className="vol-slider light-slider"
            type="range"
            min={0}
            max={100}
            value={backlight}
            disabled={!s.lgOnline}
            onChange={(e) => setBacklight(Number(e.currentTarget.value))}
            onPointerDown={() => (dragging.current = true)}
            onPointerUp={() => {
              dragging.current = false;
              s.setBacklight(backlight);
            }}
            onPointerCancel={() => {
              dragging.current = false;
              s.setBacklight(backlight);
            }}
            onKeyUp={() => s.setBacklight(backlight)}
          />
          <span className="light-pct">{backlight}%</span>
        </div>
        <div className="muted ph-note">
          Sets OLED Pixel Brightness. Source switching is on the Trinnov tab; the LG stays
          on HDMI 1 from the Altitude 16.
        </div>
      </section>
    </div>
  );
}
