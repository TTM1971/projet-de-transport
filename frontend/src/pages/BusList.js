import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import DataTable from '../components/DataTable';
import Card from '../components/Card';
import { translateStatus } from '../utils/translations';

const API_URL = 'http://localhost:8000';

export default function BusList() {
  const location = useLocation();
  const navigate = useNavigate();
  const [buses, setBuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingBus, setEditingBus] = useState(null);
  const [formData, setFormData] = useState({
    immatriculation: '',
    modele: '',
    marque: '',
    capacite: 50,
    annee: '',
    statut: 'disponible'
  });

  useEffect(() => {
    fetchBuses();
  }, []);

  // Fermer le modal quand on change de page
  useEffect(() => {
    setShowModal(false);
    setEditingBus(null);
  }, [location.pathname]);

  const fetchBuses = async () => {
    try {
      const response = await axios.get(`${API_URL}/bus/`);
      setBuses(response.data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error loading buses');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Prepare data by correctly converting types
      const submitData = {
        immatriculation: formData.immatriculation,
        modele: formData.modele || null,
        marque: formData.marque || null,
        capacite: parseInt(formData.capacite) || 50,
        annee: formData.annee ? parseInt(formData.annee) : null,
        statut: formData.statut || 'disponible'
      };
      console.log('Sending data:', submitData);
      if (editingBus) {
        await axios.put(`${API_URL}/bus/${editingBus.id}`, submitData);
        alert('Bus updated successfully!');
      } else {
        await axios.post(`${API_URL}/bus/`, submitData);
        alert('Bus created successfully!');
      }
      
      setShowModal(false);
      setEditingBus(null);
      setFormData({
        immatriculation: '',
        modele: '',
        marque: '',
        capacite: 50,
        annee: '',
        statut: 'disponible'
      });
      fetchBuses();
    } catch (error) {
      console.error('Full error:', error);
      console.error('Response:', error.response);
      alert('Error creating bus: ' + (error.response?.data?.detail || error.message || 'Network error'));
    }
  };

  const handleEdit = (bus) => {
    setEditingBus(bus);
    setFormData({
      immatriculation: bus.immatriculation,
      modele: bus.modele || '',
      marque: bus.marque || '',
      capacite: bus.capacite || 50,
      annee: bus.annee || '',
      statut: bus.statut || 'disponible'
    });
    setShowModal(true);
  };

  const handleDelete = async (bus) => {
    if (!window.confirm(`Delete bus ${bus.immatriculation}?`)) return;
    try {
      await axios.delete(`${API_URL}/bus/${bus.id}`);
      alert('Bus deleted!');
      fetchBuses();
    } catch (error) {
      alert('Error deleting bus');
    }
  };

  const columns = [
    { header: 'ID', field: 'id' },
    { header: 'Plate Number', field: 'immatriculation' },
    { header: 'Brand', field: 'marque' },
    { header: 'Model', field: 'modele' },
    { header: 'Capacity', field: 'capacite' },
    { header: 'Year', field: 'annee' },
    { header: 'Status', field: 'statut', formatter: (value) => translateStatus(value) }
  ];

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container bus-list">
      <div className="page-header">
        <h1>Bus Management</h1>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          + Add Bus
        </button>
      </div>

      <Card>
        <div style={{ marginBottom: '15px', color: '#666', fontSize: '0.9em' }}>
          <strong>Tip:</strong> Click on a row or on a bus plate number to view its maintenance history and assigned drivers.
        </div>
        <DataTable
          columns={columns}
          data={buses}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onRowClick={(bus) => navigate(`/bus/${bus.id}`)}
        />
      </Card>

      {showModal && (
        <div className="modal-overlay" onClick={() => { setShowModal(false); setEditingBus(null); }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingBus ? 'Edit Bus' : 'New Bus'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Plate Number *</label>
                <input
                  type="text"
                  required
                  value={formData.immatriculation}
                  onChange={(e) => setFormData({...formData, immatriculation: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Brand</label>
                <input
                  type="text"
                  value={formData.marque}
                  onChange={(e) => setFormData({...formData, marque: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Model</label>
                <input
                  type="text"
                  value={formData.modele}
                  onChange={(e) => setFormData({...formData, modele: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Capacity</label>
                <input
                  type="number"
                  value={formData.capacite}
                  onChange={(e) => setFormData({...formData, capacite: e.target.value === '' ? 50 : parseInt(e.target.value) || 50})}
                />
              </div>
              <div className="form-group">
                <label>Year</label>
                <input
                  type="number"
                  value={formData.annee}
                  onChange={(e) => setFormData({...formData, annee: e.target.value === '' ? '' : e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select
                  value={formData.statut}
                  onChange={(e) => setFormData({...formData, statut: e.target.value})}
                >
                  <option value="disponible">Available</option>
                  <option value="en_service">In Service</option>
                  <option value="en_maintenance">In Maintenance</option>
                  <option value="hors_service">Out of Service</option>
                </select>
              </div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingBus ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
