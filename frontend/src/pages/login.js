import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Logo from '../components/Logo';
export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password);
    
    if (result.success) {
      // Rediriger selon le rÃ´le
      const role = result.user.role;
      switch(role) {
        case 'admin':
          navigate('/dashboard');
          break;
        case 'agent':
          navigate('/vente');
          break;
        case 'gestionnaire':
          navigate('/bus');
          break;
        case 'maintenance':
          navigate('/maintenance');
          break;
        default:
          navigate('/dashboard');
      }
    } else {
      setError(result.error || 'Invalid credentials');
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <Logo variant="large" />
          </div>
          
          <form onSubmit={handleSubmit} className="login-form">
            {error && <div className="error-message">{error}</div>}
            
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                placeholder="Enter your username"
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
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            
            <button type="submit" className="btn-login" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
          
          <div className="login-register-link">
            <p>Don't have an account? <Link to="/register">Create an account</Link></p>
          </div>
          
          <div className="login-info">
            <p><strong>Test Accounts:</strong></p>
            <ul>
              <li>Admin: <code>admin</code> / <code>admin123</code></li>
              <li>Agent Ottawa: <code>agent_ottawa</code> / <code>agent123</code></li>
              <li>Manager Ottawa: <code>gestionnaire_ottawa</code> / <code>gest123</code></li>
              <li>Manager Montreal: <code>gestionnaire_montreal</code> / <code>gest123</code></li>
              <li>Maintenance: <code>maintenance</code> / <code>maint123</code></li>
              <li>Chauffeur: <code>chauffeur_demo</code> / <code>chauffeur123</code></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

