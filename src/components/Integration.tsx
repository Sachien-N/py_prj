import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Server, ArrowRight, CheckCircle2, XCircle, Clock, 
  RefreshCw, Shield, AlertTriangle, Zap, Wallet, CreditCard
} from 'lucide-react';

export default function Integration() {
  const [syncStatus, setSyncStatus] = useState<Record<string, 'idle' | 'syncing' | 'success' | 'error'>>({
    'b-to-a': 'idle',
    'c-to-a': 'idle',
    'a-to-b': 'idle',
    'a-to-c': 'idle',
  });

  const simulateSync = (id: string) => {
    setSyncStatus(prev => ({ ...prev, [id]: 'syncing' }));
    setTimeout(() => {
      setSyncStatus(prev => ({ ...prev, [id]: 'success' }));
      setTimeout(() => {
        setSyncStatus(prev => ({ ...prev, [id]: 'idle' }));
      }, 3000);
    }, 2000);
  };

  const dataFlows = [
    {
      id: 'b-to-a',
      from: { name: 'App B — Subscription Tracker', icon: <CreditCard size={16} />, color: 'purple' },
      to: { name: 'App A — Expense Manager', icon: <Wallet size={16} />, color: 'blue' },
      endpoint: 'GET /eligible-expenses',
      data: 'Active subscription costs (monthly equivalent)',
      frequency: 'On-demand / Scheduled',
      idempotency: 'source_app + external_id prevents duplicates',
    },
    {
      id: 'c-to-a',
      from: { name: 'App C — Electricity Manager', icon: <Zap size={16} />, color: 'amber' },
      to: { name: 'App A — Expense Manager', icon: <Wallet size={16} />, color: 'blue' },
      endpoint: 'GET /eligible-expenses',
      data: 'Actual electricity bills (not estimates)',
      frequency: 'On-demand / Scheduled',
      idempotency: 'source_app + external_id prevents duplicates',
    },
    {
      id: 'a-to-b',
      from: { name: 'App A — Expense Manager', icon: <Wallet size={16} />, color: 'blue' },
      to: { name: 'App B — Subscription Tracker', icon: <CreditCard size={16} />, color: 'purple' },
      endpoint: 'GET /categories',
      data: 'Expense categories for consistent mapping',
      frequency: 'On startup / Manual refresh',
      idempotency: 'Categories are reference data, cached locally',
    },
    {
      id: 'a-to-c',
      from: { name: 'App A — Expense Manager', icon: <Wallet size={16} />, color: 'blue' },
      to: { name: 'App C — Electricity Manager', icon: <Zap size={16} />, color: 'amber' },
      endpoint: 'GET /categories',
      data: 'Expense categories for consistent mapping',
      frequency: 'On startup / Manual refresh',
      idempotency: 'Categories are reference data, cached locally',
    },
  ];

  const integrationRules = [
    { rule: 'Use HTTPS for all production API calls', critical: true },
    { rule: 'Configure API base URLs via environment variables', critical: true },
    { rule: 'Never hardcode localhost URLs in production', critical: true },
    { rule: 'Authenticate with Bearer tokens', critical: true },
    { rule: 'Use configurable timeouts (default: 10s)', critical: false },
    { rule: 'Implement bounded retries (max 3 attempts)', critical: false },
    { rule: 'Validate external responses with Pydantic', critical: true },
    { rule: 'Use idempotent imports (source_app + external_id)', critical: true },
    { rule: 'Never overwrite manual records automatically', critical: true },
    { rule: 'Distinguish estimated vs actual charges clearly', critical: true },
    { rule: 'Remain functional when peer APIs are unavailable', critical: true },
    { rule: 'Log sync status and errors for debugging', critical: false },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 p-8"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
            <Server size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Cross-Application Integration</h1>
            <p className="text-violet-300 text-sm">Real REST API communication between all three apps</p>
          </div>
        </div>
        <p className="text-gray-400 max-w-3xl">
          The three applications communicate exclusively through their public HTTPS REST API endpoints. 
          Each integration is idempotent, authenticated, and gracefully handles failures.
        </p>
      </motion.div>

      {/* Data Flow Diagram */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Data Flow Architecture</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <div className="flex flex-col lg:flex-row items-center justify-center gap-4 lg:gap-8">
            {/* App B */}
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-4 text-center w-48">
              <CreditCard size={24} className="text-purple-400 mx-auto mb-2" />
              <p className="font-semibold text-white text-sm">App B</p>
              <p className="text-xs text-gray-500">Subscriptions</p>
            </div>

            {/* Arrow B→A */}
            <div className="flex flex-col items-center">
              <ArrowRight size={20} className="text-purple-400 rotate-0 lg:rotate-0" />
              <span className="text-xs text-gray-500 mt-1">eligible-expenses</span>
            </div>

            {/* App A (Center) */}
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 text-center w-48">
              <Wallet size={24} className="text-blue-400 mx-auto mb-2" />
              <p className="font-semibold text-white text-sm">App A</p>
              <p className="text-xs text-gray-500">Expenses Hub</p>
            </div>

            {/* Arrow A→C */}
            <div className="flex flex-col items-center">
              <span className="text-xs text-gray-500 mb-1">categories</span>
              <ArrowRight size={20} className="text-blue-400" />
            </div>

            {/* App C */}
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 text-center w-48">
              <Zap size={24} className="text-amber-400 mx-auto mb-2" />
              <p className="font-semibold text-white text-sm">App C</p>
              <p className="text-xs text-gray-500">Electricity</p>
            </div>
          </div>

          {/* Reverse arrows */}
          <div className="flex flex-col lg:flex-row items-center justify-center gap-4 lg:gap-8 mt-4">
            <div className="w-48" />
            <div className="flex flex-col items-center">
              <ArrowRight size={20} className="text-amber-400 rotate-180" />
              <span className="text-xs text-gray-500 mt-1">eligible-expenses</span>
            </div>
            <div className="w-48" />
            <div className="flex flex-col items-center">
              <ArrowRight size={20} className="text-blue-400 rotate-180" />
              <span className="text-xs text-gray-500 mt-1">categories</span>
            </div>
            <div className="w-48" />
          </div>
        </div>
      </div>

      {/* Sync Simulation */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Synchronization Simulation</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {dataFlows.map((flow) => (
            <div key={flow.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400">
                    {flow.from.icon}
                  </div>
                  <ArrowRight size={14} className="text-gray-600" />
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400">
                    {flow.to.icon}
                  </div>
                </div>
                <button
                  onClick={() => simulateSync(flow.id)}
                  disabled={syncStatus[flow.id] === 'syncing'}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 text-xs font-medium border border-blue-500/20 hover:bg-blue-500/20 disabled:opacity-50 transition-colors"
                >
                  <RefreshCw size={12} className={syncStatus[flow.id] === 'syncing' ? 'animate-spin' : ''} />
                  {syncStatus[flow.id] === 'syncing' ? 'Syncing...' : 
                   syncStatus[flow.id] === 'success' ? 'Done!' : 'Sync Now'}
                </button>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-20">Endpoint:</span>
                  <code className="text-xs text-white font-mono">{flow.endpoint}</code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-20">Data:</span>
                  <span className="text-xs text-gray-300">{flow.data}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-20">Idempotency:</span>
                  <span className="text-xs text-gray-400">{flow.idempotency}</span>
                </div>
              </div>

              {/* Status indicator */}
              <div className="mt-3 pt-3 border-t border-gray-800">
                {syncStatus[flow.id] === 'idle' && (
                  <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <Clock size={12} /> Ready to sync
                  </div>
                )}
                {syncStatus[flow.id] === 'syncing' && (
                  <div className="flex items-center gap-1.5 text-xs text-blue-400">
                    <RefreshCw size={12} className="animate-spin" /> Fetching data...
                  </div>
                )}
                {syncStatus[flow.id] === 'success' && (
                  <div className="flex items-center gap-1.5 text-xs text-green-400">
                    <CheckCircle2 size={12} /> Synced successfully (3 new, 0 duplicates)
                  </div>
                )}
                {syncStatus[flow.id] === 'error' && (
                  <div className="flex items-center gap-1.5 text-xs text-red-400">
                    <XCircle size={12} /> Sync failed — peer API unavailable
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Integration Rules */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Integration Rules</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {integrationRules.map((item) => (
              <div key={item.rule} className="flex items-start gap-2">
                {item.critical ? (
                  <Shield size={14} className="text-red-400 mt-0.5 flex-shrink-0" />
                ) : (
                  <CheckCircle2 size={14} className="text-green-400 mt-0.5 flex-shrink-0" />
                )}
                <span className="text-sm text-gray-300">{item.rule}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Error Handling */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Error Handling Strategy</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              title: 'Timeout',
              desc: 'Default 10s timeout. Bounded retry with exponential backoff (max 3 attempts).',
              action: 'Log warning, show "Sync unavailable" in UI, continue without external data.',
              icon: <Clock size={18} className="text-amber-400" />,
            },
            {
              title: 'HTTP Error',
              desc: 'Handle 4xx (client error) and 5xx (server error) separately.',
              action: '4xx: Log and alert. 5xx: Retry with backoff. Show error status in dashboard.',
              icon: <AlertTriangle size={18} className="text-red-400" />,
            },
            {
              title: 'Invalid Response',
              desc: 'Validate all external responses with Pydantic schemas.',
              action: 'Reject invalid data, log the raw response for debugging, do not import.',
              icon: <XCircle size={18} className="text-orange-400" />,
            },
          ].map((item) => (
            <div key={item.title} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                {item.icon}
                <h3 className="font-semibold text-white text-sm">{item.title}</h3>
              </div>
              <p className="text-xs text-gray-400 mb-2">{item.desc}</p>
              <p className="text-xs text-gray-500">→ {item.action}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Acceptance Workflow */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Complete Acceptance Workflow</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="space-y-3">
            {[
              'Create a subscription in Application B (e.g., Netflix, $14.99/month)',
              'Retrieve it through Application B\'s public API (GET /subscriptions)',
              'Trigger sync in Application A — import the eligible charge',
              'Confirm the budget summary in App A updates correctly',
              'Synchronize again — confirm NO duplicate is created (idempotency)',
              'Record a simulated electricity reading in Application C',
              'Verify consumption calculation and estimated bill in App C',
              'Record actual bill/payment only when explicitly labelled as demo input',
              'Sync eligible electricity expense info into Application A',
              'Verify all three apps work independently',
              'Turn off one API — confirm others continue functioning',
              'Restart an app — verify records persist (database persistence)',
            ].map((step, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-bold text-green-400">{i + 1}</span>
                </div>
                <span className="text-sm text-gray-300">{step}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Integration Checklist */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Integration Checklist</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            'All three APIs accessible via public HTTPS URLs',
            'Bearer token authentication working on protected endpoints',
            'App A can fetch subscriptions from App B',
            'App A can fetch electricity expenses from App C',
            'App B can fetch categories from App A',
            'App C can fetch categories from App A',
            'No duplicate records after repeated syncs',
            'Manual sync button works on each dashboard',
            'Last sync timestamp displayed correctly',
            'Graceful degradation when peer API is down',
            'Estimated vs actual charges clearly distinguished',
            'All data persists after application restart',
          ].map((item) => (
            <div key={item} className="flex items-center gap-2 bg-gray-900 border border-gray-800 rounded-lg px-4 py-3">
              <CheckCircle2 size={16} className="text-green-400 flex-shrink-0" />
              <span className="text-sm text-gray-300">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
