import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import DataTable from '../components/DataTable';
import Card from '../components/Card';
import API_URL from '../config/api';
import { useAuth } from '../context/AuthContext';

/**
 * Liste des conducteurs — création désactivée (provisionnement RH / scripts).
 * Suppression : administrateur uniquement.
 */
export default function GestionChauffeurs() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
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
      alert('Erreur de chargement des conducteurs');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!editingChauffeur) return;
    try {
      await axios.put(`${API_URL}/chauffeurs/${editingChauffeur.id}`, formData);
      alert('Conducteur mis à jour.');
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
      alert('Erreur : ' + (error.response?.data?.detail || error.message));
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
    if (!isAdmin) return;
    if (!window.confirm(`Supprimer le conducteur ${chauffeur.prenom} ${chauffeur.nom} ?`)) return;
    try {
      await axios.delete(`${API_URL}/chauffeurs/${chauffeur.id}`);
      alert('Conducteur supprimé.');
      fetchChauffeurs();
    } catch (error) {
      alert('Erreur lors de la suppression');
    }
  };

  const columns = [
    { header: 'ID', field: 'id' },
    { header: 'Nom', field: 'nom' },
    { header: 'Prénom', field: 'prenom' },
    { header: 'Permis', field: 'numero_permis' },
    { header: 'Téléphone', field: 'telephone' },
    { header: 'Statut', field: 'statut', formatter: (value) => {
      const translations = { 
        'actif': 'Actif', 
        'en_conge': 'Congé', 
        'conge': 'Congé',
        'inactif': 'Inactif',
        'suspendu': 'Suspendu'
      };
      return translations[value] || value;
    }}
  ];

  if (loading) return <div className="loading">Chargement…</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Conducteurs</h1>
        </div>
      </div>

      <Card>
        <DataTable
          columns={columns}
          data={chauffeurs}
          onEdit={handleEdit}
          onDelete={isAdmin ? handleDelete : undefined}
          onRowClick={(row) => navigate(`/chauffeurs/${row.id}/planning`)}
        />
      </Card>

      {showModal && editingChauffeur && (
        <div className="modal-overlay" onClick={() => {
          setShowModal(false);
          setEditingChauffeur(null);
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Modifier le conducteur</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Nom *</label>
                <input
                  type="text"
                  required
                  value={formData.nom}
                  onChange={(e) => setFormData({...formData, nom: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Prénom *</label>
                <input
                  type="text"
                  required
                  value={formData.prenom}
                  onChange={(e) => setFormData({...formData, prenom: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Numéro de permis *</label>
                <input
                  type="text"
                  required
                  value={formData.numero_permis}
                  onChange={(e) => setFormData({...formData, numero_permis: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Téléphone</label>
                <input
                  type="text"
                  value={formData.telephone}
                  onChange={(e) => setFormData({...formData, telephone: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Statut</label>
                <select
                  value={formData.statut}
                  onChange={(e) => setFormData({...formData, statut: e.target.value})}
                >
                  <option value="actif">Actif</option>
                  <option value="en_conge">Congé</option>
                  <option value="inactif">Inactif</option>
                  <option value="suspendu">Suspendu</option>
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
                  Annuler
                </button>
                <button type="submit" className="btn-primary">
                  Enregistrer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
