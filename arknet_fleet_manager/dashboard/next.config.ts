import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  // Disable Turbopack due to internal errors - use webpack instead
  // turbopack: {
  //   root: ".",
  // },
};

export default nextConfig;
