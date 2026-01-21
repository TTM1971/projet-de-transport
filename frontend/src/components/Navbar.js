import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Logo from './Logo';
import './Navbar.css';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState(null);
  const { user, logout, canAccess } = useAuth();
  const navigate = useNavigate();
  const gestionDropdownRef = useRef(null);
  const suiviDropdownRef = useRef(null);
  const adminDropdownRef = useRef(null);

  // Fermer les dropdowns quand on clique en dehors
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (openDropdown === 'gestion' && gestionDropdownRef.current && !gestionDropdownRef.current.contains(event.target)) {
        setOpenDropdown(null);
      } else if (openDropdown === 'suivi' && suiviDropdownRef.current && !suiviDropdownRef.current.contains(event.target)) {
        setOpenDropdown(null);
      } else if (openDropdown === 'admin' && adminDropdownRef.current && !adminDropdownRef.current.contains(event.target)) {
        setOpenDropdown(null);
      }
    };

    if (openDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [openDropdown]);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMenuOpen(false);
  };

  if (!user) return null;

  const toggleDropdown = (dropdownName) => {
    setOpenDropdown(openDropdown === dropdownName ? null : dropdownName);
  };

  const getRoleLabel = (role) => {
    const labels = {
      admin: 'Administrator',
      agent: 'Agent',
      gestionnaire: 'Manager',
      maintenance: 'Maintenance'
    };
    return labels[role] || role;
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/dashboard" className="brand-link">
          <Logo variant="compact" />
        </Link>
      </div>
      <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>
        Menu
      </button>
      <div className={`nav-links ${menuOpen ? 'open' : ''}`}>
        {canAccess('dashboard') && (
          <Link to="/dashboard" onClick={() => setMenuOpen(false)}>Dashboard</Link>
        )}
        {canAccess('vente') && (
          <Link to="/vente" onClick={() => setMenuOpen(false)}>Ticket Sales</Link>
        )}
        {(canAccess('bus') || canAccess('lignes') || canAccess('destinations') || canAccess('departs') || canAccess('departs_read') || canAccess('billets_read')) && (
          <div className="nav-dropdown" ref={gestionDropdownRef}>
            <span onClick={() => toggleDropdown('gestion')}>Management</span>
            {openDropdown === 'gestion' && (
            <div className="dropdown-content">
                {canAccess('bus') && <Link to="/bus" onClick={() => { setMenuOpen(false); setOpenDropdown(null); }}>Buses</Link>}
                {canAccess('lignes') && <Link to="/lignes" onClick={() => { setMenuOpen(false); setOpenDropdown(null); }}>Lines</Link>}
                {(canAccess('departs') || canAccess('departs_read')) && (
                  <Link to="/departs" onClick={() => { setMenuOpen(false); setOpenDropdown(null); }}>
                    {canAccess('departs') ? 'Departures' : 'Schedules & Routes'}
                  </Link>
                )}
                {canAccess('chauffeurs') && <Link to="/chauffeurs" onClick={() => { setMenuOpen(false); setOpenDropdown(null); }}>Drivers</Link>}
                {canAccess('destinations') && <Link to="/destinations" onClick={() => { setMenuOpen(false); setOpenDropdown(null); }}>Destinations</Link>}
                {canAccess('billets_read') && <Link to="/billets" onClick={() => { setMenuOpen(false); setOpenDropdown(null); }}>Tickets</Link>}
            </div>
            )}
          </div>
        )}
        {(canAccess('flotte') || canAccess('maintenance')) && (
          <div className="nav-dropdown" ref={suiviDropdownRef}>
            <span onClick={() => toggleDropdown('suivi')}>Monitoring</span>
            {openDropdown === 'suivi' && (
            <div className="dropdown-content">
                {canAccess('flotte') && <Link to="/suivi-flotte" onClick={() => { setMenuOpen(false); setOpenDropdown(null); }}>Fleet</Link>}
                {canAccess('maintenance') && <Link to="/maintenance" onClick={() => { setMenuOpen(false); setOpenDropdown(null); }}>Maintenance</Link>}
            </div>
            )}
          </div>
        )}
        {(user.role === 'admin' || user.role === 'gestionnaire') && (
          <div className="nav-dropdown" ref={adminDropdownRef}>
            <span onClick={() => toggleDropdown('admin')}>{user.role === 'admin' ? 'Administration' : 'Admin'}</span>
            {openDropdown === 'admin' && (
            <div className="dropdown-content">
                {user.role === 'admin' && <Link to="/users" onClick={() => { setMenuOpen(false); setOpenDropdown(null); }}>Users</Link>}
                <Link to="/users/approval" onClick={() => { setMenuOpen(false); setOpenDropdown(null); }}>
                  Account Approval
                  {user.role === 'gestionnaire' ? ' (Agents/Maintenance)' : ''}
                </Link>
            </div>
            )}
          </div>
        )}
        <div className="user-info">
          <span className="user-role-label">{getRoleLabel(user.role)}</span>
          <span className="username">{user.username}</span>
          <button className="btn-logout" onClick={handleLogout}>Logout</button>
        </div>
      </div>
    </nav>
  );
}
