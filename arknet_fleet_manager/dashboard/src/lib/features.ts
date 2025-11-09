import {
  MapPin,
  BarChart3,
  ShieldCheck,
  Users,
  CreditCard,
  Globe,
} from "lucide-react";
import React from "react";

// Define the shape of a feature
export interface Feature {
  slug: string;       // used for navigation, e.g. "gps-tracking"
  title: string;      // short title for cards and detail pages
  tagline?: string;   // optional tagline for hero section
  shortDesc: string;  // short description for landing page cards
  longDesc: string;   // longer description for detail pages
  heroImage?: string; // optional hero image path (from /public)
  icon: React.ComponentType<{ className?: string }>;   // lucide-react icon component
  benefits?: {        // optional audience-specific benefits
    passengers: string[];
    operators: string[];
    government: string[];
  };
  media?: {           // optional media gallery
    images?: string[];
    videos?: string[];
  };
}

// Export an array of features (typed with Feature[])
export const features: Feature[] = [
  {
    slug: "gps-tracking",
    title: "Real-Time GPS Tracking",
    tagline: "Live location for passengers, visibility for operators, oversight for government.",
    shortDesc:
      "Passengers see your ZR van live on the map, reducing wait times and boosting ridership.",
    longDesc:
      "ArkNet Transit provides real-time GPS tracking that allows passengers to see exactly where ZR vans are. This reduces uncertainty, builds trust, and increases ridership while giving operators clear visibility into fleet activity. Government agencies also benefit from accurate data for oversight and planning.",
    heroImage: "/images/features/gps-tracking/hero.jpg",
    icon: MapPin,
    benefits: {
      passengers: [
        "See where vans are in real time",
        "Shorter waiting times",
        "Improved safety and trust",
      ],
      operators: [
        "Better fleet visibility",
        "Higher ridership from improved reliability",
        "Reduced idle time on routes",
      ],
      government: [
        "Accurate data for planning",
        "Better oversight of PSV operations",
        "Supports national transit modernization",
      ],
    },
    media: {
      images: [
        "/images/features/gps-tracking/demo1.jpg",
        "/images/features/gps-tracking/demo2.jpg",
      ],
      videos: ["/videos/features/gps-tracking/demo.mp4"],
    },
  },
  {
    slug: "analytics",
    title: "Route & Profit Analytics",
    shortDesc:
      "Every trip generates data. Heatmaps and reports help maximize earnings and cut wasted trips.",
    longDesc:
      "Our analytics tools turn every trip into actionable insights. Operators can see which routes are most profitable, identify inefficiencies, and plan services more effectively. Data-driven reports also support better long-term investment and government planning.",
    heroImage: "/images/features/analytics/hero.jpg",
    icon: BarChart3,
    media: {
      images: [
        "/images/features/analytics/demo1.jpg",
        "/images/features/analytics/demo2.jpg",
      ],
      videos: ["/videos/features/analytics/demo.mp4"],
    },
  },
  {
    slug: "safety",
    title: "Safety & Incident Protection",
    shortDesc:
      "Panic button, GPS-linked alerts, and incident logs protect both drivers and passengers.",
    longDesc:
      "Safety is at the heart of ArkNet Transit. Features like an integrated panic button, GPS-linked alerts, and digital incident logging provide peace of mind for passengers, operators, and regulators. Incidents are recorded with location data to improve accountability and response times.",
    heroImage: "/images/features/safety/hero.jpg",
    icon: ShieldCheck,
    media: {
      images: [
        "/images/features/safety/demo1.jpg",
        "/images/features/safety/demo2.jpg",
      ],
      videos: ["/videos/features/safety/demo.mp4"],
    },
  },
  {
    slug: "passenger-experience",
    title: "Passenger Experience",
    shortDesc:
      "Ratings, feedback, and live tracking build trust and loyalty across the commuting public.",
    longDesc:
      "Passengers can rate rides, provide feedback, and track vans in real time. This transparency builds trust, improves service quality, and encourages greater use of the transport system. A positive passenger experience leads to higher ridership and stronger operator reputation.",
    heroImage: "/images/features/passenger-experience/hero.jpg",
    icon: Users,
    media: {
      images: [
        "/images/features/passenger-experience/demo1.jpg",
        "/images/features/passenger-experience/demo2.jpg",
      ],
      videos: ["/videos/features/passenger-experience/demo.mp4"],
    },
  },
  {
    slug: "affordability",
    title: "Affordable Adoption",
    shortDesc:
      "Low-cost hardware (US $400) with flexible financing and optional dashboards from $5/month.",
    longDesc:
      "ArkNet Transit is designed to be accessible. The hardware is low-cost at US $400, with financing options available. Optional operator dashboards start at just $5/month, making adoption feasible even for smaller operators. This ensures technology benefits are widely available across Barbados.",
    heroImage: "/images/features/affordability/hero.jpg",
    icon: CreditCard,
    media: {
      images: [
        "/images/features/affordability/demo1.jpg",
        "/images/features/affordability/demo2.jpg",
      ],
      videos: ["/videos/features/affordability/demo.mp4"],
    },
  },
  {
    slug: "barbados-fit",
    title: "Tailored for Barbados",
    shortDesc:
      "Purpose-built for ZR vans and PSV operations, aligned with BIMPay and local transport policy.",
    longDesc:
      "Unlike one-size-fits-all solutions, ArkNet Transit is built specifically for Barbados. It aligns with PSV operations, integrates seamlessly with BIMPay for cashless options, and supports government policy goals. This local fit ensures adoption is smooth, relevant, and impactful.",
    heroImage: "/images/features/barbados-fit/hero.jpg",
    icon: Globe,
    media: {
      images: [
        "/images/features/barbados-fit/demo1.jpg",
        "/images/features/barbados-fit/demo2.jpg",
      ],
      videos: ["/videos/features/barbados-fit/demo.mp4"],
    },
  },
];
