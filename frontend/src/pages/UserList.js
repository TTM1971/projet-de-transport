import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import DataTable from '../components/DataTable';
import Card from '../components/Card';
import BackButton from '../components/BackButton';
import API_URL from '../config/api';

export default function UserList() {
  const location = useLocation();
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ username: '', password: '', role: 'agent', ville: '' });
  const [villes, setVilles] = useState([]);

  useEffect(() => { fetchUsers(); fetchVilles(); }, []);

  // Fermer le modal quand on change de page
  useEffect(() => {
    setShowModal(false);
  }, [location.pathname]);

  const fetchUsers = async () => {
    try {
      const res = await axios.get(`${API_URL}/users/`);
      setUsers(res.data);
    } catch (error) { alert('Error'); } finally { setLoading(false); }
  };

  const fetchVilles = async () => {
    try {
      const res = await axios.get(`${API_URL}/villes/`);
      setVilles(res.data.active || []);
    } catch {
      setVilles([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation: Manager cannot create admin or manager accounts
    if (user?.role === 'gestionnaire' && ['admin', 'gestionnaire'].includes(formData.role)) {
      alert('A manager cannot create admin or manager accounts.');
      return;
    }
    
    try {
      await axios.post(`${API_URL}/users/`, formData);
      alert('User created! The account is inactive and requires approval.');
      setShowModal(false);
      setFormData({ username: '', password: '', role: 'agent', ville: '' }); // Reset form
      fetchUsers();
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Error creating account';
      alert('Error: ' + errorMessage);
    }
  };

  const handleDelete = async (user) => {
    if (!window.confirm(`Delete ${user.username}?`)) return;
    try {
      await axios.delete(`${API_URL}/users/${user.id}`);
      fetchUsers();
    } catch (error) { alert('Error'); }
  };

  const navigate = useNavigate();

  const columns = [
    { header: 'ID', field: 'id' },
    { header: 'Username', field: 'username' },
    { header: 'Role', field: 'role' },
    { header: 'Ville', field: 'ville' }
  ];

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>User Management</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-secondary" onClick={() => navigate('/users/approval')}>
            View Pending Accounts
          </button>
          {(user?.role === 'admin' || user?.role === 'gestionnaire') && (
            <button className="btn-primary" onClick={() => setShowModal(true)}>+ Create Account</button>
          )}
        </div>
      </div>
      <Card><DataTable columns={columns} data={users} onDelete={handleDelete} /></Card>
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>New User</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group"><label>Username *</label><input required value={formData.username} onChange={(e) => setFormData({...formData, username: e.target.value})} /></div>
              <div className="form-group"><label>Password *</label><input type="password" required value={formData.password} onChange={(e) => setFormData({...formData, password: e.target.value})} /></div>
              <div className="form-group"><label>Ville *</label>
                <select required value={formData.ville} onChange={(e) => setFormData({...formData, ville: e.target.value})}>
                  <option value="">-- Choisir --</option>
                  {villes.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              </div>
              <div className="form-group"><label>Role</label>
                <select value={formData.role} onChange={(e) => setFormData({...formData, role: e.target.value})}>
                  <option value="agent">Agent</option>
                  <option value="maintenance">Maintenance Technician</option>
                  {user?.role === 'admin' && (
                    <>
                      <option value="gestionnaire">Manager</option>
                      <option value="admin">Admin</option>
                    </>
                  )}
                </select>
                {user?.role === 'gestionnaire' && (
                  <small style={{ display: 'block', marginTop: '5px', color: '#666' }}>
                    A manager can only create agent or maintenance technician accounts.
                  </small>
                )}
              </div>
              <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#fff3cd', borderRadius: '4px', fontSize: '0.9em' }}>
                <strong>Note:</strong> The new account will be created inactive and will require approval to become active.
              </div>
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
