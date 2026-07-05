import { MediaContent } from "./MediaContent";
import type { PoolHouse } from "./live";

export function MediaTab({ s }: { s: PoolHouse }) {
  const online = s.plex?.reachable === "online" || s.shieldActive;
  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Media</h1>
        <span className={`pill ${online ? "pill-on" : "pill-off"}`}>{online ? "online" : "—"}</span>
      </div>
      <section className="card">
        <MediaContent s={s} />
      </section>
    </div>
  );
}
