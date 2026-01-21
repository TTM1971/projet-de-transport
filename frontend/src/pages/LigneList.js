import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import DataTable from '../components/DataTable';
import Card from '../components/Card';
import './CommonPages.css';

const API_URL = 'http://localhost:8000';

export default function LigneList() {
  const location = useLocation();
  const [lignes, setLignes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    numero: '', nom: '', point_depart: '', point_arrivee: '',
    distance_km: '', duree_minutes: '', tarif: '', statut: 'active'
  });

  useEffect(() => { fetchLignes(); }, []);

  // Fermer le modal quand on change de page
  useEffect(() => {
    setShowModal(false);
  }, [location.pathname]);

  const fetchLignes = async () => {
    try {
      const res = await axios.get(`${API_URL}/lignes/`);
      setLignes(res.data);
    } catch (error) {
      alert('Error loading');
    } finally { setLoading(false); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/lignes/`, formData);
      alert('Line created!');
      setShowModal(false);
      fetchLignes();
    } catch (error) {
      alert('Error: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (ligne) => {
    if (!window.confirm(`Delete line ${ligne.numero}?`)) return;
    try {
      await axios.delete(`${API_URL}/lignes/${ligne.id}`);
      fetchLignes();
    } catch (error) { alert('Error'); }
  };

  const columns = [
    { header: 'ID', field: 'id' },
    { header: 'Number', field: 'numero' },
    { header: 'Name', field: 'nom' },
    { header: 'Departure', field: 'point_depart' },
    { header: 'Arrival', field: 'point_arrivee' },
    { header: 'Fare', field: 'tarif', formatter: (value) => typeof value === 'number' ? value.toFixed(2) : value },
    { header: 'Status', field: 'statut', formatter: (value) => {
      const translations = { 'active': 'Active', 'inactive': 'Inactive' };
      return translations[value] || value;
    }}
  ];

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Line Management</h1>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Add</button>
      </div>
      <Card>
        <DataTable columns={columns} data={lignes} onDelete={handleDelete} />
      </Card>
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>New Line</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group"><label>Number *</label><input required value={formData.numero} onChange={(e) => setFormData({...formData, numero: e.target.value})} /></div>
              <div className="form-group"><label>Name *</label><input required value={formData.nom} onChange={(e) => setFormData({...formData, nom: e.target.value})} /></div>
              <div className="form-group"><label>Departure *</label><input required value={formData.point_depart} onChange={(e) => setFormData({...formData, point_depart: e.target.value})} /></div>
              <div className="form-group"><label>Arrival *</label><input required value={formData.point_arrivee} onChange={(e) => setFormData({...formData, point_arrivee: e.target.value})} /></div>
              <div className="form-group"><label>Distance (km)</label><input type="number" value={formData.distance_km} onChange={(e) => setFormData({...formData, distance_km: e.target.value})} /></div>
              <div className="form-group"><label>Duration (min)</label><input type="number" value={formData.duree_minutes} onChange={(e) => setFormData({...formData, duree_minutes: e.target.value})} /></div>
              <div className="form-group"><label>Fare</label><input type="number" step="0.01" value={formData.tarif} onChange={(e) => setFormData({...formData, tarif: e.target.value})} /></div>
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
