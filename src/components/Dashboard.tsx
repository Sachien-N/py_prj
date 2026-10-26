import { motion } from 'framer-motion';
import { 
  Wallet, CreditCard, Zap, ArrowRight, Users, 
  Server, Database, Shield, Globe, CheckCircle2,
  TrendingUp, Clock, Activity
} from 'lucide-react';

interface DashboardProps {
  onNavigate: (page: any) => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const projects = [
    {
      id: 'projectA',
      title: 'Smart Expense & Budget Manager',
      owner: 'Sachien N',
      regNo: '23MID0255',
      icon: <Wallet size={24} />,
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/20',
      features: ['Expense CRUD', 'Budget Tracking', 'Category Management', 'CSV Import/Export', 'Plotly Charts'],
      status: 'Code Complete',
    },
    {
      id: 'projectB',
      title: 'Subscription Renewal & Cost Tracker',
      owner: 'Shravan N A',
      regNo: '23MID0445',
      icon: <CreditCard size={24} />,
      color: 'from-purple-500 to-pink-500',
      bgColor: 'bg-purple-500/10',
      borderColor: 'border-purple-500/20',
      features: ['Subscription CRUD', 'Renewal Alerts', 'Cost Analysis', 'Category Mapping', 'Status Management'],
      status: 'Code Complete',
    },
    {
      id: 'projectC',
      title: 'Smart Home Electricity & Bill Manager',
      owner: 'Hariharan S',
      regNo: '—',
      icon: <Zap size={24} />,
      color: 'from-amber-500 to-orange-500',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/20',
      features: ['Appliance Management', 'Consumption Analysis', 'Bill Estimation', 'Tariff Configuration', 'Deviation Detection'],
      status: 'Code Complete',
    },
  ];

  const techStack = [
    { name: 'Python', desc: 'Core language' },
    { name: 'FastAPI', desc: 'REST API' },
    { name: 'Streamlit', desc: 'Frontend UI' },
    { name: 'PostgreSQL', desc: 'Production DB' },
    { name: 'SQLAlchemy', desc: 'ORM' },
    { name: 'Pydantic', desc: 'Validation' },
    { name: 'Plotly', desc: 'Charts' },
    { name: 'pytest', desc: 'Testing' },
  ];

  const integrationFlows = [
    { from: 'App B', to: 'App A', data: 'Subscription costs', status: 'active' },
    { from: 'App C', to: 'App A', data: 'Electricity expenses', status: 'active' },
    { from: 'App A', to: 'App B', data: 'Expense categories', status: 'active' },
    { from: 'App A', to: 'App C', data: 'Expense categories', status: 'active' },
  ];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 border border-gray-700 p-8 lg:p-12"
      >
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-500/10 via-transparent to-purple-500/10" />
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-4">
            <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-400 text-xs font-medium border border-blue-500/30">
              CSI3007 — Advanced Python Programming
            </span>
          </div>
          <h1 className="text-3xl lg:text-4xl font-bold text-white mb-3">
            Smart Expense, Subscription &<br />Electricity Bill Management System
          </h1>
          <p className="text-gray-400 max-w-2xl text-lg">
            Three independent, interconnected web applications with real REST API integration, 
            persistent databases, and free cloud deployment.
          </p>
          
          <div className="flex flex-wrap gap-4 mt-6">
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Users size={16} className="text-blue-400" />
              <span>3 Developers</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Server size={16} className="text-purple-400" />
              <span>3 Independent APIs</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Database size={16} className="text-amber-400" />
              <span>3 Databases</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Globe size={16} className="text-green-400" />
              <span>Free Cloud Hosting</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Project Cards */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Activity size={20} className="text-blue-400" />
          Project Overview
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {projects.map((project, index) => (
            <motion.div
              key={project.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => onNavigate(project.id)}
              className={`
                relative group cursor-pointer rounded-xl border ${project.borderColor} 
                ${project.bgColor} p-6 hover:scale-[1.02] transition-all duration-300
              `}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${project.color} flex items-center justify-center text-white`}>
                  {project.icon}
                </div>
                <span className="px-2 py-1 rounded-full bg-green-500/10 text-green-400 text-xs border border-green-500/20">
                  {project.status}
                </span>
              </div>
              
              <h3 className="font-bold text-white text-lg mb-1">{project.title}</h3>
              <p className="text-sm text-gray-400 mb-4">
                {project.owner} {project.regNo !== '—' && `· ${project.regNo}`}
              </p>
              
              <div className="flex flex-wrap gap-1.5 mb-4">
                {project.features.map((f) => (
                  <span key={f} className="px-2 py-0.5 rounded-md bg-gray-800/50 text-gray-300 text-xs">
                    {f}
                  </span>
                ))}
              </div>
              
              <div className="flex items-center text-sm text-blue-400 group-hover:text-blue-300">
                <span>View Details</span>
                <ArrowRight size={14} className="ml-1 group-hover:translate-x-1 transition-transform" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Shield size={20} className="text-purple-400" />
          Technology Stack
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {techStack.map((tech) => (
            <div key={tech.name} className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors">
              <p className="font-semibold text-white text-sm">{tech.name}</p>
              <p className="text-xs text-gray-500">{tech.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Integration Flows */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-green-400" />
          API Integration Flows
        </h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="grid grid-cols-12 gap-4 px-4 py-3 bg-gray-800/50 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            <div className="col-span-3">From</div>
            <div className="col-span-3">To</div>
            <div className="col-span-4">Data</div>
            <div className="col-span-2">Status</div>
          </div>
          {integrationFlows.map((flow, i) => (
            <div key={i} className="grid grid-cols-12 gap-4 px-4 py-3 border-t border-gray-800 items-center text-sm">
              <div className="col-span-3 font-medium text-white">{flow.from}</div>
              <div className="col-span-3 text-gray-300">{flow.to}</div>
              <div className="col-span-4 text-gray-400">{flow.data}</div>
              <div className="col-span-2">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 text-xs">
                  <CheckCircle2 size={10} /> Active
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'API Endpoints', value: '40+', icon: <Server size={18} />, color: 'text-blue-400' },
          { label: 'Test Cases', value: '80+', icon: <CheckCircle2 size={18} />, color: 'text-green-400' },
          { label: 'DB Models', value: '15+', icon: <Database size={18} />, color: 'text-purple-400' },
          { label: 'Integration Points', value: '4', icon: <Clock size={18} />, color: 'text-amber-400' },
        ].map((stat) => (
          <div key={stat.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className={`${stat.color} mb-2`}>{stat.icon}</div>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
            <p className="text-xs text-gray-500">{stat.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
