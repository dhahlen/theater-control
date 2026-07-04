import { useState } from "react";
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

function Detail({ label, value }: { label: string; value?: string | number | null }) {
  if (value === undefined || value === null || value === "") return null;
  return (
    <div className="np-detail">
      <span className="np-detail-label">{label}</span>
      <span className="np-detail-value">{value}</span>
    </div>
  );
}

function PlexNowPlaying({ np }: { np: Record<string, unknown> }) {
  const g = (k: string) => np[k] as never;
  const title = (g("title") as string) ?? "";
  const show = g("grandparent_title") as string | undefined;
  const thumb = g("thumb") as string | undefined;
  const dur = g("duration_ms") as number | undefined;
  const off = g("offset_ms") as number | undefined;
  const bitrate = g("bitrate") as number | undefined;
  const width = g("width") as number | undefined;
  const height = g("height") as number | undefined;
  const resolution = g("resolution") as string | undefined;
  const file = g("file") as string | undefined;
  const size = g("file_size") as number | undefined;
  const transcoding = g("transcoding") as boolean | undefined;
  const pct = dur && off ? Math.min(100, (off / dur) * 100) : 0;

  return (
    <div className="nowplaying">
      {thumb && (
        <img className="np-art" src={`/api/plex/art?path=${encodeURIComponent(thumb)}`} alt="" />
      )}
      <div className="np-info">
        <div className="np-title">{title}</div>
        {show && <div className="np-show">{show}</div>}
        <div className="np-progress">
          <div className="np-bar">
            <div className="np-bar-fill" style={{ width: `${pct}%` }} />
          </div>
          <div className="np-times">
            <span>{fmtTime(off)}</span>
            <span>{fmtTime(dur)}</span>
          </div>
        </div>
        <div className="np-details">
          <Detail
            label="Quality"
            value={resolution ? resolution.toUpperCase() : width && height ? `${width}×${height}` : undefined}
          />
          <Detail label="Bitrate" value={bitrate ? `${(bitrate / 1000).toFixed(1)} Mbps` : undefined} />
          <Detail label="Video" value={g("video_codec") as string} />
          <Detail
            label="Audio"
            value={
              (g("audio_codec") as string)
                ? `${g("audio_codec")}${g("audio_channels") ? ` ${g("audio_channels")}ch` : ""}`
                : undefined
            }
          />
          <Detail label="Container" value={g("container") as string} />
          <Detail label="Playback" value={transcoding ? "Transcode" : "Direct Play"} />
          <Detail label="Size" value={size ? `${(size / 1e9).toFixed(2)} GB` : undefined} />
          <Detail label="Player" value={g("player") as string} />
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
            <div className="np-idle muted">Nothing playing</div>
          )}
          <div className="plex-frame">
            {webUrl ? (
              <iframe title="Plex" src={webUrl} />
            ) : (
              <span className="muted">Plex web URL not configured</span>
            )}
          </div>
        </>
      )}
      {tab === "Kaleidescape" && kaleidescape && <KaleidescapeRemote device={kaleidescape} />}
    </Panel>
  );
}
