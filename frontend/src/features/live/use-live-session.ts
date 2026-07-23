import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { LiveClient, type LiveSource } from "@/lib/api/live";
import type { LiveEnd, LiveState } from "@/schemas";

export type LiveStatus = "idle" | "connecting" | "live" | "ended" | "error";

/** Intrinsic resolution of the streamed video (from decoded frames). */
export interface FrameSize {
  w: number;
  h: number;
}

/**
 * Owns one live workout's connection lifecycle and latest state payload.
 *
 * The page binds a canvas: JPEG frames are painted at full speed while JSON
 * state throttles into React at stream rate. The canvas is laid out with
 * `object-fit: contain`, so whatever resolution the engine streams keeps its
 * aspect ratio with zero stretching or cropping — `frameSize` additionally
 * lets the page reserve exactly matching layout space (any video resolution,
 * portrait or landscape, supported automatically).
 *
 * Also measures wall-clock processing time (start → end) for the completion
 * summary and exposes `reset()` so a finished workout returns the UI to the
 * setup step without any navigation.
 */
export function useLiveSession(exerciseId: string | undefined) {
  const [status, setStatus] = useState<LiveStatus>("idle");
  const [state, setState] = useState<LiveState | null>(null);
  const [result, setResult] = useState<LiveEnd | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [frameSize, setFrameSize] = useState<FrameSize | null>(null);
  const [processingSeconds, setProcessingSeconds] = useState<number | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const clientRef = useRef<LiveClient | null>(null);
  const startedAtRef = useRef<number | null>(null);
  const frameSizeRef = useRef<FrameSize | null>(null);
  const qc = useQueryClient();

  const bindCanvas = useCallback((canvas: HTMLCanvasElement | null) => {
    canvasRef.current = canvas;
  }, []);

  const paint = useCallback(async (blob: Blob) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    try {
      const bmp = await createImageBitmap(blob);
      if (canvas.width !== bmp.width || canvas.height !== bmp.height) {
        canvas.width = bmp.width;
        canvas.height = bmp.height;
      }
      // Publish the frame size once per resolution change; it drives the
      // stage's aspect-ratio so the layout hugs the real video shape.
      const prev = frameSizeRef.current;
      if (!prev || prev.w !== bmp.width || prev.h !== bmp.height) {
        frameSizeRef.current = { w: bmp.width, h: bmp.height };
        setFrameSize({ w: bmp.width, h: bmp.height });
      }
      canvas.getContext("2d")?.drawImage(bmp, 0, 0);
      bmp.close();
    } catch {
      /* undecodable frame: skip it, stream keeps going */
    }
  }, []);

  const start = useCallback(
    (source: LiveSource, video?: string) => {
      if (!exerciseId) return;
      clientRef.current?.disconnect();
      setStatus("connecting");
      setError(null);
      setResult(null);
      setState(null);
      setFrameSize(null);
      frameSizeRef.current = null;
      setProcessingSeconds(null);
      startedAtRef.current = performance.now();
      const client = new LiveClient();
      client.connect(
        exerciseId,
        source,
        {
          onFrame: (blob) => void paint(blob),
          onMessage: (msg) => {
            if (msg.type === "state") {
              setStatus("live");
              setState(msg);
            } else if (msg.type === "end") {
              setStatus("ended");
              setResult(msg);
              if (startedAtRef.current != null) {
                setProcessingSeconds((performance.now() - startedAtRef.current) / 1000);
                startedAtRef.current = null;
              }
              qc.invalidateQueries({ queryKey: ["sessions"] });
            } else {
              setStatus("error");
              setError(msg.message);
            }
          },
          onClose: () => setStatus((s) => (s === "connecting" || s === "live" ? "ended" : s)),
        },
        video,
      );
      clientRef.current = client;
    },
    [exerciseId, paint, qc],
  );

  const stop = useCallback(() => clientRef.current?.stop(), []);

  /** Back to the setup step: drop the connection and every workout artifact. */
  const reset = useCallback(() => {
    clientRef.current?.disconnect();
    clientRef.current = null;
    startedAtRef.current = null;
    frameSizeRef.current = null;
    setStatus("idle");
    setState(null);
    setResult(null);
    setError(null);
    setFrameSize(null);
    setProcessingSeconds(null);
  }, []);

  useEffect(() => () => clientRef.current?.disconnect(), []);

  return {
    status,
    state,
    result,
    error,
    frameSize,
    processingSeconds,
    bindCanvas,
    start,
    stop,
    reset,
  };
}
