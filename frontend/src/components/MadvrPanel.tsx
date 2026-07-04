import { sendCommand } from "../api";
import type { DeviceState } from "../types";
import { Btn, Panel, Stat } from "./common";

// Dashboard card: status plus the profile-change button. The full remote lives
// on the MadVR tab, keeping this card short so the Theater tab never scrolls.
export function MadvrPanel({ device }: { device?: DeviceState }) {
  if (!device) return null;
  const signal = (device.extra?.signal as Record<string, string>) ?? {};
  const temps = (device.extra?.temperatures as Record<string, number>) ?? {};
  const cmd = (command: string) => sendCommand("madvr", command).catch((e) => console.error(e));

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
      <div className="row btn-row">
        <Btn onClick={() => cmd("profile_cycle")}>Profile ⟳</Btn>
      </div>
    </Panel>
  );
}
