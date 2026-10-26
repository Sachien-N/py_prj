import { motion } from 'framer-motion';
import { 
  Network, Globe, Database, Server, Monitor, 
  ArrowRight, ArrowDown, Shield, Wifi, Cloud
} from 'lucide-react';

export default function Architecture() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 p-8"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center">
            <Network size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">System Architecture</h1>
            <p className="text-indigo-300 text-sm">Three independent applications with REST API integration</p>
          </div>
        </div>
        <p className="text-gray-400 max-w-3xl">
          Each application has its own frontend, backend API, and database. They communicate exclusively 
          through public HTTPS REST API endpoints. The system works even when individual developers' 
          computers are offline.
        </p>
      </motion.div>

      {/* Architecture Diagram */}
      <div>
        <h2 className="text-xl font-bold text-white mb-6">High-Level Architecture</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 lg:p-8">
          {/* Top Layer - Frontends */}
          <div className="mb-6">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Frontend Layer (Streamlit Community Cloud)</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Monitor size={16} className="text-blue-400" />
                  <span className="text-sm font-medium text-white">Expense Manager UI</span>
                </div>
                <p className="text-xs text-gray-500">Sachien · Port 8501</p>
              </div>
              <div className="bg-purple-500/5 border border-purple-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Monitor size={16} className="text-purple-400" />
                  <span className="text-sm font-medium text-white">Subscription Tracker UI</span>
                </div>
                <p className="text-xs text-gray-500">Shravan · Port 8502</p>
              </div>
              <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Monitor size={16} className="text-amber-400" />
                  <span className="text-sm font-medium text-white">Electricity Manager UI</span>
                </div>
                <p className="text-xs text-gray-500">Hariharan · Port 8503</p>
              </div>
            </div>
          </div>

          {/* Arrows */}
          <div className="flex justify-center my-4">
            <div className="flex flex-col items-center text-gray-600">
              <ArrowDown size={20} />
              <span className="text-xs mt-1">HTTPS REST API</span>
            </div>
          </div>

          {/* Middle Layer - APIs */}
          <div className="mb-6">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Backend Layer (Render / Railway)</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Server size={16} className="text-blue-400" />
                  <span className="text-sm font-medium text-white">FastAPI Backend A</span>
                </div>
                <p className="text-xs text-gray-500">Sachien · Port 8001</p>
              </div>
              <div className="bg-purple-500/5 border border-purple-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Server size={16} className="text-purple-400" />
                  <span className="text-sm font-medium text-white">FastAPI Backend B</span>
                </div>
                <p className="text-xs text-gray-500">Shravan · Port 8002</p>
              </div>
              <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Server size={16} className="text-amber-400" />
                  <span className="text-sm font-medium text-white">FastAPI Backend C</span>
                </div>
                <p className="text-xs text-gray-500">Hariharan · Port 8003</p>
              </div>
            </div>
          </div>

          {/* Cross-connections */}
          <div className="my-6 p-4 bg-indigo-500/5 border border-indigo-500/20 rounded-xl">
            <p className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-3">Cross-Application API Calls</p>
            <div className="space-y-2">
              {[
                { from: 'App A', to: 'App B', desc: 'GET /eligible-expenses → Fetch subscription costs' },
                { from: 'App A', to: 'App C', desc: 'GET /eligible-expenses → Fetch electricity expenses' },
                { from: 'App B', to: 'App A', desc: 'GET /categories → Fetch expense categories' },
                { from: 'App C', to: 'App A', desc: 'GET /categories → Fetch expense categories' },
              ].map((flow, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 text-xs font-medium">{flow.from}</span>
                  <ArrowRight size={14} className="text-gray-600" />
                  <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 text-xs font-medium">{flow.to}</span>
                  <span className="text-gray-400 text-xs hidden sm:inline">{flow.desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Arrows */}
          <div className="flex justify-center my-4">
            <div className="flex flex-col items-center text-gray-600">
              <ArrowDown size={20} />
              <span className="text-xs mt-1">SQLAlchemy ORM</span>
            </div>
          </div>

          {/* Bottom Layer - Databases */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Database Layer (Neon PostgreSQL)</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Database size={16} className="text-blue-400" />
                  <span className="text-sm font-medium text-white">Database A</span>
                </div>
                <p className="text-xs text-gray-500">Sachien · PostgreSQL</p>
              </div>
              <div className="bg-purple-500/5 border border-purple-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Database size={16} className="text-purple-400" />
                  <span className="text-sm font-medium text-white">Database B</span>
                </div>
                <p className="text-xs text-gray-500">Shravan · PostgreSQL</p>
              </div>
              <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Database size={16} className="text-amber-400" />
                  <span className="text-sm font-medium text-white">Database C</span>
                </div>
                <p className="text-xs text-gray-500">Hariharan · PostgreSQL</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Hosting Architecture */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Free Hosting Providers</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Cloud size={18} className="text-red-400" />
              <h3 className="font-semibold text-white">Streamlit Cloud</h3>
            </div>
            <p className="text-xs text-gray-400 mb-2">Frontend hosting for all three Streamlit apps</p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>• Free community cloud</li>
              <li>• Connect GitHub repo</li>
              <li>• Auto-deploy on push</li>
              <li>• Public HTTPS URL</li>
              <li>• Sleeps after inactivity</li>
            </ul>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Server size={18} className="text-cyan-400" />
              <h3 className="font-semibold text-white">Render</h3>
            </div>
            <p className="text-xs text-gray-400 mb-2">Backend API hosting for all three FastAPI apps</p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>• Free web service tier</li>
              <li>• Connect GitHub repo</li>
              <li>• Custom build/start commands</li>
              <li>• Public HTTPS URL</li>
              <li>• Sleeps after 15 min idle</li>
            </ul>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Database size={18} className="text-green-400" />
              <h3 className="font-semibold text-white">Neon PostgreSQL</h3>
            </div>
            <p className="text-xs text-gray-400 mb-2">Persistent database for all three applications</p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>• Free tier: 0.5 GiB storage</li>
              <li>• Serverless PostgreSQL</li>
              <li>• Connection string provided</li>
              <li>• Branching support</li>
              <li>• Persistent across restarts</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Security */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Security Architecture</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { title: 'Authentication', desc: 'Bearer token auth for service-to-service API calls. Tokens stored in environment variables only.' },
            { title: 'CORS Configuration', desc: 'Production CORS configured for actual frontend origins only. Never wildcard in production.' },
            { title: 'Secret Management', desc: 'All secrets in environment variables. Never committed to Git. Rotated through hosting platform UI.' },
            { title: 'Input Validation', desc: 'Pydantic schemas validate all inputs. SQL injection prevented via SQLAlchemy ORM parameterized queries.' },
          ].map((item) => (
            <div key={item.title} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <Shield size={16} className="text-green-400" />
                <h3 className="font-semibold text-white text-sm">{item.title}</h3>
              </div>
              <p className="text-xs text-gray-400">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Key Principles */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Design Principles</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              'Each app independently deployable',
              'No shared databases between apps',
              'HTTPS-only in production',
              'No hardcoded localhost in production',
              'Graceful degradation when peer APIs are down',
              'Idempotent synchronization (no duplicates)',
              'Estimated vs actual clearly distinguished',
              'Manual records never auto-overwritten',
              'Fixed-precision Decimal for money',
              'ISO currency codes throughout',
            ].map((principle) => (
              <div key={principle} className="flex items-start gap-2">
                <div className="w-5 h-5 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <div className="w-2 h-2 rounded-full bg-green-400" />
                </div>
                <span className="text-sm text-gray-300">{principle}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
