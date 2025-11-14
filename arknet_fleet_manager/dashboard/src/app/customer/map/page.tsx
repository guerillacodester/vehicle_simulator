"use client";

import Link from "next/link";
import { Rajdhani } from "next/font/google";
import dynamic from "next/dynamic";

const rajdhani = Rajdhani({ subsets: ["latin"], weight: ["500", "700"] });

// Dynamically import LeafletMapClient to avoid SSR issues
const LeafletMapClient = dynamic(
  () => import("../../../components/map/LeafletMapClient"),
  { ssr: false }
);

export default function FullscreenMapPage() {
  return (
    <div className="fixed inset-0 bg-[#02081a] flex flex-col">
      {/* Header bar */}
      <header className="flex items-center justify-between px-6 py-4 bg-[#021028]/80 backdrop-blur-md border-b border-white/10 z-50">
        <h1 className={`${rajdhani.className} text-2xl font-bold text-amber-300`}>
          Live Transit Map
        </h1>
        
        <Link
          href="/customer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg transition-all duration-200 text-white"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
          <span className="text-sm font-medium">Close</span>
        </Link>
      </header>

      {/* Fullscreen map */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <LeafletMapClient height="calc(100vh - 73px)" />
      </div>
    </div>
  );
}
