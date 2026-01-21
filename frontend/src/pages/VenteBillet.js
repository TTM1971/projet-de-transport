import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import Card from '../components/Card';
import Logo from '../components/Logo';
import { formatPrice } from '../utils/currency';
import './CommonPages.css';

const API_URL = 'http://localhost:8000';

export default function VenteBillet() {
  const location = useLocation();
  const { user } = useAuth();
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [departs, setDeparts] = useState([]);
  const [departsByDate, setDepartsByDate] = useState([]);
  const [selectedDepart, setSelectedDepart] = useState(null);
  const [lignes, setLignes] = useState([]);
  const [destinations, setDestinations] = useState([]);
  const [buses, setBuses] = useState([]);
  const [chauffeurs, setChauffeurs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(1); // 1: Date selection, 2: Departure selection, 3: Details, 4: Confirmation
  const [formData, setFormData] = useState({
    nom_client: '',
    telephone_client: '',
    siege: '',
    mode_paiement: 'espece'
  });
  const [billetCreated, setBilletCreated] = useState(null);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedDate) {
      fetchDepartsByDate(selectedDate);
    }
  }, [selectedDate]);

  // Réinitialiser le formulaire quand on change de page
  useEffect(() => {
    setStep(1);
    setSelectedDepart(null);
    setBilletCreated(null);
    setFormData({
      nom_client: '',
      telephone_client: '',
      siege: '',
      mode_paiement: 'espece'
    });
  }, [location.pathname]);

  const fetchInitialData = async () => {
    try {
      const [departsRes, lignesRes, destRes, busesRes, chauffeursRes, usersRes] = await Promise.all([
        axios.get(`${API_URL}/departs/`),
        axios.get(`${API_URL}/lignes/`),
        axios.get(`${API_URL}/destinations/`),
        axios.get(`${API_URL}/bus/`),
        axios.get(`${API_URL}/chauffeurs/`),
        axios.get(`${API_URL}/users/`)
      ]);
      setDeparts(departsRes.data);
      setLignes(lignesRes.data.filter(l => l.statut === 'active'));
      setDestinations(destRes.data);
      setBuses(busesRes.data);
      setChauffeurs(chauffeursRes.data);
      setUsers(usersRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error:', error);
      alert('Error loading data: ' + (error.response?.data?.detail || error.message));
      setLoading(false);
    }
  };

  const fetchDepartsByDate = async (dateStr) => {
    try {
      const response = await axios.get(`${API_URL}/departs/date/${dateStr}`);
      // Filtrer seulement les départs programmés avec des places disponibles
      const available = response.data.filter(d => 
        d.statut === 'programme' && d.places_disponibles > 0
      );
      setDepartsByDate(available);
    } catch (error) {
      console.error('Error:', error);
      setDepartsByDate([]);
    }
  };

  const handleDateSelect = (date) => {
    setSelectedDate(date);
    setStep(2);
  };

  const handleDepartSelect = (depart) => {
    setSelectedDepart(depart);
    // Initialiser le formulaire avec les valeurs par défaut
    setFormData({
      nom_client: '',
      telephone_client: '',
      siege: '',
      mode_paiement: 'espece'
    });
    setStep(3);
  };

  const getLigneInfo = (ligneId) => {
    const ligne = lignes.find(l => l.id === ligneId);
    return ligne ? ligne : null;
  };

  const getDestinationFromLigne = (ligneId) => {
    const ligne = getLigneInfo(ligneId);
    if (!ligne) return null;
    // Trouver une destination qui correspond au point d'arrivée
    const destination = destinations.find(d => 
      d.nom.toLowerCase().includes(ligne.point_arrivee.toLowerCase()) ||
      ligne.point_arrivee.toLowerCase().includes(d.nom.toLowerCase())
    );
    return destination || destinations[0]; // Fallback sur la première destination
  };

  const getChauffeurInfo = (chauffeurId) => {
    const chauffeur = chauffeurs.find(c => c.id === chauffeurId);
    return chauffeur ? chauffeur : null;
  };

  const formatHeure = (heure) => {
    if (!heure) return '';
    if (typeof heure === 'string') return heure;
    if (heure.hour !== undefined) {
      return `${String(heure.hour).padStart(2, '0')}:${String(heure.minute || 0).padStart(2, '0')}`;
    }
    return heure.toString();
  };

  const handleFinalSubmit = async (e) => {
    e.preventDefault();
    if (!selectedDepart) return;

    // Validation
    if (!formData.nom_client || !formData.nom_client.trim()) {
      alert('Please enter the client name.');
      return;
    }

    if (!formData.telephone_client || !formData.telephone_client.trim()) {
      alert('Please enter the client phone number.');
      return;
    }

    try {
      // Récupérer l'agent_id depuis l'utilisateur connecté
      let currentUser = null;
      
      // D'abord, essayer de trouver dans la liste des users chargés
      if (users && users.length > 0 && user?.username) {
        currentUser = users.find(u => u.username === user.username);
      }
      
      // Si non trouvé, utiliser l'endpoint /auth/me pour obtenir les infos complètes
      if (!currentUser || !currentUser.id) {
        try {
          const userResponse = await axios.get(`${API_URL}/auth/me`);
          currentUser = {
            id: userResponse.data.id,
            username: userResponse.data.username,
            role: userResponse.data.role
          };
        } catch (userError) {
          console.error('Error retrieving user:', userError);
          // If /auth/me endpoint doesn't work, try to find in users by username
          if (users && users.length > 0 && user?.username) {
            currentUser = users.find(u => u.username === user.username);
          }
          
          if (!currentUser || !currentUser.id) {
            alert('Error: Unable to retrieve user information. Please log in again.');
            return;
          }
        }
      }

      // Validate departure data
      if (!selectedDepart.bus_id) {
        alert('Error: The selected departure has no assigned bus.');
        return;
      }
      
      if (!selectedDepart.destination_id) {
        alert('Error: The selected departure has no assigned destination.');
        return;
      }
      
      if (!selectedDepart.prix || selectedDepart.prix <= 0) {
        alert('Error: The departure price is invalid.');
        return;
      }

      // Verify that all IDs are valid
      if (isNaN(parseInt(selectedDepart.id)) || parseInt(selectedDepart.id) <= 0) {
        alert('Error: Invalid departure ID.');
        return;
      }
      if (isNaN(parseInt(selectedDepart.bus_id)) || parseInt(selectedDepart.bus_id) <= 0) {
        alert('Error: Invalid bus ID.');
        return;
      }
      if (isNaN(parseInt(selectedDepart.destination_id)) || parseInt(selectedDepart.destination_id) <= 0) {
        alert('Error: Invalid destination ID.');
        return;
      }
      if (isNaN(parseInt(currentUser.id)) || parseInt(currentUser.id) <= 0) {
        alert('Error: Invalid agent ID.');
        return;
      }
      if (isNaN(parseFloat(selectedDepart.prix)) || parseFloat(selectedDepart.prix) <= 0) {
        alert('Error: Invalid price.');
        return;
      }

      // Les informations de bus et destination viennent du départ sélectionné
      const billetData = {
        depart_id: parseInt(selectedDepart.id),
        bus_id: parseInt(selectedDepart.bus_id),
        destination_id: parseInt(selectedDepart.destination_id),
        ligne_id: selectedDepart.ligne_id && !isNaN(parseInt(selectedDepart.ligne_id)) ? parseInt(selectedDepart.ligne_id) : null,
        chauffeur_id: selectedDepart.chauffeur_id && !isNaN(parseInt(selectedDepart.chauffeur_id)) ? parseInt(selectedDepart.chauffeur_id) : null,
        siege: formData.siege && formData.siege.toString().trim() !== '' && !isNaN(parseInt(formData.siege)) ? parseInt(formData.siege) : null,
        agent_id: parseInt(currentUser.id),
        mode_paiement: formData.mode_paiement || 'espece',
        montant: parseFloat(selectedDepart.prix),
        nom_client: formData.nom_client.trim() || null,
        telephone_client: formData.telephone_client.trim() || null
      };

      console.log('Sending ticket data:', billetData);
      console.log('Data types:', {
        depart_id: typeof billetData.depart_id,
        bus_id: typeof billetData.bus_id,
        destination_id: typeof billetData.destination_id,
        agent_id: typeof billetData.agent_id,
        montant: typeof billetData.montant
      });

      const res = await axios.post(`${API_URL}/billets/`, billetData);
      console.log('Ticket creation response:', res.data);
      setBilletCreated(res.data);
      setStep(4);
      
      // Reload departures to update available seats
      await fetchDepartsByDate(selectedDate);
    } catch (error) {
      console.error('Full error during sale:', error);
      console.error('Error response:', error.response);
      console.error('Error details:', error.response?.data);
      
      let errorMessage = 'Error during sale';
      if (error.response?.data) {
        if (error.response.data.detail) {
          // If detail is a string
          if (typeof error.response.data.detail === 'string') {
            errorMessage = error.response.data.detail;
          } 
          // If detail is an array (Pydantic validation errors)
          else if (Array.isArray(error.response.data.detail)) {
            errorMessage = error.response.data.detail.map(e => e.msg || e.loc.join('.') + ': ' + e.msg).join('\n');
          }
          else {
            errorMessage = JSON.stringify(error.response.data.detail);
          }
        } else if (error.response.data.message) {
          errorMessage = error.response.data.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert('Error during sale: ' + errorMessage);
    }
  };

  const handleNewSale = () => {
    setStep(1);
    setSelectedDate(new Date().toISOString().split('T')[0]);
    setSelectedDepart(null);
    setFormData({
      nom_client: '',
      telephone_client: '',
      siege: '',
      mode_paiement: 'espece'
    });
    setBilletCreated(null);
    fetchDepartsByDate(new Date().toISOString().split('T')[0]);
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <h1>Ticket Sales</h1>

      {step === 1 && (
        <Card title="Step 1: Select a Date">
          <div style={{ marginBottom: '30px' }}>
            <label style={{ display: 'block', marginBottom: '10px', fontWeight: 500, fontSize: '1.1rem' }}>
              Choose a date to see available departures:
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              style={{
                padding: '12px',
                fontSize: '1rem',
                border: '1px solid #ddd',
                borderRadius: '4px',
                width: '100%',
                maxWidth: '300px'
              }}
            />
          </div>
          <button
            className="btn-primary"
            onClick={() => handleDateSelect(selectedDate)}
            disabled={!selectedDate}
            style={{ padding: '12px 24px', fontSize: '1rem' }}
          >
            View Available Departures
          </button>
        </Card>
      )}

      {step === 2 && (
        <Card title={`Step 2: Choose a Departure - ${new Date(selectedDate).toLocaleDateString('en-US')}`}>
          <div style={{ marginBottom: '20px' }}>
            <button 
              className="btn-secondary" 
              onClick={() => setStep(1)}
              style={{ marginBottom: '10px' }}
            >
              ← Change Date
            </button>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => {
                setSelectedDate(e.target.value);
                fetchDepartsByDate(e.target.value);
              }}
              min={new Date().toISOString().split('T')[0]}
              style={{
                padding: '8px',
                marginLeft: '10px',
                fontSize: '0.9rem',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
            />
          </div>
          
          {departsByDate.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
              <p>No departures available for this date.</p>
              <button className="btn-secondary" onClick={() => setStep(1)}>
                Choose Another Date
              </button>
            </div>
          ) : (
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
              gap: '20px' 
            }}>
              {departsByDate.map(depart => {
                const ligne = getLigneInfo(depart.ligne_id);
                const destination = destinations.find(d => d.id === depart.destination_id);
                const bus = buses.find(b => b.id === depart.bus_id);
                const chauffeur = getChauffeurInfo(depart.chauffeur_id);
                return (
                  <div
                    key={depart.id}
                    onClick={() => handleDepartSelect(depart)}
                    style={{
                      padding: '20px',
                      border: '2px solid #4a90e2',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      background: 'white'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#e3f2fd';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'white';
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    {ligne && (
                      <>
                        <h3 style={{ marginTop: 0, color: '#4a90e2' }}>
                          Line {ligne.numero}
                        </h3>
                        <p style={{ margin: '8px 0', fontWeight: 500 }}>
                          {ligne.point_depart} → {ligne.point_arrivee}
                        </p>
                      </>
                    )}
                    {destination && (
                      <p style={{ margin: '8px 0', fontSize: '0.95rem', color: '#555' }}>
                        <strong>Destination:</strong> {destination.nom}
                      </p>
                    )}
                    {bus && (
                      <p style={{ margin: '8px 0', fontSize: '0.95rem', color: '#555' }}>
                        <strong>Bus:</strong> {bus.immatriculation}
                      </p>
                    )}
                    {chauffeur && (
                      <p style={{ margin: '8px 0', fontSize: '0.95rem', color: '#555' }}>
                        <strong>Driver:</strong> {chauffeur.prenom} {chauffeur.nom}
                      </p>
                    )}
                    <p style={{ margin: '8px 0' }}>
                      <strong>Time:</strong> {formatHeure(depart.heure_depart)}
                    </p>
                    <p style={{ margin: '8px 0' }}>
                      <strong>Available Seats:</strong> {depart.places_disponibles}
                    </p>
                    <p style={{ 
                      margin: '8px 0', 
                      fontSize: '1.5rem', 
                      fontWeight: 'bold', 
                      color: '#27ae60' 
                    }}>
                      {formatPrice(depart.prix)}
                    </p>
                    <p style={{ marginTop: '12px', fontSize: '0.9rem', color: '#666' }}>
                      Click to select
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      )}

      {step === 3 && selectedDepart && (
        <Card title="Step 3: Ticket Details">
          <div style={{ marginBottom: '20px' }}>
            <button 
              className="btn-secondary" 
              onClick={() => setStep(2)}
            >
              ← Back to Departures
            </button>
          </div>
          
          {(() => {
            const ligne = getLigneInfo(selectedDepart.ligne_id);
            return (
              <form onSubmit={handleFinalSubmit}>
                <div style={{ 
                  background: '#f8f9fa', 
                  padding: '20px', 
                  borderRadius: '8px', 
                  marginBottom: '20px' 
                }}>
                  <h3 style={{ marginTop: 0 }}>Trip Information</h3>
                  {ligne && (
                    <>
                      <p><strong>Line:</strong> {ligne.numero} - {ligne.point_depart} → {ligne.point_arrivee}</p>
                      <p><strong>Date:</strong> {new Date(selectedDate).toLocaleDateString('en-US')}</p>
                      <p><strong>Departure Time:</strong> {formatHeure(selectedDepart.heure_depart)}</p>
                    </>
                  )}
                  {(() => {
                    const bus = buses.find(b => b.id === selectedDepart.bus_id);
                    return bus && (
                      <p><strong>Bus Number:</strong> {bus.immatriculation}</p>
                    );
                  })()}
                  {(() => {
                    const destination = destinations.find(d => d.id === selectedDepart.destination_id);
                    return destination && (
                      <p><strong>Destination:</strong> {destination.nom} - {destination.ville || ''}</p>
                    );
                  })()}
                  {(() => {
                    const chauffeur = getChauffeurInfo(selectedDepart.chauffeur_id);
                    return chauffeur && (
                      <p><strong>Driver:</strong> {chauffeur.prenom} {chauffeur.nom} ({chauffeur.numero_permis})</p>
                    );
                  })()}
                  <p><strong>Available Seats:</strong> {selectedDepart.places_disponibles}</p>
                  <p><strong>Price:</strong> <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#27ae60' }}>{formatPrice(selectedDepart.prix)}</span></p>
                </div>

                <h3 style={{ marginBottom: '20px', color: '#1a1a1a' }}>Client Information</h3>

                <div className="form-group">
                  <label>Client Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.nom_client}
                    onChange={(e) => setFormData({...formData, nom_client: e.target.value})}
                    placeholder="Enter full client name"
                  />
                </div>

                <div className="form-group">
                  <label>Phone Number *</label>
                  <input
                    type="tel"
                    required
                    value={formData.telephone_client}
                    onChange={(e) => setFormData({...formData, telephone_client: e.target.value})}
                    placeholder="Ex: +237 6XX XXX XXX"
                  />
                </div>

                <div className="form-group">
                  <label>Seat (optional)</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.siege}
                    onChange={(e) => setFormData({...formData, siege: e.target.value})}
                    placeholder="Seat number"
                  />
                </div>

                <div className="form-group">
                  <label>Payment Method *</label>
                  <select
                    required
                    value={formData.mode_paiement}
                    onChange={(e) => setFormData({...formData, mode_paiement: e.target.value})}
                  >
                    <option value="espece">Cash</option>
                    <option value="carte">Card</option>
                    <option value="mobile">Mobile Payment</option>
                  </select>
                </div>

                <div className="form-actions">
                  <button type="button" className="btn-secondary" onClick={() => setStep(2)}>
                    Back
                  </button>
                  <button type="submit" className="btn-primary">
                    Confirm Sale
                  </button>
                </div>
              </form>
            );
          })()}
        </Card>
      )}

      {step === 4 && billetCreated && selectedDepart && (() => {
        const bus = buses.find(b => b.id === selectedDepart.bus_id);
        const destination = destinations.find(d => d.id === selectedDepart.destination_id);
        const ligne = getLigneInfo(selectedDepart.ligne_id);
        
        return (
          <Card title="Invoice - Ticket Created Successfully!">
            <div style={{ padding: '20px' }}>
              <div style={{ 
                background: '#ffffff', 
                border: '2px solid #e5e5e5',
                padding: '30px', 
                borderRadius: '8px', 
                margin: '20px auto',
                maxWidth: '600px'
              }}>
                <div style={{ textAlign: 'center', marginBottom: '30px', borderBottom: '2px solid #e5e5e5', paddingBottom: '20px' }}>
                  <div style={{ margin: '0 0 10px 0' }}>
                    <Logo variant="compact" />
                  </div>
                  <h3 style={{ margin: '0', color: '#666', fontWeight: 'normal' }}>INVOICE N° {billetCreated.id}</h3>
                </div>

                <div style={{ marginBottom: '30px' }}>
                  <h4 style={{ marginBottom: '15px', color: '#1a1a1a', borderBottom: '1px solid #e5e5e5', paddingBottom: '10px' }}>
                    Client Information
                  </h4>
                  <p><strong>Name:</strong> {billetCreated.nom_client || 'Not provided'}</p>
                  <p><strong>Phone:</strong> {billetCreated.telephone_client || 'Not provided'}</p>
                </div>

                <div style={{ marginBottom: '30px' }}>
                  <h4 style={{ marginBottom: '15px', color: '#1a1a1a', borderBottom: '1px solid #e5e5e5', paddingBottom: '10px' }}>
                    Trip Details
                  </h4>
                  {ligne && (
                    <p><strong>Line:</strong> {ligne.numero} - {ligne.point_depart} → {ligne.point_arrivee}</p>
                  )}
                  <p><strong>Date:</strong> {new Date(selectedDate).toLocaleDateString('en-US')}</p>
                  <p><strong>Departure Time:</strong> {formatHeure(selectedDepart.heure_depart)}</p>
                  {bus && (
                    <p><strong>Bus Number:</strong> {bus.immatriculation}</p>
                  )}
                  {destination && (
                    <p><strong>Destination:</strong> {destination.nom} - {destination.ville || ''}</p>
                  )}
                  {(() => {
                    const chauffeur = getChauffeurInfo(selectedDepart.chauffeur_id);
                    return chauffeur && (
                      <p><strong>Driver:</strong> {chauffeur.prenom} {chauffeur.nom} (License: {chauffeur.numero_permis})</p>
                    );
                  })()}
                  {billetCreated.siege && (
                    <p><strong>Seat:</strong> {billetCreated.siege}</p>
                  )}
                </div>

                <div style={{ 
                  background: '#f8f9fa', 
                  padding: '20px', 
                  borderRadius: '8px',
                  marginBottom: '30px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span><strong>Amount:</strong></span>
                    <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#27ae60' }}>
                      {formatPrice(billetCreated.montant)}
                    </span>
                  </div>
                  <p><strong>Payment Method:</strong> {billetCreated.mode_paiement}</p>
                  <p><strong>Purchase Date:</strong> {new Date(billetCreated.date_achat).toLocaleString('en-US')}</p>
                </div>

                <div style={{ 
                  background: '#e8f5e9', 
                  padding: '15px', 
                  borderRadius: '8px',
                  marginBottom: '20px',
                  textAlign: 'center'
                }}>
                  <p style={{ margin: '0', fontWeight: 'bold', color: '#2e7d32' }}>QR Code:</p>
                  <code style={{ 
                    background: '#ffffff', 
                    padding: '8px 16px', 
                    borderRadius: '4px',
                    fontSize: '1rem',
                    display: 'inline-block',
                    marginTop: '8px'
                  }}>{billetCreated.code_qr}</code>
                </div>

                <div style={{ textAlign: 'center', marginTop: '30px' }}>
                  <button className="btn-primary" onClick={handleNewSale} style={{ marginRight: '10px' }}>
                    New Sale
                  </button>
                  <button 
                    className="btn-secondary" 
                    onClick={() => window.print()}
                  >
                    Print Invoice
                  </button>
                </div>
              </div>
            </div>
          </Card>
        );
      })()}
    </div>
  );
}
