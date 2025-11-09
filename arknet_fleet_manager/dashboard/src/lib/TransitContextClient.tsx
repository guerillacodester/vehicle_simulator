"use client";
import React from "react";
import { getTransitProvider } from "./transitProvider";

import type { TransitDataProvider } from "@transit/TransitDataProvider";

const TransitContext = React.createContext<TransitDataProvider | null>(null);

export function TransitContextProvider({ children }: { children: React.ReactNode }) {
  const provider = React.useMemo(() => getTransitProvider(), []);
  return <TransitContext.Provider value={provider}>{children}</TransitContext.Provider>;
}

export function useTransit() {
  const ctx = React.useContext(TransitContext);
  if (!ctx) throw new Error("useTransit must be used within TransitContextProvider");
  return ctx;
}
