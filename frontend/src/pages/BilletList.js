import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import DataTable from '../components/DataTable';
import Card from '../components/Card';
import { formatPrice } from '../utils/currency';
import API_URL from '../config/api';

export default function BilletList() {
  const location = useLocation();
  const { user, canAccess } = useAuth();
  // Les agents peuvent seulement consulter les billets, pas les créer/modifier/supprimer depuis cette page
  // (Ils utilisent la page VenteBillet pour créer des billets)
  const canEdit = user?.role !== 'agent';
  const [billets, setBillets] = useState([]);
  const [buses, setBuses] = useState([]);
  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [departs, setDeparts] = useState([]);
  const [formData, setFormData] = useState({ depart_id: '', bus_id: '', destination_id: '', ligne_id: '', siege: '', agent_id: 1, mode_paiement: 'espece', montant: '' });

  useEffect(() => {
    fetchData();
  }, []);

  // Fermer le modal quand on change de page
  useEffect(() => {
    setShowModal(false);
  }, [location.pathname]);

  const fetchData = async () => {
    try {
      const [billetsRes, busesRes, destRes, departsRes] = await Promise.all([
        axios.get(`${API_URL}/billets/`),
        axios.get(`${API_URL}/bus/`),
        axios.get(`${API_URL}/destinations/`),
        axios.get(`${API_URL}/departs/`)
      ]);
      setBillets(billetsRes.data);
      setBuses(busesRes.data);
      setDestinations(destRes.data);
      setDeparts(departsRes.data || []);
    } catch (error) {
      console.error('Error loading data:', error);
      alert('Error loading data');
    } finally { setLoading(false); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.depart_id) {
      alert('Please select a departure.');
      return;
    }
    
    try {
      // Prepare data by correctly converting types
      const billetData = {
        bus_id: parseInt(formData.bus_id),
        destination_id: parseInt(formData.destination_id),
        ligne_id: formData.ligne_id && formData.ligne_id.trim() !== '' ? parseInt(formData.ligne_id) : null,
        siege: formData.siege && formData.siege.toString().trim() !== '' ? parseInt(formData.siege) : null,
        agent_id: parseInt(formData.agent_id) || 1,
        mode_paiement: formData.mode_paiement || 'espece',
        montant: parseFloat(formData.montant),
        // NOTE: depart_id is now mandatory in the new system
        // If you want to create a ticket without departure, use the VenteBillet page
        // For this form, we must create a departure first or select an existing departure
      };
      
      // If depart_id is not provided, we cannot create the ticket
      if (!formData.depart_id) {
        alert('Error: A departure is required to create a ticket. Please use the "Ticket Sales" page to create tickets with departures.');
        return;
      }
      
      billetData.depart_id = parseInt(formData.depart_id);
      
      await axios.post(`${API_URL}/billets/`, billetData);
      alert('Ticket created successfully!');
      setShowModal(false);
      setFormData({ bus_id: '', destination_id: '', ligne_id: '', siege: '', agent_id: 1, mode_paiement: 'espece', montant: '', depart_id: '' });
      fetchData();
    } catch (error) {
      console.error('Error creating ticket:', error);
      let errorMessage = 'Error creating ticket';
      if (error.response?.data) {
        if (error.response.data.detail) {
          if (typeof error.response.data.detail === 'string') {
            errorMessage = error.response.data.detail;
          } else if (Array.isArray(error.response.data.detail)) {
            errorMessage = error.response.data.detail.map(e => {
              const field = e.loc ? e.loc.join('.') : 'field';
              return `${field}: ${e.msg}`;
            }).join('\n');
          }
        }
      }
      alert(errorMessage);
    }
  };

  const handleDelete = async (billet) => {
    if (!window.confirm(`Delete ticket #${billet.id}?`)) return;
    try {
      await axios.delete(`${API_URL}/billets/${billet.id}`);
      fetchData();
    } catch (error) { alert('Error'); }
  };

  const columns = [
    { header: 'ID', field: 'id' },
    { header: 'Bus ID', field: 'bus_id' },
    { header: 'Destination ID', field: 'destination_id' },
    { header: 'Seat', field: 'siege' },
    { header: 'Amount', field: 'montant', formatter: (value) => formatPrice(value) },
    { header: 'Payment', field: 'mode_paiement', formatter: (value) => {
      const translations = { 'espece': 'Cash', 'carte': 'Card', 'mobile': 'Mobile Payment' };
      return translations[value] || value;
    }},
    { header: 'Date', field: 'date_achat' },
    { header: 'Status', field: 'statut', formatter: (value) => {
      const translations = { 'valide': 'Valid', 'utilise': 'Used', 'annule': 'Cancelled', 'rembourse': 'Refunded' };
      return translations[value] || value;
    }}
  ];

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>{canEdit ? 'Ticket Management' : 'View Tickets'}</h1>
        {canEdit && (
          <button className="btn-primary" onClick={async () => {
            // Reload data before opening modal
            await fetchData();
            setShowModal(true);
          }}>+ New Ticket</button>
        )}
        {!canEdit && (
          <p style={{ color: '#666', fontSize: '0.95rem', marginTop: '10px' }}>
            To sell a ticket, use the "Ticket Sales" page
          </p>
        )}
      </div>
      <Card>
        <DataTable 
          columns={columns} 
          data={billets} 
          onEdit={canEdit ? null : null} 
          onDelete={canEdit ? handleDelete : null} 
        />
      </Card>
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>New Ticket</h2>
            <p style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#fff3cd', borderRadius: '4px', color: '#856404' }}>
              <strong>Note:</strong> To create a ticket, you must first select a departure. 
              Bus and destination information will be automatically retrieved from the selected departure.
            </p>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Departure *</label>
                <select 
                  required 
                  value={formData.depart_id} 
                  onChange={(e) => {
                    const departId = e.target.value;
                    const selectedDepart = departs.find(d => d.id.toString() === departId);
                    setFormData({
                      ...formData, 
                      depart_id: departId,
                      bus_id: selectedDepart ? selectedDepart.bus_id.toString() : '',
                      destination_id: selectedDepart ? selectedDepart.destination_id.toString() : '',
                      ligne_id: selectedDepart ? (selectedDepart.ligne_id ? selectedDepart.ligne_id.toString() : '') : '',
                      montant: selectedDepart ? selectedDepart.prix.toString() : ''
                    });
                  }}
                >
                  <option value="">Select a departure</option>
                  {departs && departs.length > 0 ? (
                    departs.map(d => {
                      const date = new Date(d.date_depart);
                      const heure = d.heure_depart ? (typeof d.heure_depart === 'string' ? d.heure_depart : `${String(d.heure_depart.hour || 0).padStart(2, '0')}:${String(d.heure_depart.minute || 0).padStart(2, '0')}`) : '';
                      return (
                        <option key={d.id} value={d.id}>
                          Departure #{d.id} - {date.toLocaleDateString('en-US')} {heure} - {d.places_disponibles} seats - {formatPrice(d.prix)}
                        </option>
                      );
                    })
                  ) : (
                    <option value="" disabled>No departures available</option>
                  )}
                </select>
              </div>
              
              <div className="form-group">
                <label>Bus</label>
                <select 
                  value={formData.bus_id} 
                  disabled
                  style={{ backgroundColor: '#f5f5f5', cursor: 'not-allowed' }}
                >
                  <option value="">First select a departure</option>
                  {buses && buses.length > 0 && formData.bus_id ? (
                    buses.filter(b => b.id.toString() === formData.bus_id).map(b => 
                      <option key={b.id} value={b.id}>{b.immatriculation}</option>
                    )
                  ) : null}
                </select>
                <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
                  The bus is automatically selected based on the departure
                </small>
              </div>
              
              <div className="form-group">
                <label>Destination</label>
                <select 
                  value={formData.destination_id} 
                  disabled
                  style={{ backgroundColor: '#f5f5f5', cursor: 'not-allowed' }}
                >
                  <option value="">First select a departure</option>
                  {destinations && destinations.length > 0 && formData.destination_id ? (
                    destinations.filter(d => d.id.toString() === formData.destination_id).map(d => 
                      <option key={d.id} value={d.id}>{d.nom} - {formatPrice(d.tarif)}</option>
                    )
                  ) : null}
                </select>
                <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
                  The destination is automatically selected based on the departure
                </small>
              </div>
              
              <div className="form-group">
                <label>Seat (optional)</label>
                <input 
                  type="number" 
                  min="1"
                  value={formData.siege} 
                  onChange={(e) => setFormData({...formData, siege: e.target.value})} 
                />
              </div>
              
              <div className="form-group">
                <label>Amount *</label>
                <input 
                  type="number" 
                  step="0.01" 
                  required 
                  value={formData.montant} 
                  disabled
                  style={{ backgroundColor: '#f5f5f5', cursor: 'not-allowed' }}
                />
                <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
                  The amount is automatically set based on the departure
                </small>
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
                <button type="button" className="btn-secondary" onClick={() => {
                  setShowModal(false);
                  setFormData({ depart_id: '', bus_id: '', destination_id: '', ligne_id: '', siege: '', agent_id: 1, mode_paiement: 'espece', montant: '' });
                }}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
