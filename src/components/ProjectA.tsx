import { motion } from 'framer-motion';
import { 
  Wallet, CheckCircle2, ArrowRight, Database, Server, 
  Globe, FileText, Terminal, Code2, BarChart3,
  Upload, Download, Filter, Search, PieChart
} from 'lucide-react';

export default function ProjectA() {
  const features = [
    { title: 'Expense CRUD', desc: 'Add, edit, delete and view expenses with full details', icon: <FileText size={16} /> },
    { title: 'Budget Management', desc: 'Create monthly category budgets with utilization tracking', icon: <BarChart3 size={16} /> },
    { title: 'Category Rules', desc: 'Transparent, editable merchant categorization rules', icon: <Filter size={16} /> },
    { title: 'Search & Filter', desc: 'Search, filter and paginate through expense records', icon: <Search size={16} /> },
    { title: 'CSV Import/Export', desc: 'Import and export expenses via CSV files', icon: <Upload size={16} /> },
    { title: 'Plotly Charts', desc: 'Monthly spending, category breakdowns, and trend visualization', icon: <PieChart size={16} /> },
    { title: 'Subscription Sync', desc: 'Fetch subscription costs from Application B', icon: <Server size={16} /> },
    { title: 'Electricity Sync', desc: 'Fetch electricity expense records from Application C', icon: <Database size={16} /> },
  ];

  const apiEndpoints = [
    { method: 'GET', path: '/health', desc: 'Health check' },
    { method: 'GET', path: '/expenses', desc: 'List expenses (paginated)' },
    { method: 'POST', path: '/expenses', desc: 'Create expense' },
    { method: 'GET', path: '/expenses/{id}', desc: 'Get expense by ID' },
    { method: 'PUT', path: '/expenses/{id}', desc: 'Update expense' },
    { method: 'DELETE', path: '/expenses/{id}', desc: 'Delete expense' },
    { method: 'GET', path: '/categories', desc: 'List all categories' },
    { method: 'GET', path: '/category/{name}', desc: 'Get category details' },
    { method: 'GET', path: '/categorize', desc: 'Auto-categorize merchant' },
    { method: 'GET', path: '/summary', desc: 'Monthly summary' },
    { method: 'POST', path: '/budgets', desc: 'Create budget' },
    { method: 'GET', path: '/budgets', desc: 'List budgets' },
    { method: 'POST', path: '/sync/subscriptions', desc: 'Sync from App B' },
    { method: 'POST', path: '/sync/electricity', desc: 'Sync from App C' },
  ];

  const categories = ['Food', 'Travel', 'Bills', 'Entertainment', 'Shopping', 'Subscriptions', 'Other'];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-gradient-to-br from-blue-950/50 to-cyan-950/50 border border-blue-500/20 p-8"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
            <Wallet size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Smart Expense & Budget Manager</h1>
            <p className="text-blue-300 text-sm">Project A · Sachien N · 23MID0255</p>
          </div>
        </div>
        <p className="text-gray-400 max-w-3xl">
          A professional personal-finance dashboard that tracks expenses, manages budgets by category, 
          integrates with subscription and electricity data from peer applications, and provides 
          comprehensive spending analytics with Plotly visualizations.
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
              className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-blue-500/30 transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400 mb-3">
                {feature.icon}
              </div>
              <h3 className="font-semibold text-white text-sm mb-1">{feature.title}</h3>
              <p className="text-xs text-gray-500">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Categories */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Supported Categories</h2>
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <span key={cat} className="px-4 py-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm font-medium">
              {cat}
            </span>
          ))}
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
              <Database size={16} className="text-blue-400" /> Expense Model
            </h3>
            <div className="space-y-2 text-sm">
              {['id: Integer (PK)', 'date: Date', 'merchant: String', 'amount: Decimal(10,2)', 'category: String (FK)', 'payment_method: String', 'description: Text', 'source_app: String', 'external_id: String', 'synced_at: DateTime', 'created_at: DateTime'].map((field) => (
                <div key={field} className="font-mono text-xs text-gray-400 bg-gray-800/50 rounded px-3 py-1.5">{field}</div>
              ))}
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
              <Database size={16} className="text-cyan-400" /> Budget Model
            </h3>
            <div className="space-y-2 text-sm">
              {['id: Integer (PK)', 'month: String (YYYY-MM)', 'category: String', 'budget_amount: Decimal(10,2)', 'spent_amount: Decimal(10,2)', 'remaining: Decimal(10,2)', 'utilization_pct: Float', 'created_at: DateTime', 'updated_at: DateTime'].map((field) => (
                <div key={field} className="font-mono text-xs text-gray-400 bg-gray-800/50 rounded px-3 py-1.5">{field}</div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Setup Instructions */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Quick Setup (Windows PowerShell)</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <Terminal size={16} className="text-blue-400" />
            <span className="text-sm font-medium text-white">PowerShell Commands</span>
          </div>
          <pre className="text-xs text-gray-300 font-mono overflow-x-auto space-y-1">
{`# Create virtual environment
python -m venv venv
.\\venv\\Scripts\\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set environment variables
$env:DATABASE_URL="postgresql://user:pass@host/db"
$env:API_SECRET="your-secret-key"
$env:APP_B_URL="https://shravan-api.onrender.com"
$env:APP_C_URL="https://hariharan-api.onrender.com"

# Initialize database
python -c "from database import init_db; init_db()"

# Start FastAPI backend
uvicorn main:app --reload --port 8001

# Start Streamlit frontend (new terminal)
streamlit run app.py --server.port 8501`}
          </pre>
        </div>
      </div>
    </div>
  );
}
