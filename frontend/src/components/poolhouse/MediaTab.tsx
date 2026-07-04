import type { PoolHouse } from "./live";

interface NowPlaying {
  title?: string;
  grandparent_title?: string;
  episode?: string;
  state?: string;
  player?: string;
  year?: number;
}

export function MediaTab({ s }: { s: PoolHouse }) {
  const np = s.plex?.extra?.now_playing as NowPlaying | undefined;
  const online = s.plex?.reachable === "online";
  const title = np
    ? [np.grandparent_title, np.title].filter(Boolean).join(" — ")
    : null;

  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Plex</h1>
        <span className={`pill ${online ? "pill-on" : "pill-off"}`}>{s.plex?.reachable ?? "—"}</span>
      </div>
      <section className="card">
        <div className="info-grid">
          <div><span className="muted">Server</span><strong>Shared PMS</strong></div>
          <div><span className="muted">Player</span><strong>Pool House SHIELD</strong></div>
          <div><span className="muted">State</span><strong>{np?.state ?? "idle"}</strong></div>
        </div>
      </section>
      <section className="card ph-embed">
        <div className="embed-frame">
          {title ? (
            <>
              <div className="embed-title">{title}</div>
              <div className="muted">{np?.episode ?? (np?.year ? String(np.year) : "")}</div>
            </>
          ) : (
            <>
              <div className="embed-title">Nothing playing</div>
              <div className="muted">Browse and play on the Pool House SHIELD.</div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
