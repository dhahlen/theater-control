import type { DeviceMap } from "../types";
import { Dot } from "./common";
import { MuteIcon, sourceLabel } from "./icons";
import { RoomSwitcher, type Room } from "./RoomSwitcher";
import type { PoolHouseState } from "./poolhouse/state";

interface StatusItem {
  label: string;
  value: React.ReactNode;
  on?: boolean;
  muted?: boolean;
}

export function StatusBar({
  devices,
  connected,
  room,
  onRoomChange,
  ph,
}: {
  devices: DeviceMap;
  connected: boolean;
  room: Room;
  onRoomChange: (r: Room) => void;
  ph: PoolHouseState;
}) {
  const jvc = devices.jvc;
  const trinnov = devices.trinnov;
  const volume = trinnov?.extra?.volume as number | undefined;
  const muted = trinnov?.extra?.mute as boolean | undefined;
  const source = trinnov?.input ?? jvc?.input;

  const theaterPower = jvc?.power === "on" ? "ON" : jvc?.power ? jvc.power.toUpperCase() : "—";
  const poolhouse = room === "poolhouse";

  const items: StatusItem[] = poolhouse
    ? [
        { label: "Display", value: ph.power ? "ON" : "STANDBY", on: ph.power },
        { label: "Source", value: sourceLabel(ph.source) },
        { label: "Volume", value: ph.muted ? "Muted" : `${ph.volume} dB`, muted: ph.muted },
      ]
    : [
        { label: "Theater", value: theaterPower, on: jvc?.power === "on" },
        { label: "Source", value: source ? sourceLabel(source) : "—" },
        {
          label: "Volume",
          value: muted ? "Muted" : volume !== undefined ? `${volume} dB` : "—",
          muted,
        },
      ];

  return (
    <div className="statusbar">
      <div className="brand">
        <span className="brand-mark">◐</span> {poolhouse ? "Pool House Control" : "Theater Control"}
      </div>
      <RoomSwitcher room={room} onSelect={onRoomChange} />
      <div className="status-items">
        {items.map((it) => (
          <div className="status-item" key={it.label}>
            <span className="si-label">{it.label}</span>
            <span className={`si-value si-vol ${it.on ? "on" : ""} ${it.muted ? "si-muted" : ""}`}>
              {it.muted && <MuteIcon muted size={18} />}
              {it.value}
            </span>
          </div>
        ))}
      </div>
      <div className="conn">
        <Dot reach={connected ? "online" : "offline"} />
        <span>{connected ? "live" : "reconnecting"}</span>
      </div>
    </div>
  );
}
