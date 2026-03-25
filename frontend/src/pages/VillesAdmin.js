import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import API_URL from '../config/api';
import { useAuth } from '../context/AuthContext';
import { formatApiError } from '../utils/apiError';

export default function VillesAdmin() {
  const navigate = useNavigate();
  const { setActiveCity } = useAuth();
  const [active, setActive] = useState([]);
  const [available, setAvailable] = useState([]);
  const [selected, setSelected] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const load = async () => {
    const res = await axios.get(`${API_URL}/villes/`);
    setActive(res.data.active || []);
    setAvailable(res.data.available_to_add || []);
  };

  useEffect(() => {
    (async () => {
      try {
        setLoadError('');
        await load();
      } catch (e) {
        console.error(e);
        if (e.response) {
          setLoadError(
            formatApiError(
              e.response.data?.detail,
              `Erreur ${e.response.status}`,
            ),
          );
        } else if (e.code === 'ERR_NETWORK' || (e.message || '').includes('Network Error')) {
          setLoadError(
            "Impossible de joindre l'API. Lancez la stack : « docker compose up -d » depuis la racine du projet, ou uvicorn sur le port 8000. Si vous utilisez le frontend dans Docker, ouvrez l'app via http://localhost (Nginx) ou http://localhost:3000 ; vérifiez les logs du conteneur frontend ([setupProxy] doit pointer vers le backend).",
          );
        } else {
          setLoadError(e.message || 'Erreur lors du chargement des villes.');
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const addVille = async (e) => {
    e.preventDefault();
    if (!selected) return;
    await axios.post(`${API_URL}/villes/`, { ville: selected });
    setSelected('');
    await load();
  };

  if (loading) return <div className="loading">Chargement...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Villes</h1>
      </div>

      {loadError && (
        <div className="error-message" style={{ marginBottom: 16 }}>
          {loadError}
        </div>
      )}

      <Card title="Ajouter une ville">
        <form onSubmit={addVille} style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <select value={selected} onChange={(e) => setSelected(e.target.value)} required>
            <option value="">-- Choisir une ville --</option>
            {available.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
          <button type="submit" className="btn-primary">Ajouter</button>
        </form>
      </Card>

      <Card title="Villes actives">
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Ville</th>
                <th>Dashboard ville</th>
              </tr>
            </thead>
            <tbody>
              {active.length === 0 ? (
                <tr><td colSpan={2} className="empty-state">Aucune ville active</td></tr>
              ) : active.map((v) => (
                <tr key={v}>
                  <td>{v}</td>
                  <td>
                    <button type="button" className="btn-edit" onClick={() => { setActiveCity(v); navigate(`/dashboard/ville/${encodeURIComponent(v)}`); }}>
                      Ouvrir
                    </button>
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

