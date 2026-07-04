export function MediaTab() {
  return (
    <div className="devview">
      <div className="devview-head">
        <h1>Plex</h1>
        <span className="pill pill-on">online</span>
      </div>
      <section className="card">
        <div className="info-grid">
          <div><span className="muted">Server</span><strong>Shared PMS</strong></div>
          <div><span className="muted">Player</span><strong>Pool House SHIELD</strong></div>
          <div><span className="muted">Now playing</span><strong>—</strong></div>
        </div>
      </section>
      <section className="card ph-embed">
        <div className="embed-frame">
          <div className="embed-title">Plex Web</div>
          <div className="muted">Embedded browse and play on the Pool House SHIELD.</div>
        </div>
      </section>
    </div>
  );
}
