'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function AuthTestValidPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Logging in...');
  const [details, setDetails] = useState<{ user?: { username?: string }; error?: string } | null>(null);
  const router = useRouter();

  useEffect(() => {
    async function login() {
      try {
        setStatus('loading');
        setMessage('Sending login request...');

        const response = await fetch('http://localhost:7000/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            username: 'fleet_manager',
            password: 'Ga25w123'
          })
        });

        if (response.ok) {
          const data = await response.json();
          setStatus('success');
          setMessage('✓ Login successful!');
          setDetails(data);

          setTimeout(() => {
            router.push('/telemetry-wall-demo');
          }, 2000);
        } else {
          const errorText = await response.text();
          setStatus('error');
          setMessage('✗ Login failed');
          setDetails({ error: `${response.status} - ${errorText}` });
        }
      } catch (error: unknown) {
        setStatus('error');
        setMessage('✗ Connection error');
        setDetails({ error: error instanceof Error ? error.message : String(error) });
      }
    }

    login();
  }, [router]);

  return (
    <div style={{ maxWidth: 600, margin: '50px auto', padding: 20, fontFamily: 'Arial, sans-serif' }}>
      <h1>Authentication Test - Valid Login</h1>
      <div
        style={{
          padding: 10,
          margin: '10px 0',
          borderRadius: 5,
          backgroundColor:
            status === 'success' ? '#d4edda' : status === 'error' ? '#f8d7da' : '#d1ecf1',
          color:
            status === 'success' ? '#155724' : status === 'error' ? '#721c24' : '#0c5460'
        }}
      >
        {message}
      </div>
      {details && (
        <div style={{ marginTop: 20 }}>
          {details.user && (
            <>
              <p><strong>User:</strong> {details.user.username || 'N/A'}</p>
              <p><strong>JWT Cookie:</strong> Set (httpOnly)</p>
              <p>Redirecting to telemetry wall demo in 2 seconds...</p>
            </>
          )}
          {details.error && (
            <p><strong>Error:</strong> {details.error}</p>
          )}
        </div>
      )}
    </div>
  );
}
