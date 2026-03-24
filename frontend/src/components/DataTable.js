import React from 'react';
export default function DataTable({ columns, data, onEdit, onDelete, onRowClick }) {
  return (
    <div className="data-table-container">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col, idx) => (
              <th key={idx}>{col.header}</th>
            ))}
            {(onEdit || onDelete) && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length + (onEdit || onDelete ? 1 : 0)} className="empty-state">
                No data available
              </td>
            </tr>
          ) : (
            data.map((row, rowIdx) => (
              <tr 
                key={rowIdx}
                onClick={() => onRowClick && onRowClick(row)}
                style={onRowClick ? { cursor: 'pointer' } : {}}
              >
                {columns.map((col, colIdx) => {
                  // If it's the immatriculation field and we can click, make it clickable
                  if (col.field === 'immatriculation' && onRowClick) {
                    const cellValue = col.formatter ? col.formatter(row[col.field], row) : row[col.field];
                    return (
                      <td 
                        key={colIdx}
                        style={{ color: '#3498db', textDecoration: 'underline' }}
                        onClick={(e) => { e.stopPropagation(); onRowClick(row); }}
                      >
                        {cellValue}
                      </td>
                    );
                  }
                  const cellValue = col.formatter ? col.formatter(row[col.field], row) : row[col.field];
                  return <td key={colIdx}>{cellValue}</td>;
                })}
                {(onEdit || onDelete) && (
                  <td className="actions" onClick={(e) => e.stopPropagation()}>
                    {onEdit && (
                      <button className="btn-edit" onClick={(e) => { e.stopPropagation(); onEdit(row); }}>
                        Edit
                      </button>
                    )}
                    {onDelete && (
                      <button className="btn-delete" onClick={(e) => { e.stopPropagation(); onDelete(row); }}>
                        Delete
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
