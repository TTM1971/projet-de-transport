import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import API_URL from '../config/api';
import { formatApiError } from '../utils/apiError';
import { useAuth } from '../context/AuthContext';
import Card from '../components/Card';

/**
 * Interface unique : chauffeurs (trajets), agents et gestionnaires (quarts de guichet).
 * - Gestionnaire : agents + chauffeurs uniquement.
 * - Admin : + gestionnaires.
 */
export default function HorairesEquipe() {
  const { user } = useAuth();
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('chauffeurs'); // chauffeurs | agents | gestionnaires

  const [selectedUserId, setSelectedUserId] = useState(null);
  const [shifts, setShifts] = useState([]);
  const [form, setForm] = useState({
    work_date: new Date().toISOString().slice(0, 10),
    start_time: '09:00',
    end_time: '17:00',
    break_minutes: 30,
    notes: '',
  });

  useEffect(() => {
    setSelectedUserId(null);
    setShifts([]);
  }, [tab]);

  useEffect(() => {
    let c = false;
    (async () => {
      try {
        const res = await axios.get(`${API_URL}/planning/schedulable-overview`);
        if (!c) setOverview(res.data);
      } catch (e) {
        if (!c) setError(formatApiError(e.response?.data?.detail, 'Chargement impossible'));
      } finally {
        if (!c) setLoading(false);
      }
    })();
    return () => {
      c = true;
    };
  }, []);

  const loadShifts = async (uid) => {
    setSelectedUserId(uid);
    try {
      const res = await axios.get(`${API_URL}/planning/staff-shifts/${uid}`);
      setShifts(res.data || []);
    } catch (e) {
      setError(formatApiError(e.response?.data?.detail, 'Impossible de charger les quarts'));
    }
  };

  const submitShift = async (e) => {
    e.preventDefault();
    if (!selectedUserId) return;
    try {
      await axios.post(`${API_URL}/planning/staff-shifts`, {
        user_id: selectedUserId,
        work_date: new Date(form.work_date + 'T12:00:00').toISOString(),
        start_time: form.start_time,
        end_time: form.end_time,
        timezone: 'America/Toronto',
        break_minutes: Number(form.break_minutes) || 0,
        notes: form.notes || null,
      });
      await loadShifts(selectedUserId);
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail, 'Erreur'));
    }
  };

  const removeShift = async (id) => {
    if (!window.confirm('Supprimer ce quart ?')) return;
    try {
      await axios.delete(`${API_URL}/planning/staff-shifts/${id}`);
      if (selectedUserId) await loadShifts(selectedUserId);
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail, 'Erreur'));
    }
  };

  if (loading) return <div className="page-container loading">Chargement…</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Horaires équipe</h1>
      </div>

      {error && <div className="error-message mb-4">{error}</div>}

      <div className="flex gap-2 mb-6 flex-wrap">
        <button
          type="button"
          className={tab === 'chauffeurs' ? 'btn-primary' : 'btn-secondary'}
          onClick={() => setTab('chauffeurs')}
        >
          Chauffeurs
        </button>
        <button
          type="button"
          className={tab === 'agents' ? 'btn-primary' : 'btn-secondary'}
          onClick={() => setTab('agents')}
        >
          Agents
        </button>
        {overview?.can_manage_gestionnaires && (
          <button
            type="button"
            className={tab === 'gestionnaires' ? 'btn-primary' : 'btn-secondary'}
            onClick={() => setTab('gestionnaires')}
          >
            Gestionnaires
          </button>
        )}
      </div>

      {tab === 'chauffeurs' && overview && (
        <Card title="Conducteurs">
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Statut</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {overview.chauffeurs.map((c) => (
                  <tr key={c.id}>
                    <td>
                      {c.prenom} {c.nom}
                    </td>
                    <td>{c.statut}</td>
                    <td>
                      <Link className="btn-edit" to={`/chauffeurs/${c.id}/planning`}>
                        Planning trajets
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === 'agents' && overview && (
        <Card title="Agents">
          <div className="grid gap-6" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))' }}>
            <div>
              <h4 className="mb-2">Sélectionner un agent</h4>
              <ul className="space-y-1">
                {overview.agents.map((a) => (
                  <li key={a.id}>
                    <button
                      type="button"
                      className={selectedUserId === a.id ? 'text-brand-700 font-semibold' : ''}
                      onClick={() => loadShifts(a.id)}
                    >
                      {a.first_name || a.username} {a.last_name || ''} - {a.username}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              {selectedUserId && (
                <>
                  <h4 className="mb-2">Nouveau quart</h4>
                  <form onSubmit={submitShift} className="space-y-3">
                    <label className="form-group">
                      Date
                      <input
                        type="date"
                        value={form.work_date}
                        onChange={(e) => setForm({ ...form, work_date: e.target.value })}
                        required
                        className="w-full"
                      />
                    </label>
                    <label className="form-group">
                      Début
                      <input
                        type="time"
                        value={form.start_time}
                        onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                        required
                        className="w-full"
                      />
                    </label>
                    <label className="form-group">
                      Fin
                      <input
                        type="time"
                        value={form.end_time}
                        onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                        required
                        className="w-full"
                      />
                    </label>
                    <label className="form-group">
                      Pause en min
                      <input
                        type="number"
                        min="0"
                        value={form.break_minutes}
                        onChange={(e) => setForm({ ...form, break_minutes: e.target.value })}
                        className="w-full"
                      />
                    </label>
                    <button type="submit" className="btn-primary">
                      Enregistrer le quart
                    </button>
                  </form>
                  <h4 className="mt-6 mb-2">Quarts enregistrés</h4>
                  <ul className="text-sm space-y-1">
                    {shifts.map((s) => (
                      <li key={s.id} className="flex justify-between gap-2">
                        <span>
                          {String(s.work_date).slice(0, 10)} {s.start_time}–{s.end_time} - pause {s.break_minutes} min
                        </span>
                        <button type="button" className="btn-delete text-xs" onClick={() => removeShift(s.id)}>
                          Supprimer
                        </button>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </div>
        </Card>
      )}

      {tab === 'gestionnaires' && overview?.can_manage_gestionnaires && (
        <Card title="Gestionnaires">
          <div className="grid gap-6" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))' }}>
            <div>
              <h4 className="mb-2">Sélectionner un gestionnaire</h4>
              <ul className="space-y-1">
                {overview.gestionnaires.map((a) => (
                  <li key={a.id}>
                    <button
                      type="button"
                      className={selectedUserId === a.id ? 'text-brand-700 font-semibold' : ''}
                      onClick={() => loadShifts(a.id)}
                    >
                      {a.first_name || a.username} {a.last_name || ''} - {a.username}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              {selectedUserId && overview.gestionnaires.some((g) => g.id === selectedUserId) && (
                <>
                  <h4 className="mb-2">Nouveau quart</h4>
                  <form onSubmit={submitShift} className="space-y-3">
                    <label className="form-group">
                      Date
                      <input
                        type="date"
                        value={form.work_date}
                        onChange={(e) => setForm({ ...form, work_date: e.target.value })}
                        required
                        className="w-full"
                      />
                    </label>
                    <label className="form-group">
                      Début
                      <input
                        type="time"
                        value={form.start_time}
                        onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                        required
                        className="w-full"
                      />
                    </label>
                    <label className="form-group">
                      Fin
                      <input
                        type="time"
                        value={form.end_time}
                        onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                        required
                        className="w-full"
                      />
                    </label>
                    <label className="form-group">
                      Pause en min
                      <input
                        type="number"
                        min="0"
                        value={form.break_minutes}
                        onChange={(e) => setForm({ ...form, break_minutes: e.target.value })}
                        className="w-full"
                      />
                    </label>
                    <button type="submit" className="btn-primary">
                      Enregistrer le quart
                    </button>
                  </form>
                  <h4 className="mt-6 mb-2">Quarts enregistrés</h4>
                  <ul className="text-sm space-y-1">
                    {shifts.map((s) => (
                      <li key={s.id} className="flex justify-between gap-2">
                        <span>
                          {String(s.work_date).slice(0, 10)} {s.start_time}–{s.end_time} - pause {s.break_minutes} min
                        </span>
                        <button type="button" className="btn-delete text-xs" onClick={() => removeShift(s.id)}>
                          Supprimer
                        </button>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
