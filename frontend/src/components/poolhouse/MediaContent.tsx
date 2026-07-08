import { Btn } from "../common";
import { ErrorBoundary } from "../ErrorBoundary";
import { PlexNowPlaying } from "../MediaPanel";
import type { PoolHouse } from "./live";

// Shows the richest available now-playing for the room: the Plex card when a
// Plex session is active, otherwise the Shield's current app (Netflix, Prime,
// Apple TV, etc.) via ADB, otherwise an idle state.
export function MediaContent({ s }: { s: PoolHouse }) {
  const np = s.plex?.extra?.now_playing as Record<string, unknown> | undefined;
  if (np)
    return (
      <ErrorBoundary label="Media card unavailable">
        <PlexNowPlaying np={np} deviceId="ph_plex" />
      </ErrorBoundary>
    );
  if (s.shieldActive) return <ShieldNowPlaying s={s} />;
  return (
    <div className="np-idle">
      <div className="np-idle-title">Nothing playing</div>
      <div className="muted">Start something on the Pool House SHIELD and it will show here.</div>
    </div>
  );
}

function ShieldNowPlaying({ s }: { s: PoolHouse }) {
  const paused = s.shieldState === "paused";
  const key = s.shieldKey;
  return (
    <div className="shield-np">
      <div className="shield-head">
        <div>
          <div className="shield-app">{s.shieldApp}</div>
          {s.shieldTitle && <div className="tt-title">{s.shieldTitle}</div>}
          {s.shieldSubtitle && <div className="tt-sub">{s.shieldSubtitle}</div>}
        </div>
        <span className={`pill ${paused ? "pill-off" : "pill-on"}`}>{s.shieldState}</span>
      </div>
      <div className="row btn-row">
        <Btn onClick={() => key("previous")}>⏮</Btn>
        <Btn onClick={() => key("play_pause")}>{paused ? "▶︎ Play" : "⏸ Pause"}</Btn>
        <Btn onClick={() => key("stop")}>⏹ Stop</Btn>
        <Btn onClick={() => key("next")}>⏭</Btn>
      </div>
      <div className="muted ph-note">Transport sent to the Shield over ADB.</div>
    </div>
  );
}
