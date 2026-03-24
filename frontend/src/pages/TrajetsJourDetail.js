import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import BackButton from '../components/BackButton';
import { formatPrice } from '../utils/currency';
import API_URL from '../config/api';

export default function TrajetsJourDetail() {
  const { date } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (date) {
      fetchData();
    }
  }, [date]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/analytics/detail/trajets/jour/${date}`, {
        timeout: 120000 // 2 minutes de timeout
      });
      setData(response.data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error loading trips: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!data) return <div className="loading">No data available</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div style={{ marginBottom: '20px' }}>
            <BackButton />
          </div>
          <h1>Trips for {formatDate(date)}</h1>
          <p style={{ color: '#666', marginTop: '10px' }}>
            {data.nombre_trajets} trip(s) completed today
          </p>
        </div>
      </div>

      {data.nombre_trajets === 0 ? (
        <Card>
          <p style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            No trips recorded for this day
          </p>
        </Card>
      ) : (
        data.trajets.map((trajet) => (
          <Card key={trajet.depart_id} style={{ marginBottom: '20px' }}>
            <div style={{ marginBottom: '20px', paddingBottom: '20px', borderBottom: '2px solid #e5e5e5' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
                <div>
                  <h2 style={{ margin: '0 0 10px 0', color: '#1a1a1a' }}>
                    Trip #{trajet.depart_id}
                  </h2>
                  <div style={{ fontSize: '1.2em', color: '#666', marginBottom: '15px' }}>
                    {trajet.ligne?.point_depart || 'N/A'} → {trajet.ligne?.point_arrivee || 'N/A'}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.5em', fontWeight: 'bold', color: '#27ae60', marginBottom: '5px' }}>
                    {formatPrice(trajet.chiffre_affaires_trajet)}
                  </div>
                  <div style={{ color: '#666' }}>
                    {trajet.nombre_billets_vendus} ticket(s) sold
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px' }}>
                <div>
                  <strong>Bus:</strong>
                  <p style={{ margin: '5px 0' }}>
                    {trajet.bus?.immatriculation || 'N/A'} 
                    ({trajet.bus?.marque || ''} {trajet.bus?.modele || ''})
                  </p>
                  <p style={{ margin: '5px 0', fontSize: '0.9em', color: '#666' }}>
                    Capacity: {trajet.bus?.capacite || 'N/A'} seats
                  </p>
                </div>
                
                <div>
                  <strong>Destination:</strong>
                  <p style={{ margin: '5px 0' }}>
                    {trajet.destination?.nom || 'N/A'}
                  </p>
                  <p style={{ margin: '5px 0', fontSize: '0.9em', color: '#666' }}>
                    {trajet.destination?.ville || ''}
                  </p>
                  <p style={{ margin: '5px 0', fontSize: '0.9em', color: '#666' }}>
                    Fare: {formatPrice(trajet.destination?.tarif || 0)}
                  </p>
                </div>

                <div>
                  <strong>Schedule:</strong>
                  <p style={{ margin: '5px 0' }}>
                    Departure: {trajet.heure_depart || 'N/A'}
                  </p>
                  {trajet.heure_arrivee_estimee && (
                    <p style={{ margin: '5px 0' }}>
                      Estimated Arrival: {trajet.heure_arrivee_estimee}
                    </p>
                  )}
                </div>

                <div>
                  <strong>Status:</strong>
                  <p style={{ margin: '5px 0' }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '4px',
                      backgroundColor: trajet.statut === 'termine' ? '#27ae60' : 
                                      trajet.statut === 'en_cours' ? '#3498db' : '#f39c12',
                      color: 'white',
                      fontWeight: 'bold'
                    }}>
                      {trajet.statut === 'termine' ? 'Completed' : 
                       trajet.statut === 'en_cours' ? 'In Progress' : 
                       trajet.statut === 'programme' ? 'Scheduled' : 
                       trajet.statut === 'annule' ? 'Cancelled' : 
                       trajet.statut || 'N/A'}
                    </span>
                  </p>
                  <p style={{ margin: '5px 0', fontSize: '0.9em', color: '#666' }}>
                    Available Seats: {trajet.places_disponibles}
                  </p>
                </div>
              </div>
            </div>

            {/* Drivers */}
            <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <h3 style={{ marginTop: 0, marginBottom: '15px', color: '#666' }}>Assigned Drivers</h3>
              {trajet.chauffeurs_assignes && trajet.chauffeurs_assignes.length > 0 ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
                  {trajet.chauffeurs_assignes.map((chauffeur, idx) => (
                    <div 
                      key={idx}
                      style={{
                        padding: '10px',
                        backgroundColor: chauffeur.type_affectation === 'jour' ? '#ebf5fb' : '#ecf0f1',
                        borderRadius: '4px'
                      }}
                    >
                      <strong>{chauffeur.prenom} {chauffeur.nom}</strong>
                      <div style={{ fontSize: '0.9em', color: '#666', marginTop: '5px' }}>
                        Type: {chauffeur.type_affectation === 'jour' ? 'Day' : 'Night'}
                      </div>
                      <div style={{ fontSize: '0.9em', color: '#666' }}>
                        License: {chauffeur.numero_permis}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#999', fontStyle: 'italic' }}>
                  No driver assigned for this trip
                </p>
              )}
            </div>

            {/* Cashiers */}
            {trajet.caissieres && trajet.caissieres.length > 0 && (
              <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#fff3e0', borderRadius: '8px' }}>
                <h3 style={{ marginTop: 0, marginBottom: '15px', color: '#666' }}>Cashiers</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px' }}>
                  {trajet.caissieres.map((caissiere, idx) => (
                    <div 
                      key={idx}
                      style={{
                        padding: '10px',
                        backgroundColor: '#fff',
                        borderRadius: '4px',
                        border: '1px solid #e67e22'
                      }}
                    >
                      <strong>{caissiere.first_name || caissiere.username} {caissiere.last_name || ''}</strong>
                      <p style={{ margin: '5px 0' }}>Turnover: {formatPrice(caissiere.ca)}</p>
                      <p style={{ margin: '5px 0' }}>Tickets sold: {caissiere.billets_vendus}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Ticket Details */}
            {trajet.billets && trajet.billets.length > 0 && (
              <div>
                <h3 style={{ marginBottom: '15px', color: '#666' }}>Ticket Details ({trajet.billets.length})</h3>
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9em' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f8f9fa', position: 'sticky', top: 0 }}>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Client</th>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Phone</th>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Seat</th>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Amount</th>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Payment</th>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Status</th>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Purchase Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {trajet.billets.map((billet) => (
                        <tr key={billet.id} style={{ borderBottom: '1px solid #eee' }}>
                          <td style={{ padding: '10px' }}>{billet.nom_client || 'N/A'}</td>
                          <td style={{ padding: '10px' }}>{billet.telephone_client || 'N/A'}</td>
                          <td style={{ padding: '10px' }}>{billet.siege || 'N/A'}</td>
                          <td style={{ padding: '10px', fontWeight: 'bold' }}>
                            {formatPrice(billet.montant)}
                          </td>
                          <td style={{ padding: '10px' }}>
                            {billet.mode_paiement === 'espece' ? 'Cash' : 
                             billet.mode_paiement === 'carte' ? 'Card' : 
                             billet.mode_paiement === 'mobile' ? 'Mobile Payment' : 
                             billet.mode_paiement || 'N/A'}
                          </td>
                          <td style={{ padding: '10px' }}>
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              backgroundColor: billet.statut === 'valide' || billet.statut === 'utilise' ? '#27ae60' : '#e74c3c',
                              color: 'white',
                              fontSize: '0.85em'
                            }}>
                              {billet.statut === 'valide' ? 'Valid' : 
                               billet.statut === 'utilise' ? 'Used' : 
                               billet.statut === 'annule' ? 'Cancelled' : 
                               billet.statut === 'rembourse' ? 'Refunded' : 
                               billet.statut || 'N/A'}
                            </span>
                          </td>
                          <td style={{ padding: '10px', fontSize: '0.85em' }}>
                            {billet.date_achat ? new Date(billet.date_achat).toLocaleString('en-US') : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div style={{ marginTop: '20px', textAlign: 'center' }}>
              <button
                className="btn-primary"
                onClick={() => navigate(`/bus/${trajet.bus?.id}`)}
              >
                View Complete Bus Details
              </button>
            </div>
          </Card>
        ))
      )}
    </div>
  );
}
