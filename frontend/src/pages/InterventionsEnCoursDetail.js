import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import BackButton from '../components/BackButton';
import { formatPrice } from '../utils/currency';
import { translateBreakdownType, translateSeverity } from '../utils/translations';
import API_URL from '../config/api';

export default function InterventionsEnCoursDetail() {
  const navigate = useNavigate();
  const [interventions, setInterventions] = useState([]);
  const [buses, setBuses] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [interventionsRes, busesRes, usersRes] = await Promise.all([
        axios.get(`${API_URL}/ateliers/?statut=en_cours`).catch(() => ({ data: [] })),
        axios.get(`${API_URL}/bus/`),
        axios.get(`${API_URL}/users/`).catch(() => ({ data: [] }))
      ]);
      
      setInterventions(interventionsRes.data || []);
      setBuses(busesRes.data);
      setUsers(usersRes.data || []);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getBus = (busId) => {
    return buses.find(b => b.id === busId);
  };

  const getTechnicien = (technicienId) => {
    if (!technicienId) return null;
    return users.find(u => u.id === technicienId);
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
          <h1>Interventions in Progress ({interventions.length})</h1>
          <p style={{ color: '#666', marginTop: '10px' }}>
            Detailed list of interventions currently in progress on buses
          </p>
        </div>
      </div>

      {interventions.length === 0 ? (
        <Card>
          <p style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            No interventions in progress currently
          </p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {interventions.map(intervention => {
            const bus = getBus(intervention.bus_id);
            const technicien = getTechnicien(intervention.technicien_id);

            return (
              <Card key={intervention.id}>
                <div style={{ marginBottom: '15px', paddingBottom: '15px', borderBottom: '2px solid #e5e5e5' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '15px' }}>
                        <h2 style={{ margin: 0, color: '#1a1a1a' }}>
                          Bus: {bus?.immatriculation || `Bus #${intervention.bus_id}`}
                        </h2>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          backgroundColor: '#e74c3c',
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '0.9em'
                        }}>
                          In Progress
                        </span>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px' }}>
                        <div>
                          <strong>Breakdown type:</strong>
                          <p style={{ margin: '5px 0' }}>{translateBreakdownType(intervention.type_panne) || 'N/A'}</p>
                        </div>
                        <div>
                          <strong>Severity:</strong>
                          <p style={{ margin: '5px 0' }}>
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
                          </p>
                        </div>
                        <div>
                          <strong>Entry date:</strong>
                          <p style={{ margin: '5px 0' }}>{formatDate(intervention.date_entree)}</p>
                        </div>
                        {technicien && (
                          <div>
                            <strong>Assigned technician:</strong>
                            <p style={{ margin: '5px 0' }}>
                              {technicien.first_name || technicien.username} {technicien.last_name || ''}
                            </p>
                          </div>
                        )}
                        {intervention.cout_intervention && (
                          <div>
                            <strong>Estimated cost:</strong>
                            <p style={{ margin: '5px 0' }}>{formatPrice(intervention.cout_intervention)}</p>
                          </div>
                        )}
                      </div>

                      {intervention.description && (
                        <div style={{ marginTop: '15px' }}>
                          <strong>Problem description:</strong>
                          <p style={{ 
                            margin: '5px 0', 
                            padding: '10px', 
                            backgroundColor: '#f9f9f9', 
                            borderRadius: '4px',
                            whiteSpace: 'pre-wrap'
                          }}>
                            {intervention.description}
                          </p>
                        </div>
                      )}

                      {intervention.pieces_remplacees && (
                        <div style={{ marginTop: '10px' }}>
                          <strong>Parts to replace:</strong>
                          <p style={{ margin: '5px 0', color: '#666' }}>
                            {intervention.pieces_remplacees}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  {bus && (
                    <button
                      className="btn-primary"
                      onClick={() => navigate(`/bus/${bus.id}`)}
                    >
                      View bus details
                    </button>
                  )}
                  <button
                    className="btn-secondary"
                    onClick={() => navigate('/maintenance')}
                  >
                    Manage interventions
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
