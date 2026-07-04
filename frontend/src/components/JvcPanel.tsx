import { sendCommand } from "../api";
import type { DeviceState } from "../types";
import { Btn, Panel, Stat } from "./common";

export function JvcPanel({ device }: { device?: DeviceState }) {
  if (!device) return null;
  const lowLatency = device.extra?.low_latency as string | undefined;
  const signal = device.extra?.source_status as string | undefined;

  const cmd = (command: string, params?: Record<string, unknown>) =>
    sendCommand("jvc", command, params).catch((e) => console.error(e));

  return (
    <Panel title="JVC NZ900" device={device}>
      <div className="row">
        <Stat label="Power" value={device.power ?? "—"} />
        <Stat label="Input" value={device.input ?? "—"} />
      </div>
      <div className="row">
        <Stat label="Low latency" value={lowLatency ?? "—"} />
        <Stat label="Signal" value={signal ?? "—"} />
      </div>
      <div className="subhead">Low latency</div>
      <div className="row btn-row">
        <Btn onClick={() => cmd("low_latency", { state: "on" })} active={lowLatency === "on"}>
          On
        </Btn>
        <Btn onClick={() => cmd("low_latency", { state: "off" })} active={lowLatency === "off"}>
          Off
        </Btn>
      </div>
    </Panel>
  );
}
