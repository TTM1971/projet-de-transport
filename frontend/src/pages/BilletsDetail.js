import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import Card from '../components/Card';
import BackButton from '../components/BackButton';
import { formatPrice } from '../utils/currency';

const API_URL = 'http://localhost:8000';
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function BilletsDetail() {
  const navigate = useNavigate();
  const location = useLocation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const todayOnly = location.state?.todayOnly || false;
  const [startDate, setStartDate] = useState(() => {
    if (todayOnly) {
      return new Date().toISOString().split('T')[0];
    }
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [expandedDays, setExpandedDays] = useState(new Set());

  useEffect(() => {
    fetchData();
  }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/analytics/detail/billets/jours`, {
        params: {
          start_date: startDate,
          end_date: endDate
        },
        timeout: 120000 // 2 minutes de timeout
      });
      setData(response.data);
      // Auto-expand today if todayOnly
      if (todayOnly && response.data.donnees_par_jour.length > 0) {
        const today = new Date().toISOString().split('T')[0];
        setExpandedDays(new Set([today]));
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error loading data');
    } finally {
      setLoading(false);
    }
  };

  const toggleDay = (date) => {
    const newExpanded = new Set(expandedDays);
    if (newExpanded.has(date)) {
      newExpanded.delete(date);
    } else {
      newExpanded.add(date);
    }
    setExpandedDays(newExpanded);
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!data) return <div className="loading">No data available</div>;

  const trendRows = [...(data.donnees_par_jour || [])].sort((a, b) => String(a.date).localeCompare(String(b.date)));
  const ticketsChartData = {
    labels: trendRows.map((j) => new Date(j.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
    datasets: [
      {
        label: 'Tickets',
        data: trendRows.map((j) => Number(j.nombre_transactions || 0)),
        backgroundColor: 'rgba(243, 156, 18, 0.6)',
        borderColor: 'rgb(243, 156, 18)',
        borderWidth: 1,
      },
    ],
  };
  const ticketsChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
    },
    scales: {
      y: { beginAtZero: true },
    },
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div style={{ marginBottom: '20px' }}>
            <BackButton />
          </div>
          <h1>{todayOnly ? "Tickets Sold Today" : "Tickets Sold - Details"}</h1>
          <p style={{ color: '#666', marginTop: '10px' }}>
            Breakdown of tickets sold by day with all details
          </p>
        </div>
        {!todayOnly && (
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <label>
              From: <input 
                type="date" 
                value={startDate} 
                onChange={(e) => setStartDate(e.target.value)}
                style={{ padding: '8px', marginLeft: '5px' }}
              />
            </label>
            <label>
              To: <input 
                type="date" 
                value={endDate} 
                onChange={(e) => setEndDate(e.target.value)}
                style={{ padding: '8px', marginLeft: '5px' }}
              />
            </label>
            <button className="btn-primary" onClick={fetchData}>Refresh</button>
          </div>
        )}
      </div>

      <Card>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '30px' }}>
          <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '5px' }}>Total Tickets Sold</div>
            <div style={{ fontSize: '2em', fontWeight: 'bold', color: '#f39c12' }}>
              {data.total_transactions}
            </div>
          </div>
          <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '5px' }}>Total Turnover</div>
            <div style={{ fontSize: '2em', fontWeight: 'bold', color: '#27ae60' }}>
              {formatPrice(data.total_ca)}
            </div>
          </div>
          <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '5px' }}>Days</div>
            <div style={{ fontSize: '2em', fontWeight: 'bold', color: '#9b59b6' }}>
              {data.donnees_par_jour.length}
            </div>
          </div>
        </div>
      </Card>

      <Card title="Tickets Trend">
        <div className="chart-container">
          <Bar data={ticketsChartData} options={ticketsChartOptions} />
        </div>
      </Card>

      {data.donnees_par_jour.map((jour) => {
        const isExpanded = expandedDays.has(jour.date);
        const trajetsArray = Object.values(jour.trajets || {});
        
        return (
          <Card key={jour.date} style={{ marginBottom: '20px' }}>
            <div 
              style={{ 
                cursor: 'pointer',
                padding: '15px',
                backgroundColor: isExpanded ? '#f8f9fa' : 'white',
                borderRadius: '8px',
                border: '2px solid #e5e5e5',
                transition: 'all 0.3s'
              }}
              onClick={() => navigate(`/dashboard/details/trajets/${jour.date}`)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 style={{ margin: 0, color: '#1a1a1a' }}>
                    {formatDate(jour.date)}
                  </h2>
                  <div style={{ display: 'flex', gap: '30px', marginTop: '10px' }}>
                    <span style={{ color: '#666' }}>
                      <strong>Tickets:</strong> {jour.nombre_transactions}
                    </span>
                    <span style={{ color: '#666' }}>
                      <strong>Turnover:</strong> {formatPrice(jour.chiffre_affaires_total)}
                    </span>
                    <span style={{ color: '#666' }}>
                      <strong>Trips:</strong> {trajetsArray.length}
                    </span>
                  </div>
                </div>
                <div style={{ fontSize: '1.5em', color: '#3498db' }}>
                  Click to view all trips →
                </div>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
