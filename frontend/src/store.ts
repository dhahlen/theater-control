// Live state store fed by the WebSocket, with REST snapshot as the initial load
// and automatic reconnect. Exposes device state and per-scene progress.

import { useEffect, useRef, useState, useCallback } from "react";
import type { DeviceMap, StepResult, WsEvent } from "./types";

export interface SceneProgress {
  running: boolean;
  overall: string | null;
  steps: StepResult[];
}

export interface Store {
  devices: DeviceMap;
  connected: boolean;
  progress: Record<string, SceneProgress>;
  markSceneStarted: (scene: string) => void;
}

function wsUrl(): string {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}/ws`;
}

export function useStore(): Store {
  const [devices, setDevices] = useState<DeviceMap>({});
  const [connected, setConnected] = useState(false);
  const [progress, setProgress] = useState<Record<string, SceneProgress>>({});
  const wsRef = useRef<WebSocket | null>(null);

  const markSceneStarted = useCallback((scene: string) => {
    setProgress((p) => ({ ...p, [scene]: { running: true, overall: null, steps: [] } }));
  }, []);

  useEffect(() => {
    let closed = false;
    let retry: ReturnType<typeof setTimeout>;

    const connect = () => {
      const ws = new WebSocket(wsUrl());
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!closed) retry = setTimeout(connect, 2000);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data) as WsEvent;
        if (msg.type === "snapshot") {
          setDevices(msg.state.devices ?? {});
        } else if (msg.type === "device") {
          setDevices((d) => ({ ...d, [msg.device_id]: msg.state }));
        } else if (msg.type === "progress") {
          setProgress((p) => {
            const cur = p[msg.scene] ?? { running: true, overall: null, steps: [] };
            const steps = cur.steps.filter((s) => s.step !== msg.step.step);
            steps.push(msg.step);
            return { ...p, [msg.scene]: { ...cur, running: true, steps } };
          });
        } else if (msg.type === "routine") {
          setProgress((p) => {
            const cur = p[msg.scene] ?? { running: false, overall: null, steps: [] };
            return {
              ...p,
              [msg.scene]: { ...cur, running: false, overall: msg.result.overall },
            };
          });
        }
      };
    };

    connect();
    return () => {
      closed = true;
      clearTimeout(retry);
      wsRef.current?.close();
    };
  }, []);

  return { devices, connected, progress, markSceneStarted };
}
