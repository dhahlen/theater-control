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

function Badge({ children }: { children: ReactNode }) {
  return <span className="np-badge">{children}</span>;
}

function Detail({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="np-detail">
      <span className="np-detail-label">{label}</span>
      <span className="np-detail-value">{value}</span>
    </div>
  );
}

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
  const dur = g("duration_ms") as number | undefined;
  const off = g("offset_ms") as number | undefined;
  const bitrate = g("bitrate") as number | undefined;
  const resolution = g("resolution") as string | undefined;
  const dynamicRange = g("dynamic_range") as string | undefined;
  const videoCodec = g("video_codec") as string | undefined;
  const audioCodec = g("audio_codec") as string | undefined;
  const audioCh = g("audio_channels") as number | undefined;
  const container = g("container") as string | undefined;
  const frameRate = g("frame_rate") as string | undefined;
  const file = g("file") as string | undefined;
  const size = g("file_size") as number | undefined;
  const transcoding = g("transcoding") as boolean | undefined;
  const year = g("year") as number | undefined;
  const rating = g("content_rating") as string | undefined;
  const runtime = g("runtime_min") as number | undefined;
  const genres = (g("genres") as string[] | undefined) ?? [];
  const ratings = (g("ratings") as { source: string; value: number }[] | undefined) ?? [];
  const summary = g("summary") as string | undefined;
  // Tautulli-sourced detail (present only when Tautulli is configured).
  const product = g("product") as string | undefined;
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
  const remaining = dur && off ? dur - off : undefined;
  const eta = remaining
    ? new Date(Date.now() + remaining).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : undefined;

  const cmd = (command: string) => sendCommand(deviceId, command).catch((e) => console.error(e));

  return (
    <div className="nowplaying">
      {thumb && (
        <img className="np-art" src={`/api/plex/art?path=${encodeURIComponent(thumb)}`} alt="" />
      )}
      <div className="np-info">
        <div className="np-title">{heading}</div>
        {subheading && <div className="np-show">{subheading}</div>}
        {metaLine && <div className="np-meta">{metaLine}</div>}
        {genres.length > 0 && <div className="np-genres">{genres.join(" · ")}</div>}

        {ratings.length > 0 && (
          <div className="np-ratings">
            {ratings.map((r) => (
              <span key={r.source} className="np-rating">
                <strong>{r.source}</strong> {r.value.toFixed(1)}
              </span>
            ))}
          </div>
        )}

        <div className="np-badges">
          {resolution && <Badge>{resolution.toUpperCase()}</Badge>}
          {dynamicRange && <Badge>{dynamicRange}</Badge>}
          {videoCodec && <Badge>{videoCodec.toUpperCase()}</Badge>}
          {audioCodec && <Badge>{audioCodec.toUpperCase()}{audioCh ? ` ${audioCh}ch` : ""}</Badge>}
          {container && <Badge>{container.toUpperCase()}</Badge>}
          {frameRate && <Badge>{frameRate}</Badge>}
          {bitrate && <Badge>{(bitrate / 1000).toFixed(1)} Mbps</Badge>}
          <Badge>{transcoding ? "Transcode" : "Direct Play"}</Badge>
        </div>

        {product && (
          <div className="np-details">
            <Detail label="Product" value={product} />
            {qualityLine && <Detail label="Quality" value={qualityLine} />}
            {streamDecision && <Detail label="Stream" value={streamDecision} />}
            {containerDecision && <Detail label="Container" value={containerDecision} />}
            {videoDecision && <Detail label="Video" value={videoDecision} />}
            {audioDecision && <Detail label="Audio" value={audioDecision} />}
            {location && <Detail label="Location" value={ip ? `${location}: ${ip}` : location} />}
            {bandwidth && <Detail label="Bandwidth" value={`${(bandwidth / 1000).toFixed(1)} Mbps`} />}
          </div>
        )}

        <div className="np-progress">
          <div className="np-bar">
            <div className="np-bar-fill" style={{ width: `${pct}%` }} />
          </div>
          <div className="np-times">
            <span>{fmtTime(off)}</span>
            <span>{eta ? `ETA ${eta} · ` : ""}-{fmtTime(remaining ?? 0)}</span>
          </div>
        </div>

        <div className="row btn-row">
          <Btn onClick={() => cmd("play")}>▶︎ Play</Btn>
          <Btn onClick={() => cmd("pause")}>⏸ Pause</Btn>
          <Btn onClick={() => cmd("stop")}>⏹ Stop</Btn>
        </div>

        {summary && <div className="np-summary">{summary}</div>}
        <div className="np-foot">
          {g("player") && <span>{g("player") as string}</span>}
          {size && <span>{(size / 1e9).toFixed(2)} GB</span>}
        </div>
        {file && <div className="np-file" title={file}>{file}</div>}
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
