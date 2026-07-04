import type { DeviceMap } from "../types";
import { Dot } from "./common";
import { MuteIcon, sourceLabel } from "./icons";

export function StatusBar({ devices, connected }: { devices: DeviceMap; connected: boolean }) {
  const jvc = devices.jvc;
  const trinnov = devices.trinnov;
  const volume = trinnov?.extra?.volume as number | undefined;
  const muted = trinnov?.extra?.mute as boolean | undefined;
  const source = trinnov?.input ?? jvc?.input;

  const theaterPower = jvc?.power === "on" ? "ON" : jvc?.power ? jvc.power.toUpperCase() : "—";

  return (
    <div className="statusbar">
      <div className="brand">
        <span className="brand-mark">◐</span> Theater Control
      </div>
      <div className="status-items">
        <div className="status-item">
          <span className="si-label">Theater</span>
          <span className={`si-value ${jvc?.power === "on" ? "on" : ""}`}>{theaterPower}</span>
        </div>
        <div className="status-item">
          <span className="si-label">Source</span>
          <span className="si-value">{source ? sourceLabel(source) : "—"}</span>
        </div>
        <div className="status-item">
          <span className="si-label">Volume</span>
          <span className={`si-value si-vol ${muted ? "si-muted" : ""}`}>
            {muted && <MuteIcon muted size={18} />}
            {muted ? "Muted" : volume !== undefined ? `${volume} dB` : "—"}
          </span>
        </div>
      </div>
      <div className="conn">
        <Dot reach={connected ? "online" : "offline"} />
        <span>{connected ? "live" : "reconnecting"}</span>
      </div>
    </div>
  );
}
