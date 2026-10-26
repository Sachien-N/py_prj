import { motion } from 'framer-motion';
import { 
  Zap, Database, Server, Lightbulb, Thermometer, 
  TrendingUp, AlertTriangle, FileBarChart, Gauge, Plug
} from 'lucide-react';

export default function ProjectC() {
  const features = [
    { title: 'Appliance Management', desc: 'Manage fans, lights, refrigerators, ACs with rated power', icon: <Plug size={16} /> },
    { title: 'Meter Readings', desc: 'Manual and clearly labelled simulated readings', icon: <Gauge size={16} /> },
    { title: 'Consumption Calc', desc: 'Calculate consumption in kWh per appliance', icon: <Thermometer size={16} /> },
    { title: 'Bill Estimation', desc: 'Configurable domestic tariff slabs with charges', icon: <FileBarChart size={16} /> },
    { title: 'Actual Bills', desc: 'Store actual electricity bills separately from estimates', icon: <FileBarChart size={16} /> },
    { title: 'Payment Records', desc: 'Track payments separately from bills and estimates', icon: <TrendingUp size={16} /> },
    { title: 'Deviation Detection', desc: 'Detect significant consumption deviations', icon: <AlertTriangle size={16} /> },
    { title: 'Export Reports', desc: 'Export readings and billing reports', icon: <Lightbulb size={16} /> },
  ];

  const apiEndpoints = [
    { method: 'GET', path: '/health', desc: 'Health check' },
    { method: 'GET', path: '/readings', desc: 'List meter readings' },
    { method: 'POST', path: '/readings', desc: 'Add meter reading' },
    { method: 'GET', path: '/consumption', desc: 'Consumption analysis' },
    { method: 'GET', path: '/bill/estimate', desc: 'Estimated bill' },
    { method: 'GET', path: '/bill/actual', desc: 'Actual bills' },
    { method: 'POST', path: '/bill/actual', desc: 'Record actual bill' },
    { method: 'GET', path: '/payments', desc: 'Payment records' },
    { method: 'POST', path: '/payments', desc: 'Record payment' },
    { method: 'GET', path: '/appliances', desc: 'List appliances' },
    { method: 'POST', path: '/appliances', desc: 'Add appliance' },
    { method: 'GET', path: '/tariffs', desc: 'Tariff configuration' },
    { method: 'PUT', path: '/tariffs', desc: 'Update tariff slabs' },
    { method: 'POST', path: '/sync/categories', desc: 'Fetch categories from App A' },
    { method: 'GET', path: '/eligible-expenses', desc: 'Expenses for App A' },
  ];

  const tariffSlabs = [
    { range: '0–100 kWh', rate: '₹3.50/unit', label: 'Low' },
    { range: '101–200 kWh', rate: '₹4.80/unit', label: 'Medium' },
    { range: '201–500 kWh', rate: '₹6.50/unit', label: 'High' },
    { range: '500+ kWh', rate: '₹8.00/unit', label: 'Very High' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-gradient-to-br from-amber-950/50 to-orange-950/50 border border-amber-500/20 p-8"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
            <Zap size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Smart Home Electricity & Bill Manager</h1>
            <p className="text-amber-300 text-sm">Project C · Hariharan S</p>
          </div>
        </div>
        <p className="text-gray-400 max-w-3xl">
          An independent electricity-consumption and billing website that manages home appliances, 
          tracks meter readings, calculates consumption and estimated bills using configurable tariff slabs, 
          detects anomalies, and shares eligible expense data with the Expense Manager.
        </p>
      </motion.div>

      {/* Features */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-amber-500/30 transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400 mb-3">
                {feature.icon}
              </div>
              <h3 className="font-semibold text-white text-sm mb-1">{feature.title}</h3>
              <p className="text-xs text-gray-500">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Tariff Slabs */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Configurable Tariff Slabs</h2>
        <p className="text-sm text-gray-400 mb-3">
          <span className="text-amber-400">⚠️ Note:</span> These are example configurable slabs. 
          Actual official tariffs should be verified and documented with source and effective date.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {tariffSlabs.map((slab) => (
            <div key={slab.range} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="text-xs text-gray-500 mb-1">{slab.label}</div>
              <div className="font-bold text-white text-lg">{slab.rate}</div>
              <div className="text-xs text-gray-400 mt-1">{slab.range}</div>
            </div>
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

      {/* Data Models */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Data Models</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
              <Database size={16} className="text-amber-400" /> Appliance
            </h3>
            <div className="space-y-1.5">
              {['id: Integer (PK)', 'name: String', 'type: String', 'rated_power_watts: Integer', 'avg_hours_per_day: Float', 'location: String', 'status: String'].map((f) => (
                <div key={f} className="font-mono text-xs text-gray-400 bg-gray-800/50 rounded px-3 py-1">{f}</div>
              ))}
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
              <Database size={16} className="text-orange-400" /> MeterReading
            </h3>
            <div className="space-y-1.5">
              {['id: Integer (PK)', 'date: Date', 'reading_value: Float', 'unit: String', 'is_simulated: Boolean', 'notes: Text', 'created_at: DateTime'].map((f) => (
                <div key={f} className="font-mono text-xs text-gray-400 bg-gray-800/50 rounded px-3 py-1">{f}</div>
              ))}
            </div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
              <Database size={16} className="text-yellow-400" /> Bill / Payment
            </h3>
            <div className="space-y-1.5">
              {['id: Integer (PK)', 'period: String', 'amount: Decimal(10,2)', 'type: String', 'status: String', 'paid_date: Date', 'source: String'].map((f) => (
                <div key={f} className="font-mono text-xs text-gray-400 bg-gray-800/50 rounded px-3 py-1">{f}</div>
              ))}
            </div>
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
uvicorn main:app --reload --port 8003

# Start Streamlit frontend (new terminal)
streamlit run app.py --server.port 8503`}
          </pre>
        </div>
      </div>
    </div>
  );
}
