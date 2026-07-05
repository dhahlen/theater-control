import { useState } from "react";
import type { ReactNode } from "react";
import { sendCommand } from "../api";
import type { DeviceState } from "../types";
import { Btn, Panel } from "./common";

// Kaleidescape transport remote. Buttons map to the adapter capability names.
function KaleidescapeRemote({ device }: { device: DeviceState }) {
  const cmd = (command: string) =>
    sendCommand("kaleidescape", command).catch((e) => console.error(e));
  const title = device.extra?.title as string | undefined;
  const play = device.extra?.play_status as string | undefined;

  return (
    <div className="kal-remote">
      <div className="kal-now">
        <span className="muted">Now playing</span>
        <strong>{title ?? "—"}</strong>
        <span className="muted">{play ?? ""}</span>
      </div>
      <div className="dpad">
        <div />
        <Btn onClick={() => cmd("up")}>▲</Btn>
        <div />
        <Btn onClick={() => cmd("left")}>◀</Btn>
        <Btn onClick={() => cmd("select")}>OK</Btn>
        <Btn onClick={() => cmd("right")}>▶</Btn>
        <div />
        <Btn onClick={() => cmd("down")}>▼</Btn>
        <div />
      </div>
      <div className="row btn-row">
        <Btn onClick={() => cmd("menu")}>Menu</Btn>
        <Btn onClick={() => cmd("cancel")}>Back</Btn>
      </div>
      <div className="row btn-row">
        <Btn onClick={() => cmd("scan_reverse")}>⏪</Btn>
        <Btn onClick={() => cmd("previous")}>⏮</Btn>
        <Btn onClick={() => cmd("play")}>▶︎</Btn>
        <Btn onClick={() => cmd("pause")}>⏸</Btn>
        <Btn onClick={() => cmd("stop")}>⏹</Btn>
        <Btn onClick={() => cmd("next")}>⏭</Btn>
        <Btn onClick={() => cmd("scan_forward")}>⏩</Btn>
      </div>
    </div>
  );
}

function fmtTime(ms?: number): string {
  if (!ms || ms < 0) return "0:00";
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = String(s % 60).padStart(2, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="tt-row">
      <span className="tt-row-label">{label}</span>
      <span className="tt-row-value">{value}</span>
    </div>
  );
}

function decCodec(decision?: string, detail?: string): string | undefined {
  if (decision && detail) return `${decision} (${detail})`;
  return decision ?? detail ?? undefined;
}

