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
import './DashboardAdmin.css';

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
  const [period, setPeriod] = useState(30); // 30 jours par défaut
  const [historicalData, setHistoricalData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chartType, setChartType] = useState('line'); // 'line' ou 'bar'

  useEffect(() => {
    fetchData();
  }, [period]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [historicalRes, summaryRes] = await Promise.all([
        axios.get(`${API_URL}/analytics/dashboard/historical?days=${period}`),
        axios.get(`${API_URL}/analytics/dashboard/summary`)
      ]);
      setHistoricalData(historicalRes.data.data);
      setSummary(summaryRes.data);
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

  // Revenue Chart (CAD)
  const caChartData = {
    labels: dates,
    datasets: [
      {
        label: 'Revenue (CAD)',
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
        <p className="dashboard-subtitle">
          Interactive performance visualization over {period} day{period > 1 ? 's' : ''}
        </p>
      </div>

      {/* Summary Statistics */}
      {summary && (
        <div className="stats-grid">
          <StatsWidget
            title="Total Revenue (CAD)"
            value={formatPrice(summary.chiffre_affaires_total)}
            color="#27ae60"
            onClick={() => navigate('/dashboard/details/ca')}
          />
          <StatsWidget
            title="Today's Revenue (CAD)"
            value={formatPrice(summary.chiffre_affaires_aujourdhui)}
            color="#3498db"
            onClick={() => navigate('/dashboard/details/ca', { state: { todayOnly: true } })}
          />
          <StatsWidget
            title="Tickets Sold (Total)"
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
            onClick={() => window.location.href = '/dashboard/maintenance/service'}
          />
          <StatsWidget
            title="Buses in Maintenance"
            value={summary.buses_maintenance}
            color="#e67e22"
            onClick={() => window.location.href = '/dashboard/maintenance/bus'}
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
            onClick={() => window.location.href = '/dashboard/maintenance/interventions'}
          />
        </div>
      )}

      {/* Controls */}
      <div className="dashboard-controls">
        <div className="period-selector">
          <label>Period:</label>
          <button
            className={period === 7 ? 'active' : ''}
            onClick={() => setPeriod(7)}
          >
            7 days
          </button>
          <button
            className={period === 30 ? 'active' : ''}
            onClick={() => setPeriod(30)}
          >
            30 days
          </button>
          <button
            className={period === 90 ? 'active' : ''}
            onClick={() => setPeriod(90)}
          >
            90 days
          </button>
          <button
            className={period === 365 ? 'active' : ''}
            onClick={() => setPeriod(365)}
          >
            1 year
          </button>
        </div>
        <div className="chart-type-selector">
          <label>Chart Type:</label>
          <button
            className={chartType === 'line' ? 'active' : ''}
            onClick={() => setChartType('line')}
          >
            Line
          </button>
          <button
            className={chartType === 'bar' ? 'active' : ''}
            onClick={() => setChartType('bar')}
          >
            Bars
          </button>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <Card title="Revenue Evolution (CAD)">
          <div className="chart-container">
            {chartType === 'line' ? (
              <Line data={caChartData} options={chartOptions} />
            ) : (
              <Bar data={caChartData} options={chartOptions} />
            )}
          </div>
        </Card>

        <Card title="Tickets Sold Evolution">
          <div className="chart-container">
            {chartType === 'line' ? (
              <Line data={billetsChartData} options={chartOptions} />
            ) : (
              <Bar data={billetsChartData} options={chartOptions} />
            )}
          </div>
        </Card>

        <Card title="Buses in Service Evolution">
          <div className="chart-container">
            {chartType === 'line' ? (
              <Line data={busChartData} options={chartOptions} />
            ) : (
              <Bar data={busChartData} options={chartOptions} />
            )}
          </div>
        </Card>

        <Card title="Maintenance Interventions Evolution">
          <div className="chart-container">
            {chartType === 'line' ? (
              <Line data={maintenanceChartData} options={chartOptions} />
            ) : (
              <Bar data={maintenanceChartData} options={chartOptions} />
            )}
          </div>
        </Card>

        <Card title="Active Lines Evolution">
          <div className="chart-container">
            {chartType === 'line' ? (
              <Line data={lignesChartData} options={chartOptions} />
            ) : (
              <Bar data={lignesChartData} options={chartOptions} />
            )}
          </div>
        </Card>

        <Card title="Destinations Evolution">
          <div className="chart-container">
            {chartType === 'line' ? (
              <Line data={destinationsChartData} options={chartOptions} />
            ) : (
              <Bar data={destinationsChartData} options={chartOptions} />
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
