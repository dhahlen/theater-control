export type Room = "theater" | "poolhouse";

// Additive room selector. The theater is the default room; Pool House is a
// Phase 2 preview that reuses the adapter and orchestration layers with a
// different device set (see docs/usecases/pool-house.md).
const ROOMS: { key: Room; label: string }[] = [
  { key: "theater", label: "Theater" },
  { key: "poolhouse", label: "Pool House" },
];

export function RoomSwitcher({ room, onSelect }: { room: Room; onSelect: (r: Room) => void }) {
  return (
    <div className="room-switcher" role="tablist" aria-label="Room">
      {ROOMS.map((r) => (
        <button
          key={r.key}
          role="tab"
          aria-selected={room === r.key}
          className={`room-tab ${room === r.key ? "room-tab-active" : ""}`}
          onClick={() => onSelect(r.key)}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}
