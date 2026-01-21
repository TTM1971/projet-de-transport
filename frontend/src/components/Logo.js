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
          <span className="logo-letter">M</span>anagement
        </div>
        <div className="logo-line">
          <span className="logo-letter">E</span>nhanced
        </div>
        <div className="logo-line">
          <span className="logo-letter">G</span>round
        </div>
        <div className="logo-line">
          <span className="logo-letter">A</span>nalytics <span className="logo-amp">&</span>
        </div>
        <div className="logo-line">
          <span className="logo-letter">N</span>etwork
        </div>
        <div className="logo-line">
          <span className="logo-letter">E</span>ngine
        </div>
      </div>
    </div>
  );
}
