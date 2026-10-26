import { motion } from 'framer-motion';
import { 
  CreditCard, Database, Server, Bell, Calendar, 
  Tag, RefreshCw, TrendingDown, Clock, AlertTriangle
} from 'lucide-react';

export default function ProjectB() {
  const features = [
    { title: 'Subscription CRUD', desc: 'Add, edit, delete and list all subscriptions', icon: <CreditCard size={16} /> },
    { title: 'Renewal Tracking', desc: 'Upcoming renewals within 7, 15 and 30 days', icon: <Bell size={16} /> },
    { title: 'Cost Analysis', desc: 'Monthly-equivalent and annual cost calculations', icon: <TrendingDown size={16} /> },
    { title: 'Status Management', desc: 'Active, Paused, Cancelled and Expired states', icon: <Tag size={16} /> },
    { title: 'Category Mapping', desc: 'Map subscription categories to App A categories', icon: <RefreshCw size={16} /> },
    { title: 'Search & Filter', desc: 'Search by name, filter by status, category, tags', icon: <Calendar size={16} /> },
    { title: 'API Exposure', desc: 'Share eligible subscription records with App A', icon: <Server size={16} /> },
    { title: 'Integration Settings', desc: 'Configure API connections and sync preferences', icon: <Clock size={16} /> },
  ];

  const apiEndpoints = [
    { method: 'GET', path: '/health', desc: 'Health check' },
    { method: 'GET', path: '/subscriptions', desc: 'List subscriptions' },
    { method: 'POST', path: '/subscriptions', desc: 'Create subscription' },
    { method: 'GET', path: '/subscriptions/{id}', desc: 'Get subscription' },
    { method: 'PUT', path: '/subscriptions/{id}', desc: 'Update subscription' },
    { method: 'DELETE', path: '/subscriptions/{id}', desc: 'Delete subscription' },
    { method: 'GET', path: '/renewals', desc: 'Upcoming renewals' },
    { method: 'GET', path: '/total', desc: 'Total subscription cost' },
    { method: 'GET', path: '/category/{name}', desc: 'Category breakdown' },
    { method: 'GET', path: '/tags', desc: 'List all tags' },
    { method: 'POST', path: '/sync/categories', desc: 'Fetch categories from App A' },
    { method: 'GET', path: '/eligible-expenses', desc: 'Expenses for App A' },
  ];

  const billingFrequencies = ['Monthly', 'Quarterly', 'Half-Yearly', 'Annual'];
  const statuses = ['Active', 'Paused', 'Cancelled', 'Expired'];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-gradient-to-br from-purple-950/50 to-pink-950/50 border border-purple-500/20 p-8"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <CreditCard size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Subscription Renewal & Cost Tracker</h1>
            <p className="text-purple-300 text-sm">Project B · Shravan N A · 23MID0445</p>
          </div>
        </div>
        <p className="text-gray-400 max-w-3xl">
          An independent subscription management website that tracks all recurring services, 
          calculates costs across billing frequencies, alerts for upcoming renewals, and shares 
          eligible expense data with the Expense Manager application.
        </p>
      </motion.div>

      {/* Features Grid */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-purple-500/30 transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400 mb-3">
                {feature.icon}
              </div>
              <h3 className="font-semibold text-white text-sm mb-1">{feature.title}</h3>
              <p className="text-xs text-gray-500">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Billing & Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <h2 className="text-xl font-bold text-white mb-4">Billing Frequencies</h2>
          <div className="flex flex-wrap gap-2">
            {billingFrequencies.map((freq) => (
              <span key={freq} className="px-4 py-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm font-medium">
                {freq}
              </span>
            ))}
          </div>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white mb-4">Subscription Statuses</h2>
          <div className="flex flex-wrap gap-2">
            {statuses.map((status) => {
              const colors: Record<string, string> = {
                Active: 'bg-green-500/10 border-green-500/20 text-green-300',
                Paused: 'bg-amber-500/10 border-amber-500/20 text-amber-300',
                Cancelled: 'bg-red-500/10 border-red-500/20 text-red-300',
                Expired: 'bg-gray-500/10 border-gray-500/20 text-gray-300',
              };
              return (
                <span key={status} className={`px-4 py-2 rounded-lg border text-sm font-medium ${colors[status]}`}>
                  {status}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* API Endpoints */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">API Endpoints</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 bg-gray-800/30">
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Method</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Endpoint</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Description</th>
                </tr>
              </thead>
              <tbody>
                {apiEndpoints.map((ep, i) => (
                  <tr key={i} className="border-t border-gray-800/50 hover:bg-gray-800/20">
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                        ep.method === 'GET' ? 'bg-green-500/10 text-green-400' :
                        ep.method === 'POST' ? 'bg-blue-500/10 text-blue-400' :
                        ep.method === 'PUT' ? 'bg-amber-500/10 text-amber-400' :
                        'bg-red-500/10 text-red-400'
                      }`}>
                        {ep.method}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs text-white">{ep.path}</td>
                    <td className="px-4 py-2.5 text-gray-400">{ep.desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Data Model */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Data Model</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
            <Database size={16} className="text-purple-400" /> Subscription Model
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {[
              'id: Integer (PK)', 'service_name: String', 'category: String',
              'plan: String', 'amount: Decimal(10,2)', 'currency: String(3)',
              'billing_frequency: String', 'start_date: Date', 'renewal_date: Date',
              'status: String', 'tags: JSON', 'notes: Text',
              'created_at: DateTime', 'updated_at: DateTime'
            ].map((field) => (
              <div key={field} className="font-mono text-xs text-gray-400 bg-gray-800/50 rounded px-3 py-1.5">{field}</div>
            ))}
          </div>
        </div>
      </div>

      {/* Setup */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Quick Setup (macOS Terminal)</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <pre className="text-xs text-gray-300 font-mono overflow-x-auto">
{`# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@host/db"
export API_SECRET="your-secret-key"
export APP_A_URL="https://sachien-api.onrender.com"

# Initialize database
python -c "from database import init_db; init_db()"

# Start FastAPI backend
uvicorn main:app --reload --port 8002

# Start Streamlit frontend (new terminal)
streamlit run app.py --server.port 8502`}
          </pre>
        </div>
      </div>
    </div>
  );
}
