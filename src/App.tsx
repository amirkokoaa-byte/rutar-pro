/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Router, Wifi, Users, Activity, Lock, User, Globe, ChevronLeft, RefreshCw, Monitor, Smartphone, Tv } from 'lucide-react';

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeTab, setActiveTab] = useState('wifi');
  const [isScanning, setIsScanning] = useState(false);
  const [devices, setDevices] = useState<{name: string, ip: string, mac: string, type: 'pc' | 'phone' | 'tv'}[]>([]);
  
  const [wifiSettings, setWifiSettings] = useState({ ssid: 'MyHomeNetwork', password: 'securepassword123', mode: '802.11b/g/n' });
  const [isSavingWifi, setIsSavingWifi] = useState(false);
  const [wifiSaveSuccess, setWifiSaveSuccess] = useState(false);

  const [qosSettings, setQosSettings] = useState({ mac: '', speedLimit: '', quotaLimit: '' });
  const [isSavingQos, setIsSavingQos] = useState(false);
  const [qosSaveSuccess, setQosSaveSuccess] = useState(false);

  const handleQosSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingQos(true);
    setQosSaveSuccess(false);
    
    // محاكاة إرسال طلب لتغيير إعدادات QoS أو الحظر في الراوتر
    setTimeout(() => {
      setIsSavingQos(false);
      setQosSaveSuccess(true);
      setTimeout(() => setQosSaveSuccess(false), 3000);
    }, 2000);
  };

  const handleWifiSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingWifi(true);
    setWifiSaveSuccess(false);
    
    // محاكاة إرسال طلب لتغيير الإعدادات في الراوتر
    setTimeout(() => {
      setIsSavingWifi(false);
      setWifiSaveSuccess(true);
      setTimeout(() => setWifiSaveSuccess(false), 3000);
    }, 2000);
  };

  const handleScan = () => {
    setIsScanning(true);
    // محاكاة عملية فحص الشبكة
    setTimeout(() => {
      setDevices([
        { name: 'Desktop-PC', ip: '192.168.1.5', mac: '00:1A:2B:3C:4D:5E', type: 'pc' },
        { name: 'iPhone-13', ip: '192.168.1.12', mac: 'A1:B2:C3:D4:E5:F6', type: 'phone' },
        { name: 'Smart-TV', ip: '192.168.1.20', mac: '11:22:33:44:55:66', type: 'tv' },
        { name: 'Galaxy-S21', ip: '192.168.1.15', mac: '5A:4B:3C:2D:1E:0F', type: 'phone' },
      ]);
      setIsScanning(false);
    }, 2000);
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoggedIn(true);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex font-sans" dir="rtl">
      {/* Sidebar */}
      <aside className="w-72 bg-gray-800 border-l border-gray-700 flex flex-col">
        <div className="p-6 flex items-center gap-3 border-b border-gray-700">
          <div className="p-2.5 bg-blue-600 rounded-xl shadow-lg shadow-blue-500/20">
            <Router className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">مدير الراوتر</h1>
            <p className="text-xs text-gray-400">Local Network Manager</p>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          <SidebarItem 
            icon={<Wifi className="w-5 h-5" />} 
            label="إعدادات الواي فاي" 
            isActive={activeTab === 'wifi'} 
            onClick={() => isLoggedIn && setActiveTab('wifi')} 
            disabled={!isLoggedIn} 
          />
          <SidebarItem 
            icon={<Users className="w-5 h-5" />} 
            label="الأجهزة المتصلة" 
            isActive={activeTab === 'devices'} 
            onClick={() => isLoggedIn && setActiveTab('devices')} 
            disabled={!isLoggedIn} 
          />
          <SidebarItem 
            icon={<Activity className="w-5 h-5" />} 
            label="التحكم في السرعات" 
            isActive={activeTab === 'speed'} 
            onClick={() => isLoggedIn && setActiveTab('speed')} 
            disabled={!isLoggedIn} 
          />
        </nav>

        <div className="p-4 border-t border-gray-700 text-sm text-gray-500 text-center bg-gray-800/50">
          V 1.0.0 - Offline Mode
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col bg-[#0f172a] relative overflow-hidden">
        {/* Background decorative blobs */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-3xl transform translate-x-1/2 -translate-y-1/2 pointer-events-none"></div>
        
        {!isLoggedIn ? (
          <div className="flex-1 flex items-center justify-center p-8 z-10">
            <div className="w-full max-w-md bg-gray-800/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-gray-700/50 p-10">
              <div className="text-center mb-10">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-900 border border-gray-700 shadow-inner mb-6">
                  <Lock className="w-8 h-8 text-blue-500" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-3">تسجيل الدخول</h2>
                <p className="text-gray-400 text-sm">أدخل بيانات اعتماد الراوتر المحلي للاتصال</p>
              </div>

              <form onSubmit={handleLogin} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-300 mb-2">عنوان IP</label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                      <Globe className="w-5 h-5 text-gray-500 group-focus-within:text-blue-500 transition-colors" />
                    </div>
                    <input 
                      type="text" 
                      defaultValue="192.168.1.1" 
                      dir="ltr" 
                      className="block w-full pr-12 pl-4 py-3.5 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-left font-mono text-lg" 
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-300 mb-2">اسم المستخدم</label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                      <User className="w-5 h-5 text-gray-500 group-focus-within:text-blue-500 transition-colors" />
                    </div>
                    <input 
                      type="text" 
                      placeholder="admin" 
                      dir="ltr" 
                      className="block w-full pr-12 pl-4 py-3.5 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-left" 
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-300 mb-2">كلمة المرور</label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                      <Lock className="w-5 h-5 text-gray-500 group-focus-within:text-blue-500 transition-colors" />
                    </div>
                    <input 
                      type="password" 
                      placeholder="••••••••" 
                      dir="ltr" 
                      className="block w-full pr-12 pl-4 py-3.5 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-left font-mono tracking-widest" 
                    />
                  </div>
                </div>

                <button 
                  type="submit" 
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 px-4 rounded-xl transition-all duration-200 mt-8 flex items-center justify-center gap-2 shadow-lg shadow-blue-600/30 hover:shadow-blue-600/50 active:scale-[0.98]"
                >
                  <span>دخول</span>
                  <ChevronLeft className="w-5 h-5" />
                </button>
              </form>
            </div>
          </div>
        ) : (
          <div className="flex-1 p-10 z-10 flex flex-col">
            <header className="mb-10 flex justify-between items-end">
              <div>
                <h2 className="text-4xl font-bold text-white mb-2">
                  {activeTab === 'wifi' && 'إعدادات الواي فاي'}
                  {activeTab === 'devices' && 'الأجهزة المتصلة'}
                  {activeTab === 'speed' && 'التحكم في السرعات'}
                </h2>
                <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                  متصل بالراوتر: 192.168.1.1
                </div>
              </div>
              <button 
                onClick={() => setIsLoggedIn(false)}
                className="text-sm text-gray-400 hover:text-white transition-colors px-4 py-2 rounded-lg hover:bg-gray-800"
              >
                تسجيل الخروج
              </button>
            </header>

            {activeTab === 'wifi' ? (
              <div className="w-full max-w-3xl mx-auto flex flex-col bg-gray-800/50 border border-gray-700/50 rounded-3xl p-8 backdrop-blur-sm shadow-xl">
                <div className="flex justify-between items-center mb-8 border-b border-gray-700/50 pb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-1">إعدادات الواي فاي</h3>
                    <p className="text-gray-400 text-sm">تعديل اسم الشبكة، كلمة المرور، ووضع البث</p>
                  </div>
                  <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20">
                    <Wifi className="w-6 h-6 text-blue-400" />
                  </div>
                </div>

                <form onSubmit={handleWifiSave} className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">اسم الشبكة (SSID)</label>
                    <input 
                      type="text" 
                      value={wifiSettings.ssid}
                      onChange={e => setWifiSettings({...wifiSettings, ssid: e.target.value})}
                      dir="ltr" 
                      className="block w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-left" 
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">كلمة المرور (WLAN Password)</label>
                    <input 
                      type="password" 
                      value={wifiSettings.password}
                      onChange={e => setWifiSettings({...wifiSettings, password: e.target.value})}
                      dir="ltr" 
                      className="block w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-left font-mono tracking-widest" 
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">وضع الشبكة (Network Mode)</label>
                    <select 
                      value={wifiSettings.mode}
                      onChange={e => setWifiSettings({...wifiSettings, mode: e.target.value})}
                      dir="ltr" 
                      className="block w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-left appearance-none"
                    >
                      <option value="802.11b/g/n">802.11b/g/n (متوافق مع معظم الأجهزة)</option>
                      <option value="802.11b/g">802.11b/g (أجهزة قديمة)</option>
                      <option value="802.11n">802.11n only (سرعة وأداء أفضل)</option>
                    </select>
                  </div>

                  <div className="pt-4 border-t border-gray-700/50">
                    <button 
                      type="submit" 
                      disabled={isSavingWifi}
                      className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3.5 px-4 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-blue-600/30 hover:shadow-blue-600/50 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSavingWifi ? (
                        <>
                          <RefreshCw className="w-5 h-5 animate-spin" />
                          <span>جاري الحفظ وتطبيق الإعدادات...</span>
                        </>
                      ) : (
                        <span>حفظ الإعدادات</span>
                      )}
                    </button>
                    {wifiSaveSuccess && (
                      <p className="text-emerald-400 text-sm text-center mt-3 font-medium">تم حفظ الإعدادات بنجاح!</p>
                    )}
                  </div>
                </form>
              </div>
            ) : activeTab === 'devices' ? (
              <div className="w-full max-w-5xl mx-auto flex flex-col h-full bg-gray-800/50 border border-gray-700/50 rounded-3xl p-8 backdrop-blur-sm shadow-xl">
                <div className="flex justify-between items-center mb-8 border-b border-gray-700/50 pb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-1">الأجهزة المتصلة حالياً</h3>
                    <p className="text-gray-400 text-sm">قائمة بالأجهزة المتصلة بشبكة الواي فاي والكابل</p>
                  </div>
                  <button 
                    onClick={handleScan}
                    disabled={isScanning}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20 active:scale-[0.98]"
                  >
                    <RefreshCw className={`w-5 h-5 ${isScanning ? 'animate-spin' : ''}`} />
                    <span className="font-semibold">{isScanning ? 'جاري الفحص...' : 'فحص الشبكة'}</span>
                  </button>
                </div>
                
                <div className="flex-1 overflow-hidden bg-gray-900/50 rounded-2xl border border-gray-700/50">
                  <div className="overflow-x-auto h-full">
                    <table className="w-full text-right">
                      <thead className="bg-gray-800/80 border-b border-gray-700/50 text-gray-400 text-sm sticky top-0">
                        <tr>
                          <th className="px-6 py-4 font-semibold w-1/3">اسم الجهاز</th>
                          <th className="px-6 py-4 font-semibold w-1/4">عنوان IP</th>
                          <th className="px-6 py-4 font-semibold w-1/4">عنوان MAC</th>
                          <th className="px-6 py-4 font-semibold text-center w-1/6">الحالة</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-700/50">
                        {devices.length === 0 ? (
                          <tr>
                            <td colSpan={4} className="px-6 py-20 text-center text-gray-500">
                              <div className="flex flex-col items-center justify-center">
                                <Monitor className="w-12 h-12 mb-4 text-gray-600" />
                                <p className="text-lg">{isScanning ? 'جاري البحث عن الأجهزة المتصلة...' : 'اضغط على "فحص الشبكة" لعرض الأجهزة'}</p>
                              </div>
                            </td>
                          </tr>
                        ) : (
                          devices.map((device, idx) => (
                            <tr key={idx} className="hover:bg-gray-800/30 transition-colors">
                              <td className="px-6 py-4">
                                <div className="flex items-center gap-4">
                                  <div className="p-2.5 bg-gray-800 rounded-xl text-blue-400 border border-gray-700/50">
                                    {device.type === 'pc' && <Monitor className="w-5 h-5" />}
                                    {device.type === 'phone' && <Smartphone className="w-5 h-5" />}
                                    {device.type === 'tv' && <Tv className="w-5 h-5" />}
                                  </div>
                                  <span className="font-medium text-gray-200" dir="ltr">{device.name}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 font-mono text-sm text-gray-300" dir="ltr">{device.ip}</td>
                              <td className="px-6 py-4 font-mono text-sm text-gray-400" dir="ltr">{device.mac}</td>
                              <td className="px-6 py-4 text-center">
                                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-medium border border-emerald-500/20">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                  متصل
                                </span>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="w-full max-w-3xl mx-auto flex flex-col bg-gray-800/50 border border-gray-700/50 rounded-3xl p-8 backdrop-blur-sm shadow-xl">
                <div className="flex justify-between items-center mb-8 border-b border-gray-700/50 pb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-1">التحكم في السرعات والاستهلاك</h3>
                    <p className="text-gray-400 text-sm">تحديد السرعة القصوى وحظر الأجهزة عند استهلاك باقة محددة</p>
                  </div>
                  <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20">
                    <Activity className="w-6 h-6 text-blue-400" />
                  </div>
                </div>

                <form onSubmit={handleQosSave} className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">اختر الجهاز (بناءً على MAC Address)</label>
                    <select 
                      value={qosSettings.mac}
                      onChange={e => setQosSettings({...qosSettings, mac: e.target.value})}
                      dir="ltr" 
                      className="block w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-left appearance-none"
                    >
                      <option value="" disabled>-- اختر جهازاً --</option>
                      {devices.length === 0 && <option value="" disabled>لا توجد أجهزة متصلة (قم بالفحص أولاً)</option>}
                      {devices.map(device => (
                        <option key={device.mac} value={device.mac}>
                          {device.name} - {device.mac}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">السرعة القصوى (Kbps) - اختياري</label>
                    <input 
                      type="number" 
                      placeholder="مثال: 512 (لـ نصف ميجا) أو 2048 (لـ 2 ميجا)"
                      value={qosSettings.speedLimit}
                      onChange={e => setQosSettings({...qosSettings, speedLimit: e.target.value})}
                      dir="ltr" 
                      className="block w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-left" 
                    />
                    <p className="text-xs text-gray-500 mt-2 text-right">اترك الحقل فارغاً إذا كنت لا ترغب في تحديد سرعة معينة.</p>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">الحد الأقصى للاستهلاك (جيجابايت) - اختياري</label>
                    <input 
                      type="number" 
                      placeholder="مثال: 10"
                      value={qosSettings.quotaLimit}
                      onChange={e => setQosSettings({...qosSettings, quotaLimit: e.target.value})}
                      dir="ltr" 
                      className="block w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-left" 
                    />
                    <p className="text-xs text-gray-500 mt-2 text-right">سيتم مراقبة الجهاز وحظره تلقائياً (MAC Filter) عند تجاوز هذا الحد.</p>
                  </div>

                  <div className="pt-4 border-t border-gray-700/50">
                    <button 
                      type="submit" 
                      disabled={isSavingQos || !qosSettings.mac}
                      className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3.5 px-4 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-blue-600/30 hover:shadow-blue-600/50 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSavingQos ? (
                        <>
                          <RefreshCw className="w-5 h-5 animate-spin" />
                          <span>جاري الحفظ والتطبيق...</span>
                        </>
                      ) : (
                        <span>تطبيق الإعدادات</span>
                      )}
                    </button>
                    {qosSaveSuccess && (
                      <p className="text-emerald-400 text-sm text-center mt-3 font-medium">تم تطبيق إعدادات السرعة والحظر بنجاح!</p>
                    )}
                  </div>
                </form>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function SidebarItem({ icon, label, isActive, onClick, disabled }: { icon: React.ReactNode, label: string, isActive: boolean, onClick: () => void, disabled: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-200 group ${
        isActive
          ? 'bg-blue-600 text-white shadow-md shadow-blue-900/20'
          : disabled
          ? 'text-gray-600 cursor-not-allowed'
          : 'text-gray-400 hover:bg-gray-700/50 hover:text-gray-100'
      }`}
    >
      <div className={`${isActive ? 'text-white' : disabled ? 'text-gray-600' : 'text-gray-400 group-hover:text-blue-400'}`}>
        {icon}
      </div>
      <span className="font-semibold text-[15px]">{label}</span>
    </button>
  );
}
