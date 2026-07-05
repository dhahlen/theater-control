import { PlexNowPlaying } from "../MediaPanel";
import type { PoolHouse } from "./live";

export function MediaTab({ s }: { s: PoolHouse }) {
  const np = s.plex?.extra?.now_playing as Record<string, unknown> | undefined;
  const online = s.plex?.reachable === "online";

  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Plex</h1>
        <span className={`pill ${online ? "pill-on" : "pill-off"}`}>{s.plex?.reachable ?? "—"}</span>
      </div>
      <section className="card">
        {np ? (
          <PlexNowPlaying np={np} deviceId="ph_plex" />
        ) : (
          <div className="np-idle">
            <div className="np-idle-title">Nothing playing</div>
            <div className="muted">Start something on the Pool House SHIELD and it will show here.</div>
          </div>
        )}
      </section>
    </div>
  );
}
