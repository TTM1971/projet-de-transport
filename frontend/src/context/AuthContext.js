import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API_URL = 'http://localhost:8000';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Vérifier si on a un token enregistré
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`;
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        username,
        password
      });
      
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      
      // Décoder le token pour obtenir les infos utilisateur (simplifié)
      // En production, vous devriez décoder le JWT côté serveur ou avoir un endpoint /me
      const payload = JSON.parse(atob(access_token.split('.')[1]));
      const userData = { username: payload.sub, role: payload.role };
      
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true, user: userData };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Erreur de connexion' 
      };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

  const hasRole = (allowedRoles) => {
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  const canAccess = (permission) => {
    if (!user) return false;
    
    const role = user.role;
    
    // Définition des permissions par rôle selon les spécifications
    const permissions = {
      // Admin : Accès complet à toutes les fonctionnalités
      admin: ['all'],
      
      // Gestionnaire : Gestion quotidienne des trajets, horaires, chauffeurs, billets
      gestionnaire: [
        'dashboard',           // Tableau de bord
        'bus',                 // Vue d'ensemble des véhicules
        'bus_read',            // Consultation des véhicules
        'lignes',              // Gestion des lignes de bus
        'destinations',        // Gestion des destinations
        'departs',             // Gestion des trajets et horaires
        'chauffeurs',          // Assignation créneaux, suivi performances
        'chauffeurs_read',     // Consultation des chauffeurs
        'billets',             // Gestion des réservations et billets
        'billets_read',        // Consultation des billets
        'flotte',              // Vue d'ensemble sur l'état des véhicules
        'flotte_read'          // Consultation de la flotte
      ],
      
      // Agent : Accueil, assistance, vente de billets
      agent: [
        'dashboard',           // Tableau de bord (statistiques de vente)
        'vente',               // Acheter des billets
        'billets_read',        // Consulter les réservations
        'departs',             // Accès à la page départs (mais en lecture seule via canEdit)
        'departs_read',        // Informations sur les trajets et horaires (lecture seule)
        'destinations_read',   // Informations sur les destinations
        'lignes_read',         // Informations sur les lignes
        'support_client'       // Support client (à implémenter)
      ],
      
      // Maintenance : Enregistrement interventions, suivi véhicules
      maintenance: [
        'dashboard',           // Tableau de bord (interventions)
        'maintenance',         // Enregistrer interventions (pannes, réparations, pièces)
        'maintenance_read',    // Consulter les interventions
        'flotte_read',         // Suivi des véhicules
        'bus_read',            // Consultation des véhicules
        'bus_update'           // Mise à jour statut des véhicules
      ]
    };
    
    // Admin a accès à tout
    if (role === 'admin') return true;
    
    const rolePerms = permissions[role] || [];
    
    // Vérifier si la permission est directement dans la liste
    if (rolePerms.includes(permission)) return true;
    
    // Vérifier si 'all' est dans les permissions
    if (rolePerms.includes('all')) return true;
    
    // Pour les permissions de type "read", vérifier aussi les permissions générales
    // Par exemple, si on a 'billets' on a aussi 'billets_read'
    if (permission.endsWith('_read')) {
      const basePermission = permission.replace('_read', '');
      if (rolePerms.includes(basePermission)) return true;
    }
    
    return false;
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, hasRole, canAccess, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
