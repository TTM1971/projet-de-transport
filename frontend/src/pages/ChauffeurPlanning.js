import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import API_URL from '../config/api';
import { formatApiError } from '../utils/apiError';
import Card from '../components/Card';

/**
 * Planning conducteur : assignation de départs, suggestions ML (entraînement = admin uniquement).
 */
export default function ChauffeurPlanning() {
  const { chauffeurId } = useParams();
  const [loading, setLoading] = useState(true);
  const [chauffeur, setChauffeur] = useState(null);
  const [departs, setDeparts] = useState([]);
  const [lignes, setLignes] = useState([]);
  const [candidats, setCandidats] = useState([]);
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');
  const [planningDate, setPlanningDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [selectedTripId, setSelectedTripId] = useState(null);
  const [selectedFreeHour, setSelectedFreeHour] = useState(null);
  const [selectedDepartForSlot, setSelectedDepartForSlot] = useState('');
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignError, setAssignError] = useState('');

  const loadPlanning = async () => {
    setError('');
    const res = await axios.get(`${API_URL}/chauffeurs/${chauffeurId}/planning/departs`);
    setChauffeur(res.data.chauffeur);
    setDeparts(res.data.departs || []);
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [lr, dr] = await Promise.all([
          axios.get(`${API_URL}/lignes/`),
          axios.get(`${API_URL}/departs/?skip=0&limit=500`),
        ]);
        if (!cancelled) {
          setLignes(lr.data || []);
          const future = new Date();
          future.setHours(0, 0, 0, 0);
          const list = (dr.data || []).filter((d) => {
            const dt = new Date(d.date_depart);
            return dt >= future && d.statut !== 'annule';
          });
          setCandidats(list);
        }
      } catch (e) {
        if (!cancelled) setError(formatApiError(e.response?.data?.detail, 'Chargement impossible'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [chauffeurId]);

  useEffect(() => {
    if (!chauffeurId) return;
    (async () => {
      try {
        await loadPlanning();
      } catch (e) {
        setError(formatApiError(e.response?.data?.detail, 'Chargement planning impossible'));
      }
    })();
  }, [chauffeurId]);

  const handleAssignFromSlot = async (e) => {
    e.preventDefault();
    setMsg('');
    setAssignError('');
    if (!selectedDepartForSlot) return;
    try {
      await axios.post(`${API_URL}/chauffeurs/${chauffeurId}/planning/assign-depart`, {
        depart_id: Number(selectedDepartForSlot),
      });
      setMsg('Départ attribué avec succès.');
      setSelectedDepartForSlot('');
      setSelectedFreeHour(null);
      setShowAssignModal(false);
      await loadPlanning();
    } catch (err) {
      setAssignError(formatApiError(err.response?.data?.detail, 'Assignation impossible'));
    }
  };

  const canUnassignDepart = (d) => {
    if (!d?.date || !d?.heure) return false;
    const departAt = new Date(`${d.date}T${String(d.heure).slice(0, 5)}:00`);
    if (Number.isNaN(departAt.getTime())) return false;
    const nowPlus2h = new Date(Date.now() + 2 * 60 * 60 * 1000);
    return departAt > nowPlus2h;
  };

  const handleUnassign = async (departId) => {
    setMsg('');
    setError('');
    try {
      await axios.delete(`${API_URL}/chauffeurs/${chauffeurId}/planning/unassign-depart/${departId}`);
      setMsg('Trajet retiré du chauffeur avec succès.');
      if (selectedTripId === departId) setSelectedTripId(null);
      await loadPlanning();
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail, 'Suppression impossible'));
    }
  };

  if (loading && !chauffeur) {
    return <div className="page-container loading">Chargement…</div>;
  }

  const lineDurationById = new Map(lignes.map((l) => [l.id, Number(l.duree_minutes || 120)]));
  const dayTrips = departs
    .filter((d) => d.date === planningDate)
    .map((d) => {
      const [h, m] = String(d.heure || "00:00").split(":").map((x) => Number(x || 0));
      const start = h * 60 + m;
      const tripDuration = lineDurationById.get(d.ligne_id) || 120;
      const blockedDuration = tripDuration + 180; // Pause obligatoire 3h après trajet
      return { ...d, start, end: start + blockedDuration, tripDuration, blockedDuration };
    })
    .sort((a, b) => a.start - b.start);

  const slots = [];
  for (let hour = 6; hour < 22; hour += 1) {
    const slotStart = hour * 60;
    const slotEnd = (hour + 1) * 60;
    const occupiedBy = dayTrips.find((t) => t.start < slotEnd && t.end > slotStart);
    slots.push({ hour, occupiedBy });
  }
  const selectedTrip = dayTrips.find((t) => t.id === selectedTripId) || null;
  const assignedWindows = (departs || [])
    .filter((d) => d.date && d.heure)
    .map((d) => {
      const [h, m] = String(d.heure || "00:00").split(":").map((x) => Number(x || 0));
      const startDate = new Date(`${d.date}T${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:00`);
      const tripDuration = lineDurationById.get(d.ligne_id) || 120;
      const blockedMinutes = tripDuration + 180;
      const endDate = new Date(startDate.getTime() + blockedMinutes * 60000);
      return { startDate, endDate };
    });
  const hasOverlap = (aStart, aEnd, bStart, bEnd) => aStart < bEnd && bStart < aEnd;
  const slotCandidates = selectedFreeHour === null
    ? []
    : (candidats || []).filter((d) => {
        if (!d.date_depart) return false;
        const dt = new Date(d.date_depart);
        const dateStr = dt.toISOString().slice(0, 10);
        if (dateStr !== planningDate) return false;
        if (Number(d.chauffeur_id) === Number(chauffeurId)) return false;
        const h = dt.getHours();
        if (h !== selectedFreeHour) return false;
        const tripDuration = lineDurationById.get(d.ligne_id) || 120;
        const blockedMinutes = tripDuration + 180;
        const candStart = dt;
        const candEnd = new Date(dt.getTime() + blockedMinutes * 60000);
        return !assignedWindows.some((w) => hasOverlap(candStart, candEnd, w.startDate, w.endDate));
      });

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="mt-2">
            Planning — {chauffeur ? `${chauffeur.prenom} ${chauffeur.nom}` : `ID ${chauffeurId}`}
          </h1>
        </div>
      </div>

      {error && <div className="error-message mb-4">{error}</div>}
      {msg && <div className="success-banner mb-4" style={{ padding: '10px', background: '#e8f5e9', borderRadius: 8 }}>{msg}</div>}

      <Card title="Planning journalier">
        <div style={{ marginBottom: 12 }}>
          <label className="form-group">
            <span>Date à visualiser</span>
            <input type="date" value={planningDate} onChange={(e) => setPlanningDate(e.target.value)} />
          </label>
        </div>
        <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))' }}>
          {slots.map((s) => (
            <button
              key={s.hour}
              type="button"
              onClick={() => {
                if (s.occupiedBy) {
                  setSelectedTripId(s.occupiedBy.id);
                  setSelectedFreeHour(null);
                  setSelectedDepartForSlot('');
                  setAssignError('');
                } else {
                  setSelectedTripId(null);
                  setSelectedFreeHour(s.hour);
                  setAssignError('');
                  setShowAssignModal(true);
                }
              }}
              className={s.occupiedBy ? 'btn-secondary' : 'btn-primary'}
              style={{ textAlign: 'left', opacity: s.occupiedBy ? 1 : 0.7 }}
            >
              <div><strong>{String(s.hour).padStart(2, '0')}:00 - {String(s.hour + 1).padStart(2, '0')}:00</strong></div>
              <div style={{ fontSize: 12 }}>
                {s.occupiedBy
                  ? `Occupé · #${s.occupiedBy.id} ${s.occupiedBy.ligne_nom || s.occupiedBy.ligne_id}`
                  : 'Libre'}
              </div>
            </button>
          ))}
        </div>
        {selectedTrip && (
          <div style={{ marginTop: 12, padding: 12, border: '1px solid #d7dde5', borderRadius: 8 }}>
            <strong>Détail du trajet sélectionné</strong>
            <div>ID: #{selectedTrip.id}</div>
            <div>Heure: {selectedTrip.heure}</div>
            <div>Ligne: {selectedTrip.ligne_nom || selectedTrip.ligne_id}</div>
            <div>Destination: {selectedTrip.destination_nom || selectedTrip.destination_id}</div>
            <div>Durée trajet: {selectedTrip.tripDuration} min</div>
            <div>Blocage total - pause incluse: {selectedTrip.blockedDuration} min</div>
            <div>Statut: {selectedTrip.statut}</div>
          </div>
        )}
      </Card>

      {showAssignModal && selectedFreeHour !== null && (
        <div className="modal-overlay" onClick={() => { setShowAssignModal(false); setSelectedDepartForSlot(''); setAssignError(''); }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Assigner un départ</h2>
            <div style={{ marginBottom: 8 }}>
              Créneau libre sélectionné: <strong>{String(selectedFreeHour).padStart(2, '0')}:00</strong>
            </div>
            <form onSubmit={handleAssignFromSlot} className="space-y-3">
              <label className="form-group">
                <span>Choisir un départ à assigner</span>
                <select
                  value={selectedDepartForSlot}
                  onChange={(e) => setSelectedDepartForSlot(e.target.value)}
                  required
                  className="w-full"
                >
                  <option value="">— Choisir —</option>
                  {slotCandidates.map((d) => (
                    <option key={d.id} value={d.id}>
                      #{d.id} · {String(d.date_depart).slice(0, 16).replace('T', ' ')} · ligne {d.ligne_id} · bus {d.bus_id}
                    </option>
                  ))}
                </select>
              </label>
              {slotCandidates.length === 0 && (
                <div style={{ marginTop: 8, fontSize: 13, color: '#666' }}>
                  Aucun départ disponible sur ce créneau.
                </div>
              )}
              {assignError && (
                <div className="error-message" style={{ marginTop: 8 }}>
                  {assignError}
                </div>
              )}
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => { setShowAssignModal(false); setSelectedDepartForSlot(''); setAssignError(''); }}>
                  Annuler
                </button>
                <button type="submit" className="btn-primary" disabled={slotCandidates.length === 0}>
                  Assigner ce départ
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <Card title="Trajets assignés à ce chauffeur">
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Heure</th>
                <th>Ligne</th>
                <th>Destination</th>
                <th>Statut</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {departs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="empty-state">
                    Aucun départ assigné
                  </td>
                </tr>
              ) : (
                departs.map((d) => (
                  <tr key={d.id}>
                    <td>{d.id}</td>
                    <td>{d.date}</td>
                    <td>{d.heure}</td>
                    <td>{d.ligne_nom || d.ligne_id}</td>
                    <td>{d.destination_nom || d.destination_id}</td>
                    <td>{d.statut}</td>
                    <td>
                      <button
                        type="button"
                        className="btn-delete"
                        disabled={!canUnassignDepart(d)}
                        title={canUnassignDepart(d) ? 'Retirer ce trajet' : 'Suppression autorisée uniquement au moins 2h avant le départ'}
                        onClick={() => handleUnassign(d.id)}
                        style={!canUnassignDepart(d) ? { opacity: 0.55, cursor: 'not-allowed' } : undefined}
                      >
                        Retirer
                      </button>
                    </td>
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
