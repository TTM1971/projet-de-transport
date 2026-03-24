import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import BackButton from '../components/BackButton';
import { formatPrice } from '../utils/currency';
import API_URL from '../config/api';

export default function AgentDeparts() {
  const navigate = useNavigate();
  const [departs, setDeparts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    fetchDeparts();
  }, [selectedDate]);

  const fetchDeparts = async () => {
    try {
      setLoading(true);
      // Récupérer uniquement les départs du jour et futurs
      const today = new Date().toISOString().split('T')[0];
      const response = await axios.get(`${API_URL}/departs/date/${selectedDate >= today ? selectedDate : today}`);
      
      // Filtrer pour ne garder que les départs du jour et futurs, avec places disponibles
      const todayDate = new Date(today).setHours(0, 0, 0, 0);
      const filteredDeparts = response.data
        .filter(depart => {
          const departDate = new Date(depart.date_depart).setHours(0, 0, 0, 0);
          return departDate >= todayDate && 
                 depart.places_disponibles > 0 && 
                 depart.statut !== 'annule';
        })
        .sort((a, b) => {
          const dateA = new Date(a.date_depart);
          const dateB = new Date(b.date_depart);
          if (dateA.getTime() === dateB.getTime()) {
            return a.heure_depart.localeCompare(b.heure_depart);
          }
          return dateA - dateB;
        });
      
      setDeparts(filteredDeparts);
    } catch (error) {
      console.error('Error:', error);
      alert('Error loading departures');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const formatHeure = (heure) => {
    if (!heure) return '';
    if (typeof heure === 'string') return heure;
    if (heure.hour !== undefined) {
      return `${String(heure.hour).padStart(2, '0')}:${String(heure.minute || 0).padStart(2, '0')}`;
    }
    return heure.toString();
  };

  // Format data for DataTable
  const formattedData = departs.map(depart => ({
    ...depart,
    date_display: formatDate(depart.date_depart),
    heure_display: formatHeure(depart.heure_depart),
    prix_display: formatPrice(depart.prix),
    places_display: `${depart.places_disponibles} available seats`
  }));

  const tableColumns = [
    { header: 'Date', field: 'date_display' },
    { header: 'Time', field: 'heure_display' },
    { header: 'Price', field: 'prix_display' },
    { header: 'Seats', field: 'places_display' },
    { header: 'Status', field: 'statut', formatter: (value) => {
      const translations = { 'programme': 'Scheduled', 'en_cours': 'In Progress', 'termine': 'Completed', 'annule': 'Cancelled' };
      return translations[value] || value;
    }}
  ];

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Available Departures</h1>
        <BackButton />
      </div>

      <Card>
        <div style={{ marginBottom: '20px' }}>
          <label style={{ marginRight: '10px', fontWeight: 500 }}>Filter by date (from today):</label>
          <input
            type="date"
            value={selectedDate}
            min={new Date().toISOString().split('T')[0]}
            onChange={(e) => {
              const selected = e.target.value;
              const today = new Date().toISOString().split('T')[0];
              setSelectedDate(selected >= today ? selected : today);
            }}
            style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
          />
        </div>
        <p style={{ color: '#666', marginBottom: '20px', fontStyle: 'italic' }}>
          Note: Only today's and future departures are displayed. Past departures are not accessible.
        </p>
        {departs.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#666', padding: '40px' }}>
            No departures available for this date or future dates.
          </p>
        ) : (
          <DataTable
            columns={tableColumns}
            data={formattedData}
            onEdit={null}
            onDelete={null}
          />
        )}
      </Card>
    </div>
  );
}
