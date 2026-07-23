import type { LiveMessage } from "@/schemas";

export type LiveSource = "webcam" | "video";

export interface LiveCallbacks {
  /** One JPEG blob per processed frame (draw onto a canvas). */
  onFrame: (blob: Blob) => void;
  onMessage: (message: LiveMessage) => void;
  onClose: () => void;
}

/**
 * Thin WebSocket client for the live coaching stream.
 *
 * One socket per workout: binary frames carry video, text frames carry
 * metrics — keeping heavy pixels out of the JSON path.
 */
export class LiveClient {
  private ws: WebSocket | null = null;

  connect(exercise: string, source: LiveSource, cb: LiveCallbacks, video?: string) {
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    const params = new URLSearchParams({ exercise, source });
    if (video) params.set("video", video);
    const ws = new WebSocket(`${protocol}://${location.host}/ws/live?${params}`);
    ws.binaryType = "blob";
    ws.onmessage = (event) => {
      if (typeof event.data === "string") {
        cb.onMessage(JSON.parse(event.data) as LiveMessage);
      } else {
        cb.onFrame(event.data as Blob);
      }
    };
    ws.onclose = () => {
      this.ws = null;
      cb.onClose();
    };
    this.ws = ws;
    return ws;
  }

  stop() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: "stop" }));
    }
  }

  disconnect() {
    this.ws?.close();
  }

  get connected() {
    return this.ws !== null;
  }
}
