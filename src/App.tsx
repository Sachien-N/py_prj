import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, Wallet, CreditCard, Zap, Network, 
  Server, BookOpen, Rocket, Users, ChevronRight, 
  CheckCircle2, AlertCircle, Clock, ArrowRight,
  Menu, X, Github, ExternalLink, Database, Shield,
  Code2, FileText, Terminal, Cloud
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import ProjectA from './components/ProjectA';
import ProjectB from './components/ProjectB';
import ProjectC from './components/ProjectC';
import Architecture from './components/Architecture';
import ApiDocs from './components/ApiDocs';
import Deployment from './components/Deployment';
import Integration from './components/Integration';

type Page = 'dashboard' | 'projectA' | 'projectB' | 'projectC' | 'architecture' | 'api' | 'deployment' | 'integration';

const navItems: { id: Page; label: string; icon: React.ReactNode; group: string }[] = [
  { id: 'dashboard', label: 'Overview', icon: <LayoutDashboard size={18} />, group: 'main' },
  { id: 'projectA', label: 'Expense Manager', icon: <Wallet size={18} />, group: 'projects' },
  { id: 'projectB', label: 'Subscription Tracker', icon: <CreditCard size={18} />, group: 'projects' },
  { id: 'projectC', label: 'Electricity Manager', icon: <Zap size={18} />, group: 'projects' },
  { id: 'architecture', label: 'Architecture', icon: <Network size={18} />, group: 'technical' },
  { id: 'api', label: 'API Documentation', icon: <BookOpen size={18} />, group: 'technical' },
  { id: 'integration', label: 'Integration', icon: <Server size={18} />, group: 'technical' },
  { id: 'deployment', label: 'Deployment Guide', icon: <Rocket size={18} />, group: 'technical' },
];

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <Dashboard onNavigate={setCurrentPage} />;
      case 'projectA': return <ProjectA />;
      case 'projectB': return <ProjectB />;
      case 'projectC': return <ProjectC />;
      case 'architecture': return <Architecture />;
      case 'api': return <ApiDocs />;
      case 'deployment': return <Deployment />;
      case 'integration': return <Integration />;
      default: return <Dashboard onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex">
      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-40 lg:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        ${sidebarOpen ? 'w-64' : 'w-20'} 
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        bg-gray-900 border-r border-gray-800 
        transition-all duration-300 flex flex-col
      `}>
        {/* Logo */}
        <div className="p-4 border-b border-gray-800 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Code2 size={20} className="text-white" />
          </div>
          {sidebarOpen && (
            <div className="overflow-hidden">
              <h1 className="font-bold text-sm text-white">CSI3007</h1>
              <p className="text-xs text-gray-400">Advanced Python</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {['main', 'projects', 'technical'].map((group) => (
            <div key={group} className="mb-4">
              {sidebarOpen && (
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-2">
                  {group === 'main' ? 'Main' : group === 'projects' ? 'Projects' : 'Technical'}
                </p>
              )}
              {navItems.filter(item => item.group === group).map((item) => (
                <button
                  key={item.id}
                  onClick={() => { setCurrentPage(item.id); setMobileMenuOpen(false); }}
                  className={`
                    w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm
                    transition-all duration-200
                    ${currentPage === item.id 
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' 
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'}
                  `}
                >
                  {item.icon}
                  {sidebarOpen && <span>{item.label}</span>}
                </button>
              ))}
            </div>
          ))}
        </nav>

        {/* Sidebar toggle */}
        <div className="p-3 border-t border-gray-800 hidden lg:block">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors text-sm"
          >
            {sidebarOpen ? <ChevronRight size={16} className="rotate-180" /> : <ChevronRight size={16} />}
            {sidebarOpen && <span>Collapse</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-gray-950/80 backdrop-blur-xl border-b border-gray-800 px-4 lg:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-800 text-gray-400"
            >
              <Menu size={20} />
            </button>
            <div>
              <h2 className="font-semibold text-white">
                {navItems.find(i => i.id === currentPage)?.label || 'Dashboard'}
              </h2>
              <p className="text-xs text-gray-500">Smart Management System</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-xs text-green-400">All Systems Operational</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 p-4 lg:p-6 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentPage}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {renderPage()}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
