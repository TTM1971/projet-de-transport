import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import Card from '../components/Card';
import { formatApiError } from '../utils/apiError';
import API_URL from '../config/api';
export default function UserApproval() {
  const { user } = useAuth();
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    fetchPendingUsers();
  }, []);

  const fetchPendingUsers = async () => {
    try {
      setLoading(true);
      setErrorMessage('');
      const response = await axios.get(`${API_URL}/users/pending`);
      setPendingUsers(response.data);
    } catch (error) {
      console.error('Error:', error);
      setErrorMessage(
        formatApiError(
          error.response?.data?.detail,
          'Impossible de charger les comptes en attente.'
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (userId) => {
    if (!window.confirm('Approuver ce compte ? L’utilisateur pourra se connecter.')) {
      return;
    }

    try {
      await axios.post(`${API_URL}/users/${userId}/approve`);
      alert('Compte approuvé.');
      fetchPendingUsers();
    } catch (error) {
      console.error('Error:', error);
      alert('Erreur : ' + formatApiError(error.response?.data?.detail, "Impossible d'approuver le compte."));
    }
  };

  const handleReject = async (userId, username) => {
    if (
      !window.confirm(
        `Refuser et supprimer la demande pour « ${username} » ? Cette action est définitive (compte encore inactif uniquement).`
      )
    ) {
      return;
    }

    try {
      await axios.post(`${API_URL}/users/${userId}/reject`);
      alert('Demande refusée — le compte a été supprimé.');
      fetchPendingUsers();
    } catch (error) {
      console.error('Error:', error);
      alert('Erreur : ' + formatApiError(error.response?.data?.detail, 'Impossible de refuser ce compte.'));
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRoleLabel = (role) => {
    const roles = {
      'admin': 'Administrator',
      'gestionnaire': 'Manager',
      'agent': 'Agent',
      'maintenance': 'Maintenance Technician'
    };
    return roles[role] || role;
  };

  // Format data for DataTable
  const formattedData = pendingUsers.map(u => ({
    ...u,
    role_display: getRoleLabel(u.role),
    created_at_display: formatDate(u.created_at),
    full_name: `${u.first_name || ''} ${u.last_name || ''}`.trim() || 'N/A',
    email_display: u.email || 'N/A'
  }));

  const tableColumns = [
    { header: 'ID', field: 'id' },
    { header: 'Username', field: 'username' },
    { header: 'Full Name', field: 'full_name' },
    { header: 'Email', field: 'email_display' },
    { header: 'Role', field: 'role_display' },
    { header: 'Ville', field: 'ville' },
    { header: 'Creation Date', field: 'created_at_display' }
  ];

  // Vérifier les permissions (mêmes règles qu’au backend pour approuver / refuser)
  const canModerate = (pendingUser) => {
    if (user?.role === 'admin') {
      return true;
    }
    if (user?.role === 'gestionnaire') {
      return ['agent', 'maintenance'].includes(pendingUser.role);
    }
    return false;
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Account Approval</h1>
      </div>

      <Card>
        {errorMessage && (
          <div style={{ marginBottom: '20px', padding: '12px 16px', backgroundColor: '#ffeaea', borderRadius: '4px', border: '1px solid #ffb3b3', color: '#9d1d1d' }}>
            {errorMessage}
          </div>
        )}
        {pendingUsers.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <p>No accounts pending approval.</p>
            <p style={{ marginTop: '10px', fontSize: '0.9em' }}>
              All accounts have been approved or there are no new requests.
            </p>
          </div>
        ) : (
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    {tableColumns.map((col, idx) => (
                      <th key={idx}>{col.header}</th>
                    ))}
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {formattedData.length === 0 ? (
                    <tr>
                      <td colSpan={tableColumns.length + 1} className="empty-state">
                        No data available
                      </td>
                    </tr>
                  ) : (
                    formattedData.map((row) => (
                      <tr key={row.id}>
                        {tableColumns.map((col, colIdx) => (
                          <td key={colIdx}>{row[col.field]}</td>
                        ))}
                        <td className="actions">
                          {canModerate(row) ? (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                              <button
                                type="button"
                                className="btn-primary"
                                onClick={() => handleApprove(row.id)}
                                style={{ padding: '6px 12px', fontSize: '0.9em', width: 'auto' }}
                              >
                                Approuver
                              </button>
                              <button
                                type="button"
                                className="btn-delete"
                                onClick={() => handleReject(row.id, row.username)}
                                style={{ padding: '6px 12px', fontSize: '0.9em' }}
                              >
                                Rejeter
                              </button>
                            </div>
                          ) : (
                            <span style={{ color: '#999', fontSize: '0.9em', fontStyle: 'italic' }}>
                              Non autorisé
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
        )}
      </Card>
    </div>
  );
}
