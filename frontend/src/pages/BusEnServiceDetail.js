import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import BackButton from '../components/BackButton';

const API_URL = 'http://localhost:8000';

export default function BusEnServiceDetail() {
  const navigate = useNavigate();
  const [buses, setBuses] = useState([]);
  const [chauffeurs, setChauffeurs] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const busesRes = await axios.get(`${API_URL}/bus/`);
      const allBuses = busesRes.data;
      const busEnService = allBuses.filter(b => b.statut === 'en_service');
      
      setBuses(busEnService);
      
      // Récupérer les chauffeurs assignés pour chaque bus
      const chauffeursData = {};
      for (const bus of busEnService) {
        try {
          const chauffeursRes = await axios.get(`${API_URL}/bus/${bus.id}/chauffeurs`);
          chauffeursData[bus.id] = chauffeursRes.data;
        } catch (error) {
          console.error(`Error retrieving drivers for bus ${bus.id}:`, error);
          chauffeursData[bus.id] = { chauffeurs: [] };
        }
      }
      setChauffeurs(chauffeursData);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div style={{ marginBottom: '20px' }}>
            <BackButton />
          </div>
          <h1>Buses in Service ({buses.length})</h1>
          <p style={{ color: '#666', marginTop: '10px' }}>
            Detailed list of buses currently in service
          </p>
        </div>
      </div>

      {buses.length === 0 ? (
        <Card>
          <p style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            No buses in service currently
          </p>
        </Card>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
          {buses.map(bus => {
            const busChauffeurs = chauffeurs[bus.id] || { chauffeurs: [] };
            const chauffeurJour = busChauffeurs.chauffeur_jour;
            const chauffeurNuit = busChauffeurs.chauffeur_nuit;

            return (
              <Card key={bus.id}>
                <div style={{ marginBottom: '15px', paddingBottom: '15px', borderBottom: '2px solid #e5e5e5' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                    <h2 style={{ margin: 0, color: '#1a1a1a' }}>
                      {bus.immatriculation}
                    </h2>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '4px',
                      backgroundColor: '#27ae60',
                      color: 'white',
                      fontWeight: 'bold',
                      fontSize: '0.9em'
                    }}>
                      In Service
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '10px' }}>
                    <p style={{ margin: '5px 0', fontSize: '0.9em' }}>
                      <strong>Make:</strong> {bus.marque || 'N/A'}
                    </p>
                    <p style={{ margin: '5px 0', fontSize: '0.9em' }}>
                      <strong>Model:</strong> {bus.modele || 'N/A'}
                    </p>
                    <p style={{ margin: '5px 0', fontSize: '0.9em' }}>
                      <strong>Year:</strong> {bus.annee || 'N/A'}
                    </p>
                    <p style={{ margin: '5px 0', fontSize: '0.9em' }}>
                      <strong>Capacity:</strong> {bus.capacite} seats
                    </p>
                  </div>
                </div>

                <div style={{ marginBottom: '15px' }}>
                  <h3 style={{ fontSize: '1em', marginBottom: '10px', color: '#666' }}>Assigned drivers</h3>
                  {chauffeurJour && (
                    <div style={{ marginBottom: '8px', padding: '8px', backgroundColor: '#ebf5fb', borderRadius: '4px' }}>
                      <strong>Day:</strong> {chauffeurJour.chauffeur?.prenom} {chauffeurJour.chauffeur?.nom}
                    </div>
                  )}
                  {chauffeurNuit && (
                    <div style={{ padding: '8px', backgroundColor: '#ecf0f1', borderRadius: '4px' }}>
                      <strong>Night:</strong> {chauffeurNuit.chauffeur?.prenom} {chauffeurNuit.chauffeur?.nom}
                    </div>
                  )}
                  {!chauffeurJour && !chauffeurNuit && (
                    <p style={{ color: '#999', fontStyle: 'italic', fontSize: '0.9em' }}>
                      No driver assigned
                    </p>
                  )}
                </div>

                <button
                  className="btn-primary"
                  onClick={() => navigate(`/bus/${bus.id}`)}
                  style={{ width: '100%' }}
                >
                  View full details
                </button>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
