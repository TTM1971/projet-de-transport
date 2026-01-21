import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import DataTable from '../components/DataTable';
import Card from '../components/Card';
import { formatPrice } from '../utils/currency';
import './CommonPages.css';

const API_URL = 'http://localhost:8000';

export default function DestinationList() {
  const location = useLocation();
  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ nom: '', ville: '', adresse: '', tarif: '', duree_estimee_minutes: '' });

  useEffect(() => { fetchDestinations(); }, []);

  // Fermer le modal quand on change de page
  useEffect(() => {
    setShowModal(false);
  }, [location.pathname]);

  const fetchDestinations = async () => {
    try {
      const res = await axios.get(`${API_URL}/destinations/`);
      setDestinations(res.data);
    } catch (error) { alert('Error'); } finally { setLoading(false); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/destinations/`, formData);
      alert('Destination created!');
      setShowModal(false);
      fetchDestinations();
    } catch (error) { alert('Error'); }
  };

  const handleDelete = async (dest) => {
    if (!window.confirm(`Delete ${dest.nom}?`)) return;
    try {
      await axios.delete(`${API_URL}/destinations/${dest.id}`);
      fetchDestinations();
    } catch (error) { alert('Error'); }
  };

  const columns = [
    { header: 'ID', field: 'id' },
    { header: 'Name', field: 'nom' },
    { header: 'City', field: 'ville' },
    { header: 'Fare', field: 'tarif', formatter: (value) => formatPrice(value) },
    { header: 'Estimated Duration (min)', field: 'duree_estimee_minutes' }
  ];

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header"><h1>Destination Management</h1>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Add</button>
      </div>
      <Card><DataTable columns={columns} data={destinations} onDelete={handleDelete} /></Card>
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>New Destination</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group"><label>Name *</label><input required value={formData.nom} onChange={(e) => setFormData({...formData, nom: e.target.value})} /></div>
              <div className="form-group"><label>City</label><input value={formData.ville} onChange={(e) => setFormData({...formData, ville: e.target.value})} /></div>
              <div className="form-group"><label>Address</label><input value={formData.adresse} onChange={(e) => setFormData({...formData, adresse: e.target.value})} /></div>
              <div className="form-group"><label>Fare *</label><input type="number" step="0.01" required value={formData.tarif} onChange={(e) => setFormData({...formData, tarif: e.target.value})} /></div>
              <div className="form-group"><label>Estimated Duration (min)</label><input type="number" value={formData.duree_estimee_minutes} onChange={(e) => setFormData({...formData, duree_estimee_minutes: e.target.value})} /></div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
