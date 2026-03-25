import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import StatsWidget from '../components/StatsWidget';
import { formatPrice } from '../utils/currency';
import API_URL from '../config/api';

export default function DashboardVille() {
  const { ville } = useParams();
  const city = decodeURIComponent(ville || '');
  const [summary, setSummary] = useState(null);
  const [historical, setHistorical] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setLoadError('');
        const [s, h] = await Promise.all([
          axios.get(`${API_URL}/analytics/dashboard/summary?ville=${encodeURIComponent(city)}`),
          axios.get(`${API_URL}/analytics/dashboard/historical?days=30&ville=${encodeURIComponent(city)}`),
        ]);
        setSummary(s.data);
        setHistorical(h.data?.data || []);
      } catch (e) {
        console.error(e);
        setLoadError(
          "Impossible de charger le dashboard. Vérifiez que l'API est démarrée (port 8000)."
        );
      } finally {
        setLoading(false);
      }
    })();
  }, [city]);

  if (loading) return <div className="loading">Chargement...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Dashboard - {city}</h1>
      </div>

      {loadError && (
        <div className="error-message" style={{ marginBottom: 16 }}>
          {loadError}
        </div>
      )}

      {summary && (
        <div className="stats-grid">
          <StatsWidget title="Total Revenue" value={formatPrice(summary.chiffre_affaires_total)} color="#27ae60" />
          <StatsWidget title="Total Tickets Sold" value={summary.total_billets} color="#f39c12" />
          <StatsWidget title="Active Lines" value={summary.lignes_actives} color="#9b59b6" />
          <StatsWidget title="Destinations" value={summary.destinations} color="#e74c3c" />
        </div>
      )}

      <Card title={`Historique 30 jours - ${city}`}>
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>CA</th>
                <th>Billets</th>
                <th>Lignes actives</th>
              </tr>
            </thead>
            <tbody>
              {historical.length === 0 ? (
                <tr><td colSpan={4} className="empty-state">Aucune donnée</td></tr>
              ) : historical.map((d) => (
                <tr key={d.date}>
                  <td>{d.date}</td>
                  <td>{formatPrice(d.chiffre_affaires || 0)}</td>
                  <td>{d.billets_vendus || 0}</td>
                  <td>{d.lignes_actives || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

