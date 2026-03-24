import React, { useState } from 'react';
import { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import Logo from '../components/Logo';
import { formatApiError } from '../utils/apiError';
const API_URL = 'http://localhost:8000';

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('agent');
  const [ville, setVille] = useState('');
  const [villes, setVilles] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const loadVilles = async () => {
      try {
        const res = await axios.get(`${API_URL}/villes`);
        setVilles(res.data.active || []);
      } catch (_) {
        setVilles([]);
      }
    };
    loadVilles();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    // Validations
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must contain at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/auth/register`, {
        username,
        password,
        role,
        ville
      });
      
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail, 'Erreur lors de la création du compte.'));
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="login-page">
        <div className="login-container">
          <div className="login-card">
            <div className="login-header">
              <Logo variant="large" />
              <p style={{ marginTop: '20px' }}>Account created successfully!</p>
            </div>
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <p>Redirecting to login page...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <Logo variant="large" />
            <p style={{ marginTop: '20px' }}>Create an account</p>
          </div>
          
          <form onSubmit={handleSubmit} className="login-form">
            {error && <div className="error-message">{error}</div>}
            
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                placeholder="Choose a username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="Repeat the password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="ville">Ville</label>
              <select
                id="ville"
                value={ville}
                onChange={(e) => setVille(e.target.value)}
                required
                disabled={loading}
              >
                <option value="">-- Choisir --</option>
                {villes.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="role">Role</label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                disabled={loading}
              >
                <option value="agent">Agent</option>
                <option value="gestionnaire">Manager</option>
                <option value="maintenance">Maintenance</option>
              </select>
            </div>
            
            <button type="submit" className="btn-login" disabled={loading}>
              {loading ? 'Creating...' : 'Create Account'}
            </button>
          </form>
          
          <div className="login-register-link">
            <p>Already have an account? <Link to="/login">Sign in</Link></p>
          </div>
        </div>
      </div>
    </div>
  );
}