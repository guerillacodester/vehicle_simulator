"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { HeroSection, FeatureGrid, FeatureCardData } from "@/components/landing";

const features: FeatureCardData[] = [
  {
    icon: '⚙️',
    title: 'Service Manager',
    description: 'Start, stop, and monitor all system services including Strapi, GPSCentCom, geospatial services, and the vehicle simulator.',
    href: '/services',
  },
  {
    icon: '🚐',
    title: 'Fleet Monitor',
    description: 'Real-time tracking and monitoring of all vehicles in the fleet with live GPS data and status updates.',
    comingSoon: true,
  },
  {
    icon: '🗺️',
    title: 'Route Management',
    description: 'Configure routes, depots, and geofences. Manage operational zones and optimize logistics planning.',
    comingSoon: true,
  },
  {
    icon: '👥',
    title: 'Commuter Service',
    description: 'Manage passenger requests, bookings, and ride assignments. Monitor commuter service performance metrics.',
    comingSoon: true,
  },
  {
    icon: '📊',
    title: 'Analytics',
    description: 'Comprehensive analytics and reporting for fleet operations, service performance, and system health metrics.',
    comingSoon: true,
  },
  {
    icon: '⚡',
    title: 'System Health',
    description: 'Monitor system resources, API performance, database health, and overall platform status at a glance.',
    comingSoon: true,
  },
];

export default function Home() {
  return (
    <DashboardLayout title="ArkNet Fleet Manager" currentPath="/">
      <HeroSection
        title="Welcome to ArkNet"
        subtitle="Centralized logistics management and service orchestration platform"
      />
      <FeatureGrid features={features} />
    </DashboardLayout>
  );
}
