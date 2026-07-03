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
        <div className="plex-frame">
          {webUrl ? (
            <iframe title="Plex" src={webUrl} />
          ) : (
            <span className="muted">Plex web URL not configured</span>
          )}
        </div>
      )}
      {tab === "Kaleidescape" && kaleidescape && <KaleidescapeRemote device={kaleidescape} />}
    </Panel>
  );
}
