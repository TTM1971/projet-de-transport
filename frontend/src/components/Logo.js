import React from 'react';
import './Logo.css';

export default function Logo({ variant = 'default' }) {
  // variant peut être 'default', 'large', 'small', 'compact'
  
  if (variant === 'compact') {
    return (
      <div className="logo-compact">
        <span className="logo-acronym">MEGANE</span>
      </div>
    );
  }

  return (
    <div className={`logo ${variant}`}>
      <div className="logo-acronym">MEGANE</div>
      <div className="logo-description">
        <div className="logo-line">
          <span className="logo-letter">M</span>obility
        </div>
        <div className="logo-line">
          <span className="logo-letter">E</span>ngine
        </div>
        <div className="logo-line">
          <span className="logo-letter">G</span>uidance
        </div>
        <div className="logo-line">
          <span className="logo-letter">A</span>nalytics
        </div>
        <div className="logo-line">
          <span className="logo-letter">N</span>etworked
        </div>
        <div className="logo-line">
          <span className="logo-letter">E</span>valuation
        </div>
      </div>
    </div>
  );
}
