import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import DataTable from '../components/DataTable';
import Card from '../components/Card';
import './CommonPages.css';

const API_URL = 'http://localhost:8000';

export default function GestionChauffeurs() {
  const location = useLocation();
  const [chauffeurs, setChauffeurs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingChauffeur, setEditingChauffeur] = useState(null);
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    numero_permis: '',
    telephone: '',
    statut: 'actif'
  });

  useEffect(() => {
    fetchChauffeurs();
  }, []);

  // Fermer le modal quand on change de page
  useEffect(() => {
    setShowModal(false);
    setEditingChauffeur(null);
  }, [location.pathname]);

  const fetchChauffeurs = async () => {
    try {
      const response = await axios.get(`${API_URL}/chauffeurs/`);
      setChauffeurs(response.data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error loading drivers');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingChauffeur) {
        await axios.put(`${API_URL}/chauffeurs/${editingChauffeur.id}`, formData);
        alert('Driver updated successfully!');
      } else {
        await axios.post(`${API_URL}/chauffeurs/`, formData);
        alert('Driver created successfully!');
      }
      setShowModal(false);
      setEditingChauffeur(null);
      setFormData({
        nom: '',
        prenom: '',
        numero_permis: '',
        telephone: '',
        statut: 'actif'
      });
      fetchChauffeurs();
    } catch (error) {
      alert('Error: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (chauffeur) => {
    setEditingChauffeur(chauffeur);
    setFormData({
      nom: chauffeur.nom,
      prenom: chauffeur.prenom,
      numero_permis: chauffeur.numero_permis,
      telephone: chauffeur.telephone || '',
      statut: chauffeur.statut
    });
    setShowModal(true);
  };

  const handleDelete = async (chauffeur) => {
    if (!window.confirm(`Delete driver ${chauffeur.prenom} ${chauffeur.nom}?`)) return;
    try {
      await axios.delete(`${API_URL}/chauffeurs/${chauffeur.id}`);
      alert('Driver deleted!');
      fetchChauffeurs();
    } catch (error) {
      alert('Error deleting driver');
    }
  };

  const columns = [
    { header: 'ID', field: 'id' },
    { header: 'Last Name', field: 'nom' },
    { header: 'First Name', field: 'prenom' },
    { header: 'License Number', field: 'numero_permis' },
    { header: 'Phone', field: 'telephone' },
    { header: 'Status', field: 'statut', formatter: (value) => {
      const translations = { 
        'actif': 'Active', 
        'en_conge': 'On Leave', 
        'inactif': 'Inactive',
        'suspendu': 'Suspended'
      };
      return translations[value] || value;
    }}
  ];

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Driver Management</h1>
        <button className="btn-primary" onClick={() => {
          setEditingChauffeur(null);
          setFormData({
            nom: '',
            prenom: '',
            numero_permis: '',
            telephone: '',
            statut: 'actif'
          });
          setShowModal(true);
        }}>
          + Add Driver
        </button>
      </div>

      <Card>
        <DataTable
          columns={columns}
          data={chauffeurs}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </Card>

      {showModal && (
        <div className="modal-overlay" onClick={() => {
          setShowModal(false);
          setEditingChauffeur(null);
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingChauffeur ? 'Edit Driver' : 'New Driver'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Last Name *</label>
                <input
                  type="text"
                  required
                  value={formData.nom}
                  onChange={(e) => setFormData({...formData, nom: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>First Name *</label>
                <input
                  type="text"
                  required
                  value={formData.prenom}
                  onChange={(e) => setFormData({...formData, prenom: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>License Number *</label>
                <input
                  type="text"
                  required
                  value={formData.numero_permis}
                  onChange={(e) => setFormData({...formData, numero_permis: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input
                  type="text"
                  value={formData.telephone}
                  onChange={(e) => setFormData({...formData, telephone: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select
                  value={formData.statut}
                  onChange={(e) => setFormData({...formData, statut: e.target.value})}
                >
                  <option value="actif">Active</option>
                  <option value="en_conge">On Leave</option>
                  <option value="inactif">Inactive</option>
                  <option value="suspendu">Suspended</option>
                </select>
              </div>
              <div className="form-actions">
                <button 
                  type="button" 
                  className="btn-secondary" 
                  onClick={() => {
                    setShowModal(false);
                    setEditingChauffeur(null);
                  }}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingChauffeur ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
