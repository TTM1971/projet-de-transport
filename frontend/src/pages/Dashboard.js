import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import StatsWidget from '../components/StatsWidget';
import Card from '../components/Card';
import DashboardAdmin from '../components/DashboardAdmin';
import { formatPrice } from '../utils/currency';
const API_URL = 'http://localhost:8000';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // Déclarer tous les hooks AVANT tout return conditionnel
  const [stats, setStats] = useState({
    bus: 0,
    lignes: 0,
    destinations: 0,
    billets: 0,
    busEnService: 0,
    busMaintenance: 0,
    chiffreAffaires: 0,
    billetsAujourdhui: 0,
    departs: 0,
    chauffeurs: 0,
    interventions: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Ne pas appeler fetchStats si c'est un admin (qui utilisera DashboardAdmin)
    if (user?.role !== 'admin') {
      fetchStats();
    } else {
      setLoading(false); // Si admin, on ne charge pas les stats ici
    }
  }, [user?.role]);

  const fetchStats = async () => {
    try {
      const role = user?.role;
      const requests = [];

      // Admin et Gestionnaire : Statistiques complètes
      if (role === 'admin' || role === 'gestionnaire') {
        requests.push(
          axios.get(`${API_URL}/bus/`),
          axios.get(`${API_URL}/lignes/`),
          axios.get(`${API_URL}/destinations/`),
          axios.get(`${API_URL}/billets/`)
        );
        if (role === 'admin') {
          requests.push(axios.get(`${API_URL}/chauffeurs/`));
        }
      }
      
      // Agent : Statistiques de vente (utiliser le nouvel endpoint)
      if (role === 'agent') {
        requests.push(
          axios.get(`${API_URL}/analytics/agent/dashboard`)
        );
      }
      
      // Maintenance : Statistiques de maintenance
      if (role === 'maintenance') {
        requests.push(
          axios.get(`${API_URL}/bus/`),
          axios.get(`${API_URL}/ateliers/`).catch(() => ({ data: [] })) // Si l'endpoint n'existe pas
        );
      }

      const results = await Promise.all(requests.map(req => req.catch(() => ({ data: [] }))));
      let resultIndex = 0;

      if (role === 'admin' || role === 'gestionnaire') {
        const buses = results[resultIndex++]?.data || [];
        const lignes = results[resultIndex++]?.data || [];
        const destinations = results[resultIndex++]?.data || [];
        const billets = results[resultIndex++]?.data || [];
        const chauffeurs = (role === 'admin' ? results[resultIndex++]?.data : []) || [];

        const busEnService = buses.filter(b => b.statut === 'en_service').length;
        const busMaintenance = buses.filter(b => b.statut === 'en_maintenance').length;

        // Calculer le chiffre d'affaires (admin uniquement)
        const chiffreAffaires = role === 'admin' 
          ? billets.reduce((sum, b) => sum + (parseFloat(b.montant) || 0), 0)
          : 0;

        // Billets vendus aujourd'hui
        const aujourdhui = new Date().toISOString().split('T')[0];
        const billetsAujourdhui = billets.filter(b => {
          const dateAchat = b.date_achat ? new Date(b.date_achat).toISOString().split('T')[0] : '';
          return dateAchat === aujourdhui;
        }).length;

        setStats({
          bus: buses.length,
          lignes: lignes.length,
          destinations: destinations.length,
          billets: billets.length,
          busEnService,
          busMaintenance,
          chiffreAffaires,
          billetsAujourdhui,
          departs: 0,
          chauffeurs: chauffeurs.length
        });
      } else if (role === 'agent') {
        const agentData = results[resultIndex++]?.data || {};

        setStats({
          bus: 0,
          lignes: 0,
          destinations: 0,
          billets: agentData.billets_vendus_aujourdhui || 0,
          busEnService: 0,
          busMaintenance: 0,
          chiffreAffaires: agentData.ca_aujourdhui || 0,
          billetsAujourdhui: agentData.billets_vendus_aujourdhui || 0,
          departs: agentData.departs_disponibles || 0,
          chauffeurs: 0
        });
      } else if (role === 'maintenance') {
        const buses = results[resultIndex++]?.data || [];
        const ateliers = results[resultIndex++]?.data || [];

        const busMaintenance = buses.filter(b => b.statut === 'en_maintenance').length;
        const interventionsEnCours = ateliers.filter(a => a.statut === 'en_cours').length;

        setStats({
          bus: buses.length,
          lignes: 0,
          destinations: 0,
          billets: 0,
          busEnService: buses.filter(b => b.statut === 'en_service').length,
          busMaintenance,
          chiffreAffaires: 0,
          billetsAujourdhui: 0,
          departs: 0,
          chauffeurs: 0,
          interventions: interventionsEnCours
        });
      }
    } catch (error) {
      console.error('Error loading statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  // If admin, use DashboardAdmin with charts
  // This check must be AFTER all hooks but BEFORE loading check
  if (user?.role === 'admin') {
    return <DashboardAdmin />;
  }

  if (loading) return <div className="loading">Loading...</div>;

  const role = user?.role;

  // Manager Dashboard: Operational view
  if (role === 'gestionnaire') {
    return (
      <div className="page-container dashboard">
        <h1>Dashboard - Management</h1>
        <p style={{ color: '#666', marginBottom: '30px' }}>Overview of routes, schedules and performance</p>
        
        <div className="stats-grid">
          <StatsWidget
            title="Buses in Service"
            value={stats.busEnService}
            color="#27ae60"
          />
          <StatsWidget
            title="Buses in Maintenance"
            value={stats.busMaintenance}
            color="#e67e22"
          />
          <StatsWidget
            title="Active Lines"
            value={stats.lignes}
            color="#9b59b6"
          />
          <StatsWidget
            title="Destinations"
            value={stats.destinations}
            color="#e74c3c"
          />
          <StatsWidget
            title="Tickets Sold"
            value={stats.billets}
            color="#f39c12"
          />
          <StatsWidget
            title="Tickets Today"
            value={stats.billetsAujourdhui}
            color="#3498db"
          />
        </div>

        <div className="dashboard-cards">
          <Card title="Operational Management">
            <p>Manage routes, schedules, driver assignments and track performance.</p>
          </Card>
        </div>
      </div>
    );
  }

  // Agent Dashboard: Sales view
  if (role === 'agent') {
    return (
      <div className="page-container dashboard">
        <h1>Dashboard - Sales</h1>
        <p style={{ color: '#666', marginBottom: '30px' }}>Your sales statistics and customer information</p>
        
        <div className="stats-grid">
          <StatsWidget
            title="Today's Revenue"
            value={formatPrice(stats.chiffreAffaires)}
            color="#27ae60"
            onClick={() => navigate('/dashboard/details/ca', { state: { todayOnly: true } })}
          />
          <StatsWidget
            title="Tickets Sold Today"
            value={stats.billetsAujourdhui}
            color="#3498db"
            onClick={() => navigate('/dashboard/details/billets', { state: { todayOnly: true } })}
          />
          <StatsWidget
            title="Available Departures"
            value={stats.departs}
            color="#f39c12"
            onClick={() => navigate('/agent/departs')}
          />
          <StatsWidget
            title="Total Tickets Sold"
            value={stats.billets}
            color="#9b59b6"
            onClick={() => navigate('/dashboard/details/billets')}
          />
        </div>

        <div className="dashboard-cards">
          <Card title="Customer Support">
            <p>View reservations and help customers with route and schedule information.</p>
          </Card>
        </div>
      </div>
    );
  }

  // Maintenance Dashboard: Interventions view
  if (role === 'maintenance') {
    return (
      <div className="page-container dashboard">
        <h1>Dashboard - Maintenance</h1>
        <p style={{ color: '#666', marginBottom: '30px' }}>Intervention tracking and vehicle status</p>
        
        <div className="stats-grid">
          <StatsWidget
            title="Buses in Maintenance"
            value={stats.busMaintenance}
            color="#e67e22"
            onClick={() => navigate('/dashboard/maintenance/bus')}
          />
          <StatsWidget
            title="Buses in Service"
            value={stats.busEnService}
            color="#27ae60"
            onClick={() => navigate('/dashboard/maintenance/service')}
          />
          <StatsWidget
            title="Ongoing Interventions"
            value={stats.interventions}
            color="#e74c3c"
            onClick={() => navigate('/dashboard/maintenance/interventions')}
          />
          <StatsWidget
            title="Total Vehicles"
            value={stats.bus}
            color="#4a90e2"
          />
        </div>

        <div className="dashboard-cards">
          <Card title="Intervention Recording">
            <p>Record breakdowns, repairs, parts changed and intervention dates for ML analysis.</p>
          </Card>
        </div>
      </div>
    );
  }

  // Default (should not happen)
  return (
    <div className="page-container dashboard">
      <h1>Dashboard</h1>
      <p>Loading...</p>
    </div>
  );
}
