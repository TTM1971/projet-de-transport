import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import DataTable from '../components/DataTable';
import Card from '../components/Card';
import { formatPrice } from '../utils/currency';

const API_URL = 'http://localhost:8000';

export default function GestionDeparts() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, canAccess } = useAuth();
  // Les agents ont seulement 'departs_read', donc ils ne peuvent pas créer/modifier/supprimer
  // Les gestionnaires et admins ont 'departs', donc ils peuvent tout faire
  const canEdit = canAccess('departs') && user?.role !== 'agent';
  const [departs, setDeparts] = useState([]);
  const [lignes, setLignes] = useState([]);
  const [destinations, setDestinations] = useState([]);  // Nouveau
  const [buses, setBuses] = useState([]);
  const [chauffeurs, setChauffeurs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingDepart, setEditingDepart] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedDestinationPrix, setSelectedDestinationPrix] = useState(null);  // Pour afficher le prix
  const [selectedBusCapacity, setSelectedBusCapacity] = useState(null);  // Capacité du bus sélectionné
  const [formData, setFormData] = useState({
    ligne_id: '',
    destination_id: '',  // Nouveau
    bus_id: '',
    chauffeur_id: '',
    date_depart: new Date().toISOString().split('T')[0], // YYYY-MM-DD
    heure_depart: '08:00',
    places_disponibles: 50,
    statut: 'programme'
  });

  useEffect(() => {
    fetchData();
  }, []);

  // Fermer le modal quand on change de page
  useEffect(() => {
    setShowModal(false);
    setEditingDepart(null);
  }, [location.pathname]);

  const fetchData = async () => {
    try {
      console.log('Loading data...');
      const [departsRes, lignesRes, destinationsRes, busesRes, chauffeursRes] = await Promise.all([
        axios.get(`${API_URL}/departs/`),
        axios.get(`${API_URL}/lignes/`),
        axios.get(`${API_URL}/destinations/`),  // Nouveau
        axios.get(`${API_URL}/bus/`),
        axios.get(`${API_URL}/chauffeurs/`)
      ]);
      
      const lignesData = lignesRes.data || [];
      const destinationsData = destinationsRes.data || [];  // Nouveau
      const busesData = busesRes.data || [];
      const chauffeursData = chauffeursRes.data || [];
      
      console.log('Données reçues:', {
        lignes: lignesData.length,
        destinations: destinationsData.length,  // Nouveau
        buses: busesData.length,
        chauffeurs: chauffeursData.length,
        lignesData: lignesData,
        destinationsData: destinationsData,  // Nouveau
        busesData: busesData
      });
      
      setDeparts(departsRes.data || []);
      setLignes(lignesData);
      setDestinations(destinationsData);  // Nouveau
      setBuses(busesData);
      setChauffeurs(chauffeursData);
      
      // Retourner les données pour utilisation immédiate
      return { lignesData, destinationsData, busesData, chauffeursData };
    } catch (error) {
      console.error('Error loading:', error);
      console.error('Error details:', error.response?.data);
      alert('Error loading data: ' + (error.response?.data?.detail || error.message));
      setLignes([]);
      setDestinations([]);  // Nouveau
      setBuses([]);
      setChauffeurs([]);
      return { lignesData: [], destinationsData: [], busesData: [], chauffeursData: [] };
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartsByDate = async (dateStr) => {
    try {
      const response = await axios.get(`${API_URL}/departs/date/${dateStr}`);
      setDeparts(response.data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const handleDateChange = (e) => {
    const date = e.target.value;
    setSelectedDate(date);
    fetchDepartsByDate(date);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation des champs requis (chauffeur_id est maintenant optionnel)
    if (!formData.ligne_id || !formData.destination_id || !formData.bus_id) {
      alert('Please fill in all required fields (Line, Destination, Bus).');
      return;
    }
    
    try {
      // Le backend combine date_depart (datetime) et heure_depart (string "HH:MM")
      // On envoie la date à minuit, le backend utilisera heure_depart pour l'heure réelle
      const dateTime = new Date(formData.date_depart + 'T00:00:00');
      
      const departData = {
        ligne_id: parseInt(formData.ligne_id),
        destination_id: parseInt(formData.destination_id),  // Nouveau - le prix sera récupéré automatiquement
        bus_id: parseInt(formData.bus_id),
        date_depart: dateTime.toISOString(),
        heure_depart: formData.heure_depart, // Format "HH:MM"
        places_disponibles: parseInt(formData.places_disponibles),
        statut: formData.statut
      };
      
      // Si un chauffeur est spécifié, l'inclure, sinon laisser undefined pour assignation automatique
      if (formData.chauffeur_id) {
        departData.chauffeur_id = parseInt(formData.chauffeur_id);
      }

      console.log('Envoi des données:', departData);

      let response;
      if (editingDepart) {
        response = await axios.put(`${API_URL}/departs/${editingDepart.id}`, departData);
        console.log('Réponse modification:', response.data);
        alert('Departure updated successfully!');
      } else {
        response = await axios.post(`${API_URL}/departs/`, departData);
        console.log('Creation response:', response.data);
        alert('Departure created successfully!');
      }
      
      // Fermer le modal et réinitialiser
      setShowModal(false);
      setEditingDepart(null);
      setSelectedDestinationPrix(null);
      setSelectedBusCapacity(null);
      setFormData({
        ligne_id: '',
        destination_id: '',
        bus_id: '',
        chauffeur_id: '',
        date_depart: new Date().toISOString().split('T')[0],
        heure_depart: '08:00',
        places_disponibles: 50,
        statut: 'programme'
      });
      
      // Recharger les données
      await fetchData();
    } catch (error) {
      console.error('Error submitting:', error);
      console.error('Error details:', error.response?.data);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message;
      alert('Error: ' + errorMessage);
    }
  };

  const handleEdit = async (depart) => {
    setEditingDepart(depart);
    const dateStr = new Date(depart.date_depart).toISOString().split('T')[0]; // YYYY-MM-DD
    const heureStr = depart.heure_depart ? 
      (typeof depart.heure_depart === 'string' ? depart.heure_depart : 
       `${String(depart.heure_depart.hour || depart.heure_depart).padStart(2, '0')}:${String(depart.heure_depart.minute || '00').padStart(2, '0')}`) 
      : '08:00';
    
    const destinationId = depart.destination_id ? depart.destination_id.toString() : '';
    // Trouver le prix de la destination pour l'afficher
    const destination = destinations.find(d => d.id === depart.destination_id);
    const prix = destination ? destination.tarif : depart.prix;
    
    // Trouver le bus pour obtenir sa capacité
    const bus = buses.find(b => b.id === depart.bus_id);
    const capacite = bus ? (bus.capacite || 0) : 0;
    setSelectedBusCapacity(capacite);
    
    // Calculer les places disponibles : capacité - 2 (chauffeur/assistant) - billets vendus
    let placesDisponibles = capacite - 2;
    try {
      const response = await axios.get(`${API_URL}/departs/${depart.id}/billets/count`);
      const billetsVendus = response.data.billets_vendus || 0;
      placesDisponibles = Math.max(0, capacite - 2 - billetsVendus);
    } catch (error) {
      console.error('Erreur lors du calcul des places:', error);
      // Utiliser la valeur actuelle si on ne peut pas récupérer le nombre de billets
      placesDisponibles = depart.places_disponibles;
    }
    
    setFormData({
      ligne_id: depart.ligne_id.toString(),
      destination_id: destinationId,
      bus_id: depart.bus_id.toString(),
      chauffeur_id: depart.chauffeur_id.toString(),
      date_depart: dateStr,
      heure_depart: heureStr,
      places_disponibles: placesDisponibles,
      statut: depart.statut
    });
    setSelectedDestinationPrix(prix);
    setShowModal(true);
  };

  const handleDelete = async (depart) => {
    if (!window.confirm(`Delete departure #${depart.id}?`)) return;
    try {
      await axios.delete(`${API_URL}/departs/${depart.id}`);
      alert('Departure deleted!');
      fetchData();
    } catch (error) {
      alert('Error deleting departure');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatHeure = (heure) => {
    if (!heure) return '';
    if (typeof heure === 'string') return heure;
    if (heure.hour !== undefined) {
      return `${String(heure.hour).padStart(2, '0')}:${String(heure.minute || 0).padStart(2, '0')}`;
    }
    return heure.toString();
  };

  const getLigneInfo = (ligneId) => {
    const ligne = lignes.find(l => l.id === ligneId);
    return ligne ? `${ligne.numero} - ${ligne.point_depart} → ${ligne.point_arrivee}` : `Line #${ligneId}`;
  };

  const getBusInfo = (busId) => {
    const bus = buses.find(b => b.id === busId);
    return bus ? bus.immatriculation : `Bus #${busId}`;
  };

  const getChauffeurInfo = (chauffeurId) => {
    const chauffeur = chauffeurs.find(c => c.id === chauffeurId);
    return chauffeur ? `${chauffeur.prenom} ${chauffeur.nom}` : `Driver #${chauffeurId}`;
  };

  const getDestinationInfo = (destinationId) => {
    const destination = destinations.find(d => d.id === destinationId);
    return destination ? `${destination.nom} - ${destination.ville || ''} (${formatPrice(destination.tarif)})` : `Destination #${destinationId}`;
  };

  const columns = [
    { header: 'ID', field: 'id' },
    { 
      header: 'Line', 
      field: 'ligne_id',
      formatter: (value) => getLigneInfo(value)
    },
    { 
      header: 'Bus', 
      field: 'bus_id',
      formatter: (value) => getBusInfo(value)
    },
    { 
      header: 'Driver', 
      field: 'chauffeur_id',
      formatter: (value) => getChauffeurInfo(value)
    },
    { 
      header: 'Date/Time', 
      field: 'date_depart',
      formatter: (value, row) => {
        const date = formatDate(value);
        const heure = formatHeure(row.heure_depart);
        return `${date} - ${heure}`;
      }
    },
    { header: 'Seats', field: 'places_disponibles' },
    { header: 'Price', field: 'prix', formatter: (value) => formatPrice(value) },
    { header: 'Status', field: 'statut', formatter: (value) => {
      const translations = { 'programme': 'Scheduled', 'en_cours': 'In Progress', 'termine': 'Completed', 'annule': 'Cancelled' };
      return translations[value] || value;
    }}
  ];

  if (loading) return <div className="loading">Loading...</div>;

  // Formatter les données pour DataTable
  const formattedData = departs.map(depart => ({
    ...depart,
    ligne_display: getLigneInfo(depart.ligne_id),
    bus_display: getBusInfo(depart.bus_id),
    chauffeur_display: getChauffeurInfo(depart.chauffeur_id),
    date_heure_display: `${formatDate(depart.date_depart)} - ${formatHeure(depart.heure_depart)}`,
    prix_display: formatPrice(depart.prix)
  }));

  // Colonnes simplifiées pour DataTable
  const tableColumns = [
    { header: 'ID', field: 'id' },
    { header: 'Line', field: 'ligne_display' },
    { header: 'Bus', field: 'bus_display' },
    { header: 'Driver', field: 'chauffeur_display' },
    { header: 'Date/Time', field: 'date_heure_display' },
    { header: 'Seats', field: 'places_disponibles' },
    { header: 'Price', field: 'prix_display' },
    { header: 'Status', field: 'statut', formatter: (value) => {
      const translations = { 'programme': 'Scheduled', 'en_cours': 'In Progress', 'termine': 'Completed', 'annule': 'Cancelled' };
      return translations[value] || value;
    }}
  ];

  return (
    <div className="page-container">
             <div className="page-header">
               <h1>{canEdit ? 'Departure Management' : 'Schedules & Routes'}</h1>
               <div style={{ display: 'flex', gap: '10px' }}>
                 {canEdit && (
                   <button className="btn-secondary" onClick={() => navigate('/departs/generate')}>
                     Generate Future Departures
                   </button>
                 )}
                 {canEdit && (
               <button className="btn-primary" onClick={async () => {
          setEditingDepart(null);
          setFormData({
            ligne_id: '',
            destination_id: '',
            bus_id: '',
            chauffeur_id: '',
            date_depart: new Date().toISOString().split('T')[0],
            heure_depart: '08:00',
            places_disponibles: 50,
            statut: 'programme'
          });
          setSelectedDestinationPrix(null);
          setSelectedBusCapacity(null);
          // Recharger les données avant d'ouvrir le modal
          try {
            const { lignesData, destinationsData, busesData, chauffeursData } = await fetchData();
            // Vérifier que les données sont bien chargées
            console.log('Données chargées pour le modal:', { 
              lignes: lignesData.length,
              destinations: destinationsData.length,
              buses: busesData.length, 
              chauffeurs: chauffeursData.length 
            });
            
            if (lignesData.length === 0) {
              alert('No lines available. Please create a line first.');
              return;
            }
            if (destinationsData.length === 0) {
              alert('No destinations available. Please create a destination first.');
              return;
            }
            if (busesData.length === 0) {
              alert('No buses available. Please create a bus first.');
              return;
            }
            if (chauffeursData.length === 0) {
              alert('No drivers available. Please create a driver first.');
              return;
            }
            
            setShowModal(true);
          } catch (error) {
            console.error('Error loading data:', error);
            alert('Error loading data. Please try again.');
          }
        }}>
          + Add Departure
        </button>
        )}
               </div>
               {!canEdit && (
                 <p style={{ color: '#666', fontSize: '0.95rem', marginTop: '10px' }}>
                   View schedules and available routes to help clients
                 </p>
               )}
             </div>

      <Card>
        <div style={{ marginBottom: '20px' }}>
          <label style={{ marginRight: '10px', fontWeight: 500 }}>Filter by date:</label>
          <input
            type="date"
            value={selectedDate}
            onChange={handleDateChange}
            style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
          />
          <button 
            onClick={() => {
              setSelectedDate(new Date().toISOString().split('T')[0]);
              fetchData();
            }}
            style={{ marginLeft: '10px', padding: '8px 16px', backgroundColor: '#f0f0f0', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer' }}
          >
            View All
          </button>
        </div>
        <DataTable
          columns={tableColumns}
          data={formattedData}
          onEdit={canEdit ? handleEdit : null}
          onDelete={canEdit ? handleDelete : null}
        />
      </Card>

      {showModal && (
        <div className="modal-overlay" onClick={() => {
          setShowModal(false);
          setEditingDepart(null);
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingDepart ? 'Edit Departure' : 'New Departure'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Line *</label>
                <select
                  required
                  value={formData.ligne_id}
                  onChange={(e) => setFormData({...formData, ligne_id: e.target.value})}
                >
                  <option value="">Select a line</option>
                  {lignes && lignes.length > 0 ? (
                    lignes.map(l => (
                      <option key={l.id} value={l.id}>
                        {l.numero || `Line ${l.id}`} - {l.point_depart} → {l.point_arrivee}
                      </option>
                    ))
                  ) : (
                    <option value="" disabled>No lines available (loading...)</option>
                  )}
                </select>
                {lignes.length === 0 && (
                  <small style={{ color: '#666', fontStyle: 'italic' }}>
                    No lines recorded. Please create a line first.
                  </small>
                )}
              </div>
              <div className="form-group">
                <label>Destination *</label>
                <select
                  required
                  value={formData.destination_id}
                  onChange={(e) => {
                    const destId = e.target.value;
                    const destination = destinations.find(d => d.id.toString() === destId);
                    setSelectedDestinationPrix(destination ? destination.tarif : null);
                    setFormData({...formData, destination_id: destId});
                  }}
                >
                  <option value="">Select a destination</option>
                  {destinations && destinations.length > 0 ? (
                    destinations.map(d => (
                      <option key={d.id} value={d.id}>
                        {d.nom} - {d.ville || ''} ({formatPrice(d.tarif)})
                      </option>
                    ))
                  ) : (
                    <option value="" disabled>No destinations available (loading...)</option>
                  )}
                </select>
                {destinations.length === 0 && (
                  <small style={{ color: '#666', fontStyle: 'italic' }}>
                    No destinations recorded. Please create a destination first.
                  </small>
                )}
                {selectedDestinationPrix !== null && (
                  <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#e8f5e9', borderRadius: '4px', color: '#2e7d32', fontWeight: 500 }}>
                    Price: {selectedDestinationPrix ? formatPrice(selectedDestinationPrix) : 'N/A'}
                  </div>
                )}
              </div>
              <div className="form-group">
                <label>Bus *</label>
                <select
                  required
                  value={formData.bus_id}
                  onChange={async (e) => {
                    const busId = e.target.value;
                    const bus = buses.find(b => b.id.toString() === busId);
                    
                    if (bus) {
                      const capacite = bus.capacite || 0;
                      setSelectedBusCapacity(capacite);
                      
                      // Calculate available seats
                      // For a new departure: capacity - 2 (driver + assistant)
                      // For modification: capacity - 2 - tickets already sold
                      let placesDisponibles = capacite - 2; // Exclude driver and assistant
                      
                      if (editingDepart) {
                        // Get number of tickets sold for this departure
                        try {
                          const response = await axios.get(`${API_URL}/departs/${editingDepart.id}/billets/count`);
                          const billetsVendus = response.data.billets_vendus || 0;
                          placesDisponibles = capacite - 2 - billetsVendus;
                        } catch (error) {
                          console.error('Error calculating seats:', error);
                        }
                      }
                      
                      // Ensure the number is positive
                      placesDisponibles = Math.max(0, placesDisponibles);
                      
                      setFormData({
                        ...formData, 
                        bus_id: busId,
                        places_disponibles: placesDisponibles
                      });
                    } else {
                      setSelectedBusCapacity(null);
                      setFormData({...formData, bus_id: busId});
                    }
                  }}
                >
                  <option value="">Select a bus</option>
                  {buses && buses.length > 0 ? (
                    buses.map(b => (
                      <option key={b.id} value={b.id}>
                        {b.immatriculation} - {b.marque || ''} {b.modele || ''} ({b.capacite || 0} seats)
                      </option>
                    ))
                  ) : (
                    <option value="" disabled>No buses available (loading...)</option>
                  )}
                </select>
                {buses.length === 0 && (
                  <small style={{ color: '#666', fontStyle: 'italic' }}>
                    No buses recorded. Please create a bus first.
                  </small>
                )}
                {selectedBusCapacity !== null && (
                  <small style={{ color: '#666', marginTop: '8px', display: 'block' }}>
                    Bus capacity: {selectedBusCapacity} seats. Available seats: {formData.places_disponibles} (capacity - 2 for driver/assistant{editingDepart ? ' - tickets sold' : ''})
                  </small>
                )}
              </div>
              <div className="form-group">
                <label>Driver (Optional - Auto-assigned if empty)</label>
                <select
                  value={formData.chauffeur_id}
                  onChange={(e) => setFormData({...formData, chauffeur_id: e.target.value})}
                  disabled={!canEdit}
                  style={!canEdit ? { backgroundColor: '#f5f5f5', cursor: 'not-allowed' } : {}}
                >
                  <option value="">Leave empty for automatic assignment</option>
                  {chauffeurs && chauffeurs.length > 0 ? (
                    chauffeurs.map(c => (
                      <option key={c.id} value={c.id}>
                        {c.prenom} {c.nom} - {c.numero_permis}
                      </option>
                    ))
                  ) : (
                    <option value="" disabled>No drivers available</option>
                  )}
                </select>
                {!formData.chauffeur_id && (
                  <small style={{ color: '#2196f3', display: 'block', marginTop: '5px' }}>
                    If left empty, the system will automatically assign the driver based on time (before 6 PM = day, after = night).
                    The bus must have two drivers assigned (one day, one night).
                  </small>
                )}
              </div>
              <div className="form-group">
                <label>Departure Date *</label>
                <input
                  type="date"
                  required
                  value={formData.date_depart}
                  onChange={(e) => setFormData({...formData, date_depart: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Departure Time *</label>
                <input
                  type="time"
                  required
                  value={formData.heure_depart}
                  onChange={(e) => setFormData({...formData, heure_depart: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Available Seats *</label>
                <input
                  type="number"
                  required
                  min="0"
                  readOnly
                  value={formData.places_disponibles}
                  style={{ backgroundColor: '#f5f5f5', cursor: 'not-allowed' }}
                />
                <small style={{ color: '#666', marginTop: '8px', display: 'block' }}>
                  This field is automatically calculated based on the selected bus (capacity - 2 seats for driver/assistant{editingDepart ? ' - tickets already sold' : ''})
                </small>
              </div>
              <div className="form-group">
                <label>Status</label>
                <select
                  value={formData.statut}
                  onChange={(e) => setFormData({...formData, statut: e.target.value})}
                >
                  <option value="programme">Scheduled</option>
                  <option value="en_cours">In Progress</option>
                  <option value="termine">Completed</option>
                  <option value="annule">Cancelled</option>
                </select>
              </div>
              <div className="form-actions">
                <button 
                  type="button" 
                  className="btn-secondary" 
                  onClick={() => {
                    setShowModal(false);
                    setEditingDepart(null);
                  }}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingDepart ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
