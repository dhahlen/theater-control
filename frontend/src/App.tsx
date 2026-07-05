import { useEffect, useState } from "react";
import { useStore } from "./store";
import { StatusBar } from "./components/StatusBar";
import { SceneBar } from "./components/SceneBar";
import { Toolbar, type TabDef } from "./components/Toolbar";
import { TrinnovPanel } from "./components/TrinnovPanel";
import { LightingPanel } from "./components/LightingPanel";
import { MediaPanel } from "./components/MediaPanel";
import { MadvrPanel } from "./components/MadvrPanel";
import { JvcPanel } from "./components/JvcPanel";
import { TrinnovView } from "./components/views/TrinnovView";
import { MadvrView } from "./components/views/MadvrView";
import { JvcView } from "./components/views/JvcView";
import { PoolHouseRoom } from "./components/poolhouse/PoolHouseRoom";
import { usePoolHouse } from "./components/poolhouse/live";
import type { Room } from "./components/RoomSwitcher";

interface UiConfig {
  sources: string[];
  default_source: string;
  devices: string[];
}

const ALL_TABS: TabDef[] = [
  { key: "theater", label: "Theater" },
  { key: "trinnov", label: "Trinnov", device: "trinnov" },
  { key: "madvr", label: "MadVR", device: "madvr" },
  { key: "jvc", label: "JVC", device: "jvc" },
  { key: "media", label: "Media" },
  { key: "lighting", label: "Lighting", device: "hue" },
];

export function App() {
  const { devices, connected, progress, markSceneStarted } = useStore();
  const [ui, setUi] = useState<UiConfig>({ sources: [], default_source: "", devices: [] });
  const [tab, setTab] = useState("theater");
  const [room, setRoom] = useState<Room>("theater");
  const ph = usePoolHouse(devices);

  useEffect(() => {
    fetch("/api/ui-config")
      .then((r) => (r.ok ? r.json() : null))
      .then((c) => c && setUi(c))
      .catch(() => undefined);
  }, []);

  const hasMedia = Boolean(devices.plex || devices.kaleidescape);
  const tabs = ALL_TABS.filter((t) => {
    if (t.key === "media") return hasMedia;
    if (t.device) return Boolean(devices[t.device]);
    return true;
  });

  if (room === "poolhouse") {
    return (
      <div className="app">
        <StatusBar devices={devices} connected={connected} room={room} onRoomChange={setRoom} ph={ph} />
        <PoolHouseRoom s={ph} />
      </div>
    );
  }

  return (
    <div className="app">
      <StatusBar devices={devices} connected={connected} room={room} onRoomChange={setRoom} ph={ph} />
      <Toolbar tabs={tabs} active={tab} onSelect={setTab} devices={devices} />

      {tab === "theater" && (
        <>
          <SceneBar
            sources={ui.sources}
            defaultSource={ui.default_source || ui.sources[0] || "shield"}
            progress={progress}
            markSceneStarted={markSceneStarted}
          />
          <div className="grid">
            <MediaPanel plex={devices.plex} kaleidescape={devices.kaleidescape} />
            <div className="grid-col">
              <TrinnovPanel device={devices.trinnov} />
              <LightingPanel device={devices.hue} />
            </div>
            <div className="grid-col">
              <JvcPanel device={devices.jvc} />
              <MadvrPanel device={devices.madvr} />
            </div>
          </div>
        </>
      )}

      {tab === "trinnov" && <TrinnovView device={devices.trinnov} />}
      {tab === "madvr" && <MadvrView device={devices.madvr} />}
      {tab === "jvc" && <JvcView device={devices.jvc} />}
      {tab === "media" && (
        <div className="single-view">
          <MediaPanel plex={devices.plex} kaleidescape={devices.kaleidescape} />
        </div>
      )}
      {tab === "lighting" && (
        <div className="single-view">
          <LightingPanel device={devices.hue} />
        </div>
      )}
    </div>
  );
}
