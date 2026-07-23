import { createContext, useCallback, useContext, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, XCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface Toast {
  id: number;
  title: string;
  variant: "success" | "error";
}

const ToastContext = createContext<{ push: (title: string, variant?: Toast["variant"]) => void }>({
  push: () => {},
});

/** Minimal notification system — one context, auto-dismissing toasts. */
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((title: string, variant: Toast["variant"] = "success") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, title, variant }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  }, []);
  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-72 flex-col gap-2">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 12, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.97 }}
              className="pointer-events-auto flex items-center gap-2 rounded-xl border border-border bg-card p-3 text-sm shadow-lg"
            >
              {t.variant === "success" ? (
                <CheckCircle2 className="size-4 shrink-0 text-success" />
              ) : (
                <XCircle className="size-4 shrink-0 text-destructive" />
              )}
              <span className="flex-1">{t.title}</span>
              <button
                aria-label="Dismiss"
                className={cn("rounded-md p-0.5 text-muted-foreground hover:text-foreground")}
                onClick={() => setToasts((x) => x.filter((y) => y.id !== t.id))}
              >
                <X className="size-3.5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
