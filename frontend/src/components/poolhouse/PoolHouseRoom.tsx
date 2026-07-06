import { useState } from "react";
import { Toolbar, type TabDef } from "../Toolbar";
import type { PoolHouse } from "./live";
import { OverviewTab } from "./OverviewTab";
import { DisplayTab } from "./DisplayTab";
import { TrinnovTab } from "./TrinnovTab";
import { LightingTab } from "./LightingTab";
import { MediaTab } from "./MediaTab";
import { GamingPcView } from "../views/GamingPcView";

const BASE_TABS: TabDef[] = [
  { key: "overview", label: "Pool House" },
  { key: "display", label: "Display" },
  { key: "trinnov", label: "Trinnov" },
  { key: "lighting", label: "Lighting" },
  { key: "media", label: "Media" },
];

export function PoolHouseRoom({ s }: { s: PoolHouse }) {
  const [tab, setTab] = useState("overview");

  if (!s.configured) {
    return <div className="view-empty muted">Pool House devices are not configured.</div>;
  }

  // The gaming PC is shared with the theater; show its tab here too when present.
  const tabs = s.gamingPc
    ? [...BASE_TABS, { key: "gamingpc", label: "Gaming PC" }]
    : BASE_TABS;

  return (
    <>
      <Toolbar tabs={tabs} active={tab} onSelect={setTab} devices={{}} />
      {tab === "overview" && <OverviewTab s={s} />}
      {tab === "display" && <DisplayTab s={s} />}
      {tab === "trinnov" && <TrinnovTab s={s} />}
      {tab === "lighting" && <LightingTab s={s} />}
      {tab === "media" && <MediaTab s={s} />}
      {tab === "gamingpc" && <GamingPcView device={s.gamingPc} />}
    </>
  );
}
