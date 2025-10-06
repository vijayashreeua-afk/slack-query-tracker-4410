import React from 'react';

/**
// PUBLIC_INTERFACE
// QueriesList renders a table of queries with basic pagination and inline actions.
*/
function QueriesList({ items, page, pageSize, total, onPageChange, onUpdate, onDelete, loading }) {
  const totalPages = Math.max(1, Math.ceil((total || 0) / pageSize));
  const disablePrev = page <= 1 || loading;
  const disableNext = page >= totalPages || loading;

  const handleResolveToggle = (item) => {
    const isResolved = item.status === 'resolved';
    const payload = {
      status: isResolved ? 'open' : 'resolved',
      resolved_at: isResolved ? null : new Date().toISOString(),
    };
    onUpdate?.(item.id ?? item._id ?? item.thread_url, payload);
  };

  const handleDelete = (item) => {
    const id = item.id ?? item._id ?? item.thread_url;
    onDelete?.(id);
  };

  const formatDate = (d) => {
    if (!d) return '';
    const dt = typeof d === 'string' ? new Date(d) : d;
    if (Number.isNaN(dt.getTime())) return '';
    return dt.toLocaleString();
  };

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>User</th>
            <th>Thread URL</th>
            <th>Resolver</th>
            <th>Status</th>
            <th>Created At</th>
            <th>Resolved At</th>
            <th style={{ width: 160 }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items && items.length ? items.map((item, idx) => (
            <tr key={(item.id ?? item._id ?? item.thread_url ?? idx) + '-' + idx}>
              <td>{item.user || item.user_name || '-'}</td>
              <td>
                {item.thread_url ? (
                  <a href={item.thread_url} target="_blank" rel="noreferrer" style={{ color: 'var(--primary)', textDecoration: 'none' }}>
                    Open thread
                  </a>
                ) : '-'}
              </td>
              <td>{item.resolver || '-'}</td>
              <td>
                <span className={`badge ${String(item.status || '').toLowerCase()}`}>{item.status || '-'}</span>
              </td>
              <td>{formatDate(item.created_at)}</td>
              <td>{formatDate(item.resolved_at)}</td>
              <td>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn" onClick={() => handleResolveToggle(item)} disabled={loading}>
                    {item.status === 'resolved' ? 'Mark Open' : 'Mark Resolved'}
                  </button>
                  <button className="btn" onClick={() => handleDelete(item)} disabled={loading}>
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          )) : (
            <tr>
              <td colSpan="7" style={{ color: 'var(--muted)' }}>
                {loading ? 'Loading...' : 'No queries found.'}
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div className="pagination">
        <div className="info">
          Page {page} of {totalPages} • Total {total}
        </div>
        <div className="controls">
          <button className="btn" disabled={disablePrev} onClick={() => onPageChange?.(page - 1)}>Previous</button>
          <button className="btn" disabled={disableNext} onClick={() => onPageChange?.(page + 1)}>Next</button>
        </div>
      </div>
    </div>
  );
}

export default QueriesList;
