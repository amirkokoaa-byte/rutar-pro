import React, { useState } from 'react';
import { Device, RouterCredentials } from '../types';
import { Download, RefreshCw, Shield, Activity, HardDrive } from 'lucide-react';
import * as XLSX from 'xlsx';

interface Props {
  credentials: RouterCredentials;
}

export function Dashboard({ credentials }: Props) {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  
  // State for Quota limit modal
  const [activeMac, setActiveMac] = useState<string | null>(null);
  const [quotaLimit, setQuotaLimit] = useState<string>('');
  const [speedLimit, setSpeedLimit] = useState<string>('');

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${credentials.apiUrl}/api/devices`);
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();
      setDevices(data.devices || []);
    } catch (error) {
      console.error(error);
      alert('فشل جلب الأجهزة. الرجاء التأكد من تشغيل الخادم المحلي (Python API) على جهازك، والتأكد من إدخال رابط الخادم الصحيح في إعدادات الاتصال.');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyLimit = async (mac: string) => {
    if (!quotaLimit && !speedLimit) return;
    
    setActionLoading(mac);
    try {
      const payload = {
        ip: credentials.ip,
        username: credentials.username,
        password: credentials.password,
        router_id: credentials.router_id,
        mac_address: mac,
        ...(speedLimit ? { speed_limit: parseInt(speedLimit) } : {}),
        ...(quotaLimit ? { quota: parseFloat(quotaLimit) } : {}),
      };

      const response = await fetch(`${credentials.apiUrl}/api/limit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Request failed');
      alert('تم تطبيق القيود بنجاح!');
      setActiveMac(null);
      setQuotaLimit('');
      setSpeedLimit('');
    } catch (error) {
      console.error(error);
      alert('حدث خطأ أثناء تطبيق القيود.');
    } finally {
      setActionLoading(null);
    }
  };

  const exportToExcel = () => {
    if (devices.length === 0) return;
    const worksheet = XLSX.utils.json_to_sheet(devices.map(d => ({
      'IP Address': d.ip,
      'MAC Address': d.mac
    })));
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Devices');
    XLSX.writeFile(workbook, 'Router_Devices_Report.xlsx');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-500/20 rounded-lg text-emerald-400">
            <Activity size={24} />
          </div>
          <h2 className="text-xl font-bold text-slate-100">الأجهزة المتصلة بالشبكة</h2>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={fetchDevices}
            disabled={loading}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            {loading ? 'جاري الفحص...' : 'فحص الشبكة'}
          </button>
          
          <button
            onClick={exportToExcel}
            disabled={devices.length === 0}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <Download size={18} />
            تصدير Excel
          </button>
        </div>
      </div>

      <div className="bg-slate-800/50 border border-slate-700 rounded-2xl shadow-xl overflow-hidden backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-right">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-6 py-4 text-slate-300 font-semibold">IP Address</th>
                <th className="px-6 py-4 text-slate-300 font-semibold">MAC Address</th>
                <th className="px-6 py-4 text-slate-300 font-semibold text-center">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {devices.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-6 py-8 text-center text-slate-500">
                    اضغط على "فحص الشبكة" لعرض الأجهزة المتصلة
                  </td>
                </tr>
              ) : (
                devices.map((device, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                    <td className="px-6 py-4 text-slate-300 font-mono" dir="ltr">{device.ip}</td>
                    <td className="px-6 py-4 text-slate-400 font-mono text-sm" dir="ltr">{device.mac}</td>
                    <td className="px-6 py-4">
                      {activeMac === device.mac ? (
                        <div className="flex flex-col sm:flex-row items-center gap-2 justify-center">
                          <input
                            type="number"
                            placeholder="السرعة (Kbps)"
                            className="w-28 bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm text-slate-200"
                            value={speedLimit}
                            onChange={e => setSpeedLimit(e.target.value)}
                          />
                          <input
                            type="number"
                            placeholder="الحد (GB)"
                            className="w-28 bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm text-slate-200"
                            value={quotaLimit}
                            onChange={e => setQuotaLimit(e.target.value)}
                          />
                          <button
                            onClick={() => handleApplyLimit(device.mac)}
                            disabled={actionLoading === device.mac}
                            className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded transition-colors"
                          >
                            {actionLoading === device.mac ? 'جاري...' : 'تطبيق'}
                          </button>
                          <button
                            onClick={() => setActiveMac(null)}
                            className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded transition-colors"
                          >
                            إلغاء
                          </button>
                        </div>
                      ) : (
                        <div className="flex justify-center gap-2">
                          <button
                            onClick={() => setActiveMac(device.mac)}
                            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-md text-sm flex items-center gap-1.5 transition-colors"
                          >
                            <Shield size={14} />
                            تقييد الاستهلاك
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
