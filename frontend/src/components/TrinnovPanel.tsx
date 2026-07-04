import { sendCommand } from "../api";
import type { DeviceState } from "../types";
import { Btn, Panel, Stat } from "./common";
import { MuteIcon, sourceLabel } from "./icons";

export function TrinnovPanel({ device }: { device?: DeviceState }) {
  if (!device) return null;
  const volume = device.extra?.volume as number | undefined;
  const muted = device.extra?.mute as boolean | undefined;
  const sources = (device.extra?.sources as Record<string, number>) ?? {};
  const current = device.input;

  const cmd = (command: string, params?: Record<string, unknown>) =>
    sendCommand("trinnov", command, params).catch((e) => console.error(e));

  return (
    <Panel title="Trinnov" device={device}>
      <div className="row">
        <Stat label="Volume" value={volume !== undefined ? `${volume} dB` : "—"} />
        <Stat label="Mute" value={muted ? "ON" : "off"} />
      </div>
      <div className="row btn-row">
        <Btn onClick={() => cmd("volume_adjust", { delta: -2 })}>−2</Btn>
        <Btn onClick={() => cmd("volume_adjust", { delta: -0.5 })}>−0.5</Btn>
        <Btn onClick={() => cmd("volume_adjust", { delta: 0.5 })}>+0.5</Btn>
        <Btn onClick={() => cmd("volume_adjust", { delta: 2 })}>+2</Btn>
        <button
          className={`btn icon-btn ${muted ? "btn-active" : ""}`}
          aria-label={muted ? "Unmute" : "Mute"}
          onClick={() => cmd("mute", { state: muted ? "off" : "on" })}
        >
          <MuteIcon muted={muted} />
        </button>
      </div>
      <div className="subhead">Source</div>
      <div className="row btn-row wrap">
        {Object.keys(sources).map((name) => (
          <Btn key={name} onClick={() => cmd("source", { name })} active={current === name}>
            {sourceLabel(name)}
          </Btn>
        ))}
      </div>
    </Panel>
  );
}
