// Shapes mirror the backend payloads (see backend/app/api/routes.py).

export type Reachability = "online" | "offline" | "unknown";

export interface DeviceState {
  device_id: string;
  reachable: Reachability;
  power: string | null;
  input: string | null;
  extra: Record<string, unknown>;
  updated_at: number;
}

export interface Capability {
  name: string;
  params: Record<string, string[]>;
  description: string;
}

export type StepStatus =
  | "pending"
  | "running"
  | "ok"
  | "sent_unconfirmed"
  | "failed";

export interface StepResult {
  step: string;
  status: StepStatus;
  detail: string;
}

export interface RoutineResult {
  overall: "pending" | "success" | "partial" | "failed";
  steps: StepResult[];
}

export type WsEvent =
  | { type: "snapshot"; state: { devices: Record<string, DeviceState> } }
  | { type: "device"; device_id: string; state: DeviceState }
  | { type: "progress"; scene: string; step: StepResult }
  | { type: "routine"; scene: string; result: RoutineResult };

export type DeviceMap = Record<string, DeviceState>;
