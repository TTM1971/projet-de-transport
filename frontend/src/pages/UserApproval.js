import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import BackButton from '../components/BackButton';
import './CommonPages.css';

const API_URL = 'http://localhost:8000';

export default function UserApproval() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPendingUsers();
  }, []);

  const fetchPendingUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/users/pending`);
      setPendingUsers(response.data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error loading pending accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (userId) => {
    if (!window.confirm('Do you want to approve this account? The user will be able to log in after approval.')) {
      return;
    }

    try {
      await axios.post(`${API_URL}/users/${userId}/approve`);
      alert('Account approved successfully!');
      fetchPendingUsers(); // Reload list
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = error.response?.data?.detail || 'Error approving account';
      alert('Error: ' + errorMessage);
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
    { header: 'Creation Date', field: 'created_at_display' }
  ];

  // Vérifier les permissions
  const canApprove = (pendingUser) => {
    if (user?.role === 'admin') {
      return true; // Admin peut tout approuver
    }
    if (user?.role === 'gestionnaire') {
      // Gestionnaire peut approuver uniquement agents et maintenance
      return ['agent', 'maintenance'].includes(pendingUser.role);
    }
    return false;
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Account Approval</h1>
        <BackButton />
      </div>

      <Card>
        {pendingUsers.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <p>No accounts pending approval.</p>
            <p style={{ marginTop: '10px', fontSize: '0.9em' }}>
              All accounts have been approved or there are no new requests.
            </p>
          </div>
        ) : (
          <>
            <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#fff3cd', borderRadius: '4px', border: '1px solid #ffc107' }}>
              <p style={{ margin: 0, fontWeight: 500 }}>
                {pendingUsers.length} account(s) pending approval
              </p>
              <p style={{ margin: '5px 0 0 0', fontSize: '0.9em', color: '#666' }}>
                {user?.role === 'admin' 
                  ? 'As administrator, you can approve all accounts.'
                  : 'As manager, you can only approve agent and maintenance technician accounts.'}
              </p>
            </div>

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
                          {canApprove(row) ? (
                            <button
                              className="btn-primary"
                              onClick={() => handleApprove(row.id)}
                              style={{ padding: '6px 12px', fontSize: '0.9em' }}
                            >
                              Approve
                            </button>
                          ) : (
                            <span style={{ color: '#999', fontSize: '0.9em', fontStyle: 'italic' }}>
                              Not authorized
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