// Tautulli-style now-playing card: poster + blurred backdrop, right-aligned
// label rows, ratings on the poster, ETA, and inline transport controls.
export function PlexNowPlaying({
  np,
  deviceId = "plex",
}: {
  np: Record<string, unknown>;
  deviceId?: string;
}) {
  const g = (k: string) => np[k] as never;
  const title = (g("title") as string) ?? "";
  const show = g("grandparent_title") as string | undefined;
  const episode = g("episode") as string | undefined;
  const thumb = g("thumb") as string | undefined;
  const art = g("art") as string | undefined;
  const dur = g("duration_ms") as number | undefined;
  const off = g("offset_ms") as number | undefined;
  const resolution = g("resolution") as string | undefined;
  const videoCodec = g("video_codec") as string | undefined;
  const audioCodec = g("audio_codec") as string | undefined;
  const audioCh = g("audio_channels") as number | undefined;
  const container = g("container") as string | undefined;
  const transcoding = g("transcoding") as boolean | undefined;
  const year = g("year") as number | undefined;
  const rating = g("content_rating") as string | undefined;
  const runtime = g("runtime_min") as number | undefined;
  const ratings = (g("ratings") as { source: string; value: number }[] | undefined) ?? [];
  // Tautulli-sourced detail (present only when Tautulli is configured).
  const product = g("product") as string | undefined;
  const player = g("player") as string | undefined;
  const quality = g("quality_profile") as string | undefined;
  const streamBitrate = g("stream_bitrate") as number | undefined;
  const bandwidth = g("bandwidth") as number | undefined;
  const location = g("location") as string | undefined;
  const ip = g("ip_address") as string | undefined;
  const videoDecision = g("video_decision") as string | undefined;
  const audioDecision = g("audio_decision") as string | undefined;
  const containerDecision = g("container_decision") as string | undefined;
  const streamDecision = g("stream_decision") as string | undefined;

  const pct = dur && off ? Math.min(100, (off / dur) * 100) : 0;
  const heading = show ? `${show}${episode ? ` · ${episode}` : ""}` : title;
  const subheading = show ? title : undefined;
  const metaLine = [year, rating, runtime ? `${runtime} min` : null].filter(Boolean).join(" · ");
  const qualityLine = quality
    ? `${quality}${streamBitrate ? ` (${(streamBitrate / 1000).toFixed(1)} Mbps)` : ""}`
    : undefined;
  const streamVal =
    streamDecision ?? (transcoding === undefined ? undefined : transcoding ? "Transcode" : "Direct Play");
  const containerVal = decCodec(containerDecision, container?.toUpperCase());
  const videoVal = decCodec(
    videoDecision,
    [videoCodec?.toUpperCase(), resolution].filter(Boolean).join(" ") || undefined,
  );
  const audioVal = decCodec(
    audioDecision,
    [audioCodec?.toUpperCase(), audioCh ? `${audioCh}ch` : null].filter(Boolean).join(" ") || undefined,
  );
  const locationVal = location ? (ip ? `${location}: ${ip}` : location) : undefined;
  const bandwidthVal = bandwidth ? `${(bandwidth / 1000).toFixed(1)} Mbps` : undefined;
  const remaining = dur && off ? dur - off : undefined;
  const eta = remaining
    ? new Date(Date.now() + remaining).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : undefined;

  const art2 = (path: string, w: number, h: number) =>
    `/api/plex/art?path=${encodeURIComponent(path)}&w=${w}&h=${h}`;
  const cmd = (command: string) => sendCommand(deviceId, command).catch((e) => console.error(e));

  return (
    <div className="tt">
      {art && <div className="tt-bg" style={{ backgroundImage: `url(${art2(art, 720, 405)})` }} />}
      <div className="tt-scrim" />
      <div className="tt-inner">
        <div className="tt-poster-col">
          {thumb && <img className="tt-poster" src={art2(thumb, 240, 360)} alt="" />}
          {ratings.length > 0 && (
            <div className="tt-ratings">
              {ratings.map((r) => (
                <span key={r.source} className="tt-rating">
                  <strong>{r.source}</strong> {r.value.toFixed(1)}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="tt-main">
          <div className="tt-head">
            <div className="tt-headings">
              <div className="tt-title">{heading}</div>
              {subheading && <div className="tt-sub">{subheading}</div>}
              {metaLine && <div className="tt-meta">{metaLine}</div>}
            </div>
            {eta && (
              <div className="tt-eta">
                <span className="tt-eta-label">ETA</span>
                <strong>{eta}</strong>
              </div>
            )}
          </div>

          <div className="tt-rows">
            {product && <Row label="Product" value={product} />}
            {player && <Row label="Player" value={player} />}
            {qualityLine && <Row label="Quality" value={qualityLine} />}
            {streamVal && <Row label="Stream" value={streamVal} />}
            {containerVal && <Row label="Container" value={containerVal} />}
            {videoVal && <Row label="Video" value={videoVal} />}
            {audioVal && <Row label="Audio" value={audioVal} />}
            {locationVal && <Row label="Location" value={locationVal} />}
            {bandwidthVal && <Row label="Bandwidth" value={bandwidthVal} />}
          </div>
        </div>
      </div>

      <div className="tt-progress">
        <div className="tt-bar">
          <div className="tt-bar-fill" style={{ width: `${pct}%` }} />
        </div>
        <div className="tt-times">
          <span>{fmtTime(off)}</span>
          <span>-{fmtTime(remaining ?? 0)}</span>
        </div>
      </div>

      <div className="tt-controls">
        <Btn onClick={() => cmd("play")}>▶︎ Play</Btn>
        <Btn onClick={() => cmd("pause")}>⏸ Pause</Btn>
        <Btn onClick={() => cmd("stop")}>⏹ Stop</Btn>
      </div>
    </div>
  );
}

export function MediaPanel({
  plex,
  kaleidescape,
}: {
  plex?: DeviceState;
  kaleidescape?: DeviceState;
}) {
  const tabs: string[] = [];
  if (plex) tabs.push("Plex");
  if (kaleidescape) tabs.push("Kaleidescape");
  const [tab, setTab] = useState(tabs[0] ?? "Plex");
  const webUrl = plex?.extra?.web_url as string | undefined;

  return (
    <Panel title="Media" className="panel-wide">
      <div className="tabs">
        {tabs.map((t) => (
          <button key={t} className={`tab ${t === tab ? "tab-active" : ""}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>
      {tab === "Plex" && plex && (
        <>
          {plex.extra?.now_playing ? (
            <PlexNowPlaying np={plex.extra.now_playing as Record<string, unknown>} />
          ) : (
            <div className="np-idle">
              <div className="np-idle-title">Nothing playing</div>
              <div className="muted">Start something on the Shield and it will show here.</div>
              {webUrl && (
                <a className="np-browse" href={webUrl} target="_blank" rel="noreferrer">
                  Open Plex Web ↗
                </a>
              )}
            </div>
          )}
        </>
      )}
      {tab === "Kaleidescape" && kaleidescape && <KaleidescapeRemote device={kaleidescape} />}
    </Panel>
  );
}
