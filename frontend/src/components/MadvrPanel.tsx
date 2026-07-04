import type { DeviceState } from "../types";
import { Panel, Stat } from "./common";

// Dashboard card: status only. The full remote and controls live on the MadVR
// tab, which keeps this card short so the main Theater tab never scrolls.
export function MadvrPanel({ device }: { device?: DeviceState }) {
  if (!device) return null;
  const signal = (device.extra?.signal as Record<string, string>) ?? {};
  const temps = (device.extra?.temperatures as Record<string, number>) ?? {};

  return (
    <Panel title="MadVR Envy" device={device}>
      <div className="row">
        <Stat label="Incoming" value={signal.IncomingSignalInfo ?? "—"} />
      </div>
      <div className="row">
        <Stat label="Outgoing" value={signal.OutgoingSignalInfo ?? "—"} />
      </div>
      <div className="row">
        <Stat label="Aspect" value={signal.AspectRatio ?? "—"} />
        <Stat label="GPU" value={temps.gpu !== undefined ? `${temps.gpu}°C` : "—"} />
      </div>
    </Panel>
  );
}
