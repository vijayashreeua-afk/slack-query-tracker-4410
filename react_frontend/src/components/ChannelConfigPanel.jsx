import React, { useEffect, useState } from 'react';

/**
// PUBLIC_INTERFACE
// ChannelConfigPanel allows entering and saving Slack channel ID and name.
*/
function ChannelConfigPanel({ config, onSave, saving }) {
  const [channelId, setChannelId] = useState('');
  const [channelName, setChannelName] = useState('');

  useEffect(() => {
    setChannelId(config?.channelId || config?.channel_id || '');
    setChannelName(config?.channelName || config?.channel_name || '');
  }, [config]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave?.({ channelId: channelId.trim(), channelName: channelName.trim() });
  };

  return (
    <div>
      <h3 style={{ margin: '4px 0 12px 0' }}>Channel Configuration</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="label">Channel ID</label>
          <input
            className="input"
            value={channelId}
            onChange={(e) => setChannelId(e.target.value)}
            placeholder="e.g., C01234567"
            required
          />
        </div>
        <div className="form-group">
          <label className="label">Channel Name</label>
          <input
            className="input"
            value={channelName}
            onChange={(e) => setChannelName(e.target.value)}
            placeholder="e.g., support-queries"
          />
        </div>
        <button className="btn primary" type="submit" disabled={saving}>
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </form>
    </div>
  );
}

export default ChannelConfigPanel;
