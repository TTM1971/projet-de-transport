import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import Card from '../components/Card';
import BackButton from '../components/BackButton';
import { formatPrice } from '../utils/currency';

const API_URL = 'http://localhost:8000';
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function ChiffreAffairesDetail() {
  const navigate = useNavigate();
  const location = useLocation();
  const todayOnly = location?.state?.todayOnly || false;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
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
      const response = await axios.get(`${API_URL}/analytics/detail/chiffre-affaires/jours`, {
        params: {
          start_date: startDate,
          end_date: endDate
        },
        timeout: 120000 // 2 minutes de timeout
      });
      setData(response.data);
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
  const trendChartData = {
    labels: trendRows.map((j) => new Date(j.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
    datasets: [
      {
        label: 'Turnover',
        data: trendRows.map((j) => Number(j.chiffre_affaires_total || 0)),
        borderColor: 'rgb(39, 174, 96)',
        backgroundColor: 'rgba(39, 174, 96, 0.18)',
        fill: true,
        tension: 0.35,
      },
    ],
  };
  const trendChartOptions = {
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
          <h1>{todayOnly ? "Today's Turnover" : "Detailed Turnover"}</h1>
          <p style={{ color: '#666', marginTop: '10px' }}>
            Daily breakdown with all trips and transactions
          </p>
        </div>
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
      </div>

      <Card>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '30px' }}>
          <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '5px' }}>Total Turnover</div>
            <div style={{ fontSize: '2em', fontWeight: 'bold', color: '#27ae60' }}>
              {formatPrice(data.total_ca)}
            </div>
          </div>
          <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '5px' }}>Number of Transactions</div>
            <div style={{ fontSize: '2em', fontWeight: 'bold', color: '#3498db' }}>
              {data.total_transactions}
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

      <Card title="Turnover Trend">
        <div className="chart-container">
          <Line data={trendChartData} options={trendChartOptions} />
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
              onClick={() => toggleDay(jour.date)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 style={{ margin: 0, color: '#1a1a1a' }}>
                    {formatDate(jour.date)}
                  </h2>
                  <button
                    className="btn-secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/dashboard/details/trajets/${jour.date}`);
                    }}
                    style={{ marginTop: '10px' }}
                  >
                    View All Trips for This Day →
                  </button>
                  <div style={{ display: 'flex', gap: '30px', marginTop: '10px' }}>
                    <span style={{ color: '#666' }}>
                      <strong>Turnover:</strong> {formatPrice(jour.chiffre_affaires_total)}
                    </span>
                    <span style={{ color: '#666' }}>
                      <strong>Transactions:</strong> {jour.nombre_transactions}
                    </span>
                    <span style={{ color: '#666' }}>
                      <strong>Trips:</strong> {trajetsArray.length}
                    </span>
                  </div>
                </div>
                <div style={{ fontSize: '1.5em', color: '#3498db' }}>
                  {isExpanded ? '▼' : '▶'}
                </div>
              </div>
            </div>

            {isExpanded && (
              <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '2px solid #e5e5e5' }}>
                <div style={{ marginBottom: '15px', textAlign: 'right' }}>
                  <button 
                    className="btn-primary"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/dashboard/details/trajets/${jour.date}`);
                    }}
                  >
                    View All Trips for This Day in Detail →
                  </button>
                </div>
                {/* Summary by cashier */}
                {Object.keys(jour.caissieres || {}).length > 0 && (
                  <div style={{ marginBottom: '30px' }}>
                    <h3 style={{ marginBottom: '15px', color: '#666' }}>Summary by Cashier</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '15px' }}>
                      {Object.values(jour.caissieres).map((caissiere) => (
                        <div 
                          key={caissiere.agent_id}
                          style={{ 
                            padding: '15px', 
                            backgroundColor: '#ebf5fb', 
                            borderRadius: '8px',
                            border: '1px solid #3498db'
                          }}
                        >
                          <strong>{caissiere.first_name || caissiere.username} {caissiere.last_name || ''}</strong>
                          <p style={{ margin: '5px 0' }}>Turnover: {formatPrice(caissiere.ca_total)}</p>
                          <p style={{ margin: '5px 0' }}>Tickets: {caissiere.nombre_billets}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Detailed trips */}
                {trajetsArray.length > 0 && (
                  <div>
                    <h3 style={{ marginBottom: '15px', color: '#666' }}>Trips of the Day ({trajetsArray.length})</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      {trajetsArray.map((trajet) => (
                        <div 
                          key={trajet.depart_id}
                          style={{
                            padding: '20px',
                            border: '1px solid #ddd',
                            borderRadius: '8px',
                            backgroundColor: '#f9f9f9'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
                            <div>
                              <h4 style={{ margin: '0 0 10px 0', color: '#1a1a1a' }}>
                                Trip #{trajet.depart_id} - {trajet.ligne?.point_depart || 'N/A'} → {trajet.ligne?.point_arrivee || 'N/A'}
                              </h4>
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', fontSize: '0.9em' }}>
                                <div>
                                  <strong>Bus:</strong> {trajet.bus?.immatriculation || 'N/A'} 
                                  ({trajet.bus?.marque || ''} {trajet.bus?.modele || ''})
                                </div>
                                <div>
                                  <strong>Destination:</strong> {trajet.destination?.nom || 'N/A'} 
                                  {trajet.destination?.ville ? ` - ${trajet.destination.ville}` : ''}
                                </div>
                                <div>
                                  <strong>Departure Time:</strong> {trajet.heure_depart || 'N/A'}
                                </div>
                                <div>
                                  <strong>Price:</strong> {formatPrice(trajet.prix || 0)}
                                </div>
                              </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <div style={{ fontSize: '1.2em', fontWeight: 'bold', color: '#27ae60' }}>
                                {formatPrice(trajet.ca_du_trajet)}
                              </div>
                              <div style={{ fontSize: '0.9em', color: '#666' }}>
                                {trajet.nombre_billets} ticket(s)
                              </div>
                            </div>
                          </div>

                          {/* Assigned drivers */}
                          {trajet.chauffeurs_assignes && trajet.chauffeurs_assignes.length > 0 && (
                            <div style={{ marginBottom: '15px', padding: '10px', backgroundColor: '#fff', borderRadius: '4px' }}>
                              <strong>Assigned Drivers:</strong>
                              <div style={{ marginTop: '5px' }}>
                                {trajet.chauffeurs_assignes.map((ch, idx) => (
                                  <span 
                                    key={idx}
                                    style={{ 
                                      display: 'inline-block',
                                      margin: '0 10px 5px 0',
                                      padding: '5px 10px',
                                      backgroundColor: ch.type === 'jour' ? '#ebf5fb' : '#ecf0f1',
                                      borderRadius: '4px',
                                      fontSize: '0.9em'
                                    }}
                                  >
                                    {ch.prenom} {ch.nom} ({ch.type})
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Cashiers */}
                          {trajet.billets && trajet.billets.length > 0 && (
                            <div>
                              <strong>Cashiers who sold tickets:</strong>
                              <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                                {Array.from(new Set(trajet.billets.map(b => b.caissiere?.username || 'N/A'))).map((username, idx) => {
                                  const billetsCaissiere = trajet.billets.filter(b => b.caissiere?.username === username);
                                  const caCaissiere = billetsCaissiere.reduce((sum, b) => sum + (b.montant || 0), 0);
                                  return (
                                    <div 
                                      key={idx}
                                      style={{ 
                                        padding: '8px 12px',
                                        backgroundColor: '#e8f5e9',
                                        borderRadius: '4px',
                                        fontSize: '0.9em'
                                      }}
                                    >
                                      {billetsCaissiere[0]?.caissiere?.first_name || username} {billetsCaissiere[0]?.caissiere?.last_name || ''}: 
                                      {' '}{formatPrice(caCaissiere)} ({billetsCaissiere.length} ticket(s))
                                    </div>
                                  );
                                })}
                              </div>

                              <details style={{ marginTop: '15px' }}>
                                <summary style={{ cursor: 'pointer', fontWeight: 'bold', color: '#3498db' }}>
                                  View All Transactions ({trajet.billets.length})
                                </summary>
                                <div style={{ marginTop: '10px', maxHeight: '300px', overflowY: 'auto' }}>
                                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9em' }}>
                                    <thead>
                                      <tr style={{ backgroundColor: '#f8f9fa' }}>
                                        <th style={{ padding: '8px', textAlign: 'left' }}>Client</th>
                                        <th style={{ padding: '8px', textAlign: 'left' }}>Cashier</th>
                                        <th style={{ padding: '8px', textAlign: 'left' }}>Amount</th>
                                        <th style={{ padding: '8px', textAlign: 'left' }}>Seat</th>
                                        <th style={{ padding: '8px', textAlign: 'left' }}>Payment</th>
                                        <th style={{ padding: '8px', textAlign: 'left' }}>Status</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {trajet.billets.map((billet) => (
                                        <tr key={billet.id} style={{ borderBottom: '1px solid #eee' }}>
                                          <td style={{ padding: '8px' }}>
                                            {billet.nom_client || 'N/A'}
                                            {billet.telephone_client && (
                                              <div style={{ fontSize: '0.85em', color: '#666' }}>
                                                {billet.telephone_client}
                                              </div>
                                            )}
                                          </td>
                                          <td style={{ padding: '8px' }}>
                                            {billet.caissiere?.first_name || billet.caissiere?.username || 'N/A'} 
                                            {billet.caissiere?.last_name ? ` ${billet.caissiere.last_name}` : ''}
                                          </td>
                                          <td style={{ padding: '8px', fontWeight: 'bold' }}>
                                            {formatPrice(billet.montant)}
                                          </td>
                                          <td style={{ padding: '8px' }}>{billet.siege || 'N/A'}</td>
                                          <td style={{ padding: '8px' }}>
                                            {billet.mode_paiement === 'espece' ? 'Cash' : 
                                             billet.mode_paiement === 'carte' ? 'Card' : 
                                             billet.mode_paiement === 'mobile' ? 'Mobile Payment' : 
                                             billet.mode_paiement || 'N/A'}
                                          </td>
                                          <td style={{ padding: '8px' }}>
                                            <span style={{
                                              padding: '2px 8px',
                                              borderRadius: '4px',
                                              backgroundColor: billet.statut === 'valide' || billet.statut === 'utilise' ? '#27ae60' : '#e74c3c',
                                              color: 'white',
                                              fontSize: '0.85em'
                                            }}>
                                              {billet.statut === 'valide' ? 'Valid' : 
                                               billet.statut === 'utilise' ? 'Used' : 
                                               billet.statut === 'annule' ? 'Cancelled' : 
                                               billet.statut === 'rembourse' ? 'Refunded' : 
                                               billet.statut || 'N/A'}
                                            </span>
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </details>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
}
