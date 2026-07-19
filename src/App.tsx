import React, { useState } from 'react';
import { RouterCredentials } from './types';
import { RouterConfig } from './components/RouterConfig';
import { Dashboard } from './components/Dashboard';
import { WifiSettings } from './components/WifiSettings';
import { LayoutDashboard, Settings, Wifi, Activity } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'wifi' | 'config'>('dashboard');
  
  // Default credentials
  const [credentials, setCredentials] = useState<RouterCredentials>({
    apiUrl: 'http://localhost:8000',
    ip: '192.168.1.1',
    username: 'admin',
    password: '',
    router_id: 'WE_ZTE_H188A'
  });

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200" dir="rtl">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <LayoutDashboard size={20} className="text-white" />
              </div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
                Router Admin V1.0
              </h1>
            </div>
            <div className="text-sm text-slate-400 hidden sm:block">
              Developed by Amir Lamay
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Navigation Tabs */}
        <div className="flex overflow-x-auto gap-2 mb-8 pb-2 scrollbar-hide">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-colors whitespace-nowrap ${
              activeTab === 'dashboard' 
                ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' 
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <Activity size={18} />
            لوحة التحكم
          </button>
          
          <button
            onClick={() => setActiveTab('wifi')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-colors whitespace-nowrap ${
              activeTab === 'wifi' 
                ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' 
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <Wifi size={18} />
            إعدادات الواي فاي
          </button>
          
          <button
            onClick={() => setActiveTab('config')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-colors whitespace-nowrap ${
              activeTab === 'config' 
                ? 'bg-slate-700/50 text-slate-200 border border-slate-600' 
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <Settings size={18} />
            إعدادات الاتصال
          </button>
        </div>

        {/* Tab Content */}
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          {activeTab === 'config' && (
            <RouterConfig 
              credentials={credentials} 
              onSave={(creds) => {
                setCredentials(creds);
                alert('تم حفظ الإعدادات بنجاح!');
              }} 
            />
          )}

          {activeTab === 'dashboard' && (
            <Dashboard credentials={credentials} />
          )}

          {activeTab === 'wifi' && (
            <WifiSettings credentials={credentials} />
          )}
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700 bg-slate-800/50 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-slate-400 text-sm flex flex-col items-center gap-2">
            <p>Developed by <span className="font-bold text-slate-200">Amir Lamay</span></p>
            <p className="bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent font-medium">Ai Lam3y</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
