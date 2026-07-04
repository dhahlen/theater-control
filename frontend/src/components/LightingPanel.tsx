import { sendCommand } from "../api";
import type { DeviceState } from "../types";
import { Btn, Panel } from "./common";

// Manual override only. Automatic play-triggered dimming stays with Lumunarr;
// this panel does not touch that automation.
export function LightingPanel({ device }: { device?: DeviceState }) {
  if (!device) return null;
  const scenes = (device.extra?.scenes as string[]) ?? [];
  const bri = device.extra?.bri as number | undefined;

  const cmd = (command: string, params?: Record<string, unknown>) =>
    sendCommand("hue", command, params).catch((e) => console.error(e));

  const levels: [string, number][] = [
    ["Off", 0],
    ["25%", 64],
    ["50%", 127],
    ["75%", 190],
    ["100%", 254],
  ];

  return (
    <Panel title="Lighting" device={device}>
      <div className="subhead">Scenes</div>
      <div className="row btn-row wrap">
        {scenes.map((s) => (
          <Btn key={s} onClick={() => cmd("recall_scene", { scene: s })}>
            {s}
          </Btn>
        ))}
        {scenes.length === 0 && <span className="muted">no scenes configured</span>}
      </div>
      <div className="subhead">Level {bri !== undefined ? `(${Math.round((bri / 254) * 100)}%)` : ""}</div>
      <div className="row btn-row">
        {levels.map(([label, value]) => (
          <Btn key={label} onClick={() => cmd("set_level", { bri: value })}>
            {label}
          </Btn>
        ))}
      </div>
    </Panel>
  );
}
