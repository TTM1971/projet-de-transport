import React from 'react';
import Logo from '../components/Logo';
import '../App.css';

export default function Home() {
  return (
    <div className="App">
      <header className="App-header">
        <Logo variant="large" />
        <p style={{ fontSize: '1.1em', marginTop: '20px' }}>Collective Transport Management System</p>
        <p>Web application prototype for ticket management and bus tracking.</p>
      </header>
    </div>
  );
}
