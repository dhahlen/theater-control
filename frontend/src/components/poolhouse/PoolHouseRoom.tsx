import { useState } from "react";
import { Toolbar, type TabDef } from "../Toolbar";
import type { DeviceMap } from "../../types";
import type { PoolHouse } from "./live";
import { OverviewTab } from "./OverviewTab";
import { DisplayTab } from "./DisplayTab";
import { TrinnovTab } from "./TrinnovTab";
import { LightingTab } from "./LightingTab";
import { MediaTab } from "./MediaTab";
import { GamingPcView } from "../views/GamingPcView";

// Same shape and order as the theater toolbar: room overview, then the device
// tabs with an online/offline dot. Gaming PC is shared with the theater and only
// appears when configured.
const TABS: TabDef[] = [
  { key: "overview", label: "Pool House" },
  { key: "trinnov", label: "Trinnov", device: "ph_trinnov" },
  { key: "display", label: "LG TV", device: "ph_lg" },
  { key: "gamingpc", label: "Gaming PC", device: "gaming_pc" },
  { key: "media", label: "Media" },
  { key: "lighting", label: "Lighting", device: "ph_hue" },
];

export function PoolHouseRoom({ s }: { s: PoolHouse }) {
  const [tab, setTab] = useState("overview");

  if (!s.configured) {
    return <div className="view-empty muted">Pool House devices are not configured.</div>;
  }

  // Feed the toolbar the device states its dots key off. The Lighting dot uses
  // the primary Pool House zone as representative of the room's bridge.
  const poolZone = s.zones.find((z) => z.key === "poolhouse")?.device;
  const tabDevices: DeviceMap = {};
  if (s.trinnov) tabDevices.ph_trinnov = s.trinnov;
  if (s.lg) tabDevices.ph_lg = s.lg;
  if (s.gamingPc) tabDevices.gaming_pc = s.gamingPc;
  if (poolZone) tabDevices.ph_hue = poolZone;

  const tabs = TABS.filter((t) => t.key !== "gamingpc" || Boolean(s.gamingPc));

  return (
    <>
      <Toolbar tabs={tabs} active={tab} onSelect={setTab} devices={tabDevices} />
      {tab === "overview" && <OverviewTab s={s} />}
      {tab === "display" && <DisplayTab s={s} />}
      {tab === "trinnov" && <TrinnovTab s={s} />}
      {tab === "lighting" && <LightingTab s={s} />}
      {tab === "media" && <MediaTab s={s} />}
      {tab === "gamingpc" && <GamingPcView device={s.gamingPc} />}
    </>
  );
}
