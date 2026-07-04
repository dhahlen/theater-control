// Live Pool House view-model: derives per-device state from the WebSocket device
// map and exposes command dispatchers. Mirrors the theater panels, but keyed off
// the ph_* device ids the backend registers for the second room.

import { sendCommand } from "../../api";
import type { DeviceMap, DeviceState, Reachability } from "../../types";

export const UPMIXERS = ["auto", "native", "dolby", "dts", "auro3d", "legacy"];
export const PICTURE_MODES = ["Filmmaker", "Cinema", "Vivid", "Standard", "Game"];

export const PH_ZONES: { key: string; id: string; label: string }[] = [
  { key: "poolhouse", id: "ph_hue_poolhouse", label: "Pool House" },
  { key: "bar", id: "ph_hue_bar", label: "Bar" },
  { key: "lounge", id: "ph_hue_lounge", label: "Lounge" },
  { key: "office", id: "ph_hue_office", label: "Office" },
];

export interface PoolHouseZone {
  key: string;
  id: string;
  label: string;
  device?: DeviceState;
  online: boolean;
  on: boolean;
  bri: number;
  scenes: string[];
}

export interface PoolHouse {
  configured: boolean;
  lg?: DeviceState;
  trinnov?: DeviceState;
  plex?: DeviceState;
  // LG display
  lgOnline: boolean;
  power: boolean;
  // Trinnov Altitude 16
  trinnovOnline: boolean;
  source: string | null;
  sources: Record<string, number>;
  volume?: number;
  muted: boolean;
  upmixer?: string;
  dim: boolean;
  bypass: boolean;
  presets: Record<string, string>;
  currentPreset?: number;
  sourceFormat?: string;
  sampleRate?: number;
  zones: PoolHouseZone[];
  // commands
  lgPower: (on: boolean) => void;
  setPicture: (mode: string) => void;
  setSource: (name: string) => void;
  volumeAdjust: (delta: number) => void;
  volumeSet: (db: number) => void;
  setMute: (on: boolean) => void;
  setUpmixer: (mode: string) => void;
  setPreset: (index: number) => void;
  setDim: (on: boolean) => void;
  setBypass: (on: boolean) => void;
  zoneLevel: (id: string, bri: number) => void;
  zoneToggle: (id: string, on: boolean) => void;
  zoneScene: (id: string, scene: string) => void;
  roomOn: () => void;
  roomOff: () => void;
}

function send(deviceId: string, command: string, params?: Record<string, unknown>) {
  sendCommand(deviceId, command, params).catch((e) => console.error(e));
}

function isOnline(d?: DeviceState): boolean {
  return (d?.reachable as Reachability | undefined) === "online";
}

export function poolHouse(devices: DeviceMap): PoolHouse {
  const lg = devices["ph_lg"];
  const trinnov = devices["ph_trinnov"];
  const plex = devices["ph_plex"];
  const te = trinnov?.extra ?? {};

  const zones: PoolHouseZone[] = PH_ZONES.map((z) => {
    const device = devices[z.id];
    const e = device?.extra ?? {};
    return {
      ...z,
      device,
      online: isOnline(device),
      on: Boolean(e.any_on),
      bri: (e.bri as number) ?? 0,
      scenes: (e.scenes as string[]) ?? [],
    };
  });

  const source = trinnov?.input ?? null;

  return {
    configured: Boolean(lg || trinnov || plex || zones.some((z) => z.device)),
    lg,
    trinnov,
    plex,
    lgOnline: isOnline(lg),
    power: lg?.power === "on",
    trinnovOnline: isOnline(trinnov),
    source,
    sources: (te.sources as Record<string, number>) ?? {},
    volume: te.volume as number | undefined,
    muted: Boolean(te.mute),
    upmixer: te.upmixer as string | undefined,
    dim: Boolean(te.dim),
    bypass: Boolean(te.bypass),
    presets: (te.presets as Record<string, string>) ?? {},
    currentPreset: te.current_preset as number | undefined,
    sourceFormat: te.source_format as string | undefined,
    sampleRate: te.sample_rate as number | undefined,
    zones,

    lgPower: (on) => send("ph_lg", "power", { state: on ? "on" : "off" }),
    setPicture: (mode) => send("ph_lg", "picture_mode", { mode }),
    setSource: (name) => send("ph_trinnov", "source", { name }),
    volumeAdjust: (delta) => send("ph_trinnov", "volume_adjust", { delta }),
    volumeSet: (db) => send("ph_trinnov", "volume_set", { db }),
    setMute: (on) => send("ph_trinnov", "mute", { state: on ? "on" : "off" }),
    setUpmixer: (mode) => send("ph_trinnov", "upmixer", { mode }),
    setPreset: (index) => send("ph_trinnov", "preset", { index }),
    setDim: (on) => send("ph_trinnov", "dim", { state: on ? "on" : "off" }),
    setBypass: (on) => send("ph_trinnov", "bypass", { state: on ? "on" : "off" }),
    zoneLevel: (id, bri) => send(id, "set_level", { bri }),
    zoneToggle: (id, on) => send(id, "toggle", { state: on ? "on" : "off" }),
    zoneScene: (id, scene) => send(id, "recall_scene", { scene }),
    roomOn: () => {
      send("ph_lg", "power", { state: "on" });
      if (source) send("ph_trinnov", "source", { name: source });
    },
    roomOff: () => send("ph_lg", "power", { state: "off" }),
  };
}
