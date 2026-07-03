// Thin REST client. All device logic lives in the backend; the front end only
// reads state and issues intent.

import type { Capability } from "./types";

export async function sendCommand(
  deviceId: string,
  command: string,
  params: Record<string, unknown> = {},
): Promise<unknown> {
  const res = await fetch(`/api/devices/${deviceId}/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command, params }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`command failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export async function runScene(
  name: string,
  body: Record<string, unknown> = {},
): Promise<unknown> {
  const res = await fetch(`/api/scenes/${name}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`scene ${name} failed (${res.status})`);
  return res.json();
}

export interface DevicePayload {
  device_id: string;
  state: unknown;
  capabilities: Capability[];
}

export async function fetchDevices(): Promise<DevicePayload[]> {
  const res = await fetch("/api/devices");
  if (!res.ok) return [];
  const data = await res.json();
  return data.devices ?? [];
}
