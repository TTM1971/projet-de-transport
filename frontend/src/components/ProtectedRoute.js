import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children, allowedRoles = [], permission }) {
  const { user, loading, canAccess, hasRole } = useAuth();

  if (loading) {
    return <div className="loading-container">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Check by permission
  if (permission && !canAccess(permission)) {
    return (
      <div className="access-denied">
        <h2>Access Denied</h2>
        <p>You do not have the necessary permissions to access this page.</p>
        <p>Current role: <strong>{user.role}</strong></p>
      </div>
    );
  }

  // Check by role
  if (allowedRoles.length > 0 && !hasRole(allowedRoles)) {
    return (
      <div className="access-denied">
        <h2>Access Denied</h2>
        <p>This page is reserved for the following roles: {allowedRoles.join(', ')}</p>
        <p>Your role: <strong>{user.role}</strong></p>
      </div>
    );
  }

  return children;
}
