import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import BackButton from '../components/BackButton';
import { translateBreakdownType, translateSeverity } from '../utils/translations';
import './CommonPages.css';

const API_URL = 'http://localhost:8000';

export default function BusMaintenanceDetail() {
  const navigate = useNavigate();
  const [buses, setBuses] = useState([]);
  const [interventions, setInterventions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [busesRes, interventionsRes] = await Promise.all([
        axios.get(`${API_URL}/bus/`),
        axios.get(`${API_URL}/ateliers/?statut=en_cours`).catch(() => ({ data: [] }))
      ]);
      
      const allBuses = busesRes.data;
      const busMaintenance = allBuses.filter(b => b.statut === 'en_maintenance');
      
      // Pour chaque bus en maintenance, récupérer ses interventions
      const interventionsData = interventionsRes.data || [];
      
      setBuses(busMaintenance);
      setInterventions(interventionsData);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getBusInterventions = (busId) => {
    return interventions.filter(i => i.bus_id === busId);
  };

  const getGraviteColor = (gravite) => {
    const colors = {
      'mineure': '#27ae60',
      'moyenne': '#f39c12',
      'majeure': '#e67e22',
      'critique': '#e74c3c'
    };
    return colors[gravite] || '#7f8c8d';
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

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div style={{ marginBottom: '20px' }}>
            <BackButton />
          </div>
          <h1>Buses in Maintenance ({buses.length})</h1>
          <p style={{ color: '#666', marginTop: '10px' }}>
            Detailed list of buses currently in maintenance with their interventions
          </p>
        </div>
      </div>

      {buses.length === 0 ? (
        <Card>
          <p style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            No buses in maintenance currently
          </p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {buses.map(bus => {
            const busInterventions = getBusInterventions(bus.id);
            return (
              <Card key={bus.id}>
                <div style={{ marginBottom: '15px', paddingBottom: '15px', borderBottom: '2px solid #e5e5e5' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h2 style={{ margin: '0 0 10px 0', color: '#1a1a1a' }}>
                        {bus.immatriculation}
                      </h2>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', marginTop: '10px' }}>
                        <p style={{ margin: '5px 0' }}>
                          <strong>Make/Model:</strong> {bus.marque || 'N/A'} {bus.modele || ''}
                        </p>
                        <p style={{ margin: '5px 0' }}>
                          <strong>Year:</strong> {bus.annee || 'N/A'}
                        </p>
                        <p style={{ margin: '5px 0' }}>
                          <strong>Capacity:</strong> {bus.capacite} seats
                        </p>
                        <p style={{ margin: '5px 0' }}>
                          <strong>Active interventions:</strong> {busInterventions.length}
                        </p>
                      </div>
                    </div>
                    <button
                      className="btn-primary"
                      onClick={() => navigate(`/bus/${bus.id}`)}
                    >
                      View full details
                    </button>
                  </div>
                </div>

                {busInterventions.length > 0 ? (
                  <div>
                    <h3 style={{ marginBottom: '15px', color: '#666' }}>Ongoing interventions</h3>
                    <div style={{ display: 'grid', gap: '15px' }}>
                      {busInterventions.map(intervention => (
                        <div
                          key={intervention.id}
                          style={{
                            padding: '15px',
                            border: '1px solid #ddd',
                            borderRadius: '8px',
                            backgroundColor: '#f9f9f9'
                          }}
                        >
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
                            <div>
                              <strong>Breakdown type:</strong> {translateBreakdownType(intervention.type_panne) || 'N/A'}
                            </div>
                            <div>
                              <strong>Severity:</strong>{' '}
                              <span style={{
                                padding: '4px 8px',
                                borderRadius: '4px',
                                backgroundColor: getGraviteColor(intervention.gravite),
                                color: 'white',
                                fontWeight: 'bold',
                                fontSize: '0.9em'
                              }}>
                                {translateSeverity(intervention.gravite) || 'N/A'}
                              </span>
                            </div>
                            <div>
                              <strong>Entry date:</strong> {formatDate(intervention.date_entree)}
                            </div>
                            {intervention.description && (
                              <div style={{ gridColumn: '1 / -1', marginTop: '10px' }}>
                                <strong>Description:</strong> {intervention.description}
                              </div>
                            )}
                            {intervention.pieces_remplacees && (
                              <div style={{ gridColumn: '1 / -1', marginTop: '5px' }}>
                                <strong>Replaced parts:</strong> {intervention.pieces_remplacees}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p style={{ color: '#666', fontStyle: 'italic' }}>
                    No active interventions for this bus
                  </p>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
