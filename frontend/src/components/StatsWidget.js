import React from 'react';
import './StatsWidget.css';

export default function StatsWidget({ title, value, icon, color = '#4a90e2', onClick }) {
  return (
    <div 
      className="stats-widget" 
      style={{ 
        borderTopColor: color,
        cursor: onClick ? 'pointer' : 'default',
        transition: onClick ? 'all 0.3s ease' : 'none'
      }}
      onClick={onClick}
      onMouseEnter={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(-5px)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        }
      }}
      onMouseLeave={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '';
        }
      }}
    >
      {icon && (
        <div className="stats-icon" style={{ color }}>
          {icon}
        </div>
      )}
      <div className="stats-content">
        <div className="stats-title">
          {title}
          {onClick && <span style={{ fontSize: '0.8em', marginLeft: '5px', opacity: 0.7 }}>→</span>}
        </div>
        <div className="stats-value">{value}</div>
      </div>
    </div>
  );
}
