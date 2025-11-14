"use client";

import Image from "next/image";
import Link from "next/link";
import { motion, useAnimation } from "framer-motion";
import { Rajdhani, Inter } from "next/font/google";
import { Users, Building2, ShieldCheck, Settings } from "lucide-react";
import { useEffect, useRef } from "react";

const rajdhani = Rajdhani({ subsets: ["latin"], weight: ["500", "700"] });
const inter = Inter({ subsets: ["latin"], weight: ["400", "500"] });

const userTiers = [
  {
    title: "Customer Portal",
    description: "Track ZR vans, manage trips, and pay seamlessly",
    icon: Users,
    href: "/customer",
    color: "from-blue-500 to-cyan-500",
    features: ["Live tracking", "Trip history", "Digital payments", "Rate rides"]
  },
  {
    title: "Operator Portal",
    description: "Manage your fleet, optimize routes, maximize profits",
    icon: Building2,
    href: "/operator",
    color: "from-amber-500 to-orange-500",
    features: ["Fleet management", "Route analytics", "Revenue tracking", "Driver monitoring"]
  },
  {
    title: "Agency Portal",
    description: "Government oversight, compliance, and policy management",
    icon: ShieldCheck,
    href: "/agency",
    color: "from-green-500 to-emerald-500",
    features: ["System oversight", "Compliance monitoring", "Policy reports", "Analytics"]
  },
  {
    title: "Admin Portal",
    description: "System configuration and service management",
    icon: Settings,
    href: "/admin",
    color: "from-purple-500 to-pink-500",
    features: ["Service control", "User management", "System config", "Monitoring"]
  }
];

