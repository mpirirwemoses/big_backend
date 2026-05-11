import { useState } from "react";

function Home({ user, setUser }) {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [tableData, setTableData] = useState(null);
  const [message, setMessage] = useState("");
  const [activeTab, setActiveTab] = useState("pipeline");

  // ================= RUN PIPELINE =================
  const runPipeline = async () => {
    setLoading(true);
    setMessage("🚀 Running pipeline...");
    setReport(null);
    setTableData(null);

    try {
      const res = await fetch("/run-pipeline");
      const data = await res.json();

      if (data.status === "success") {
        setMessage("✅ " + data.message);
        setTableData(data.tables || null);
        if (data.analytics) {
          setReport(data.analytics);
        }
      } else {
        setMessage("❌ " + (data.message || "Pipeline failed"));
      }
    } catch (err) {
      console.error("Pipeline error:", err);
      setMessage("❌ Server not reachable. Is Flask running?");
    } finally {
      setLoading(false);
    }
  };

  // ================= FETCH REPORTS =================
  const fetchReports = async () => {
    setLoading(true);
    setMessage("📊 Loading reports...");
    setTableData(null);

    try {
      const res = await fetch("/reports");
      const data = await res.json();

      if (data.status === "success") {
        setReport(data);
        setMessage(`✅ Reports loaded successfully!`);
      } else {
        setMessage("❌ " + (data.message || "Failed to load reports"));
      }
    } catch (err) {
      console.error("Reports error:", err);
      setMessage("❌ Failed to load reports");
    } finally {
      setLoading(false);
    }
  };

  // ================= EXPORT CSV =================
  const exportCSV = async () => {
    setLoading(true);
    try {
      const res = await fetch("/export-csv");
      const data = await res.json();
      
      if (data.status === "success") {
        setMessage(`✅ ${data.message}: ${data.files.join(", ")}`);
      } else {
        setMessage("❌ " + (data.message || "Failed to export CSV"));
      }
    } catch (err) {
      console.error("Export error:", err);
      setMessage("❌ Failed to export CSV");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans selection:bg-indigo-100 selection:text-indigo-900">
      {/* HEADER */}
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-8 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 p-8 rounded-[2rem] shadow-2xl text-white relative overflow-hidden group">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(99,102,241,0.15),transparent)] pointer-events-none"></div>
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-indigo-200">
              PatentSphere <span className="font-light text-indigo-400">AI</span>
            </h1>
          </div>
          <p className="text-indigo-300/80 text-sm md:text-base font-medium">
            Next-generation patent data engineering & analysis. Welcome, <span className="text-white border-b border-indigo-500/30 pb-0.5">{user?.email}</span>
          </p>
        </div>
        <button
          onClick={() => setUser(null)}
          className="relative z-10 mt-6 md:mt-0 bg-white/5 hover:bg-white/10 backdrop-blur-xl text-white px-6 py-3 rounded-2xl transition-all font-semibold border border-white/10 hover:border-white/20 active:scale-95 shadow-lg flex items-center gap-2 group"
        >
          <span>Sign Out</span>
          <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7" /></svg>
        </button>
      </div>

      <div className="max-w-7xl mx-auto">
        {/* ACTION BUTTONS */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <button
            onClick={runPipeline}
            disabled={loading}
            className="group relative flex flex-col items-start p-6 bg-white hover:bg-indigo-600 rounded-3xl transition-all duration-300 shadow-sm hover:shadow-2xl hover:shadow-indigo-200 border border-slate-200 hover:border-indigo-500 overflow-hidden"
          >
            <div className="w-12 h-12 bg-indigo-50 group-hover:bg-indigo-500/20 rounded-2xl flex items-center justify-center mb-4 transition-colors">
              <span className="text-2xl group-hover:scale-110 transition-transform">🚀</span>
            </div>
            <span className="text-lg font-bold text-slate-800 group-hover:text-white transition-colors">Run Pipeline</span>
            <span className="text-sm text-slate-500 group-hover:text-indigo-100 transition-colors">Process latest TSV datasets</span>
            <div className="absolute bottom-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity translate-y-2 group-hover:translate-y-0 duration-300">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center"><svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" /></svg></div>
            </div>
          </button>
          
          <button
            onClick={fetchReports}
            disabled={loading}
            className="group relative flex flex-col items-start p-6 bg-white hover:bg-emerald-600 rounded-3xl transition-all duration-300 shadow-sm hover:shadow-2xl hover:shadow-emerald-200 border border-slate-200 hover:border-emerald-500 overflow-hidden"
          >
            <div className="w-12 h-12 bg-emerald-50 group-hover:bg-emerald-500/20 rounded-2xl flex items-center justify-center mb-4 transition-colors">
              <span className="text-2xl group-hover:scale-110 transition-transform">📊</span>
            </div>
            <span className="text-lg font-bold text-slate-800 group-hover:text-white transition-colors">Analytics</span>
            <span className="text-sm text-slate-500 group-hover:text-emerald-100 transition-colors">Generate visual insights</span>
            <div className="absolute bottom-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity translate-y-2 group-hover:translate-y-0 duration-300">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center"><svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" /></svg></div>
            </div>
          </button>

          <button
            onClick={exportCSV}
            disabled={loading}
            className="group relative flex flex-col items-start p-6 bg-white hover:bg-rose-600 rounded-3xl transition-all duration-300 shadow-sm hover:shadow-2xl hover:shadow-rose-200 border border-slate-200 hover:border-rose-500 overflow-hidden"
          >
            <div className="w-12 h-12 bg-rose-50 group-hover:bg-rose-500/20 rounded-2xl flex items-center justify-center mb-4 transition-colors">
              <span className="text-2xl group-hover:scale-110 transition-transform">📁</span>
            </div>
            <span className="text-lg font-bold text-slate-800 group-hover:text-white transition-colors">Export</span>
            <span className="text-sm text-slate-500 group-hover:text-rose-100 transition-colors">Download CSV reports</span>
            <div className="absolute bottom-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity translate-y-2 group-hover:translate-y-0 duration-300">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center"><svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" /></svg></div>
            </div>
          </button>
        </div>

        {/* MESSAGES */}
        {loading && (
          <div className="mb-8 p-6 bg-white rounded-3xl shadow-xl border border-indigo-100 flex items-center gap-6 animate-pulse">
            <div className="relative">
              <div className="w-12 h-12 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-indigo-600">...</div>
            </div>
            <div>
              <h3 className="font-bold text-slate-800">Processing Data Pipeline</h3>
              <p className="text-sm text-slate-500">Parsing complex TSV structures and updating the SQLite master database.</p>
            </div>
          </div>
        )}

        {message && !loading && (
          <div className="mb-8 p-5 bg-indigo-50 border border-indigo-100 rounded-2xl text-indigo-900 font-semibold flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
            <span className="w-8 h-8 bg-indigo-600 text-white rounded-lg flex items-center justify-center text-sm shadow-lg shadow-indigo-200">ℹ️</span>
            {message}
          </div>
        )}

        {/* NAVIGATION TABS */}
        <div className="flex gap-4 mb-8 overflow-x-auto pb-2 scrollbar-hide">
          {[
            { id: 'pipeline', label: '🗂️ Master Tables', color: 'indigo' },
            { id: 'reports', label: '📈 Visual Reports', color: 'emerald' },
            { id: 'sql', label: '🔍 Advanced Queries', color: 'blue' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-8 py-4 rounded-2xl font-bold transition-all duration-300 flex items-center gap-2 whitespace-nowrap shadow-sm border ${
                activeTab === tab.id 
                  ? `bg-indigo-600 text-white border-indigo-600 shadow-indigo-200 shadow-lg scale-105` 
                  : `bg-white text-slate-600 border-slate-200 hover:border-indigo-200 hover:bg-indigo-50`
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ================= MASTER TABLES VIEW ================= */}
        {activeTab === "pipeline" && tableData && (
          <div className="space-y-8 animate-in fade-in duration-500">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
              {[
                { title: 'Patents', icon: '📄', data: tableData.patents, count: tableData.total_counts?.patents, color: 'blue', desc: 'Intellectual Property Records' },
                { title: 'Inventors', icon: '👥', data: tableData.inventors, count: tableData.total_counts?.inventors, color: 'emerald', desc: 'Registered Entities' },
                { title: 'Companies', icon: '🏢', data: tableData.companies, count: tableData.total_counts?.companies, color: 'rose', desc: 'Assignee Organizations' },
                { title: 'Locations', icon: '📍', data: tableData.locations, count: tableData.total_counts?.locations, color: 'amber', desc: 'Geographic Distribution' },
                { title: 'Links', icon: '🔗', data: tableData.relationships, count: tableData.total_counts?.relationships, color: 'purple', desc: 'Network Intersections' }
              ].map(card => (
                <div key={card.title} className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200 hover:shadow-xl hover:shadow-slate-200 transition-all group overflow-hidden relative">
                  <div className={`absolute top-0 right-0 w-24 h-24 bg-${card.color}-500/5 rounded-full -mr-8 -mt-8 group-hover:scale-150 transition-transform`}></div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-3xl">{card.icon}</span>
                    <span className={`text-xs font-black uppercase tracking-widest px-2 py-1 rounded-lg bg-${card.color}-50 text-${card.color}-600`}>Preview</span>
                  </div>
                  <h3 className="font-black text-slate-800 text-lg mb-1">{card.title}</h3>
                  <p className="text-xs text-slate-500 mb-4">{card.desc}</p>
                  <div className="flex items-end gap-2 mb-6">
                    <span className={`text-3xl font-black text-${card.color}-600`}>{(card.count || 0).toLocaleString()}</span>
                    <span className="text-[10px] font-bold text-slate-400 mb-1.5 uppercase tracking-tighter">Total Entries</span>
                  </div>
                  
                  <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                    {card.data?.length > 0 ? (
                      card.data.map((item, i) => (
                        <div key={i} className="p-3 bg-slate-50 rounded-xl border border-slate-100 hover:border-indigo-200 hover:bg-white transition-all group/item">
                          {card.title === 'Patents' && (
                            <>
                              <p className="text-[10px] font-bold text-indigo-600 mb-1">{item.patent_id}</p>
                              <p className="text-xs font-semibold text-slate-700 line-clamp-2 leading-tight group-hover/item:text-slate-900">{item.title}</p>
                              <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-100">
                                <span className="text-[10px] bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded font-bold">{item.year}</span>
                                <span className="text-[10px] text-slate-400">{item.filing_date}</span>
                              </div>
                            </>
                          )}
                          {card.title === 'Inventors' && (
                            <>
                              <p className="text-sm font-bold text-slate-800">{item.name}</p>
                              <div className="flex justify-between items-center mt-2">
                                <span className="text-[10px] font-mono text-slate-400">{item.inventor_id}</span>
                                <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-black">{item.country}</span>
                              </div>
                            </>
                          )}
                          {card.title === 'Companies' && (
                            <>
                              <p className="text-sm font-bold text-slate-800">{item.name}</p>
                              <p className="text-[10px] font-mono text-rose-500 mt-2 truncate">{item.company_id}</p>
                            </>
                          )}
                          {card.title === 'Locations' && (
                            <>
                              <p className="text-sm font-bold text-slate-800">{item.city || 'N/A'}</p>
                              <p className="text-xs text-slate-500">{item.state ? `${item.state}, ` : ''}{item.country}</p>
                              <div className="mt-2 flex gap-2">
                                <span className="text-[8px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-100">LAT: {item.latitude?.toFixed(2)}</span>
                                <span className="text-[8px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-100">LNG: {item.longitude?.toFixed(2)}</span>
                              </div>
                            </>
                          )}
                          {card.title === 'Links' && (
                            <div className="text-[9px] font-black text-slate-500 uppercase tracking-tighter flex flex-wrap gap-1 items-center">
                              <span className="text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">{item.patent_id}</span>
                              <svg className="w-2 h-2 text-slate-300" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                              {item.inventor_id && <span className="text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">{item.inventor_id}</span>}
                              {item.company_id && <span className="text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded">{item.company_id}</span>}
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="py-20 text-center">
                        <span className="text-4xl block mb-2 opacity-20">🔍</span>
                        <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">No Data</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ================= ANALYTICS REPORTS VIEW ================= */}
        {activeTab === "reports" && report && (
          <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* STATS STRIP */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                { label: 'Total Patents', value: report.total_patents, color: 'indigo', icon: '📄' },
                { label: 'Global Companies', value: report.total_companies, color: 'rose', icon: '🏢' },
                { label: 'Top Innovators', value: report.top_inventors?.length, color: 'emerald', icon: '🏆' },
                { label: 'Territories', value: report.countries?.length, color: 'amber', icon: '🌍' }
              ].map(stat => (
                <div key={stat.label} className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100 relative overflow-hidden group hover:shadow-2xl hover:shadow-slate-200 transition-all">
                  <div className={`absolute -right-4 -bottom-4 text-6xl opacity-[0.03] group-hover:scale-150 transition-transform duration-500`}>{stat.icon}</div>
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-2">{stat.label}</p>
                  <p className={`text-4xl font-black text-${stat.color}-600 tracking-tighter`}>{(stat.value || 0).toLocaleString()}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
              {/* RANKED LISTS */}
              <div className="bg-white p-10 rounded-[3rem] shadow-sm border border-slate-100">
                <div className="flex items-center justify-between mb-8 border-b border-slate-100 pb-6">
                  <h2 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
                    <span className="w-10 h-10 bg-rose-50 rounded-2xl flex items-center justify-center text-xl shadow-inner">🏢</span>
                    Top Organizations
                  </h2>
                  <span className="text-[10px] font-bold text-slate-400 uppercase bg-slate-50 px-3 py-1.5 rounded-full border border-slate-100">By Patent Volume</span>
                </div>
                <div className="space-y-6">
                  {report.top_companies?.length > 0 ? (
                    report.top_companies.map((comp, i) => (
                      <div key={i} className="group cursor-default">
                        <div className="flex justify-between items-center mb-2">
                          <div className="flex items-center gap-4">
                            <span className="w-6 text-xs font-black text-slate-300 group-hover:text-rose-500 transition-colors">0{i+1}</span>
                            <span className="font-bold text-slate-700 group-hover:text-slate-900 transition-colors">{comp.name}</span>
                          </div>
                          <span className="text-sm font-black text-rose-600 bg-rose-50 px-3 py-1 rounded-xl">{comp.patent_count}</span>
                        </div>
                        <div className="h-2 w-full bg-slate-50 rounded-full overflow-hidden shadow-inner">
                          <div 
                            className="h-full bg-gradient-to-r from-rose-400 to-rose-600 rounded-full transition-all duration-1000 ease-out" 
                            style={{ width: `${(comp.patent_count / report.top_companies[0].patent_count) * 100}%` }}
                          />
                        </div>
                      </div>
                    ))
                  ) : <div className="py-20 text-center text-slate-400 font-bold uppercase tracking-widest">No Organization Data</div>}
                </div>
              </div>

              <div className="bg-white p-10 rounded-[3rem] shadow-sm border border-slate-100">
                <div className="flex items-center justify-between mb-8 border-b border-slate-100 pb-6">
                  <h2 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
                    <span className="w-10 h-10 bg-indigo-50 rounded-2xl flex items-center justify-center text-xl shadow-inner">🏆</span>
                    Leading Inventors
                  </h2>
                  <span className="text-[10px] font-bold text-slate-400 uppercase bg-slate-50 px-3 py-1.5 rounded-full border border-slate-100">Individual Performance</span>
                </div>
                <div className="space-y-6">
                  {report.top_inventors?.length > 0 ? (
                    report.top_inventors.map((inv, i) => (
                      <div key={i} className="group cursor-default">
                        <div className="flex justify-between items-center mb-2">
                          <div className="flex items-center gap-4">
                            <span className="w-6 text-xs font-black text-slate-300 group-hover:text-indigo-500 transition-colors">0{i+1}</span>
                            <span className="font-bold text-slate-700 group-hover:text-slate-900 transition-colors">{inv.name}</span>
                          </div>
                          <span className="text-sm font-black text-indigo-600 bg-indigo-50 px-3 py-1 rounded-xl">{inv.patent_count}</span>
                        </div>
                        <div className="h-2 w-full bg-slate-50 rounded-full overflow-hidden shadow-inner">
                          <div 
                            className="h-full bg-gradient-to-r from-indigo-400 to-indigo-600 rounded-full transition-all duration-1000 ease-out" 
                            style={{ width: `${(inv.patent_count / report.top_inventors[0].patent_count) * 100}%` }}
                          />
                        </div>
                      </div>
                    ))
                  ) : <div className="py-20 text-center text-slate-400 font-bold uppercase tracking-widest">No Inventor Data</div>}
                </div>
              </div>

              {/* TRENDS CHART */}
              <div className="lg:col-span-2 bg-slate-900 p-12 rounded-[4rem] shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none bg-[radial-gradient(circle_at_20%_30%,#6366f1,transparent)]"></div>
                <div className="relative z-10">
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-4">
                    <div>
                      <h2 className="text-3xl font-black text-white tracking-tight mb-2 flex items-center gap-3">
                        <span className="text-indigo-400">📅</span> Temporal Trends
                      </h2>
                      <p className="text-indigo-300/60 font-medium">Patent filing velocity over the last two decades</p>
                    </div>
                    <div className="flex gap-2">
                      <div className="px-4 py-2 bg-white/5 border border-white/10 rounded-2xl text-[10px] font-black text-white uppercase tracking-widest">Annual Analysis</div>
                    </div>
                  </div>
                  
                  <div className="flex items-end justify-between gap-2 h-64 border-b border-white/5 pb-2">
                    {report.trends?.length > 0 ? (
                      (() => {
                        const maxVal = Math.max(...report.trends.map(t => t.total || 0));
                        return report.trends.map((t, i) => (
                          <div key={i} className="flex-1 flex flex-col items-center group relative h-full justify-end">
                            <div className="absolute bottom-full mb-2 opacity-0 group-hover:opacity-100 transition-opacity bg-white text-slate-900 px-2 py-1 rounded text-[10px] font-black shadow-xl pointer-events-none whitespace-nowrap z-20">
                              {t.total} Patents
                            </div>
                            <div 
                              className="w-full max-w-[20px] bg-gradient-to-t from-indigo-600 to-indigo-400 rounded-t-lg transition-all duration-1000 group-hover:from-indigo-400 group-hover:to-white shadow-[0_0_20px_rgba(99,102,241,0.3)]" 
                              style={{ height: `${(t.total / maxVal) * 100}%` }}
                            />
                            <span className="text-[8px] font-black text-slate-500 mt-3 rotate-45 group-hover:text-white transition-colors">{t.year}</span>
                          </div>
                        ));
                      })()
                    ) : <div className="w-full flex items-center justify-center text-slate-600 uppercase font-black text-sm tracking-[0.5em]">Chart Offline</div>}
                  </div>
                </div>
              </div>

              {/* COUNTRY CARDS */}
              <div className="lg:col-span-2">
                <div className="flex items-center gap-4 mb-8">
                  <h2 className="text-2xl font-black text-slate-800 tracking-tight">🌍 Global Territory Distribution</h2>
                  <div className="h-[1px] flex-1 bg-slate-200"></div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
                  {report.countries?.length > 0 ? (
                    report.countries.map((c, i) => (
                      <div key={i} className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100 flex flex-col items-center text-center hover:border-indigo-400 hover:shadow-2xl hover:shadow-indigo-100 transition-all group">
                        <span className="text-4xl font-black text-slate-200 group-hover:text-indigo-100 transition-colors mb-2">{c.country?.substring(0, 2).toUpperCase()}</span>
                        <h4 className="text-sm font-black text-slate-800 mb-1">{c.country}</h4>
                        <p className="text-xs font-bold text-indigo-500 uppercase tracking-tighter">{c.total} Patents</p>
                      </div>
                    ))
                  ) : <div className="col-span-full py-10 text-center text-slate-400 uppercase font-black tracking-widest">No Territory Data</div>}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================= ADVANCED QUERIES VIEW ================= */}
        {activeTab === "sql" && report && (
          <div className="space-y-10 animate-in fade-in zoom-in-95 duration-500">
            <div className="bg-white rounded-[3rem] shadow-2xl shadow-slate-200 border border-slate-100 overflow-hidden">
              <div className="p-10 bg-slate-900 text-white flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-black tracking-tight mb-1 flex items-center gap-3">
                    <span className="text-blue-400">🔗</span> Comprehensive Data Join
                  </h2>
                  <p className="text-slate-400 text-xs font-medium uppercase tracking-widest">Relational mapping: Patents x Inventors x Organizations</p>
                </div>
                <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center font-black text-blue-400 border border-white/10 shadow-inner">Q5</div>
              </div>
              <div className="overflow-x-auto p-2">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-100">
                      {['ID', 'Title', 'Lead Inventor', 'Organization', 'Region', 'Year'].map(h => (
                        <th key={h} className="px-8 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {report.joined_data?.length > 0 ? (
                      report.joined_data.slice(0, 15).map((row, i) => (
                        <tr key={i} className="hover:bg-blue-50/30 transition-colors group">
                          <td className="px-8 py-5 text-[10px] font-bold font-mono text-blue-600">{row.patent_id}</td>
                          <td className="px-8 py-5 text-sm font-bold text-slate-800 line-clamp-1">{row.title}</td>
                          <td className="px-8 py-5 text-sm font-semibold text-slate-600">{row.inventor_name || <span className="text-slate-300 font-light italic">N/A</span>}</td>
                          <td className="px-8 py-5">
                            <span className="text-xs font-black text-rose-600 bg-rose-50 px-3 py-1 rounded-full">{row.company_name || 'Individual'}</span>
                          </td>
                          <td className="px-8 py-5 text-xs font-bold text-slate-500 uppercase tracking-tighter">{row.country || '-'}</td>
                          <td className="px-8 py-5">
                            <span className="text-[10px] font-black text-slate-400 group-hover:text-indigo-600 transition-colors">{row.year}</span>
                          </td>
                        </tr>
                      ))
                    ) : <tr><td colSpan="6" className="py-20 text-center text-slate-300 font-black uppercase tracking-widest">Table Empty</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
              {/* CTE CARD */}
              <div className="bg-white p-12 rounded-[4rem] shadow-sm border border-slate-100 flex flex-col">
                <div className="flex items-center justify-between mb-10 border-b border-slate-50 pb-8">
                  <div>
                    <h2 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
                      <span className="text-emerald-500">📊</span> Multi-Phase CTE
                    </h2>
                    <p className="text-slate-400 text-xs mt-1 font-bold uppercase tracking-widest">Complex aggregations</p>
                  </div>
                  <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center font-black text-emerald-600 border border-emerald-100">Q6</div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {report.cte_results?.map((row, i) => (
                    <div key={i} className="flex flex-col p-6 bg-slate-50 rounded-[2rem] border border-slate-100 group hover:bg-emerald-600 transition-all cursor-default">
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 group-hover:text-emerald-100">{row.country}</span>
                      <span className="text-2xl font-black text-slate-800 group-hover:text-white tracking-tighter">{row.total}</span>
                      <span className="text-[10px] font-bold text-emerald-600 group-hover:text-emerald-200 mt-2">Active Patents</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* RANKING CARD */}
              <div className="bg-white p-12 rounded-[4rem] shadow-sm border border-slate-100 flex flex-col">
                <div className="flex items-center justify-between mb-10 border-b border-slate-50 pb-8">
                  <div>
                    <h2 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
                      <span className="text-orange-500">🎯</span> Rank Over Time
                    </h2>
                    <p className="text-slate-400 text-xs mt-1 font-bold uppercase tracking-widest">Window functions & density</p>
                  </div>
                  <div className="w-10 h-10 bg-orange-50 rounded-xl flex items-center justify-center font-black text-orange-600 border border-orange-100">Q7</div>
                </div>
                <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                  {report.ranked_inventors?.map((inv, i) => (
                    <div key={i} className="flex items-center justify-between p-6 bg-slate-50 rounded-[2rem] border border-slate-100 hover:border-orange-200 transition-colors">
                      <div className="flex items-center gap-5">
                        <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-xl font-black text-orange-500 shadow-sm border border-slate-100">#{inv.rank_position}</div>
                        <div>
                          <p className="text-sm font-black text-slate-800 tracking-tight">{inv.name}</p>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">{inv.country}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-black text-orange-600 tracking-tighter">{inv.patent_count}</p>
                        <p className="text-[8px] font-black text-slate-300 uppercase tracking-[0.2em]">Dense Rank: {inv.dense_rank}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* EMPTY STATE */}
        {!report && !tableData && !loading && (
          <div className="text-center py-40 animate-in fade-in zoom-in-95 duration-700">
            <div className="w-40 h-40 bg-indigo-50 rounded-[3rem] flex items-center justify-center mx-auto mb-10 shadow-inner group">
              <span className="text-7xl group-hover:scale-125 transition-transform duration-500">🚀</span>
            </div>
            <h2 className="text-4xl font-black text-slate-800 tracking-tighter mb-4">Awaiting Signal...</h2>
            <p className="text-slate-500 font-medium max-w-md mx-auto mb-10 leading-relaxed">
              Master database is ready for ingestion. Click the <b>Run Pipeline</b> command above to synchronize with the latest TSV patent archives.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button 
                onClick={runPipeline}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-10 py-5 rounded-[2rem] font-black text-lg transition-all shadow-2xl shadow-indigo-200 hover:-translate-y-1 active:scale-95"
              >
                Initialize Pipeline
              </button>
              <button 
                onClick={fetchReports}
                className="bg-white hover:bg-slate-50 text-slate-800 px-10 py-5 rounded-[2rem] font-black text-lg transition-all border border-slate-200 hover:border-indigo-200 active:scale-95"
              >
                Restore Previous Scan
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Home;
    </div>
  );
}

export default Home;