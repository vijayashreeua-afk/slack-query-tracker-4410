import React, { useEffect, useMemo, useState } from 'react';
import './App.css';
import Toolbar from './components/Toolbar';
import ChannelConfigPanel from './components/ChannelConfigPanel';
import NewQueryForm from './components/NewQueryForm';
import QueriesList from './components/QueriesList';
import { listQueries, fetchFromSlack, exportToExcel, getChannelConfig, saveChannelConfig, createQuery, updateQuery, deleteQuery } from './api/client';

// PUBLIC_INTERFACE
function App() {
  /**
   * Main application component rendering the Slack Query Tracker dashboard.
   * Manages global UI state, messages, and integrates child components.
   */
  const [theme, setTheme] = useState('light');
  const [connectionState, setConnectionState] = useState('disconnected'); // disconnected | connected | error
  const [message, setMessage] = useState({ type: '', text: '' }); // success | error | info
  const [loading, setLoading] = useState(false);

  const [channelConfig, setChannelConfig] = useState({ channelId: '', channelName: '' });

  const [queries, setQueries] = useState([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const clearMessageAfterDelay = (delay = 2500) => {
    window.clearTimeout(clearMessageAfterDelay._t);
    clearMessageAfterDelay._t = window.setTimeout(() => setMessage({ type: '', text: '' }), delay);
  };

  const fetchConfig = async () => {
    try {
      const data = await getChannelConfig();
      setChannelConfig({
        channelId: data?.channelId || data?.channel_id || '',
        channelName: data?.channelName || data?.channel_name || '',
      });
      setConnectionState('connected');
    } catch (e) {
      setConnectionState('error');
      setMessage({ type: 'error', text: e.message || 'Failed to load channel config' });
      clearMessageAfterDelay();
    }
  };

  const loadQueries = async (opts = {}) => {
    setLoading(true);
    try {
      const p = opts.page ?? page;
      const s = opts.status ?? statusFilter;
      const q = opts.search ?? search;
      const resp = await listQueries({ page: p, pageSize, status: s, search: q });
      setQueries(resp?.items || resp?.data || []);
      setTotal(resp?.total || 0);
      if (typeof p === 'number') setPage(p);
    } catch (e) {
      setMessage({ type: 'error', text: e.message || 'Failed to load queries' });
      clearMessageAfterDelay();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
    loadQueries({ page: 1 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const themeToggle = useMemo(() => (theme === 'light' ? '🌙 Dark' : '☀️ Light'), [theme]);

  // Handlers
  const handleToggleTheme = () => setTheme(prev => (prev === 'light' ? 'dark' : 'light'));

  const handleSaveConfig = async (cfg) => {
    setLoading(true);
    try {
      await saveChannelConfig(cfg);
      setChannelConfig(cfg);
      setConnectionState('connected');
      setMessage({ type: 'success', text: 'Channel configuration saved.' });
    } catch (e) {
      setConnectionState('error');
      setMessage({ type: 'error', text: e.message || 'Failed to save channel config' });
    } finally {
      clearMessageAfterDelay();
      setLoading(false);
    }
  };

  const handleFetchFromSlack = async () => {
    setLoading(true);
    try {
      await fetchFromSlack();
      setMessage({ type: 'success', text: 'Fetched data from Slack.' });
      await loadQueries({ page: 1 });
    } catch (e) {
      setMessage({ type: 'error', text: e.message || 'Failed to fetch from Slack' });
    } finally {
      clearMessageAfterDelay();
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setLoading(true);
    try {
      const blob = await exportToExcel();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const now = new Date();
      const ts = now.toISOString().replace(/[:.]/g, '-');
      a.download = `slack-queries-${ts}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setMessage({ type: 'success', text: 'Export started. File should download shortly.' });
    } catch (e) {
      setMessage({ type: 'error', text: e.message || 'Failed to export' });
    } finally {
      clearMessageAfterDelay();
      setLoading(false);
    }
  };

  const handleRefresh = async () => loadQueries();

  const handleCreateQuery = async (payload) => {
    setLoading(true);
    try {
      await createQuery(payload);
      setMessage({ type: 'success', text: 'New query added.' });
      await loadQueries({ page: 1 });
    } catch (e) {
      setMessage({ type: 'error', text: e.message || 'Failed to add query' });
    } finally {
      clearMessageAfterDelay();
      setLoading(false);
    }
  };

  const handleUpdateQuery = async (id, payload) => {
    setLoading(true);
    try {
      await updateQuery(id, payload);
      setMessage({ type: 'success', text: 'Query updated.' });
      await loadQueries({ page });
    } catch (e) {
      setMessage({ type: 'error', text: e.message || 'Failed to update query' });
    } finally {
      clearMessageAfterDelay();
      setLoading(false);
    }
  };

  const handleDeleteQuery = async (id) => {
    setLoading(true);
    try {
      await deleteQuery(id);
      setMessage({ type: 'success', text: 'Query deleted.' });
      await loadQueries({ page });
    } catch (e) {
      setMessage({ type: 'error', text: e.message || 'Failed to delete query' });
    } finally {
      clearMessageAfterDelay();
      setLoading(false);
    }
  };

  return (
    <div className="app-root" data-theme={theme}>
      <Toolbar
        themeToggleLabel={themeToggle}
        onToggleTheme={handleToggleTheme}
        onFetchFromSlack={handleFetchFromSlack}
        onExport={handleExport}
        onRefresh={handleRefresh}
        connectionState={connectionState}
        loading={loading}
        statusFilter={statusFilter}
        onStatusFilterChange={(v) => { setStatusFilter(v); loadQueries({ page: 1, status: v }); }}
        search={search}
        onSearchChange={(v) => { setSearch(v); loadQueries({ page: 1, search: v }); }}
      />

      <div className="layout">
        <aside className="panel">
          <ChannelConfigPanel
            config={channelConfig}
            onSave={handleSaveConfig}
            saving={loading}
          />
          <NewQueryForm onCreate={handleCreateQuery} disabled={loading} />
          {message?.text ? (
            <div className={`inline-message ${message.type}`}>{message.text}</div>
          ) : null}
        </aside>

        <main className="content">
          <QueriesList
            items={queries}
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={(p) => loadQueries({ page: p })}
            onUpdate={handleUpdateQuery}
            onDelete={handleDeleteQuery}
            loading={loading}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
