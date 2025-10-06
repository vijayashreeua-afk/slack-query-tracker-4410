import React from 'react';

/**
/ PUBLIC_INTERFACE
/ Toolbar component rendering the top action bar with:
/ - Fetch from Slack
/ - Export to Excel
/ - Refresh
/ - Status filter and search
/ - Theme toggle and connection indicator
*/
function Toolbar({
  themeToggleLabel,
  onToggleTheme,
  onFetchFromSlack,
  onExport,
  onRefresh,
  connectionState,
  loading,
  statusFilter,
  onStatusFilterChange,
  search,
  onSearchChange
}) {
  return (
    <div className="toolbar">
      <div className="toolbar-inner">
        <div className="brand">
          <span className="dot" />
          <span>Slack Query Tracker</span>
          <div className="status" title={`Backend connection: ${connectionState}`}>
            <span className={`status-dot ${connectionState}`} />
            <span>{connectionState}</span>
          </div>
        </div>
        <div className="toolbar-actions">
          <select
            className="select"
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(e) => onStatusFilterChange?.(e.target.value)}
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>
          <input
            className="input"
            placeholder="Search by user, resolver, or URL..."
            value={search}
            onChange={(e) => onSearchChange?.(e.target.value)}
          />
          <button className="btn" onClick={onRefresh} disabled={loading}>Refresh</button>
          <button className="btn secondary" onClick={onFetchFromSlack} disabled={loading}>Fetch from Slack</button>
          <button className="btn primary" onClick={onExport} disabled={loading}>Export to Excel</button>
          <button className="theme-toggle" onClick={onToggleTheme} aria-label="Toggle theme">
            {themeToggleLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Toolbar;
