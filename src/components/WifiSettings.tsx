import React, { useState } from 'react';
import { RouterCredentials } from '../types';
import { Wifi, Save } from 'lucide-react';

interface Props {
  credentials: RouterCredentials;
}

export function WifiSettings({ credentials }: Props) {
  const [ssid, setSsid] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ssid && !password) return;

    setLoading(true);
    try {
      const payload = {
        ip: credentials.ip,
        username: credentials.username,
        password: credentials.password,
        router_id: credentials.router_id,
        ssid: ssid || undefined,
        password_wifi: password || undefined,
      };

      const response = await fetch(`${credentials.apiUrl}/api/wifi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Request failed');
      alert('تم تحديث إعدادات الواي فاي بنجاح!');
      setSsid('');
      setPassword('');
    } catch (error) {
      console.error(error);
      alert('حدث خطأ أثناء تحديث إعدادات الواي فاي.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-2xl shadow-xl backdrop-blur-sm">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
          <Wifi size={24} />
        </div>
        <h2 className="text-xl font-bold text-slate-100">إعدادات شبكة الواي فاي (Wi-Fi)</h2>
      </div>

      <form onSubmit={handleUpdate} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-400">اسم الشبكة الجديد (SSID)</label>
          <input
            type="text"
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
            placeholder="اتركه فارغاً إذا لم ترغب بتغييره"
            value={ssid}
            onChange={(e) => setSsid(e.target.value)}
            dir="ltr"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-400">كلمة مرور الواي فاي الجديدة</label>
          <input
            type="text"
            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
            placeholder="اتركه فارغاً إذا لم ترغب بتغييره"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            dir="ltr"
          />
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={loading || (!ssid && !password)}
            className="w-full sm:w-auto px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="animate-pulse">جاري التطبيق (قد يستغرق بعض الوقت)...</span>
            ) : (
              <>
                <Save size={20} />
                تطبيق التغييرات
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
