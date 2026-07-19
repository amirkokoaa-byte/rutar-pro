import React, { useState } from 'react';
import { RouterCredentials } from '../types';
import { Save, Settings2 } from 'lucide-react';

interface Props {
  credentials: RouterCredentials;
  onSave: (creds: RouterCredentials) => void;
}

export function RouterConfig({ credentials, onSave }: Props) {
  const [formData, setFormData] = useState<RouterCredentials>(credentials);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-2xl shadow-xl backdrop-blur-sm">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-indigo-500/20 rounded-lg text-indigo-400">
          <Settings2 size={24} />
        </div>
        <h2 className="text-xl font-bold text-slate-100">إعدادات الاتصال بالراوتر</h2>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2 md:col-span-2">
          <label className="text-sm font-medium text-slate-400">رابط الخادم المحلي (Local API)</label>
          <input
            type="text"
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
            value={formData.apiUrl}
            onChange={(e) => setFormData({ ...formData, apiUrl: e.target.value })}
            dir="ltr"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-400">IP الراوتر</label>
          <input
            type="text"
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
            value={formData.ip}
            onChange={(e) => setFormData({ ...formData, ip: e.target.value })}
            dir="ltr"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-400">نوع الراوتر (Router ID)</label>
          <select
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
            value={formData.router_id}
            onChange={(e) => setFormData({ ...formData, router_id: e.target.value })}
            dir="ltr"
          >
            <option value="WE_ZTE_H188A">WE ZTE H188A</option>
            <option value="HUAWEI_DG8045">Huawei DG8045</option>
            <option value="TP_LINK_ARCHER">TP-Link Archer</option>
            <option value="ZTE_ZXHN_H168N">ZTE ZXHN H168N</option>
          </select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-400">اسم المستخدم (Username)</label>
          <input
            type="text"
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            dir="ltr"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-400">كلمة المرور (Password)</label>
          <input
            type="password"
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            dir="ltr"
          />
        </div>

        <div className="md:col-span-2 mt-4">
          <button
            type="submit"
            className="w-full md:w-auto px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
          >
            <Save size={20} />
            حفظ الإعدادات
          </button>
        </div>
      </form>
    </div>
  );
}
