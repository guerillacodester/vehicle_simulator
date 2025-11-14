"use client";

import { features, Feature } from "@/lib/features";
import { notFound } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { useParams } from "next/navigation";

export default function FeaturePage() {
  // Get slug from the route params
  const params = useParams();
  const slug = params?.slug as string;

  // Find the feature in our list
  const feature: Feature | undefined = features.find(
    (f) => f.slug === slug
  );

  if (!feature) {
    return notFound();
  }

  // Find index and determine previous/next features
  const currentIndex = features.findIndex((f) => f.slug === slug);
  const prevFeature = currentIndex > 0 ? features[currentIndex - 1] : null;
  const nextFeature =
    currentIndex < features.length - 1 ? features[currentIndex + 1] : null;

  return (
    <main className="min-h-screen bg-gradient-to-b from-[#000b2a] via-black to-[#00133f] text-white">
      {/* Fixed Header */}
      <motion.div
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
        className="fixed top-0 w-full z-50 py-4 px-8
          bg-[#001a4d]/40 backdrop-blur-md shadow-md flex items-center justify-between"
      >
        {/* Logo links back to home */}
        <Link href="/" className="flex items-center">
          <Image
            src="/arknetlogo.png"
            alt="Arknet Logo"
            width={64}
            height={64}
            className="rounded-md drop-shadow-[0_0_12px_rgba(255,199,38,0.7)]"
          />
        </Link>

        {/* Current feature title */}
        <h1 className="text-xl font-bold text-white">{feature.title}</h1>

        {/* Back link */}
        <Link href="/" className="text-amber-400 underline">
          ← Back to Home
        </Link>
      </motion.div>

      {/* Page Content */}
      <div className="pt-24 max-w-3xl mx-auto px-6">
        {/* Hero Section */}
        {feature.heroImage && (
          <div className="mb-8">
            <Image
              src={feature.heroImage}
              alt={feature.title}
              width={1200}
              height={600}
              className="rounded-lg shadow-lg object-cover"
            />
          </div>
        )}

        {feature.tagline && (
          <p className="text-xl text-amber-400 font-semibold mb-6">
            {feature.tagline}
          </p>
        )}

        {/* Feature Title & Long Description */}
        <h2 className="text-3xl font-bold mb-4">{feature.title}</h2>
        <p className="text-gray-300 mb-8">{feature.longDesc}</p>

        {/* Audience-Specific Benefits */}
        {feature.benefits && (
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            {/* Passengers */}
            <div className="bg-[#0b1224]/80 p-4 rounded-lg shadow-lg">
              <h3 className="text-amber-300 font-bold mb-2">Passengers</h3>
              <ul className="list-disc list-inside text-gray-300">
                {feature.benefits.passengers.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>

            {/* Operators */}
            <div className="bg-[#0b1224]/80 p-4 rounded-lg shadow-lg">
              <h3 className="text-amber-300 font-bold mb-2">Operators</h3>
              <ul className="list-disc list-inside text-gray-300">
                {feature.benefits.operators.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>

            {/* Government */}
            <div className="bg-[#0b1224]/80 p-4 rounded-lg shadow-lg">
              <h3 className="text-amber-300 font-bold mb-2">Government</h3>
              <ul className="list-disc list-inside text-gray-300">
                {feature.benefits.government.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Media Gallery */}
        {feature.media && (feature.media.images || feature.media.videos) && (
          <div className="mb-12">
            <h3 className="text-amber-300 font-bold text-2xl mb-4">Gallery</h3>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Images */}
              {feature.media.images &&
                feature.media.images.map((src, i) => (
                  <div key={i} className="rounded-lg overflow-hidden shadow-lg">
                    <Image
                      src={src}
                      alt={`${feature.title} image ${i + 1}`}
                      width={600}
                      height={400}
                      className="object-cover w-full h-auto"
                    />
                  </div>
                ))}

              {/* Videos or Placeholder */}
              {feature.media.videos && feature.media.videos.length > 0 ? (
                feature.media.videos.map((src, i) => (
                  <div
                    key={i}
                    className="rounded-lg overflow-hidden shadow-lg"
                  >
                    <video
                      autoPlay
                      loop
                      muted
                      playsInline
                      className="w-full rounded-lg shadow-lg"
                    >
                      <source src={src} type="video/mp4" />
                      Your browser does not support the video tag.
                    </video>
                  </div>
                ))
              ) : feature.slug === "gps-tracking" ? (
                <div className="flex items-center justify-center bg-[#0b1224]/80 h-64 rounded-lg shadow-lg text-gray-400">
                  <p>🚐 GPS Demo Animation Placeholder (looped map with vans)</p>
                </div>
              ) : null}
            </div>
          </div>
        )}

        {/* Placeholder content box */}
        <div className="bg-[#0b1224]/80 p-6 rounded-lg shadow-lg">
          <p>
            This is the detail page for <strong>{feature.title}</strong>.  
            Later, we’ll expand this with media galleries, demo videos,
            and additional resources.
          </p>
        </div>

        {/* Next/Previous Navigation */}
        <div className="flex justify-between mt-12">
          {prevFeature ? (
            <Link
              href={`/features/${prevFeature.slug}`}
              className="text-amber-400 hover:underline"
            >
              ← {prevFeature.title}
            </Link>
          ) : (
            <div />
          )}

          {nextFeature ? (
            <Link
              href={`/features/${nextFeature.slug}`}
              className="text-amber-400 hover:underline"
            >
              {nextFeature.title} →
            </Link>
          ) : (
            <div />
          )}
        </div>
      </div>
    </main>
  );
}
