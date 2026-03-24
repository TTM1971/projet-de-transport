import React, { useEffect, useState } from 'react';
import axios from 'axios';
import API_URL from '../config/api';
import { formatApiError } from '../utils/apiError';
import Card from '../components/Card';

/**
 * Espace conducteur : tableau de bord + trajets à venir + historique récent.
 */
export default function ChauffeurEspace() {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [departs, setDeparts] = useState([]);
  const [historique, setHistorique] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [me, dash, fut, hist] = await Promise.all([
          axios.get(`${API_URL}/chauffeur/me`),
          axios.get(`${API_URL}/chauffeur/me/dashboard`),
          axios.get(`${API_URL}/chauffeur/me/departs?futures_seulement=true`),
          axios.get(`${API_URL}/chauffeur/me/historique?limit=50`),
        ]);
        if (!cancelled) {
          setProfile(me.data);
          setDashboard(dash.data);
          setDeparts(fut.data?.departs || []);
          setHistorique(hist.data?.departs || []);
        }
      } catch (e) {
        if (!cancelled) {
          setError(formatApiError(e.response?.data?.detail, 'Impossible de charger votre espace'));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <div className="page-container loading">Chargement…</div>;
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-message">{error}</div>
        <p className="text-sm text-slate-600 mt-2">
          Si votre compte vient d’être créé, un administrateur doit lier votre utilisateur à une fiche chauffeur
          (endpoint <code>PUT /chauffeurs/&#123;id&#125;/link-user</code>).
        </p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Espace chauffeur</h1>
        <p className="text-slate-600">
          Bonjour {profile?.prenom} {profile?.nom}
        </p>
      </div>

      <div
        className="grid gap-4 mb-8"
        style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}
      >
        <div className="card p-4">
          <div className="text-sm text-slate-500">Trajets effectués</div>
          <div className="text-2xl font-semibold">{dashboard?.trajets_effectues ?? '—'}</div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-slate-500">À venir</div>
          <div className="text-2xl font-semibold">{dashboard?.trajets_a_venir ?? '—'}</div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-slate-500">Passagers (billets sur trajets terminés)</div>
          <div className="text-2xl font-semibold">{dashboard?.passagers_transportes_estime ?? '—'}</div>
        </div>
      </div>

      <Card title="Prochains trajets">
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Heure</th>
                <th>Ligne</th>
                <th>Destination</th>
                <th>Billets</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {departs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="empty-state">
                    Aucun trajet à venir
                  </td>
                </tr>
              ) : (
                departs.map((d) => (
                  <tr key={d.id}>
                    <td>{d.date}</td>
                    <td>{d.heure}</td>
                    <td>{d.ligne_nom || d.ligne_id}</td>
                    <td>{d.destination_nom || d.destination_id}</td>
                    <td>{d.nb_billets}</td>
                    <td>{d.statut}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Historique récent (terminés)">
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Heure</th>
                <th>Ligne</th>
                <th>Destination</th>
                <th>Billets</th>
              </tr>
            </thead>
            <tbody>
              {historique.length === 0 ? (
                <tr>
                  <td colSpan={5} className="empty-state">
                    Aucun historique
                  </td>
                </tr>
              ) : (
                historique.map((d) => (
                  <tr key={d.id}>
                    <td>{d.date}</td>
                    <td>{d.heure}</td>
                    <td>{d.ligne_nom || d.ligne_id}</td>
                    <td>{d.destination_nom || d.destination_id}</td>
                    <td>{d.nb_billets}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
