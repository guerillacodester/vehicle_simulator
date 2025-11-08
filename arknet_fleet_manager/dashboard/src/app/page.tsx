"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { HeroSection, FeatureGrid, FeatureCardData } from "@/components/landing";

const features: FeatureCardData[] = [
  {
    icon: '🚌',
    title: 'Customer Dashboard',
    description: 'Track your bus, search routes, and view live maps as a commuter.',
    href: '/customer',
  },
  {
    icon: '�',
    title: 'Operator Dashboard',
    description: 'Manage fleet vehicles, monitor status, and assign routes as an operator.',
    href: '/operator',
  },
  {
    icon: '🏢',
    title: 'Agency Dashboard',
    description: 'View system-wide KPIs, analytics, and monitor operations as an agency.',
    href: '/agency',
  },
  {
    icon: '🛡️',
    title: 'Admin Dashboard',
    description: 'Access service management, system health, and platform controls as an admin.',
    href: '/admin',
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
