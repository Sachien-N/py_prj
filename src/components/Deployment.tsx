import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Rocket, CheckCircle2, Circle, AlertCircle, 
  ExternalLink, Terminal, Cloud, Database,
  Github, Globe, Shield, RefreshCw
} from 'lucide-react';

export default function Deployment() {
  const [activeTab, setActiveTab] = useState<'sachien' | 'shravan' | 'hariharan'>('sachien');

  const steps = [
    { num: 1, title: 'Create GitHub Account', desc: 'Sign up at github.com or sign in to existing account.', icon: <Github size={16} /> },
    { num: 2, title: 'Create Repository', desc: 'Create a new public repository for your project (e.g., sachien-expense-manager).', icon: <Github size={16} /> },
    { num: 3, title: 'Push Project Files', desc: 'Initialize git, add files, commit and push to your repository.', icon: <Terminal size={16} /> },
    { num: 4, title: 'Provision Neon Database', desc: 'Sign up at neon.tech, create a new project and database. Copy the connection string.', icon: <Database size={16} /> },
    { num: 5, title: 'Configure Backend Secrets', desc: 'Set DATABASE_URL, API_SECRET, and peer app URLs in Render environment variables.', icon: <Shield size={16} /> },
    { num: 6, title: 'Deploy FastAPI Backend', desc: 'Connect your GitHub repo to Render. Set build command: pip install -r requirements.txt. Set start command: uvicorn main:app --host 0.0.0.0 --port $PORT.', icon: <Cloud size={16} /> },
    { num: 7, title: 'Run Database Migrations', desc: 'Use Render shell or add migration to startup script: python -c "from database import init_db; init_db()"', icon: <Database size={16} /> },
    { num: 8, title: 'Verify Backend', desc: 'Visit https://your-api.onrender.com/health and https://your-api.onrender.com/docs', icon: <Globe size={16} /> },
    { num: 9, title: 'Deploy Streamlit Frontend', desc: 'Go to share.streamlit.io, connect your repo, select app.py, configure environment variables.', icon: <Cloud size={16} /> },
    { num: 10, title: 'Configure Frontend API URL', desc: 'Set API_BASE_URL to your Render backend URL in Streamlit secrets or env vars.', icon: <Shield size={16} /> },
    { num: 11, title: 'Configure CORS', desc: 'Add your Streamlit Cloud URL to backend CORS origins in Render env vars.', icon: <Shield size={16} /> },
    { num: 12, title: 'Verify Frontend', desc: 'Visit your Streamlit Cloud URL and verify the app loads and connects to the API.', icon: <Globe size={16} /> },
    { num: 13, title: 'Exchange URLs with Team', desc: 'Share your public API URL and Bearer token with teammates through a secure channel.', icon: <RefreshCw size={16} /> },
    { num: 14, title: 'Run Integration Tests', desc: 'Execute integration tests against all three public APIs to verify cross-app communication.', icon: <CheckCircle2 size={16} /> },
    { num: 15, title: 'Verify Persistence', desc: 'Restart/redeploy and confirm data persists. Verify the system works with computers off.', icon: <Database size={16} /> },
  ];



  const setupCommands = {
    sachien: `# Windows PowerShell
# 1. Install Python from python.org (3.10+)
python --version

# 2. Clone repository
git clone https://github.com/yourusername/sachien-expense-manager.git
cd sachien-expense-manager

# 3. Create virtual environment
python -m venv venv
.\\venv\\Scripts\\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file (never commit this)
# DATABASE_URL=postgresql://...
# API_SECRET=your-secret
# APP_B_URL=https://shravan-api.onrender.com
# APP_C_URL=https://hariharan-api.onrender.com

# 6. Initialize database
python -c "from database import init_db; init_db()"

# 7. Start backend (Terminal 1)
uvicorn main:app --reload --port 8001

# 8. Start frontend (Terminal 2)
streamlit run app.py --server.port 8501

# 9. Run tests
pytest tests/ -v`,

    shravan: `# macOS Terminal
# 1. Install Python via Homebrew
brew install python@3.11
python3 --version

# 2. Clone repository
git clone https://github.com/yourusername/shravan-subscription-tracker.git
cd shravan-subscription-tracker

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file (never commit this)
# DATABASE_URL=postgresql://...
# API_SECRET=your-secret
# APP_A_URL=https://sachien-api.onrender.com

# 6. Initialize database
python -c "from database import init_db; init_db()"

# 7. Start backend (Terminal 1)
uvicorn main:app --reload --port 8002

# 8. Start frontend (Terminal 2)
streamlit run app.py --server.port 8502

# 9. Run tests
pytest tests/ -v`,

    hariharan: `# macOS Terminal
# 1. Install Python via Homebrew
brew install python@3.11
python3 --version

# 2. Clone repository
git clone https://github.com/yourusername/hariharan-electricity-manager.git
cd hariharan-electricity-manager

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file (never commit this)
# DATABASE_URL=postgresql://...
# API_SECRET=your-secret
# APP_A_URL=https://sachien-api.onrender.com

# 6. Initialize database
python -c "from database import init_db; init_db()"

# 7. Start backend (Terminal 1)
uvicorn main:app --reload --port 8003

# 8. Start frontend (Terminal 2)
streamlit run app.py --server.port 8503

# 9. Run tests
pytest tests/ -v`,
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
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-rose-500 to-pink-500 flex items-center justify-center">
            <Rocket size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Deployment Guide</h1>
            <p className="text-rose-300 text-sm">Step-by-step instructions for free cloud deployment</p>
          </div>
        </div>
        <p className="text-gray-400 max-w-3xl">
          Deploy all three applications to free-tier cloud hosting. Each app works independently 
          and continues running when developers' computers are offline. Budget: ₹0/month.
        </p>
      </motion.div>

      {/* Free Tier Constraints */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <AlertCircle size={16} className="text-amber-400" />
          Free Tier Constraints & Limitations
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { provider: 'Render (Free)', limits: ['Sleeps after 15 min idle', 'Cold start ~30-60s', '750 hours/month', '512 MB RAM'] },
            { provider: 'Streamlit Cloud (Free)', limits: ['Public repos only', 'Sleeps after inactivity', 'Limited compute', 'No custom domain'] },
            { provider: 'Neon PostgreSQL (Free)', limits: ['0.5 GiB storage', '1 project', 'Compute hours limited', 'Branches share storage'] },
          ].map((item) => (
            <div key={item.provider} className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-sm font-medium text-white mb-2">{item.provider}</p>
              <ul className="space-y-1">
                {item.limits.map((l) => (
                  <li key={l} className="text-xs text-gray-400 flex items-center gap-1.5">
                    <div className="w-1 h-1 rounded-full bg-gray-600" />
                    {l}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Deployment Steps */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Deployment Checklist</h2>
        <div className="space-y-2">
          {steps.map((step) => (
            <div key={step.num} className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex items-start gap-4 hover:border-gray-700 transition-colors">
              <div className="w-8 h-8 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold text-blue-400">{step.num}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-gray-500">{step.icon}</span>
                  <h3 className="font-semibold text-white text-sm">{step.title}</h3>
                </div>
                <p className="text-xs text-gray-400">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Local Setup by Developer */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Local Development Setup</h2>
        
        {/* Tabs */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setActiveTab('sachien')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'sachien'
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            Sachien (Windows)
          </button>
          <button
            onClick={() => setActiveTab('shravan')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'shravan'
                ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            Shravan (macOS)
          </button>
          <button
            onClick={() => setActiveTab('hariharan')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'hariharan'
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            Hariharan (macOS)
          </button>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <Terminal size={16} className="text-green-400" />
            <span className="text-sm font-medium text-white">
              {activeTab === 'sachien' ? 'Windows PowerShell' : 'macOS Terminal'}
            </span>
          </div>
          <pre className="text-xs text-gray-300 font-mono overflow-x-auto whitespace-pre-wrap">
            {setupCommands[activeTab]}
          </pre>
        </div>
      </div>

      {/* Environment Variables */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Required Environment Variables</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-800/30">
                <th className="text-left px-4 py-3 text-gray-400 font-medium">Variable</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium">Description</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium">Example</th>
              </tr>
            </thead>
            <tbody>
              {[
                { var: 'DATABASE_URL', desc: 'PostgreSQL connection string', example: 'postgresql://user:pass@host/db' },
                { var: 'API_SECRET', desc: 'Bearer token for auth', example: 'your-random-secret-key' },
                { var: 'APP_A_URL', desc: 'Expense Manager API URL', example: 'https://sachien-api.onrender.com' },
                { var: 'APP_B_URL', desc: 'Subscription Tracker API URL', example: 'https://shravan-api.onrender.com' },
                { var: 'APP_C_URL', desc: 'Electricity Manager API URL', example: 'https://hariharan-api.onrender.com' },
                { var: 'CORS_ORIGINS', desc: 'Allowed frontend origins', example: 'https://sachien-expense.streamlit.app' },
                { var: 'ENVIRONMENT', desc: 'Environment name', example: 'production' },
              ].map((env) => (
                <tr key={env.var} className="border-t border-gray-800/50">
                  <td className="px-4 py-2.5 font-mono text-xs text-amber-300">{env.var}</td>
                  <td className="px-4 py-2.5 text-gray-400 text-xs">{env.desc}</td>
                  <td className="px-4 py-2.5 font-mono text-xs text-gray-500">{env.example}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Troubleshooting */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Common Issues & Fixes</h2>
        <div className="space-y-3">
          {[
            { issue: 'Render cold start timeout', fix: 'Add health check with retry. Increase request timeout to 30s. First request after sleep takes 30-60s.' },
            { issue: 'CORS errors in browser', fix: 'Verify CORS_ORIGINS includes the exact Streamlit Cloud URL (with https://). Check for trailing slashes.' },
            { issue: 'Database connection refused', fix: 'Verify DATABASE_URL is correct. Check Neon database is not paused. Ensure IP allowlist includes Render.' },
            { issue: 'Streamlit not connecting to API', fix: 'Verify API_BASE_URL secret is set in Streamlit Cloud. Check the backend /health endpoint is accessible.' },
            { issue: 'Module not found errors', fix: 'Ensure requirements.txt includes all dependencies. Check Render build logs for pip install errors.' },
            { issue: 'PowerShell execution policy', fix: 'Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser' },
          ].map((item) => (
            <div key={item.issue} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <p className="text-sm font-medium text-red-400 mb-1">⚠️ {item.issue}</p>
              <p className="text-xs text-gray-400">💡 {item.fix}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
