"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { Rajdhani, Inter } from "next/font/google";
import { Settings, Users, Database, Activity } from "lucide-react";

const rajdhani = Rajdhani({ subsets: ["latin"], weight: ["500", "700"] });
const inter = Inter({ subsets: ["latin"], weight: ["400", "500"] });

export default function AdminDashboard() {
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
          Admin Portal
        </h1>
        <nav className="flex gap-6 text-lg font-semibold">
          <Link href="/services" className="hover:text-amber-400 transition font-bold">Services</Link>
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
            System Administration
          </motion.h2>
          <p className={`${inter.className} text-lg md:text-xl text-gray-200 leading-relaxed mb-8`}>
            Manage system configuration, services, users, and monitor overall platform health.
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
              <Activity className="w-12 h-12 text-amber-400 mb-4 mx-auto drop-shadow-[0_0_10px_rgba(255,199,38,0.5)]" />
              <h4 className={`${rajdhani.className} text-xl font-bold mb-2 text-amber-300 text-center`}>
                System Status
              </h4>
              <p className={`${inter.className} text-gray-300 text-center text-3xl font-bold`}>
                Online
              </p>
              <p className={`${inter.className} text-gray-400 text-center text-sm`}>all services operational</p>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
            >
              <Users className="w-12 h-12 text-amber-400 mb-4 mx-auto drop-shadow-[0_0_10px_rgba(255,199,38,0.5)]" />
              <h4 className={`${rajdhani.className} text-xl font-bold mb-2 text-amber-300 text-center`}>
                Active Users
              </h4>
              <p className={`${inter.className} text-gray-300 text-center text-3xl font-bold`}>
                248
              </p>
              <p className={`${inter.className} text-gray-400 text-center text-sm`}>across all tiers</p>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
            >
              <Database className="w-12 h-12 text-amber-400 mb-4 mx-auto drop-shadow-[0_0_10px_rgba(255,199,38,0.5)]" />
              <h4 className={`${rajdhani.className} text-xl font-bold mb-2 text-amber-300 text-center`}>
                Database Health
              </h4>
              <p className={`${inter.className} text-gray-300 text-center text-3xl font-bold`}>
                98%
              </p>
              <p className={`${inter.className} text-gray-400 text-center text-sm`}>uptime this month</p>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
            >
              <Settings className="w-12 h-12 text-amber-400 mb-4 mx-auto drop-shadow-[0_0_10px_rgba(255,199,38,0.5)]" />
              <h4 className={`${rajdhani.className} text-xl font-bold mb-2 text-amber-300 text-center`}>
                Services Running
              </h4>
              <p className={`${inter.className} text-gray-300 text-center text-3xl font-bold`}>
                12/12
              </p>
              <p className={`${inter.className} text-gray-400 text-center text-sm`}>all operational</p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Admin Tools */}
      <section className="py-20 px-6 bg-gradient-to-b from-[#02081a] via-black to-[#02081a] border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <h3 className={`${rajdhani.className} text-3xl md:text-4xl font-bold mb-8 text-amber-300 text-center`}>
            Administration Tools
          </h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            <Link href="/services">
              <motion.div
                whileHover={{ scale: 1.02 }}
                className="p-8 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
              >
                <h4 className={`${rajdhani.className} text-2xl font-bold mb-4 text-amber-300`}>
                  Service Manager
                </h4>
                <p className={`${inter.className} text-gray-300 mb-4`}>
                  Start, stop, and monitor all system services in real-time.
                </p>
                <button className="px-6 py-3 bg-amber-400 text-black font-bold rounded-lg hover:bg-amber-300 transition">
                  Manage Services
                </button>
              </motion.div>
            </Link>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="p-8 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
            >
              <h4 className={`${rajdhani.className} text-2xl font-bold mb-4 text-amber-300`}>
                User Management
              </h4>
              <p className={`${inter.className} text-gray-300 mb-4`}>
                Create, modify, and manage user accounts across all tiers.
              </p>
              <button className="px-6 py-3 bg-amber-400 text-black font-bold rounded-lg hover:bg-amber-300 transition">
                Manage Users
              </button>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="p-8 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
            >
              <h4 className={`${rajdhani.className} text-2xl font-bold mb-4 text-amber-300`}>
                System Configuration
              </h4>
              <p className={`${inter.className} text-gray-300 mb-4`}>
                Configure system settings, environment variables, and integrations.
              </p>
              <button className="px-6 py-3 bg-amber-400 text-black font-bold rounded-lg hover:bg-amber-300 transition">
                Configure System
              </button>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="p-8 bg-[#0b1224]/80 rounded-lg shadow-lg transition hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
            >
              <h4 className={`${rajdhani.className} text-2xl font-bold mb-4 text-amber-300`}>
                Logs & Monitoring
              </h4>
              <p className={`${inter.className} text-gray-300 mb-4`}>
                View system logs, error reports, and performance metrics.
              </p>
              <button className="px-6 py-3 bg-amber-400 text-black font-bold rounded-lg hover:bg-amber-300 transition">
                View Logs
              </button>
            </motion.div>
          </div>
        </div>
      </section>
    </main>
  );
}
