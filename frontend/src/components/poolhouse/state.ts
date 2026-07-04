import { useMemo, useState } from "react";
import type { Dispatch, SetStateAction } from "react";

// Shared local state for the Pool House room mockup. Every tab reads and writes
// the same object, so a source picked on the overview shows up on the display and
// Trinnov tabs. Nothing here talks to hardware; the Pool House adapters are Phase 2.

export const SOURCES = ["shield", "gaming_pc", "switch2", "switch1", "node"];
export const LG_INPUTS = ["HDMI 1", "HDMI 2", "HDMI 3", "HDMI 4"];
export const PICTURE_MODES = ["Filmmaker", "Cinema", "Vivid", "Standard", "Game"];
export const ASPECTS = ["16:9", "Just Scan", "4:3", "Cinema Zoom"];
export const ENERGY = ["Off", "Minimum", "Medium", "Maximum", "Auto"];
export const SOUND_OUT = ["TV Speaker", "HDMI ARC", "Optical"];
export const UPMIXERS = ["auto", "native", "dolby", "dts", "auro3d", "legacy"];
export const PRESETS = ["Movie", "Music", "Night", "Stereo"];

export interface Zone {
  key: string;
  label: string;
  group: number; // Hue group id on the Office bridge (172.16.17.184)
  scenes: string[];
}

// The Pool House room contains the Bar and Lounge zones; the adjacent Office room
// is included so its lights can be adjusted here too. Only the Office group's
// scenes are known so far, so the others are left empty until their names arrive.
export const ZONES: Zone[] = [
  { key: "poolhouse", label: "Pool House", group: 3, scenes: [] },
  { key: "bar", label: "Bar", group: 4, scenes: [] },
  { key: "lounge", label: "Lounge", group: 5, scenes: [] },
  { key: "office", label: "Office", group: 1, scenes: ["Dim", "Dim - Strip only", "Bright White"] },
];

export interface PoolHouseState {
  power: boolean;
  setPower: Dispatch<SetStateAction<boolean>>;
  source: string;
  setSource: Dispatch<SetStateAction<string>>;
  lgInput: string;
  setLgInput: Dispatch<SetStateAction<string>>;
  picture: string;
  setPicture: Dispatch<SetStateAction<string>>;
  aspect: string;
  setAspect: Dispatch<SetStateAction<string>>;
  energy: string;
  setEnergy: Dispatch<SetStateAction<string>>;
  soundOut: string;
  setSoundOut: Dispatch<SetStateAction<string>>;
  volume: number;
  setVolume: Dispatch<SetStateAction<number>>;
  muted: boolean;
  setMuted: Dispatch<SetStateAction<boolean>>;
  dim: boolean;
  setDim: Dispatch<SetStateAction<boolean>>;
  bypass: boolean;
  setBypass: Dispatch<SetStateAction<boolean>>;
  upmixer: string;
  setUpmixer: Dispatch<SetStateAction<string>>;
  preset: string;
  setPreset: Dispatch<SetStateAction<string>>;
  bri: Record<string, number>;
  setBri: Dispatch<SetStateAction<Record<string, number>>>;
  scene: Record<string, string>;
  setScene: Dispatch<SetStateAction<Record<string, string>>>;
  zoneOn: Record<string, boolean>;
  setZoneOn: Dispatch<SetStateAction<Record<string, boolean>>>;
  nudge: (delta: number) => void;
}

export function usePoolHouseState(): PoolHouseState {
  const [power, setPower] = useState(false);
  const [source, setSource] = useState("shield");
  const [lgInput, setLgInput] = useState("HDMI 1");
  const [picture, setPicture] = useState("Filmmaker");
  const [aspect, setAspect] = useState("16:9");
  const [energy, setEnergy] = useState("Off");
  const [soundOut, setSoundOut] = useState("HDMI ARC");
  const [volume, setVolume] = useState(-22);
  const [muted, setMuted] = useState(false);
  const [dim, setDim] = useState(false);
  const [bypass, setBypass] = useState(false);
  const [upmixer, setUpmixer] = useState("auto");
  const [preset, setPreset] = useState("Movie");
  const [bri, setBri] = useState<Record<string, number>>({
    poolhouse: 140,
    bar: 90,
    lounge: 160,
    office: 200,
  });
  const [scene, setScene] = useState<Record<string, string>>({ office: "Dim" });
  const [zoneOn, setZoneOn] = useState<Record<string, boolean>>({
    poolhouse: true,
    bar: true,
    lounge: true,
    office: false,
  });

  const nudge = (delta: number) =>
    setVolume((v) => Math.max(-60, Math.min(0, Math.round((v + delta) * 2) / 2)));

  return useMemo(
    () => ({
      power, setPower,
      source, setSource,
      lgInput, setLgInput,
      picture, setPicture,
      aspect, setAspect,
      energy, setEnergy,
      soundOut, setSoundOut,
      volume, setVolume,
      muted, setMuted,
      dim, setDim,
      bypass, setBypass,
      upmixer, setUpmixer,
      preset, setPreset,
      bri, setBri,
      scene, setScene,
      zoneOn, setZoneOn,
      nudge,
    }),
    [power, source, lgInput, picture, aspect, energy, soundOut, volume, muted, dim,
     bypass, upmixer, preset, bri, scene, zoneOn],
  );
}
