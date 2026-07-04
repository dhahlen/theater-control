import { Btn } from "../common";
import { ZONES, type PoolHouseState } from "./state";

export function LightingTab({ s }: { s: PoolHouseState }) {
  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Lighting</h1>
        <span className="pill pill-on">online</span>
      </div>
      <div className="muted ph-note">
        Office Hue bridge (172.16.17.184). The Pool House room holds the Bar and Lounge zones;
        the Office is included for the adjacent lights.
      </div>

      {ZONES.map((z) => {
        const on = s.zoneOn[z.key] ?? false;
        return (
          <section className="card" key={z.key}>
            <div className="card-head">
              <h2>{z.label}</h2>
              <button
                className={`btn zone-toggle ${on ? "btn-active" : ""}`}
                onClick={() => s.setZoneOn((zo) => ({ ...zo, [z.key]: !on }))}
              >
                {on ? "On" : "Off"}
              </button>
            </div>
            <div className="card-label">Brightness</div>
            <input
              className="vol-slider"
              type="range"
              min={0}
              max={254}
              value={s.bri[z.key] ?? 128}
              disabled={!on}
              onChange={(e) => s.setBri((b) => ({ ...b, [z.key]: Number(e.target.value) }))}
            />
            {z.scenes.length > 0 ? (
              <>
                <div className="subhead">Scene</div>
                <div className="row btn-row wrap">
                  {z.scenes.map((sc) => (
                    <Btn
                      key={sc}
                      active={s.scene[z.key] === sc}
                      onClick={() => s.setScene((m) => ({ ...m, [z.key]: sc }))}
                    >
                      {sc}
                    </Btn>
                  ))}
                </div>
              </>
            ) : (
              <div className="muted ph-note">No saved scenes yet for this zone.</div>
            )}
          </section>
        );
      })}
    </div>
  );
}
