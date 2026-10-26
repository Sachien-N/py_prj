import { useState } from 'react';
import { motion } from 'framer-motion';
import { BookOpen, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';

interface Endpoint {
  method: string;
  path: string;
  desc: string;
  auth: boolean;
  request?: string;
  response?: string;
}

interface AppApi {
  name: string;
  color: string;
  endpoints: Endpoint[];
}

export default function ApiDocs() {
  const [expandedEndpoint, setExpandedEndpoint] = useState<string | null>(null);
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  const apis: AppApi[] = [
    {
      name: 'Application A — Expense Manager',
      color: 'blue',
      endpoints: [
        { method: 'GET', path: '/health', desc: 'Health check', auth: false, response: '{"status": "healthy", "version": "1.0.0"}' },
        { method: 'GET', path: '/expenses', desc: 'List expenses with pagination and filters', auth: false, response: '{"items": [...], "total": 50, "page": 1, "per_page": 20}' },
        { method: 'POST', path: '/expenses', desc: 'Create a new expense', auth: true, request: '{"date": "2026-01-15", "merchant": "Amazon", "amount": 49.99, "category": "Shopping", "payment_method": "Credit Card"}', response: '{"id": 1, "date": "2026-01-15", "merchant": "Amazon", ...}' },
        { method: 'GET', path: '/expenses/{expense_id}', desc: 'Get expense by ID', auth: false, response: '{"id": 1, "date": "2026-01-15", ...}' },
        { method: 'PUT', path: '/expenses/{expense_id}', desc: 'Update an expense', auth: true, request: '{"amount": 59.99}', response: '{"id": 1, "amount": 59.99, ...}' },
        { method: 'DELETE', path: '/expenses/{expense_id}', desc: 'Delete an expense', auth: true, response: '{"message": "Deleted successfully"}' },
        { method: 'GET', path: '/categories', desc: 'List all expense categories', auth: false, response: '{"categories": ["Food", "Travel", "Bills", ...]}' },
        { method: 'GET', path: '/category/{name}', desc: 'Get category details', auth: false, response: '{"name": "Food", "count": 25, "total": 1250.00}' },
        { method: 'GET', path: '/categorize?merchant=Netflix', desc: 'Auto-categorize a merchant', auth: false, response: '{"merchant": "Netflix", "category": "Subscriptions", "confidence": 0.95}' },
        { method: 'GET', path: '/summary?month=2026-01', desc: 'Monthly spending summary', auth: false, response: '{"month": "2026-01", "total": 3500.00, "by_category": {...}}' },
        { method: 'POST', path: '/budgets', desc: 'Create monthly budget', auth: true, request: '{"month": "2026-01", "category": "Food", "budget_amount": 500.00}', response: '{"id": 1, ...}' },
        { method: 'GET', path: '/budgets', desc: 'List all budgets', auth: false, response: '{"budgets": [...]}' },
        { method: 'POST', path: '/sync/subscriptions', desc: 'Sync subscriptions from App B', auth: true, response: '{"synced": 5, "new": 3, "duplicates_skipped": 2}' },
        { method: 'POST', path: '/sync/electricity', desc: 'Sync electricity expenses from App C', auth: true, response: '{"synced": 2, "new": 1, "duplicates_skipped": 1}' },
      ],
    },
    {
      name: 'Application B — Subscription Tracker',
      color: 'purple',
      endpoints: [
        { method: 'GET', path: '/health', desc: 'Health check', auth: false, response: '{"status": "healthy", "version": "1.0.0"}' },
        { method: 'GET', path: '/subscriptions', desc: 'List all subscriptions', auth: false, response: '{"items": [...], "total": 12}' },
        { method: 'POST', path: '/subscriptions', desc: 'Create subscription', auth: true, request: '{"service_name": "Netflix", "category": "Entertainment", "amount": 14.99, "currency": "USD", "billing_frequency": "monthly"}', response: '{"id": 1, ...}' },
        { method: 'GET', path: '/subscriptions/{id}', desc: 'Get subscription by ID', auth: false },
        { method: 'PUT', path: '/subscriptions/{id}', desc: 'Update subscription', auth: true },
        { method: 'DELETE', path: '/subscriptions/{id}', desc: 'Delete subscription', auth: true },
        { method: 'GET', path: '/renewals?days=30', desc: 'Upcoming renewals', auth: false, response: '{"renewals": [...], "within_days": 30}' },
        { method: 'GET', path: '/total', desc: 'Total monthly/annual cost', auth: false, response: '{"monthly_total": 150.00, "annual_total": 1800.00, "currency": "USD"}' },
        { method: 'GET', path: '/category/{name}', desc: 'Category breakdown', auth: false },
        { method: 'GET', path: '/tags', desc: 'List all tags', auth: false },
        { method: 'POST', path: '/sync/categories', desc: 'Fetch categories from App A', auth: true },
        { method: 'GET', path: '/eligible-expenses', desc: 'Expenses eligible for App A import', auth: false, response: '{"expenses": [...]}' },
      ],
    },
    {
      name: 'Application C — Electricity Manager',
      color: 'amber',
      endpoints: [
        { method: 'GET', path: '/health', desc: 'Health check', auth: false, response: '{"status": "healthy", "version": "1.0.0"}' },
        { method: 'GET', path: '/readings', desc: 'List meter readings', auth: false },
        { method: 'POST', path: '/readings', desc: 'Add meter reading', auth: true, request: '{"date": "2026-01-31", "reading_value": 5420.5, "unit": "kWh", "is_simulated": true}' },
        { method: 'GET', path: '/consumption', desc: 'Consumption analysis', auth: false, response: '{"total_kwh": 350.5, "by_appliance": {...}}' },
        { method: 'GET', path: '/bill/estimate?month=2026-01', desc: 'Estimated bill', auth: false, response: '{"month": "2026-01", "estimated_amount": 2450.00, "breakdown": {...}}' },
        { method: 'GET', path: '/bill/actual', desc: 'List actual bills', auth: false },
        { method: 'POST', path: '/bill/actual', desc: 'Record actual bill', auth: true, request: '{"period": "2026-01", "amount": 2600.00, "bill_date": "2026-02-05"}' },
        { method: 'GET', path: '/payments', desc: 'List payments', auth: false },
        { method: 'POST', path: '/payments', desc: 'Record payment', auth: true },
        { method: 'GET', path: '/appliances', desc: 'List appliances', auth: false },
        { method: 'POST', path: '/appliances', desc: 'Add appliance', auth: true, request: '{"name": "AC Bedroom", "type": "Air Conditioner", "rated_power_watts": 1500}' },
        { method: 'GET', path: '/tariffs', desc: 'Current tariff configuration', auth: false },
        { method: 'PUT', path: '/tariffs', desc: 'Update tariff slabs', auth: true },
        { method: 'POST', path: '/sync/categories', desc: 'Fetch categories from App A', auth: true },
        { method: 'GET', path: '/eligible-expenses', desc: 'Expenses eligible for App A', auth: false },
      ],
    },
  ];

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedPath(id);
    setTimeout(() => setCopiedPath(null), 2000);
  };

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'bg-green-500/10 text-green-400 border-green-500/20';
      case 'POST': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'PUT': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'DELETE': return 'bg-red-500/10 text-red-400 border-red-500/20';
      default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 p-8"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
            <BookOpen size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">API Documentation</h1>
            <p className="text-emerald-300 text-sm">Complete REST API reference for all three applications</p>
          </div>
        </div>
        <p className="text-gray-400 max-w-3xl">
          Each application exposes a documented REST API. Swagger UI is available at <code className="text-emerald-400">/docs</code> on 
          each backend. Authentication uses Bearer tokens for protected endpoints.
        </p>
      </motion.div>

      {/* Authentication Info */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="font-semibold text-white mb-2">Authentication</h3>
        <p className="text-sm text-gray-400 mb-3">
          Protected endpoints require a Bearer token in the Authorization header:
        </p>
        <div className="bg-gray-800 rounded-lg p-3 font-mono text-xs text-gray-300">
          Authorization: Bearer {'<API_SECRET>'}
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Tokens are configured via environment variables. Never commit secrets to version control.
        </p>
      </div>

      {/* API Endpoints by App */}
      {apis.map((api) => (
        <div key={api.name}>
          <h2 className="text-xl font-bold text-white mb-4">{api.name}</h2>
          <div className="space-y-2">
            {api.endpoints.map((ep) => {
              const key = `${api.name}-${ep.path}`;
              const isExpanded = expandedEndpoint === key;
              return (
                <div key={key} className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
                  <button
                    onClick={() => setExpandedEndpoint(isExpanded ? null : key)}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-800/50 transition-colors text-left"
                  >
                    <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold border ${getMethodColor(ep.method)}`}>
                      {ep.method}
                    </span>
                    <code className="text-sm text-white font-mono flex-1">{ep.path}</code>
                    {ep.auth && (
                      <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 text-xs border border-amber-500/20">
                        🔒 Auth
                      </span>
                    )}
                    {isExpanded ? <ChevronDown size={16} className="text-gray-500" /> : <ChevronRight size={16} className="text-gray-500" />}
                  </button>
                  
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      className="px-4 pb-4 border-t border-gray-800"
                    >
                      <p className="text-sm text-gray-400 mt-3 mb-3">{ep.desc}</p>
                      
                      {ep.request && (
                        <div className="mb-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-semibold text-gray-500 uppercase">Request Body</span>
                            <button 
                              onClick={() => copyToClipboard(ep.request!, key + '-req')}
                              className="text-xs text-gray-500 hover:text-white flex items-center gap-1"
                            >
                              {copiedPath === key + '-req' ? <Check size={12} /> : <Copy size={12} />}
                              {copiedPath === key + '-req' ? 'Copied' : 'Copy'}
                            </button>
                          </div>
                          <pre className="bg-gray-800 rounded-lg p-3 text-xs text-gray-300 font-mono overflow-x-auto">
                            {ep.request}
                          </pre>
                        </div>
                      )}
                      
                      {ep.response && (
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-semibold text-gray-500 uppercase">Response</span>
                            <button 
                              onClick={() => copyToClipboard(ep.response!, key + '-res')}
                              className="text-xs text-gray-500 hover:text-white flex items-center gap-1"
                            >
                              {copiedPath === key + '-res' ? <Check size={12} /> : <Copy size={12} />}
                              {copiedPath === key + '-res' ? 'Copied' : 'Copy'}
                            </button>
                          </div>
                          <pre className="bg-gray-800 rounded-lg p-3 text-xs text-gray-300 font-mono overflow-x-auto">
                            {ep.response}
                          </pre>
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {/* Error Responses */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Error Response Format</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <pre className="text-xs text-gray-300 font-mono overflow-x-auto">
{`{
  "detail": {
    "error": "validation_error",
    "message": "Amount must be positive",
    "field": "amount",
    "status_code": 422
  }
}

// Common status codes:
// 200 - Success
// 201 - Created
// 400 - Bad Request
// 401 - Unauthorized (missing/invalid token)
// 404 - Not Found
// 409 - Conflict (duplicate)
// 422 - Validation Error
// 500 - Internal Server Error
// 503 - Service Unavailable (peer API down)`}
          </pre>
        </div>
      </div>
    </div>
  );
}
