import { sendCommand } from "../api";
import type { DeviceState } from "../types";
import { Btn, Panel, Stat } from "./common";

export function MadvrPanel({ device }: { device?: DeviceState }) {
  if (!device) return null;
  const signal = (device.extra?.signal as Record<string, string>) ?? {};

  const cmd = (command: string, params?: Record<string, unknown>) =>
    sendCommand("madvr", command, params).catch((e) => console.error(e));
  const key = (button: string) => cmd("key_press", { button });

  return (
    <Panel title="MadVR Envy" device={device}>
      <div className="row">
        <Stat label="Incoming" value={signal.IncomingSignalInfo ?? "—"} />
      </div>
      <div className="row">
        <Stat label="Aspect" value={signal.AspectRatio ?? "—"} />
      </div>
      <div className="dpad">
        <div />
        <Btn onClick={() => key("UP")}>▲</Btn>
        <div />
        <Btn onClick={() => key("LEFT")}>◀</Btn>
        <Btn onClick={() => key("OK")}>OK</Btn>
        <Btn onClick={() => key("RIGHT")}>▶</Btn>
        <div />
        <Btn onClick={() => key("DOWN")}>▼</Btn>
        <div />
      </div>
      <div className="row btn-row">
        <Btn onClick={() => key("MENU")}>Menu</Btn>
        <Btn onClick={() => key("SETTINGS")}>Settings</Btn>
        <Btn onClick={() => key("INFO")}>Info</Btn>
        <Btn onClick={() => key("BACK")}>Back</Btn>
      </div>
    </Panel>
  );
}
