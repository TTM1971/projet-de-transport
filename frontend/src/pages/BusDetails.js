import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import BackButton from '../components/BackButton';
import { formatPrice } from '../utils/currency';
import { translateBreakdownType } from '../utils/translations';

const API_URL = 'http://localhost:8000';

export default function BusDetails() {
  const { busId } = useParams();
  const navigate = useNavigate();
  const [bus, setBus] = useState(null);
  const [interventions, setInterventions] = useState([]);
  const [chauffeurs, setChauffeurs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('interventions'); // 'interventions' ou 'chauffeurs'

  useEffect(() => {
    fetchBusDetails();
    fetchInterventions();
    fetchChauffeurs();
  }, [busId]);

  const fetchBusDetails = async () => {
    try {
      const response = await axios.get(`${API_URL}/bus/${busId}`);
      setBus(response.data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error loading bus details');
    }
  };

  const fetchInterventions = async () => {
    try {
      const response = await axios.get(`${API_URL}/bus/${busId}/interventions`);
      setInterventions(response.data.interventions || []);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const fetchChauffeurs = async () => {
    try {
      const response = await axios.get(`${API_URL}/bus/${busId}/chauffeurs`);
      setChauffeurs(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getGraviteColor = (gravite) => {
    const translations = {
      'mineure': { color: '#27ae60', label: 'Minor' },
      'moyenne': { color: '#f39c12', label: 'Moderate' },
      'majeure': { color: '#e67e22', label: 'Major' },
      'critique': { color: '#e74c3c', label: 'Critical' }
    };
    const item = translations[gravite] || { color: '#7f8c8d', label: gravite };
    return item.color;
  };

  const getGraviteLabel = (gravite) => {
    const translations = {
      'mineure': 'Minor',
      'moyenne': 'Moderate',
      'majeure': 'Major',
      'critique': 'Critical'
    };
    return translations[gravite] || gravite;
  };

  const getStatutColor = (statut) => {
    const colors = {
      'en_attente': '#f39c12',
      'en_cours': '#3498db',
      'terminee': '#27ae60',
      'annulee': '#e74c3c'
    };
    return colors[statut] || '#7f8c8d';
  };

  const getStatutLabel = (statut) => {
    const translations = {
      'en_attente': 'Pending',
      'en_cours': 'In Progress',
      'terminee': 'Completed',
      'annulee': 'Cancelled'
    };
    return translations[statut] || statut;
  };

  const getStatutBusLabel = (statut) => {
    const translations = {
      'en_service': 'In Service',
      'en_maintenance': 'In Maintenance',
      'hors_service': 'Out of Service',
      'disponible': 'Available'
    };
    return translations[statut] || statut;
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!bus) return <div className="loading">Bus not found</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div style={{ marginBottom: '20px' }}>
            <BackButton />
          </div>
          <h1>Bus Details: {bus.immatriculation}</h1>
        </div>
        <button 
          className="btn-primary" 
          onClick={() => navigate(`/bus/${busId}/chauffeurs`)}
        >
          Manage Assignments
        </button>
      </div>

      {/* Bus Information */}
      <Card title="Bus Information">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
          <div>
            <strong>Brand:</strong> {bus.marque || 'N/A'}
          </div>
          <div>
            <strong>Model:</strong> {bus.modele || 'N/A'}
          </div>
          <div>
            <strong>Year:</strong> {bus.annee || 'N/A'}
          </div>
          <div>
            <strong>Capacity:</strong> {bus.capacite} seats
          </div>
          <div>
            <strong>Status:</strong> 
            <span style={{ 
              marginLeft: '10px',
              padding: '4px 12px',
              borderRadius: '4px',
              backgroundColor: bus.statut === 'en_service' ? '#27ae60' : 
                              bus.statut === 'en_maintenance' ? '#e67e22' : 
                              bus.statut === 'hors_service' ? '#e74c3c' : '#95a5a6',
              color: 'white',
              fontWeight: 'bold'
            }}>
              {getStatutBusLabel(bus.statut || 'disponible')}
            </span>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '2px solid #e5e5e5' }}>
        <button
          onClick={() => setActiveTab('interventions')}
          style={{
            padding: '12px 24px',
            border: 'none',
            background: activeTab === 'interventions' ? '#1a1a1a' : 'transparent',
            color: activeTab === 'interventions' ? 'white' : '#666',
            cursor: 'pointer',
            fontWeight: activeTab === 'interventions' ? 'bold' : 'normal',
            borderBottom: activeTab === 'interventions' ? '3px solid #1a1a1a' : '3px solid transparent'
          }}
        >
          Maintenance History ({interventions.length})
        </button>
        <button
          onClick={() => setActiveTab('chauffeurs')}
          style={{
            padding: '12px 24px',
            border: 'none',
            background: activeTab === 'chauffeurs' ? '#1a1a1a' : 'transparent',
            color: activeTab === 'chauffeurs' ? 'white' : '#666',
            cursor: 'pointer',
            fontWeight: activeTab === 'chauffeurs' ? 'bold' : 'normal',
            borderBottom: activeTab === 'chauffeurs' ? '3px solid #1a1a1a' : '3px solid transparent'
          }}
        >
          Assigned Drivers ({chauffeurs?.chauffeurs?.length || 0})
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'interventions' && (
        <Card title="Maintenance Intervention History">
          {interventions.length === 0 ? (
            <p>No interventions recorded for this bus.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f8f8' }}>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Entry Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Exit Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Failure Type</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Severity</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Description</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Parts Replaced</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Cost</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {interventions.map((intervention) => (
                    <tr key={intervention.id} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '12px' }}>{formatDate(intervention.date_entree)}</td>
                      <td style={{ padding: '12px' }}>{formatDate(intervention.date_sortie)}</td>
                      <td style={{ padding: '12px' }}>{translateBreakdownType(intervention.type_panne) || 'N/A'}</td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          backgroundColor: getGraviteColor(intervention.gravite),
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '0.9em'
                        }}>
                          {getGraviteLabel(intervention.gravite || 'N/A')}
                        </span>
                      </td>
                      <td style={{ padding: '12px', maxWidth: '300px' }}>{intervention.description || 'N/A'}</td>
                      <td style={{ padding: '12px' }}>{intervention.pieces_remplacees || 'None'}</td>
                      <td style={{ padding: '12px' }}>
                        {intervention.cout_intervention ? formatPrice(intervention.cout_intervention) : 'N/A'}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          backgroundColor: getStatutColor(intervention.statut),
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '0.9em'
                        }}>
                          {getStatutLabel(intervention.statut || 'N/A')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {activeTab === 'chauffeurs' && (
        <Card title="Drivers Assigned to Bus">
          {!chauffeurs || chauffeurs.chauffeurs.length === 0 ? (
            <p>No drivers currently assigned to this bus.</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
              {chauffeurs.chauffeur_jour && (
                <div style={{
                  padding: '20px',
                  border: '2px solid #3498db',
                  borderRadius: '8px',
                  backgroundColor: '#ebf5fb'
                }}>
                  <h3 style={{ marginTop: 0, color: '#2980b9' }}>Day Driver</h3>
                  <p><strong>Name:</strong> {chauffeurs.chauffeur_jour.chauffeur?.prenom} {chauffeurs.chauffeur_jour.chauffeur?.nom}</p>
                  <p><strong>License:</strong> {chauffeurs.chauffeur_jour.chauffeur?.numero_permis}</p>
                  <p><strong>Phone:</strong> {chauffeurs.chauffeur_jour.chauffeur?.telephone || 'N/A'}</p>
                  <p><strong>Status:</strong> 
                    <span style={{
                      marginLeft: '10px',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: chauffeurs.chauffeur_jour.chauffeur?.statut === 'actif' ? '#27ae60' : '#e74c3c',
                      color: 'white',
                      fontSize: '0.9em'
                    }}>
                      {chauffeurs.chauffeur_jour.chauffeur?.statut === 'actif' ? 'Active' : 'Inactive'}
                    </span>
                  </p>
                  <p><strong>Assigned since:</strong> {formatDate(chauffeurs.chauffeur_jour.date_debut)}</p>
                  {chauffeurs.chauffeur_jour.notes && (
                    <p><strong>Notes:</strong> {chauffeurs.chauffeur_jour.notes}</p>
                  )}
                </div>
              )}
              
              {chauffeurs.chauffeur_nuit && (
                <div style={{
                  padding: '20px',
                  border: '2px solid #2c3e50',
                  borderRadius: '8px',
                  backgroundColor: '#ecf0f1'
                }}>
                  <h3 style={{ marginTop: 0, color: '#34495e' }}>Night Driver</h3>
                  <p><strong>Name:</strong> {chauffeurs.chauffeur_nuit.chauffeur?.prenom} {chauffeurs.chauffeur_nuit.chauffeur?.nom}</p>
                  <p><strong>License:</strong> {chauffeurs.chauffeur_nuit.chauffeur?.numero_permis}</p>
                  <p><strong>Phone:</strong> {chauffeurs.chauffeur_nuit.chauffeur?.telephone || 'N/A'}</p>
                  <p><strong>Status:</strong> 
                    <span style={{
                      marginLeft: '10px',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: chauffeurs.chauffeur_nuit.chauffeur?.statut === 'actif' ? '#27ae60' : '#e74c3c',
                      color: 'white',
                      fontSize: '0.9em'
                    }}>
                      {chauffeurs.chauffeur_nuit.chauffeur?.statut === 'actif' ? 'Active' : 'Inactive'}
                    </span>
                  </p>
                  <p><strong>Assigned since:</strong> {formatDate(chauffeurs.chauffeur_nuit.date_debut)}</p>
                  {chauffeurs.chauffeur_nuit.notes && (
                    <p><strong>Notes:</strong> {chauffeurs.chauffeur_nuit.notes}</p>
                  )}
                </div>
              )}
            </div>
          )}
          
          {chauffeurs && chauffeurs.chauffeurs.length > 0 && (
            <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <p style={{ margin: 0, fontStyle: 'italic', color: '#666' }}>
                <strong>Note:</strong> Each bus is assigned to two drivers who alternate their schedules (day/night). 
                If one driver is on leave, the other takes over.
              </p>
              <button 
                className="btn-primary"
                onClick={() => navigate(`/bus/${busId}/chauffeurs`)}
                style={{ marginTop: '15px' }}
              >
                Manage Assignments
              </button>
            </div>
          )}
          
          {(!chauffeurs || chauffeurs.chauffeurs.length === 0) && (
            <div style={{ marginTop: '20px' }}>
              <button 
                className="btn-primary"
                onClick={() => navigate(`/bus/${busId}/chauffeurs`)}
              >
                Assign Drivers
              </button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
