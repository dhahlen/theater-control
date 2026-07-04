import { useEffect, useState } from "react";
import { useStore } from "./store";
import { StatusBar } from "./components/StatusBar";
import { SceneBar } from "./components/SceneBar";
import { TrinnovPanel } from "./components/TrinnovPanel";
import { LightingPanel } from "./components/LightingPanel";
import { MediaPanel } from "./components/MediaPanel";
import { MadvrPanel } from "./components/MadvrPanel";
import { JvcPanel } from "./components/JvcPanel";

interface UiConfig {
  sources: string[];
  default_source: string;
  devices: string[];
}

export function App() {
  const { devices, connected, progress, markSceneStarted } = useStore();
  const [ui, setUi] = useState<UiConfig>({ sources: [], default_source: "", devices: [] });

  useEffect(() => {
    fetch("/api/ui-config")
      .then((r) => (r.ok ? r.json() : null))
      .then((c) => c && setUi(c))
      .catch(() => undefined);
  }, []);

  return (
    <div className="app">
      <StatusBar devices={devices} connected={connected} />

      <SceneBar
        sources={ui.sources}
        defaultSource={ui.default_source || ui.sources[0] || "plex"}
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
    </div>
  );
}
