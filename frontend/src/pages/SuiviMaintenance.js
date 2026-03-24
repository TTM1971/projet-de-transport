import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import { translateStatus, translateBreakdownType, translateSeverity } from '../utils/translations';
import API_URL from '../config/api';

export default function SuiviMaintenance() {
  const location = useLocation();
  const [ateliers, setAteliers] = useState([]);
  const [buses, setBuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingIntervention, setEditingIntervention] = useState(null);
  const [formData, setFormData] = useState({
    bus_id: '',
    date_entree: new Date().toISOString().slice(0, 16),
    date_sortie: '',
    type_panne: '',
    gravite: '',
    description: '',
    pieces_remplacees: '',
    cout_intervention: '',
    statut: 'en_attente'
  });

  useEffect(() => {
    fetchData();
  }, []);

  // Close modal when navigating to another page
  useEffect(() => {
    setShowModal(false);
  }, [location.pathname]);

  const fetchData = async () => {
    try {
      const [busesRes, ateliersRes] = await Promise.all([
        axios.get(`${API_URL}/bus/`),
        axios.get(`${API_URL}/ateliers/`)
      ]);
      setBuses(busesRes.data);
      setAteliers(ateliersRes.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        bus_id: parseInt(formData.bus_id),
        date_entree: formData.date_entree ? new Date(formData.date_entree).toISOString() : new Date().toISOString(),
        date_sortie: formData.date_sortie ? new Date(formData.date_sortie).toISOString() : null,
        type_panne: formData.type_panne || null,
        gravite: formData.gravite || null,
        description: formData.description || null,
        pieces_remplacees: formData.pieces_remplacees || null,
        cout_intervention: formData.cout_intervention ? parseFloat(formData.cout_intervention) : null,
        statut: formData.statut || 'en_attente'
      };
      
      if (editingIntervention) {
        await axios.put(`${API_URL}/ateliers/${editingIntervention.id}`, payload);
        alert('Intervention updated successfully!');
      } else {
        await axios.post(`${API_URL}/ateliers/`, payload);
        alert('Maintenance intervention recorded successfully!');
      }
      
      setShowModal(false);
      setEditingIntervention(null);
      setFormData({
        bus_id: '',
        date_entree: new Date().toISOString().slice(0, 16),
        date_sortie: '',
        type_panne: '',
        gravite: '',
        description: '',
        pieces_remplacees: '',
        cout_intervention: '',
        statut: 'en_attente'
      });
      fetchData();
    } catch (error) {
      alert('Error: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  const busMaintenance = buses.filter(b => b.statut === 'en_maintenance');

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Maintenance Tracking</h1>
        <button 
          className="btn-primary" 
          onClick={() => {
            setEditingIntervention(null);
            setFormData({
              bus_id: '',
              date_entree: new Date().toISOString().slice(0, 16),
              date_sortie: '',
              type_panne: '',
              gravite: '',
              description: '',
              pieces_remplacees: '',
              cout_intervention: '',
              statut: 'en_attente'
            });
            setShowModal(true);
          }}
        >
          + New Intervention
        </button>
      </div>

      <Card title={`Buses in Maintenance (${busMaintenance.length})`}>
        {busMaintenance.length === 0 ? (
          <p>No buses in maintenance currently</p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '15px' }}>
            {busMaintenance.map(bus => (
              <div key={bus.id} style={{
                padding: '15px',
                border: '2px solid #e67e22',
                borderRadius: '8px',
                background: '#fff3e0'
              }}>
                <h4>{bus.immatriculation}</h4>
                <p><strong>Model:</strong> {bus.marque} {bus.modele}</p>
                <p><strong>Capacity:</strong> {bus.capacite} seats</p>
                <p style={{ color: '#e67e22', fontWeight: 'bold' }}>In Maintenance</p>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Intervention History">
        {ateliers.length === 0 ? (
          <p>No interventions recorded.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f8f8' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Bus</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Entry Date</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Breakdown Type</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Severity</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {ateliers.map((atelier) => {
                  const bus = buses.find(b => b.id === atelier.bus_id);
                  return (
                    <tr key={atelier.id} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '12px' }}>{bus?.immatriculation || `Bus #${atelier.bus_id}`}</td>
                      <td style={{ padding: '12px' }}>
                        {atelier.date_entree ? new Date(atelier.date_entree).toLocaleDateString('en-US') : 'N/A'}
                      </td>
                      <td style={{ padding: '12px' }}>{translateBreakdownType(atelier.type_panne) || 'N/A'}</td>
                      <td style={{ padding: '12px' }}>{translateSeverity(atelier.gravite) || 'N/A'}</td>
                      <td style={{ padding: '12px' }}>{translateStatus(atelier.statut) || 'N/A'}</td>
                      <td style={{ padding: '12px' }}>
                        <button 
                          className="btn-edit"
                          onClick={() => {
                            setEditingIntervention(atelier);
                            setFormData({
                              bus_id: atelier.bus_id.toString(),
                              date_entree: atelier.date_entree ? new Date(atelier.date_entree).toISOString().slice(0, 16) : new Date().toISOString().slice(0, 16),
                              date_sortie: atelier.date_sortie ? new Date(atelier.date_sortie).toISOString().slice(0, 16) : '',
                              type_panne: atelier.type_panne || '',
                              gravite: atelier.gravite || '',
                              description: atelier.description || '',
                              pieces_remplacees: atelier.pieces_remplacees || '',
                              cout_intervention: atelier.cout_intervention || '',
                              statut: atelier.statut || 'en_attente'
                            });
                            setShowModal(true);
                          }}
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {showModal && (
        <div className="modal-overlay" onClick={() => { setShowModal(false); setEditingIntervention(null); }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px' }}>
            <h2>{editingIntervention ? 'Edit Intervention' : 'Record Maintenance Intervention'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Bus *</label>
                <select 
                  required 
                  value={formData.bus_id} 
                  onChange={(e) => setFormData({...formData, bus_id: e.target.value})}
                  disabled={!!editingIntervention}
                >
                  <option value="">Select a bus</option>
                  {buses.map(b => (
                    <option key={b.id} value={b.id}>
                      {b.immatriculation} - {b.marque} {b.modele}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Breakdown Type *</label>
                <select 
                  required
                  value={formData.type_panne} 
                  onChange={(e) => setFormData({...formData, type_panne: e.target.value})}
                >
                  <option value="">Select</option>
                  <option value="freinage">Braking</option>
                  <option value="pneus">Tires</option>
                  <option value="moteur">Engine</option>
                  <option value="électrique">Electrical</option>
                  <option value="climatisation">Air Conditioning</option>
                  <option value="carrosserie">Bodywork</option>
                  <option value="transmission">Transmission</option>
                  <option value="autre">Other</option>
                </select>
              </div>

              <div className="form-group">
                <label>Severity *</label>
                <select 
                  required
                  value={formData.gravite} 
                  onChange={(e) => setFormData({...formData, gravite: e.target.value})}
                >
                  <option value="">Select</option>
                  <option value="mineure">Minor</option>
                  <option value="moyenne">Medium</option>
                  <option value="majeure">Major</option>
                  <option value="critique">Critical</option>
                </select>
              </div>

              <div className="form-group">
                <label>Problem Description *</label>
                <textarea
                  required
                  rows="4"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Describe the problem encountered..."
                />
              </div>

              <div className="form-group">
                <label>Replaced Parts</label>
                <input
                  type="text"
                  value={formData.pieces_remplacees}
                  onChange={(e) => setFormData({...formData, pieces_remplacees: e.target.value})}
                  placeholder="Ex: Filters, Tires, Brakes, Battery..."
                />
              </div>

              <div className="form-group">
                <label>Intervention Cost</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.cout_intervention}
                  onChange={(e) => setFormData({...formData, cout_intervention: e.target.value})}
                  placeholder="0.00"
                />
              </div>

              <div className="form-group">
                <label>Entry Date *</label>
                <input
                  type="datetime-local"
                  required
                  value={formData.date_entree}
                  onChange={(e) => setFormData({...formData, date_entree: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Exit Date</label>
                <input
                  type="datetime-local"
                  value={formData.date_sortie}
                  onChange={(e) => setFormData({...formData, date_sortie: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Status *</label>
                <select 
                  required
                  value={formData.statut} 
                  onChange={(e) => setFormData({...formData, statut: e.target.value})}
                >
                  <option value="en_attente">Pending</option>
                  <option value="en_cours">In Progress</option>
                  <option value="terminee">Completed</option>
                  <option value="annulee">Cancelled</option>
                </select>
              </div>

              <div className="form-actions">
                <button 
                  type="button" 
                  className="btn-secondary" 
                  onClick={() => {
                    setShowModal(false);
                    setEditingIntervention(null);
                    setFormData({
                      bus_id: '',
                      date_entree: new Date().toISOString().slice(0, 16),
                      date_sortie: '',
                      type_panne: '',
                      gravite: '',
                      description: '',
                      pieces_remplacees: '',
                      cout_intervention: '',
                      statut: 'en_attente'
                    });
                  }}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingIntervention ? 'Update' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