export default function Home() {
  const jiggle = useAnimation();
  const jiggleRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const AMP = 1.8;
    const DUR = 0.12;
    const INT = 120;

    let intervalId: NodeJS.Timeout;
    let mounted = true;

      const startTimer = setTimeout(() => {
      if (!mounted) return;
      
      const tick = () => {
        if (!mounted) return;
        // ensure the animated element is mounted in the DOM before starting animation
        if (!jiggleRef.current) return;
        const x = (Math.random() * 2 - 1) * AMP;
        const y = (Math.random() * 2 - 1) * AMP;
        jiggle.start({ x, y, transition: { duration: DUR, ease: "easeInOut" } }).catch(() => {
          // Ignore animation errors if component unmounted or controls not ready
        });
      };

      intervalId = setInterval(tick, INT);
    }, 500); // Increased delay to ensure mount

    return () => {
      mounted = false;
      clearTimeout(startTimer);
      if (intervalId) clearInterval(intervalId);
    };
  }, [jiggle]);

  return (
    <main id="top" className="min-h-screen text-white bg-gradient-to-b from-[#000b2a] via-black to-[#00133f]">
      {/* Fixed Header */}
      <motion.div
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
        className="fixed top-0 w-full z-50 py-4 px-8 bg-[#001a4d]/40 backdrop-blur-md shadow-md flex items-center justify-between"
      >
        <div className="flex items-center mr-4 md:mr-10">
          <a href="#top" aria-label="Back to top">
            <Image
              src="/arknetlogo.png"
              alt="Arknet Logo"
              width={96}
              height={96}
              className="rounded-md drop-shadow-[0_0_18px_rgba(255,199,38,0.7)]"
            />
          </a>
        </div>

        <h1
          className={`${rajdhani.className} text-5xl md:text-7xl font-extrabold text-white tracking-widest text-center flex-1 [text-shadow:_0_0_12px_rgba(255,199,38,0.75),_0_0_28px_rgba(0,38,127,0.55)]`}
        >
          <div className="relative flex justify-left">
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <motion.div
                animate={{ x: ["-100%", "100%"] }}
                transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                className="absolute top-1/2 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-amber-400 to-transparent opacity-40"
              />
              <motion.div
                animate={{ x: ["100%", "-100%"] }}
                transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
                className="absolute top-2/3 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-400 to-transparent opacity-30"
              />
              <motion.div
                animate={{ x: ["-100%", "100%"] }}
                transition={{ duration: 5, repeat: Infinity, ease: "linear", delay: 1 }}
                className="absolute top-1/3 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-amber-200 to-transparent opacity-20"
              />
            </div>

            <div className="relative z-10 inline-block skew-x-10">
              <motion.h1
                initial={{ x: 0, y: 0 }}
                animate={jiggle}
                ref={jiggleRef}
                className={`${rajdhani.className} text-5xl md:text-7xl font-extrabold text-white tracking-widest drop-shadow-[0_0_12px_rgba(255,199,38,0.4)]`}
                style={{ willChange: "transform" }}
              >
                ArkNet Transit
              </motion.h1>
            </div>
          </div>
        </h1>

        <nav className="hidden md:flex gap-6 text-lg font-semibold">
          <Link href="/info" className="hover:text-amber-400 transition">About</Link>
          <Link href="/info#pricing" className="hover:text-amber-400 transition">Pricing</Link>
          <Link href="/info#contact" className="hover:text-amber-400 transition">Contact</Link>
        </nav>
      </motion.div>

      {/* Hero Section with Cards */}
      <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-6 py-32 overflow-hidden">
        <Image
          src="/zrvan.jpg"
          alt="ZR Van"
          fill
          priority
          className="object-cover opacity-20"
        />

        <div className="relative z-10 max-w-7xl w-full">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className={`${rajdhani.className} text-5xl md:text-7xl font-bold mb-4 text-amber-400 drop-shadow-[0_0_30px_rgba(255,199,38,0.6)]`}
          >
            Choose Your Portal
          </motion.h2>

          <p className={`${inter.className} text-xl md:text-2xl text-gray-100 mb-12 drop-shadow-lg`}>
            Select your role to access the appropriate dashboard
          </p>

          {/* 4-Tier Selector Cards - Glassmorphism */}
          <div className="grid md:grid-cols-2 gap-6 lg:gap-8 mt-12">
            {userTiers.map((tier, index) => (
              <Link key={index} href={tier.href}>
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.2 + index * 0.1 }}
                  whileHover={{ scale: 1.03, y: -8 }}
                  className="relative p-6 lg:p-8 bg-gradient-to-br from-[#0b1224]/80 via-[#1a1410]/70 to-[#0b1224]/80 backdrop-blur-lg rounded-2xl shadow-2xl border border-amber-400/20 transition hover:shadow-amber-400/40 hover:shadow-2xl hover:border-amber-400/60 cursor-pointer overflow-hidden group"
                >
                  {/* Gradient overlay */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${tier.color} opacity-0 group-hover:opacity-15 transition-opacity duration-300`}></div>

                  <div className="relative z-10">
                    <tier.icon className="w-12 h-12 lg:w-14 lg:h-14 text-amber-400 mb-3 drop-shadow-[0_0_20px_rgba(255,199,38,0.7)]" />
                    
                    <h3 className={`${rajdhani.className} text-2xl lg:text-3xl font-bold mb-2 text-amber-300 drop-shadow-lg`}>
                      {tier.title}
                    </h3>
                    
                    <p className={`${inter.className} text-gray-100 mb-4 text-sm lg:text-base`}>
                      {tier.description}
                    </p>

                    <ul className={`${inter.className} space-y-1.5 text-gray-200 text-sm`}>
                      {tier.features.map((feature, i) => (
                        <li key={i} className="flex items-center">
                          <span className="text-amber-400 mr-2">✓</span>
                          {feature}
                        </li>
                      ))}
                    </ul>

                    <div className="mt-5 inline-block px-5 py-2.5 bg-amber-400 text-black font-bold rounded-lg group-hover:bg-amber-300 transition shadow-lg">
                      Access Portal →
                    </div>
                  </div>
                </motion.div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Info Link Section */}
      <section className="py-20 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          <h3 className={`${rajdhani.className} text-3xl md:text-4xl font-bold mb-6 text-white`}>
            Want to Learn More?
          </h3>
          <p className={`${inter.className} text-lg text-gray-300 mb-8`}>
            Explore our features, pricing, and business model
          </p>
          <Link
            href="/info"
            className="inline-block px-8 py-4 bg-amber-200 text-black font-bold rounded-lg hover:bg-amber-300 transition"
          >
            View Detailed Information
          </Link>
        </div>
      </section>
    </main>
  );
}
