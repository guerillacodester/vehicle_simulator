import React from 'react';
import dynamic from 'next/dynamic';

const RouteSearch = dynamic(() => import('../../components/transit/RouteSearch'), { ssr: false });

export default function RouteSearchPage() {
  return (
    <main style={{ padding: 20 }}>
      <h1>Route & Vehicle Search (Dev)</h1>
      <RouteSearch />
    </main>
  );
}
