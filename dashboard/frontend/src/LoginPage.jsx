import React, { useState } from "react";
import { apiFetch } from "./api";
export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await apiFetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const result = await response.json();
      if (response.ok && result.success) {
        onLoginSuccess(username);
      } else {
        setError(result.message || 'Login failed');
      }
    } catch {
      setError('Server error');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: "linear-gradient(120deg,#20253e 70%,#171a21 100%)",
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <form
        onSubmit={handleSubmit}
        style={{
          background: '#252942',
          padding: '46px 44px',
          borderRadius: 18,
          boxShadow: '0 7px 38px rgba(24,40,64,0.18)',
          minWidth: 340,
          color: '#e7eaed',
        }}
      >
        <h2 style={{
          marginBottom: 25,
          fontWeight: 700,
          color: '#edf6ff',
          textAlign: 'center',
          letterSpacing: '.04em'
        }}>
          Login
        </h2>
        {error &&
          <div style={{
            background: '#371c19',
            color: '#ffe3e1',
            borderRadius: 7,
            padding: '7px 11px',
            marginBottom: 18,
            textAlign: 'center',
            fontSize: 16
          }}>
            {error}
          </div>
        }

        <div style={{ marginBottom: 18 }}>
          <label style={{ display: 'block', marginBottom: 8, color: '#b3b8be', fontWeight: 600 }}>Username</label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
            autoFocus
            style={{
              width: '100%',
              padding: '12px 13px',
              background: '#191a22',
              border: '2px solid #3b82f6',
              borderRadius: 7,
              color: '#e4eaea',
              fontSize: 17,
              outline: 'none'
            }}
          />
        </div>

        <div style={{ marginBottom: 22 }}>
          <label style={{ display: 'block', marginBottom: 8, color: '#b3b8be', fontWeight: 600 }}>Password</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            style={{
              width: '100%',
              padding: '12px 13px',
              background: '#191a22',
              border: '2px solid #3b82f6',
              borderRadius: 7,
              color: '#e4eaea',
              fontSize: 17,
              outline: 'none'
            }}
          />
        </div>

        <button
          type="submit"
          style={{
            width: '100%',
            padding: '12px 0',
            background: 'linear-gradient(100deg, #335bfa 62%, #37b8fa 100%)',
            color: '#fff',
            fontWeight: 600,
            fontSize: 18,
            border: 'none',
            borderRadius: 8,
            cursor: 'pointer',
            boxShadow: '0 2px 7px 0 rgba(24,60,160,0.09)'
          }}
        >
          Login
        </button>
      </form>
    </div>
  );
}
