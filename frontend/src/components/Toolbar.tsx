import type { DeviceMap, Reachability } from "../types";
import { Dot } from "./common";

export interface TabDef {
  key: string;
  label: string;
  device?: string; // if set, the tab only shows when that device is configured
}

export function Toolbar({
  tabs,
  active,
  onSelect,
  devices,
}: {
  tabs: TabDef[];
  active: string;
  onSelect: (key: string) => void;
  devices: DeviceMap;
}) {
  return (
    <nav className="toolbar">
      {tabs.map((t) => {
        const reach = (t.device && devices[t.device]?.reachable) as Reachability | undefined;
        return (
          <button
            key={t.key}
            className={`tool-tab ${t.key === active ? "tool-tab-active" : ""}`}
            onClick={() => onSelect(t.key)}
          >
            {reach && <Dot reach={reach} />}
            <span>{t.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
