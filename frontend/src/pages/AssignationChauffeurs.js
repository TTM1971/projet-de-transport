import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import BackButton from '../components/BackButton';
import API_URL from '../config/api';

export default function AssignationChauffeurs() {
  const { busId } = useParams();
  const navigate = useNavigate();
  const [bus, setBus] = useState(null);
  const [chauffeurs, setChauffeurs] = useState([]);
  const [assignations, setAssignations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    chauffeur_id: '',
    type_affectation: 'jour',
    date_debut: new Date().toISOString().split('T')[0],
    notes: ''
  });

  useEffect(() => {
    if (busId) {
      fetchBusDetails();
      fetchChauffeurs();
      fetchAssignations();
    }
  }, [busId]);

  const fetchBusDetails = async () => {
    try {
      const response = await axios.get(`${API_URL}/bus/${busId}`);
      setBus(response.data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const fetchChauffeurs = async () => {
    try {
      const response = await axios.get(`${API_URL}/chauffeurs/`);
      // Filter only active drivers
      setChauffeurs(response.data.filter(c => c.statut === 'actif'));
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const fetchAssignations = async () => {
    try {
      const response = await axios.get(`${API_URL}/bus/${busId}/chauffeurs`);
      setAssignations(response.data.chauffeurs || []);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/bus-chauffeurs/`, {
        bus_id: parseInt(busId),
        chauffeur_id: parseInt(formData.chauffeur_id),
        type_affectation: formData.type_affectation,
        date_debut: formData.date_debut ? new Date(formData.date_debut).toISOString() : new Date().toISOString(),
        notes: formData.notes || null
      });
      alert('Driver assigned successfully!');
      setShowModal(false);
      setFormData({
        chauffeur_id: '',
        type_affectation: 'jour',
        date_debut: new Date().toISOString().split('T')[0],
        notes: ''
      });
      fetchAssignations();
    } catch (error) {
      alert('Error: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleTerminerAssignation = async (assignationId) => {
    if (!window.confirm('Terminate this assignment?')) return;
    try {
      await axios.put(`${API_URL}/bus-chauffeurs/${assignationId}`, {
        date_fin: new Date().toISOString(),
        is_actif: false
      });
      alert('Assignment terminated successfully!');
      fetchAssignations();
    } catch (error) {
      alert('Error: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!bus) return <div className="loading">Bus not found</div>;

  const chauffeurJour = assignations.find(a => a.type_affectation === 'jour');
  const chauffeurNuit = assignations.find(a => a.type_affectation === 'nuit');

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div style={{ marginBottom: '20px' }}>
            <BackButton />
          </div>
          <h1>Driver Assignment - Bus {bus.immatriculation}</h1>
        </div>
        <button 
          className="btn-primary" 
          onClick={() => setShowModal(true)}
        >
          + Assign Driver
        </button>
      </div>

      <Card title="Current Assignments">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          <div style={{
            padding: '20px',
            border: '2px solid #3498db',
            borderRadius: '8px',
            backgroundColor: '#ebf5fb'
          }}>
            <h3 style={{ marginTop: 0, color: '#2980b9' }}>Day Driver</h3>
            {chauffeurJour ? (
              <div>
                <p><strong>Name:</strong> {chauffeurJour.chauffeur?.prenom} {chauffeurJour.chauffeur?.nom}</p>
                <p><strong>License:</strong> {chauffeurJour.chauffeur?.numero_permis}</p>
                <p><strong>Since:</strong> {new Date(chauffeurJour.date_debut).toLocaleDateString('en-US')}</p>
                <button 
                  className="btn-secondary"
                  onClick={() => handleTerminerAssignation(chauffeurJour.assignation_id)}
                  style={{ marginTop: '10px' }}
                >
                  Terminate Assignment
                </button>
              </div>
            ) : (
              <p style={{ color: '#7f8c8d', fontStyle: 'italic' }}>No driver assigned</p>
            )}
          </div>

          <div style={{
            padding: '20px',
            border: '2px solid #2c3e50',
            borderRadius: '8px',
            backgroundColor: '#ecf0f1'
          }}>
            <h3 style={{ marginTop: 0, color: '#34495e' }}>Night Driver</h3>
            {chauffeurNuit ? (
              <div>
                <p><strong>Name:</strong> {chauffeurNuit.chauffeur?.prenom} {chauffeurNuit.chauffeur?.nom}</p>
                <p><strong>License:</strong> {chauffeurNuit.chauffeur?.numero_permis}</p>
                <p><strong>Since:</strong> {new Date(chauffeurNuit.date_debut).toLocaleDateString('en-US')}</p>
                <button 
                  className="btn-secondary"
                  onClick={() => handleTerminerAssignation(chauffeurNuit.assignation_id)}
                  style={{ marginTop: '10px' }}
                >
                  Terminate Assignment
                </button>
              </div>
            ) : (
              <p style={{ color: '#7f8c8d', fontStyle: 'italic' }}>No driver assigned</p>
            )}
          </div>
        </div>

        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontStyle: 'italic', color: '#666' }}>
            <strong>Note:</strong> Each bus is assigned to two drivers who alternate their schedules (day/night). 
            If one driver is on leave, the other takes over.
          </p>
        </div>
      </Card>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Assign Driver to Bus</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Driver *</label>
                <select 
                  required
                  value={formData.chauffeur_id} 
                  onChange={(e) => setFormData({...formData, chauffeur_id: e.target.value})}
                >
                  <option value="">Select a driver</option>
                  {chauffeurs.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.prenom} {c.nom} - {c.numero_permis}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Assignment Type *</label>
                <select 
                  required
                  value={formData.type_affectation} 
                  onChange={(e) => setFormData({...formData, type_affectation: e.target.value})}
                >
                  <option value="jour">Day</option>
                  <option value="nuit">Night</option>
                </select>
                <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
                  {formData.type_affectation === 'jour' 
                    ? 'This driver will drive during day hours'
                    : 'This driver will drive during night hours'}
                </small>
              </div>

              <div className="form-group">
                <label>Start Date *</label>
                <input
                  type="date"
                  required
                  value={formData.date_debut}
                  onChange={(e) => setFormData({...formData, date_debut: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Notes (optional)</label>
                <textarea
                  rows="3"
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  placeholder="Notes on this assignment..."
                />
              </div>

              <div className="form-actions">
                <button 
                  type="button" 
                  className="btn-secondary" 
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Assign
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
