import React from 'react';
import { useNavigate } from 'react-router-dom';
export default function BackButton({ onClick, label = '← Back', className = '' }) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(-1); // Revenir à la page précédente
    }
  };

  return (
    <button 
      className={`btn-back ${className}`} 
      onClick={handleClick}
      type="button"
    >
      {label}
    </button>
  );
}
