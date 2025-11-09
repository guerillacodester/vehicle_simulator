"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { Rajdhani, Inter } from "next/font/google";
import { ShieldCheck, FileText, BarChart3, AlertCircle } from "lucide-react";

const rajdhani = Rajdhani({ subsets: ["latin"], weight: ["500", "700"] });
const inter = Inter({ subsets: ["latin"], weight: ["400", "500"] });

export default function AgencyDashboard() {
  return (
    <main className="min-h-screen text-white bg-gradient-to-b from-[#000b2a] via-black to-[#00133f]">
      {/* Fixed Header */}
      <motion.div
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
        className="fixed top-0 w-full z-50 py-4 px-8 bg-[#001a4d]/40 backdrop-blur-md shadow-md flex items-center justify-between"
      >
        <Link href="/" className="flex items-center mr-4 md:mr-10">
          <Image
            src="/arknetlogo.png"
            alt="Arknet Logo"
            width={80}
            height={80}
            className="rounded-md drop-shadow-[0_0_18px_rgba(255,199,38,0.7)]"
          />
        </Link>
        <h1 className={`${rajdhani.className} text-3xl md:text-5xl font-extrabold text-white tracking-widest text-center flex-1 [text-shadow:_0_0_12px_rgba(255,199,38,0.75),_0_0_28px_rgba(0,38,127,0.55)]`}>
          Agency Portal
        </h1>
        <nav className="hidden md:flex gap-6 text-lg font-semibold">
          <Link href="/" className="hover:text-amber-400 transition">Home</Link>
          <button className="hover:text-amber-400 transition">Logout</button>
        </nav>
      </motion.div>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className={`${rajdhani.className} text-4xl md:text-6xl font-bold mb-6 text-amber-400`}
          >
            Government Oversight
          </motion.h2>
          <p className={`${inter.className} text-lg md:text-xl text-gray-200 leading-relaxed mb-8`}>
            Monitor compliance, track system-wide performance, and access detailed analytics for policy planning.
          </p>
        </div>
      </section>

      {/* Quick Stats */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <h3 className={`${rajdhani.className} text-3xl md:text-4xl font-bold mb-8 text-amber-300 text-center`}>
            System Overview
          </h3>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
            >
              <ShieldCheck className="w-12 h-12 text-amber-400 mb-4 mx-auto drop-shadow-[0_0_10px_rgba(255,199,38,0.5)]" />
              <h4 className={`${rajdhani.className} text-xl font-bold mb-2 text-amber-300 text-center`}>
                Compliance Rate
              </h4>
              <p className={`${inter.className} text-gray-300 text-center text-3xl font-bold`}>
                94%
              </p>
              <p className={`${inter.className} text-gray-400 text-center text-sm`}>operators compliant</p>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
            >
              <BarChart3 className="w-12 h-12 text-amber-400 mb-4 mx-auto drop-shadow-[0_0_10px_rgba(255,199,38,0.5)]" />
              <h4 className={`${rajdhani.className} text-xl font-bold mb-2 text-amber-300 text-center`}>
                Active Routes
              </h4>
              <p className={`${inter.className} text-gray-300 text-center text-3xl font-bold`}>
                38
              </p>
              <p className={`${inter.className} text-gray-400 text-center text-sm`}>routes monitored</p>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
            >
              <FileText className="w-12 h-12 text-amber-400 mb-4 mx-auto drop-shadow-[0_0_10px_rgba(255,199,38,0.5)]" />
              <h4 className={`${rajdhani.className} text-xl font-bold mb-2 text-amber-300 text-center`}>
                Reports Generated
              </h4>
              <p className={`${inter.className} text-gray-300 text-center text-3xl font-bold`}>
                156
              </p>
              <p className={`${inter.className} text-gray-400 text-center text-sm`}>this month</p>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
            >
              <AlertCircle className="w-12 h-12 text-amber-400 mb-4 mx-auto drop-shadow-[0_0_10px_rgba(255,199,38,0.5)]" />
              <h4 className={`${rajdhani.className} text-xl font-bold mb-2 text-amber-300 text-center`}>
                Active Alerts
              </h4>
              <p className={`${inter.className} text-gray-300 text-center text-3xl font-bold`}>
                3
              </p>
              <p className={`${inter.className} text-gray-400 text-center text-sm`}>requiring attention</p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Recent Activity */}
      <section className="py-20 px-6 bg-gradient-to-b from-[#02081a] via-black to-[#02081a] border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <h3 className={`${rajdhani.className} text-3xl md:text-4xl font-bold mb-8 text-amber-300 text-center`}>
            Recent Activity
          </h3>
          <div className="bg-[#0b1224]/80 rounded-lg p-8 shadow-lg">
            <p className={`${inter.className} text-gray-400 text-center`}>
              Detailed oversight and compliance monitoring dashboard coming soon.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}