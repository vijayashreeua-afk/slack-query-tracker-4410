import React, { useState } from 'react';

/**
// PUBLIC_INTERFACE
// NewQueryForm provides fields to add a new query manually.
*/
function NewQueryForm({ onCreate, disabled }) {
  const [user, setUser] = useState('');
  const [threadUrl, setThreadUrl] = useState('');
  const [resolver, setResolver] = useState('');
  const [status, setStatus] = useState('open');

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreate?.({
      user: user.trim(),
      thread_url: threadUrl.trim(),
      resolver: resolver.trim(),
      status,
    });
    setUser('');
    setThreadUrl('');
    setResolver('');
    setStatus('open');
  };

  return (
    <div style={{ marginTop: 16 }}>
      <h3 style={{ margin: '0 0 12px 0' }}>Add New Query</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="label">User</label>
          <input
            className="input"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            placeholder="Name of the user"
            required
          />
        </div>
        <div className="form-group">
          <label className="label">Thread URL</label>
          <input
            className="input"
            type="url"
            value={threadUrl}
            onChange={(e) => setThreadUrl(e.target.value)}
            placeholder="https://slack.com/archives/..."
            required
          />
        </div>
        <div className="form-group">
          <label className="label">Resolver</label>
          <input
            className="input"
            value={resolver}
            onChange={(e) => setResolver(e.target.value)}
            placeholder="Who resolved the issue"
          />
        </div>
        <div className="form-group">
          <label className="label">Status</label>
          <select className="select" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
        <button className="btn" type="submit" disabled={disabled}>Add Query</button>
      </form>
    </div>
  );
}

export default NewQueryForm;
