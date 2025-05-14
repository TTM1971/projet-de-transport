import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
  return (
    <nav className="navbar">
      <h2>Transport Collectif</h2>
      <div className="nav-links">
        <Link to="/">Accueil</Link>
        <Link to="/login">Connexion</Link>
      </div>
    </nav>
  );
}
