import { Btn } from "../common";
import { LightSlider } from "./LightSlider";
import type { PoolHouse } from "./live";

export function LightingTab({ s }: { s: PoolHouse }) {
  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Lighting</h1>
      </div>
      <div className="muted ph-note">
        Office Hue bridge. The Pool House room holds the Bar and Lounge zones; the
        Office is included for the adjacent lights.
      </div>

      {s.zones.map((z) => (
        <section className="card" key={z.key}>
          <div className="card-head">
            <h2>{z.label}</h2>
            <button
              className={`btn zone-toggle ${z.on ? "btn-active" : ""}`}
              disabled={!z.online}
              onClick={() => s.zoneToggle(z.id, !z.on)}
            >
              {z.online ? (z.on ? "On" : "Off") : "offline"}
            </button>
          </div>
          <div className="card-label">Brightness</div>
          <LightSlider
            online={z.online}
            on={z.on}
            bri={z.bri}
            onCommit={(v) => s.zoneLevel(z.id, v)}
          />
          {z.scenes.length > 0 ? (
            <>
              <div className="subhead">Scene</div>
              <div className="row btn-row wrap">
                {z.scenes.map((sc) => (
                  <Btn key={sc} onClick={() => s.zoneScene(z.id, sc)}>{sc}</Btn>
                ))}
              </div>
            </>
          ) : (
            <div className="muted ph-note">No saved scenes yet for this zone.</div>
          )}
        </section>
      ))}
    </div>
  );
}
