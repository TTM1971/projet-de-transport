import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import BackButton from '../components/BackButton';
import './CommonPages.css';

const API_URL = 'http://localhost:8000';

export default function GenerateDeparts() {
  const navigate = useNavigate();
  const [lignes, setLignes] = useState([]);
  const [destinations, setDestinations] = useState([]);
  const [buses, setBuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [formData, setFormData] = useState({
    ligne_id: '',
    destination_id: '',
    bus_id: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    heure_depart: '08:00',
    jours_semaine: '' // Optionnel: '0,1,2,3,4,5,6' pour tous les jours
  });

  useEffect(() => {
    fetchData();
    // Définir la date de fin par défaut à fin février
    const today = new Date();
    const endOfFebruary = new Date(today.getFullYear(), 1, 28); // Février = mois 1
    setFormData(prev => ({
      ...prev,
      end_date: endOfFebruary.toISOString().split('T')[0]
    }));
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [lignesRes, destinationsRes, busesRes] = await Promise.all([
        axios.get(`${API_URL}/lignes/`),
        axios.get(`${API_URL}/destinations/`),
        axios.get(`${API_URL}/bus/`)
      ]);
      setLignes(lignesRes.data);
      setDestinations(destinationsRes.data);
      setBuses(busesRes.data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error loading data');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    if (!formData.ligne_id || !formData.destination_id || !formData.bus_id || !formData.start_date || !formData.end_date) {
      alert('Please fill in all required fields.');
      return;
    }

    if (new Date(formData.start_date) > new Date(formData.end_date)) {
      alert('The end date must be after the start date.');
      return;
    }

    if (new Date(formData.start_date) < new Date().toISOString().split('T')[0]) {
      alert('The start date must be today or a future date.');
      return;
    }

    try {
      setGenerating(true);
      const params = {
        start_date: formData.start_date,
        end_date: formData.end_date,
        ligne_id: parseInt(formData.ligne_id),
        destination_id: parseInt(formData.destination_id),
        bus_id: parseInt(formData.bus_id),
        heure_depart: formData.heure_depart
      };

      if (formData.jours_semaine && formData.jours_semaine.trim()) {
        params.jours_semaine = formData.jours_semaine.trim();
      }

      const response = await axios.post(`${API_URL}/departs/generate-future`, null, { params });
      
      alert(`Generation successful! ${response.data.length} departure(s) created.`);
      navigate('/departs');
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = error.response?.data?.detail || 'Error generating departures';
      alert('Error: ' + errorMessage);
    } finally {
      setGenerating(false);
    }
  };

  const getBusInfo = (busId) => {
    const bus = buses.find(b => b.id.toString() === busId);
    return bus ? `${bus.immatriculation} (${bus.modele})` : `Bus #${busId}`;
  };

  const getLigneInfo = (ligneId) => {
    const ligne = lignes.find(l => l.id.toString() === ligneId);
    return ligne ? `${ligne.numero} - ${ligne.point_depart} to ${ligne.point_arrivee}` : `Line #${ligneId}`;
  };

  const getDestinationInfo = (destinationId) => {
    const destination = destinations.find(d => d.id.toString() === destinationId);
    return destination ? `${destination.nom} - ${destination.ville || ''}` : `Destination #${destinationId}`;
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Generate Future Departures</h1>
        <BackButton />
      </div>

      <Card>
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#e3f2fd', borderRadius: '4px', border: '1px solid #2196f3' }}>
          <p style={{ margin: 0, fontWeight: 500 }}>
            Automatic departure generation
          </p>
          <p style={{ margin: '5px 0 0 0', fontSize: '0.9em', color: '#666' }}>
            This feature automatically generates departures for a given period. 
            Drivers are automatically assigned based on departure time (before 6 PM = day, after = night).
            The bus must have two drivers assigned (one day, one night) before generation.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Line *</label>
            <select
              name="ligne_id"
              required
              value={formData.ligne_id}
              onChange={handleChange}
            >
              <option value="">Select a line</option>
              {lignes.map(l => (
                <option key={l.id} value={l.id}>
                  {l.numero} - {l.point_depart} to {l.point_arrivee}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Destination *</label>
            <select
              name="destination_id"
              required
              value={formData.destination_id}
              onChange={handleChange}
            >
              <option value="">Select a destination</option>
              {destinations.map(d => (
                <option key={d.id} value={d.id}>
                  {d.nom} - {d.ville || ''}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Bus *</label>
            <select
              name="bus_id"
              required
              value={formData.bus_id}
              onChange={handleChange}
            >
              <option value="">Select a bus</option>
              {buses.map(b => (
                <option key={b.id} value={b.id}>
                  {b.immatriculation} ({b.modele}) - Capacity: {b.capacite} seats
                </option>
              ))}
            </select>
            {formData.bus_id && (
              <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
                The bus must have two drivers assigned (one day, one night) for generation to work.
              </small>
            )}
          </div>

          <div className="form-group">
            <label>Start Date *</label>
            <input
              type="date"
              name="start_date"
              required
              value={formData.start_date}
              min={new Date().toISOString().split('T')[0]}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>End Date *</label>
            <input
              type="date"
              name="end_date"
              required
              value={formData.end_date}
              min={formData.start_date}
              onChange={handleChange}
            />
            <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
              Generates departures for each day between the start date and end date (inclusive).
            </small>
          </div>

          <div className="form-group">
            <label>Departure Time *</label>
            <input
              type="time"
              name="heure_depart"
              required
              value={formData.heure_depart}
              onChange={handleChange}
            />
            <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
              Departures before 6 PM will use the day driver, those after 6 PM will use the night driver.
            </small>
          </div>

          <div className="form-group">
            <label>Days of the Week (optional)</label>
            <input
              type="text"
              name="jours_semaine"
              value={formData.jours_semaine}
              onChange={handleChange}
              placeholder="Ex: 0,1,2,3,4,5,6 for all days"
            />
            <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
              Leave empty to generate all days. Otherwise, specify the days (0=Monday, 1=Tuesday, ..., 6=Sunday). Ex: "0,1,2,3,4" for Monday to Friday.
            </small>
          </div>

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => navigate('/departs')}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={generating}>
              {generating ? 'Generating...' : 'Generate Departures'}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
}
