import { Btn } from "../common";
import { sourceLabel } from "../icons";
import type { PoolHouse } from "./live";

// The LG is fed a single HDMI (HDMI 1) from the Altitude 16, so source switching
// happens on the Trinnov, not here. Picture mode is not exposed over the webOS
// network API on this firmware, so it is set on the TV itself.
export function DisplayTab({ s }: { s: PoolHouse }) {
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
        </div>
        <div className="subhead">Power</div>
        <div className="row btn-row">
          <Btn active={s.power} onClick={() => s.lgPower(true)}>On</Btn>
          <Btn active={s.lgOnline && !s.power} onClick={() => s.lgPower(false)}>Off</Btn>
        </div>
        <div className="muted ph-note">
          Source switching is on the Trinnov tab (the LG stays on HDMI 1 from the Altitude 16).
          Picture mode is set on the TV; this webOS firmware does not expose it over the network.
        </div>
      </section>
    </div>
  );
}
