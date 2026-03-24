import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import StatsWidget from './StatsWidget';
import Card from './Card';
import { formatPrice, eurToCad } from '../utils/currency';
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const API_URL = 'http://localhost:8000';

export default function DashboardAdmin() {
  const navigate = useNavigate();
  const period = 30;
  const [historicalData, setHistoricalData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [managersActivity, setManagersActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const chartType = 'line';

  useEffect(() => {
    fetchData();
  }, [period]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [historicalRes, summaryRes, managersRes] = await Promise.all([
        axios.get(`${API_URL}/analytics/dashboard/historical?days=${period}`),
        axios.get(`${API_URL}/analytics/dashboard/summary`),
        axios.get(`${API_URL}/admin/audit/gestionnaires/activites?days=${period}`),
      ]);
      setHistoricalData(historicalRes.data.data);
      setSummary(summaryRes.data);
      setManagersActivity(managersRes.data.gestionnaires || []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Conversion EUR vers CAD (déjà fait dans formatPrice)

  // Prepare data for charts
  const dates = historicalData.map(d => {
    const date = new Date(d.date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });

  // Revenue Chart
  const caChartData = {
    labels: dates,
    datasets: [
      {
        label: 'Revenue',
        data: historicalData.map(d => eurToCad(d.chiffre_affaires)),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Tickets Sold Chart
  const billetsChartData = {
    labels: dates,
    datasets: [
      {
        label: 'Tickets Sold',
        data: historicalData.map(d => d.billets_vendus),
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Buses in Service Chart
  const busChartData = {
    labels: dates,
    datasets: [
      {
        label: 'Buses in Service',
        data: historicalData.map(d => d.bus_en_service),
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Maintenance Interventions Chart
  const maintenanceChartData = {
    labels: dates,
    datasets: [
      {
        label: 'Maintenance Interventions',
        data: historicalData.map(d => d.interventions_maintenance),
        borderColor: 'rgb(255, 159, 64)',
        backgroundColor: 'rgba(255, 159, 64, 0.2)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Active Lines Chart
  const lignesChartData = {
    labels: dates,
    datasets: [
      {
        label: 'Active Lines',
        data: historicalData.map(d => d.lignes_actives),
        borderColor: 'rgb(153, 102, 255)',
        backgroundColor: 'rgba(153, 102, 255, 0.2)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Graphique Destinations
  const destinationsChartData = {
    labels: dates,
    datasets: [
      {
        label: 'Destinations',
        data: historicalData.map(d => d.destinations),
        borderColor: 'rgb(201, 203, 207)',
        backgroundColor: 'rgba(201, 203, 207, 0.2)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Options communes pour les graphiques
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: false,
      },
      tooltip: {
        enabled: true,
      },
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false,
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
    },
  };

  if (loading) return <div className="loading">Loading data...</div>;

  return (
    <div className="page-container dashboard-admin">
      <div className="dashboard-header">
        <h1>Dashboard - Administration</h1>
      </div>

      {/* Summary Statistics */}
      {summary && (
        <div className="stats-grid">
          <StatsWidget
            title="Total Revenue"
            value={formatPrice(summary.chiffre_affaires_total)}
            color="#27ae60"
            onClick={() => navigate('/dashboard/details/ca')}
          />
          <StatsWidget
            title="Today's Revenue"
            value={formatPrice(summary.chiffre_affaires_aujourdhui)}
            color="#3498db"
            onClick={() => navigate('/dashboard/details/ca', { state: { todayOnly: true } })}
          />
          <StatsWidget
            title="Total Tickets Sold"
            value={summary.total_billets}
            color="#f39c12"
            onClick={() => navigate('/dashboard/details/billets')}
          />
          <StatsWidget
            title="Tickets Today"
            value={summary.billets_aujourdhui}
            color="#e67e22"
            onClick={() => navigate('/dashboard/details/billets', { state: { todayOnly: true } })}
          />
          <StatsWidget
            title="Buses in Service"
            value={summary.buses_en_service}
            color="#27ae60"
            onClick={() => navigate('/dashboard/maintenance/service')}
          />
          <StatsWidget
            title="Buses in Maintenance"
            value={summary.buses_maintenance}
            color="#e67e22"
            onClick={() => navigate('/dashboard/maintenance/bus')}
          />
          <StatsWidget
            title="Active Lines"
            value={summary.lignes_actives}
            color="#9b59b6"
            onClick={() => navigate('/lignes')}
          />
          <StatsWidget
            title="Destinations"
            value={summary.destinations}
            color="#e74c3c"
            onClick={() => navigate('/destinations')}
          />
          <StatsWidget
            title="Ongoing Interventions"
            value={summary.interventions_en_cours}
            color="#95a5a6"
            onClick={() => navigate('/dashboard/maintenance/interventions')}
          />
        </div>
      )}

      <Card title="Suivi des gestionnaires par ville">
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Gestionnaire</th>
                <th>Ville</th>
                <th>Actions - {period} jours</th>
                <th>Dernières actions</th>
              </tr>
            </thead>
            <tbody>
              {managersActivity.length === 0 ? (
                <tr>
                  <td colSpan={4} className="empty-state">Aucune activité</td>
                </tr>
              ) : managersActivity.map((entry) => (
                <tr key={entry.manager.id}>
                  <td>{entry.manager.first_name || entry.manager.username} {entry.manager.last_name || ''}</td>
                  <td>{entry.manager.ville || 'N/A'}</td>
                  <td>{entry.total_actions}</td>
                  <td>
                    {(entry.recent_actions || []).slice(0, 3).map((a) => a.action).join(', ') || 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
