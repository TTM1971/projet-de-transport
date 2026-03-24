import React from 'react';
import Logo from '../components/Logo';
export default function Home() {
  return (
    <div className="min-h-screen bg-[#282c34] text-white">
      <header className="flex min-h-screen flex-col items-center justify-center gap-2 p-8 text-center">
        <Logo variant="large" />
        <p className="mt-5 text-lg">Collective Transport Management System</p>
        <p className="text-white/80">Web application prototype for ticket management and bus tracking.</p>
      </header>
    </div>
  );
}
