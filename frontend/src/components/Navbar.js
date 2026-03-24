import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, logout, canAccess, activeCity, setActiveCity } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMenuOpen(false);
  };

  if (!user) return null;

  const navClass = ({ isActive }) =>
    isActive ? 'nav-link active' : 'nav-link';

  const getRoleLabel = (role) => {
    const labels = {
      admin: 'Administrator',
      agent: 'Agent',
      gestionnaire: 'Manager',
      maintenance: 'Maintenance',
      chauffeur: 'Chauffeur',
    };
    return labels[role] || role;
  };

  return (
    <>
      <header className="topbar">
        <div className="topbar-brand">
          <span className="app-name">MEGANE</span>
        </div>
        <div className="topbar-user">
          <span className="user-role">{getRoleLabel(user.role)}</span>
          <span className="user-avatar">{(user.username || 'U').charAt(0).toUpperCase()}</span>
          <button type="button" className="btn-logout btn-logout--topbar" onClick={handleLogout}>
            Déconnexion
          </button>
        </div>
      </header>

      <nav className="sidebar">
        <div className="sidebar-header">
          <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>
            Menu
          </button>
        </div>
        <div className={`nav-links ${menuOpen ? 'open' : ''}`}>
          {user.role === 'chauffeur' && (
            <NavLink to="/espace-chauffeur" end className={navClass} onClick={() => setMenuOpen(false)}>
              Espace chauffeur
            </NavLink>
          )}
          {user.role === 'admin' && !activeCity && (
            <>
              <NavLink to="/dashboard" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
                Dashboard
              </NavLink>
              <NavLink to="/horaires-equipe" className={navClass} onClick={() => setMenuOpen(false)}>
                Horaires équipe
              </NavLink>
              <NavLink to="/villes" end className={navClass} onClick={() => setMenuOpen(false)}>
                Villes
              </NavLink>
            </>
          )}
          {user.role === 'admin' && !!activeCity && (
            <>
              <div className="nav-link" style={{ fontSize: 12, opacity: 0.8 }}>
                Ville active: <strong>{activeCity}</strong>
              </div>
              <button className="btn-secondary" style={{ margin: '6px 10px' }} onClick={() => { setActiveCity(''); navigate('/villes'); }}>
                Changer de ville
              </button>
              <NavLink to="/dashboard" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
                Dashboard
              </NavLink>
              <NavLink to="/bus" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
                Bus
              </NavLink>
              <NavLink to="/lignes" className={navClass} onClick={() => setMenuOpen(false)}>
                Lignes
              </NavLink>
              <NavLink to="/departs" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
                Departs
              </NavLink>
              <NavLink to="/chauffeurs" className={navClass} onClick={() => setMenuOpen(false)}>
                Chauffeurs
              </NavLink>
              <NavLink to="/horaires-equipe" className={navClass} onClick={() => setMenuOpen(false)}>
                Horaires équipe
              </NavLink>
              <NavLink to="/destinations" className={navClass} onClick={() => setMenuOpen(false)}>
                Destinations
              </NavLink>
              <NavLink to="/billets" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
                Billets
              </NavLink>
              <NavLink to="/suivi-flotte" end className={navClass} onClick={() => setMenuOpen(false)}>
                Suivi Flotte
              </NavLink>
              <NavLink to="/maintenance" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
                Maintenance
              </NavLink>
              <NavLink to="/users" end className={navClass} onClick={() => setMenuOpen(false)}>
                Utilisateurs
              </NavLink>
            </>
          )}
          {user.role !== 'chauffeur' && user.role !== 'admin' && (
            <>
          {canAccess('dashboard') && (
            <NavLink to="/dashboard" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
              Dashboard
            </NavLink>
          )}
          {canAccess('vente') && (
            <NavLink to="/vente" end className={navClass} onClick={() => setMenuOpen(false)}>
              Ventes
            </NavLink>
          )}
          {canAccess('bus') && (
            <NavLink to="/bus" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
              Bus
            </NavLink>
          )}
          {canAccess('lignes') && (
            <NavLink to="/lignes" className={navClass} onClick={() => setMenuOpen(false)}>
              Lignes
            </NavLink>
          )}
          {(canAccess('departs') || canAccess('departs_read')) && (
            <NavLink to="/departs" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
              Departs
            </NavLink>
          )}
          {canAccess('chauffeurs') && (
            <NavLink to="/chauffeurs" className={navClass} onClick={() => setMenuOpen(false)}>
              Chauffeurs
            </NavLink>
          )}
          {canAccess('horaires_equipe') && (
            <NavLink to="/horaires-equipe" className={navClass} onClick={() => setMenuOpen(false)}>
              Horaires équipe
            </NavLink>
          )}
          {canAccess('destinations') && (
            <NavLink to="/destinations" className={navClass} onClick={() => setMenuOpen(false)}>
              Destinations
            </NavLink>
          )}
          {canAccess('billets_read') && (
            <NavLink to="/billets" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
              Billets
            </NavLink>
          )}
          {canAccess('flotte') && (
            <NavLink to="/suivi-flotte" end className={navClass} onClick={() => setMenuOpen(false)}>
              Suivi Flotte
            </NavLink>
          )}
          {canAccess('maintenance') && (
            <NavLink to="/maintenance" end={false} className={navClass} onClick={() => setMenuOpen(false)}>
              Maintenance
            </NavLink>
          )}
          {user.role === 'gestionnaire' && (
            <>
              <NavLink to="/users/approval" end className={navClass} onClick={() => setMenuOpen(false)}>
                Validation Comptes
              </NavLink>
            </>
          )}
            </>
          )}
        </div>
      </nav>
    </>
  );
}
