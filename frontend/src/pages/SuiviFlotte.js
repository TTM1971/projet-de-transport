import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Card from '../components/Card';
import StatsWidget from '../components/StatsWidget';
import { translateStatus } from '../utils/translations';

const API_URL = 'http://localhost:8000';

export default function SuiviFlotte() {
  const [buses, setBuses] = useState([]);
  const [pings, setPings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPingModal, setShowPingModal] = useState(false);
  const [pingData, setPingData] = useState({ bus_id: '', status: 'en_service' });

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [busesRes, pingsRes] = await Promise.all([
        axios.get(`${API_URL}/bus/`),
        axios.get(`${API_URL}/pings/`)
      ]);
      setBuses(busesRes.data);
      setPings(pingsRes.data.slice(-20).reverse()); // Last 20 pings
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePingSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/pings/`, { ...pingData, bus_id: parseInt(pingData.bus_id) });
      alert('Ping recorded!');
      setShowPingModal(false);
      fetchData();
    } catch (error) {
      alert('Error during recording');
    }
  };

  const getStatusColor = (statut) => {
    const colors = {
      'en_service': '#27ae60',
      'en_maintenance': '#e67e22',
      'hors_service': '#e74c3c',
      'disponible': '#3498db'
    };
    return colors[statut] || '#95a5a6';
  };

  if (loading) return <div className="loading">Loading...</div>;

  const busEnService = buses.filter(b => b.statut === 'en_service').length;
  const busMaintenance = buses.filter(b => b.statut === 'en_maintenance').length;
  const busDisponibles = buses.filter(b => b.statut === 'disponible').length;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Fleet Tracking</h1>
        <button className="btn-primary" onClick={() => setShowPingModal(true)}>+ Log Ping</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        <StatsWidget title="Total Buses" value={buses.length} color="#4a90e2" />
        <StatsWidget title="In Service" value={busEnService} color="#27ae60" />
        <StatsWidget title="In Maintenance" value={busMaintenance} color="#e67e22" />
        <StatsWidget title="Available" value={busDisponibles} color="#3498db" />
      </div>

      <Card title="Bus Status">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '15px' }}>
          {buses.map(bus => (
            <div key={bus.id} style={{
              padding: '15px',
              border: `2px solid ${getStatusColor(bus.statut)}`,
              borderRadius: '8px',
              background: '#f9f9f9'
            }}>
              <h4>{bus.immatriculation}</h4>
              <p><strong>Model:</strong> {bus.marque} {bus.modele}</p>
              <p><strong>Capacity:</strong> {bus.capacite} seats</p>
              <p><strong>Status:</strong> <span style={{ color: getStatusColor(bus.statut), fontWeight: 'bold' }}>{translateStatus(bus.statut)}</span></p>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Latest Pings (last 20)">
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {pings.length === 0 ? (
            <p>No pings recorded</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#4a90e2', color: 'white' }}>
                  <th style={{ padding: '10px' }}>ID</th>
                  <th style={{ padding: '10px' }}>Bus ID</th>
                  <th style={{ padding: '10px' }}>Status</th>
                  <th style={{ padding: '10px' }}>Date/Time</th>
                </tr>
              </thead>
              <tbody>
                {pings.map(ping => (
                  <tr key={ping.id} style={{ borderBottom: '1px solid #ddd' }}>
                    <td style={{ padding: '10px' }}>{ping.id}</td>
                    <td style={{ padding: '10px' }}>{ping.bus_id}</td>
                    <td style={{ padding: '10px' }}>{ping.status}</td>
                    <td style={{ padding: '10px' }}>{new Date(ping.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      {showPingModal && (
        <div className="modal-overlay" onClick={() => setShowPingModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Log Ping</h2>
            <form onSubmit={handlePingSubmit}>
              <div className="form-group">
                <label>Bus *</label>
                <select required value={pingData.bus_id} onChange={(e) => setPingData({...pingData, bus_id: e.target.value})}>
                  <option value="">Select</option>
                  {buses.map(b => <option key={b.id} value={b.id}>{b.immatriculation}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Status *</label>
                <select required value={pingData.status} onChange={(e) => setPingData({...pingData, status: e.target.value})}>
                  <option value="en_service">In Service</option>
                  <option value="en_maintenance">In Maintenance</option>
                  <option value="hors_service">Out of Service</option>
                  <option value="disponible">Available</option>
                </select>
              </div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowPingModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
