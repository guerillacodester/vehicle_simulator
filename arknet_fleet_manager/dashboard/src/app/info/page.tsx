"use client";

import Image from "next/image";
import { motion, useAnimation } from "framer-motion";
import { Rajdhani, Inter } from "next/font/google";
import { features } from "@/lib/features";
import Link from "next/link";
import { useEffect, useRef } from "react";

const rajdhani = Rajdhani({ subsets: ["latin"], weight: ["500", "700"] });
const inter = Inter({ subsets: ["latin"], weight: ["400", "500"] });

export default function Home() {

  const jiggle = useAnimation();
  const jiggleRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const AMP = 1.8;        // shake amplitude (px). Try 2–3 if you want stronger.
    const DUR = 0.12;       // per-step duration (s)
    const INT = 120;        // interval between steps (ms)

    const tick = () => {
      // ensure motion element mounted before starting controls
      if (!jiggleRef.current) return;
      const x = (Math.random() * 2 - 1) * AMP; // -AMP .. +AMP
      const y = (Math.random() * 2 - 1) * AMP;
      jiggle.start({ x, y, transition: { duration: DUR, ease: "easeInOut" } }).catch(() => {});
    };

    const id = setInterval(tick, INT);
    return () => clearInterval(id);
  }, [jiggle]);


  return (
    <main id="top" className="min-h-screen text-white bg-gradient-to-b from-[#000b2a] via-black to-[#00133f]">
      {/* Transparent Fixed Banner */}
      <motion.div
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
        className="fixed top-0 w-full z-50 py-4 px-8
          bg-[#001a4d]/40 backdrop-blur-md shadow-md flex items-center justify-between"
      >
        {/* Logo pinned left */}
        <div className="flex items-center  mr-4 md:mr-10">
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

        {/* Title centered with blue/gold glow */}
        <h1
          className={`${rajdhani.className} text-5xl md:text-7xl font-extrabold 
            text-white tracking-widest text-center flex-1
            [text-shadow:_0_0_12px_rgba(255,199,38,0.75),_0_0_28px_rgba(0,38,127,0.55)]`}
        >
          <div className="relative flex-1 flex justify-left">
            {/* Motion lines behind */}
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
                transition={{
                  duration: 5,
                  repeat: Infinity,
                  ease: "linear",
                  delay: 1,
                }}
                className="absolute top-1/3 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-amber-200 to-transparent opacity-20"
              />
            </div>

            {/* Main title */}
            {/* Title — keep skew, only shake the inner node */}
            {/* Title — keep skew; random shake on inner element */}
            <div className="relative z-10 inline-block skew-x-10">
              <motion.h1
                initial={{ x: 0, y: 0 }}
                animate={jiggle}
                ref={jiggleRef}
                className={`${rajdhani.className} text-5xl md:text-7xl font-extrabold 
                text-white tracking-widest drop-shadow-[0_0_12px_rgba(255,199,38,0.4)]`}
                style={{ willChange: "transform" }}
              >
                ArkNet Transit
              </motion.h1>
            </div>
          </div>
        </h1>

        {/* Navigation Links */}
        <nav className="hidden md:flex gap-6 text-lg font-semibold">
          <a href="#features" className="hover:text-amber-400 transition">Features</a>
          <a href="#about" className="hover:text-amber-400 transition">About</a>
          <a href="#pricing" className="hover:text-amber-400 transition">Pricing</a>
          <a href="#contact" className="hover:text-amber-400 transition">Contact</a>
        </nav>
      </motion.div>

      {/* Hero Section */}
      <section className="relative h-screen flex flex-col items-center justify-center text-center px-6 overflow-hidden pt-20">
        <Image
          src="/zrvan.jpg"
          alt="ZR Van"
          fill
          priority
          className="object-cover opacity-30"
        />

        <div className="relative z-10 max-w-5xl w-full">
          <motion.h2
            initial={{ filter: "brightness(1.15)", scale: 1 }}
            animate={{
              filter: [
                "brightness(1.30)",
                "brightness(0.90)",
                "brightness(1.30)",
              ],
              scale: [1, 1.02, 1],
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              repeatType: "mirror",
              ease: "easeInOut",
            }}
            className={`${rajdhani.className} text-4xl md:text-5xl font-bold mt-10 mb-6 
              text-amber-400 drop-shadow-[0_0_12px_rgba(255,199,38,0.65)]`}
          >
            Smarter Travel for Barbados
          </motion.h2>

          <p className={`${inter.className} text-lg md:text-xl text-gray-200 mb-8`}>
            Real-time rides, safer trips, smarter journeys. <br />
            Connecting passengers, operators, and government in one trusted
            system.
          </p>

          <div className="flex gap-4 justify-center">
            <a
              href="#features"
              className="relative inline-block px-6 py-3 font-bold rounded-lg 
                bg-amber-200 text-black overflow-hidden hover:bg-amber-300 transition"
            >
              <span className="relative">Learn More</span>
            </a>
            <a
              href="#contact"
              className="relative inline-block px-6 py-3 font-bold rounded-lg 
                border border-amber-200 text-amber-200 hover:text-black 
                hover:bg-amber-300 transition"
            >
              Request Quote
            </a>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="pt-12 pb-14 px-6">
        <h2
          className={`${rajdhani.className} text-4xl md:text-5xl font-bold text-center mb-16`}
        >
          Why Operators and Riders Trust ArkNet
        </h2>

        <div className="grid md:grid-cols-3 gap-12 max-w-6xl mx-auto">
          {features.map((feature, i) => (
            <Link key={i} href={`/features/${feature.slug}`}>
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg transition 
        hover:shadow-amber-400/30 hover:shadow-xl cursor-pointer"
              >
                <feature.icon className="w-12 h-12 text-amber-400 mb-4 drop-shadow-[0_0_10px_rgba(255,199,38,0.5)]" />
                <h3
                  className={`${rajdhani.className} text-2xl font-bold mb-2 text-amber-300`}
                >
                  {feature.title}
                </h3>
                <p className={`${inter.className} text-gray-300`}>
                  {feature.shortDesc}
                </p>
              </motion.div>
            </Link>
          ))}
        </div>
      </section>

      {/* About / Mission Section */}
      <section id="about" className="py-28 px-6 lg:px-12 bg-gradient-to-b from-[#02081a] via-black to-[#02081a] border-t border-white/5">
        <h2 className={`${rajdhani.className} text-4xl md:text-5xl font-bold text-center mb-6`}>
          Our Mission
        </h2>

        <p className={`${inter.className} max-w-4xl mx-auto text-center text-gray-200`}>
          ArkNet Global delivers a practical, data-driven transit platform tailored to Barbados.
          We connect passengers, operators, and government with real-time visibility, safety,
          and measurable improvements in service quality and efficiency.
        </p>

        <div className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto mt-12">
          {/* Passengers */}
          <div className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg">
            <h3 className={`${rajdhani.className} text-2xl font-bold text-amber-300 mb-2`}>Passengers</h3>
            <ul className={`${inter.className} space-y-2 text-gray-300 list-disc list-inside`}>
              <li>Live vehicle location & shorter waits</li>
              <li>Transparent ratings & feedback</li>
              <li>Safer, more reliable journeys</li>
            </ul>
          </div>

          {/* Operators */}
          <div className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg">
            <h3 className={`${rajdhani.className} text-2xl font-bold text-amber-300 mb-2`}>Operators</h3>
            <ul className={`${inter.className} space-y-2 text-gray-300 list-disc list-inside`}>
              <li>Fleet visibility & route profitability</li>
              <li>Reduced idle time & improved utilization</li>
              <li>Low-cost adoption with scalable tools</li>
            </ul>
          </div>

          {/* Government */}
          <div className="p-6 bg-[#0b1224]/80 rounded-lg shadow-lg">
            <h3 className={`${rajdhani.className} text-2xl font-bold text-amber-300 mb-2`}>Government</h3>
            <ul className={`${inter.className} space-y-2 text-gray-300 list-disc list-inside`}>
              <li>Accurate, privacy-respecting oversight data</li>
              <li>Policy alignment & modernization support</li>
              <li>Evidence-based planning & reporting</li>
            </ul>
          </div>
        </div>
      </section>

{/* Pricing / Adoption Model */}
<section
  id="pricing"
  className="py-28 px-6 lg:px-12 bg-gradient-to-b from-[#00133f] via-black to-[#00133f] border-t border-white/5"
>
  <h2 className={`${rajdhani.className} text-4xl md:text-5xl font-bold text-center mb-4`}>
    Pricing & Adoption
  </h2>
  <p className={`${inter.className} max-w-5xl mx-auto text-center text-gray-200`}>
    Start lean and scale as needed. Hardware is a one-time cost. Dashboards are subscription-based.
  </p>

  <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto mt-12">

    {/* Hardware Device */}
    <div className="p-8 bg-[#0b1224]/80 rounded-lg shadow-lg h-full flex flex-col">
      <h3 className={`${rajdhani.className} text-2xl font-bold text-amber-300 mb-2`}>
        GPS Tracking Hardware Device
      </h3>
      <p className={`${inter.className} text-4xl font-extrabold text-amber-200 mb-4`}>
        BDS $400<span className="text-base font-semibold text-gray-300"> one-time</span>
      </p>
      <ul className={`${inter.className} text-gray-300 space-y-2 list-disc list-inside flex-1`}>
        <li>GPS + telemetry capture</li>
        <li>Fast install, low power</li>
        <li>Warranty & updates</li>
      </ul>
      <a href="#contact" className="mt-6 inline-block text-center w-full py-3 font-bold rounded-lg bg-amber-200 text-black hover:bg-amber-300 transition">
        Request Device
      </a>
    </div>

    {/* Operator Dashboard Kiosk */}
    <div className="p-8 bg-[#0b1224]/80 rounded-lg shadow-lg h-full flex flex-col">
      <h3 className={`${rajdhani.className} text-2xl font-bold text-amber-300 mb-2`}>
        Operator Dashboard Kiosk (opt.)
      </h3>
      <p className={`${inter.className} text-4xl font-extrabold text-amber-200 mb-4`}>
        BDS $25<span className="text-base font-semibold text-gray-300">/mo</span>
      </p>
      <ul className={`${inter.className} text-gray-300 space-y-2 list-disc list-inside flex-1`}>
        <li>Real-time fleet view</li>
        <li>Basic reports & exports</li>
        <li>Email support</li>
      </ul>
      <a href="#contact" className="mt-6 inline-block text-center w-full py-3 font-bold rounded-lg border border-amber-200 text-amber-200 hover:text-black hover:bg-amber-300 transition">
        Get Dashboard
      </a>
    </div>



    {/* Pilot / Custom */}
    <div className="p-8 bg-[#0b1224]/80 rounded-lg shadow-lg h-full flex flex-col">
      <h3 className={`${rajdhani.className} text-2xl font-bold text-amber-300 mb-2`}>
        Pilot / Custom / Addons
      </h3>
      <p className={`${inter.className} text-4xl font-extrabold text-amber-200 mb-4`}>
        POA<span className="text-base font-semibold text-gray-300"> (on request)</span>
      </p>
      <ul className={`${inter.className} text-gray-300 space-y-2 list-disc list-inside flex-1`}>
        <li>Route trials & onboarding</li>
        <li>Advanced analytics & SLAs</li>
        <li>Integration support</li>
      </ul>
      <a href="#contact" className="mt-6 inline-block text-center w-full py-3 font-bold rounded-lg border border-amber-200 text-amber-200 hover:text-black hover:bg-amber-300 transition">
        Discuss a Pilot
      </a>
    </div>
  </div>

  <p className={`${inter.className} text-sm text-gray-400 text-center mt-6`}>
    Prices indicative; taxes, shipping, and connectivity not included.
  </p>
</section>

      {/* Contact Section */}
      <section
        id="contact"
        className="py-24 px-6 bg-gradient-to-r from-[#001a4d] via-black to-[#001a4d]"
      >
        <h2
          className={`${rajdhani.className} text-4xl md:text-5xl font-bold text-center mb-12`}
        >
          Get in Touch
        </h2>
        <form className="max-w-2xl mx-auto space-y-6">
          <input
            type="text"
            name="name"
            placeholder="Your Name"
            required
            className="w-full p-4 rounded-lg bg-[#0b1224] text-white placeholder-gray-400 
              focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
          <input
            type="email"
            name="email"
            placeholder="Your Email"
            required
            className="w-full p-4 rounded-lg bg-[#0b1224] text-white placeholder-gray-400 
              focus:outline-none focus:ring-2 focus:ring-amber-400"
          />
          <textarea
            name="message"
            placeholder="Your Message"
            rows={5}
            required
            className="w-full p-4 rounded-lg bg-[#0b1224] text-white placeholder-gray-400 
              focus:outline-none focus:ring-2 focus:ring-amber-400"
          ></textarea>
          <button
            type="submit"
            className="w-full py-4 px-6 bg-amber-200 text-black font-bold rounded-lg 
              hover:bg-amber-300 transition"
          >
            Send Message
          </button>
        </form>
      </section>
    </main>
  );
}
