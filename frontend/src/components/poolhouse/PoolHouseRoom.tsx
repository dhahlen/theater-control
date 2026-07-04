import { useState } from "react";
import { Toolbar, type TabDef } from "../Toolbar";
import { usePoolHouseState } from "./state";
import { OverviewTab } from "./OverviewTab";
import { DisplayTab } from "./DisplayTab";
import { TrinnovTab } from "./TrinnovTab";
import { LightingTab } from "./LightingTab";
import { MediaTab } from "./MediaTab";

const TABS: TabDef[] = [
  { key: "overview", label: "Pool House" },
  { key: "display", label: "Display" },
  { key: "trinnov", label: "Trinnov" },
  { key: "lighting", label: "Lighting" },
  { key: "media", label: "Media" },
];

export function PoolHouseRoom() {
  const s = usePoolHouseState();
  const [tab, setTab] = useState("overview");

  return (
    <>
      <Toolbar tabs={TABS} active={tab} onSelect={setTab} devices={{}} />
      <div className="preview-banner">
        Phase 2 preview — layout mockup, not yet connected to hardware.
      </div>
      {tab === "overview" && <OverviewTab s={s} onOpen={setTab} />}
      {tab === "display" && <DisplayTab s={s} />}
      {tab === "trinnov" && <TrinnovTab s={s} />}
      {tab === "lighting" && <LightingTab s={s} />}
      {tab === "media" && <MediaTab />}
    </>
  );
}
