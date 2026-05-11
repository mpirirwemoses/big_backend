import { useState } from "react";

function Home({ user, setUser }) {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [sampleData, setSampleData] = useState(null);
  const [message, setMessage] = useState("");
  const [activeTab, setActiveTab] = useState("pipeline");

  // ================= RUN PIPELINE =================
  const runPipeline = async () => {
    setLoading(true);
    setMessage("🚀 Running pipeline...");
    setReport(null);
    setSampleData(null);

    try {
      const res = await fetch("http://127.0.0.1:5000/run-pipeline");
      const data = await res.json();

      if (data.status === "success") {
        setMessage("✅ " + data.message);
        setSampleData(data.sample || null);
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
    setSampleData(null);

    try {
      const res = await fetch("http://127.0.0.1:5000/reports");
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
      const res = await fetch("http://127.0.0.1:5000/export-csv");
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
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 bg-gradient-to-r from-indigo-600 to-purple-600 p-6 rounded-2xl shadow-xl text-white">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">
            Patent Intelligence Dashboard
          </h1>
          <p className="text-indigo-100 mt-2 text-sm">
            Welcome, <span className="font-semibold">{user?.email}</span>
          </p>
        </div>
        <button
          onClick={() => setUser(null)}
          className="mt-4 md:mt-0 bg-white/20 hover:bg-white/30 backdrop-blur text-white px-5 py-2.5 rounded-lg transition-all font-medium border border-white/10"
        >
          Logout
        </button>
      </div>

      {/* ACTION BUTTONS */}
      <div className="flex flex-wrap gap-4 mb-8">
        <button
          onClick={runPipeline}
          disabled={loading}
          className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-6 py-3 rounded-xl disabled:opacity-50 transition-all shadow-md hover:shadow-lg font-medium transform hover:-translate-y-0.5"
        >
          🚀 Run Pipeline
        </button>
        <button
          onClick={fetchReports}
          disabled={loading}
          className="flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white px-6 py-3 rounded-xl disabled:opacity-50 transition-all shadow-md hover:shadow-lg font-medium transform hover:-translate-y-0.5"
        >
          📊 Load Reports
        </button>
        <button
          onClick={exportCSV}
          disabled={loading}
          className="flex items-center gap-2 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white px-6 py-3 rounded-xl disabled:opacity-50 transition-all shadow-md hover:shadow-lg font-medium transform hover:-translate-y-0.5"
        >
          📁 Export CSV
        </button>
      </div>

      {/* TABS */}
      <div className="flex gap-2 mb-6 border-b border-gray-200 overflow-x-auto">
        <button
          onClick={() => setActiveTab("pipeline")}
          className={`px-6 py-3 font-semibold transition-all whitespace-nowrap ${
            activeTab === "pipeline"
              ? "text-indigo-600 border-b-2 border-indigo-600"
              : "text-gray-500 hover:text-gray-800 hover:bg-gray-50"
          }`}
        >
          Pipeline Data
        </button>
        <button
          onClick={() => setActiveTab("reports")}
          className={`px-6 py-3 font-semibold transition-all whitespace-nowrap ${
            activeTab === "reports"
              ? "text-indigo-600 border-b-2 border-indigo-600"
              : "text-gray-500 hover:text-gray-800 hover:bg-gray-50"
          }`}
        >
          Analytics Reports
        </button>
        <button
          onClick={() => setActiveTab("sql")}
          className={`px-6 py-3 font-semibold transition-all whitespace-nowrap ${
            activeTab === "sql"
              ? "text-indigo-600 border-b-2 border-indigo-600"
              : "text-gray-500 hover:text-gray-800 hover:bg-gray-50"
          }`}
        >
          SQL Query Results
        </button>
      </div>

      {/* LOADING INDICATOR */}
      {loading && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl flex items-center gap-3 animate-pulse">
          <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="font-medium">Processing request... This may take a moment for large datasets.</span>
        </div>
      )}

      {/* MESSAGE */}
      {message && !loading && (
        <div className="mb-6 p-4 bg-white shadow-sm border border-gray-100 rounded-xl text-gray-700 font-medium animate-fade-in">
          {message}
        </div>
      )}

      {/* ================= PIPELINE VIEW ================= */}
      {activeTab === "pipeline" && sampleData && (
        <div className="mb-10 animate-fade-in">
          <h2 className="text-2xl font-bold mb-6 text-gray-800 flex items-center gap-2">
            📊 Sample Data Preview
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* PATENTS */}
            <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <h3 className="font-bold mb-4 text-blue-600 flex items-center gap-2">
                📄 Patents ({sampleData.patents?.length || 0})
              </h3>
              <div className="max-h-96 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                {sampleData.patents?.length > 0 ? (
                  sampleData.patents.map((p, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-xs font-bold text-gray-700">{p.patent_id}</p>
                      <p className="text-sm text-gray-600 mt-1">{p.title?.substring(0, 50)}...</p>
                      {p.year && <p className="text-xs text-blue-500 mt-2 font-medium">Year: {p.year}</p>}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-sm italic">No patents found</p>
                )}
              </div>
            </div>

            {/* INVENTORS */}
            <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <h3 className="font-bold mb-4 text-green-600 flex items-center gap-2">
                👥 Inventors ({sampleData.inventors?.length || 0})
              </h3>
              <div className="max-h-96 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                {sampleData.inventors?.length > 0 ? (
                  sampleData.inventors.map((inv, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm font-bold text-gray-800">{inv.name}</p>
                      <div className="flex justify-between mt-2">
                        <span className="text-xs text-gray-500 font-mono">{inv.inventor_id}</span>
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">{inv.country}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-sm italic">No inventors found</p>
                )}
              </div>
            </div>

            {/* COMPANIES */}
            <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <h3 className="font-bold mb-4 text-rose-600 flex items-center gap-2">
                🏢 Companies ({sampleData.companies?.length || 0})
              </h3>
              <div className="max-h-96 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                {sampleData.companies?.length > 0 ? (
                  sampleData.companies.map((comp, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm font-bold text-gray-800">{comp.name}</p>
                      <p className="text-xs text-gray-500 font-mono mt-2">{comp.company_id}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-sm italic">No companies found</p>
                )}
              </div>
            </div>

            {/* RELATIONSHIPS */}
            <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <h3 className="font-bold mb-4 text-purple-600 flex items-center gap-2">
                🔗 Relationships ({sampleData.relationships?.length || 0})
              </h3>
              <div className="max-h-96 overflow-y-auto pr-2 space-y-2 custom-scrollbar">
                {sampleData.relationships?.length > 0 ? (
                  sampleData.relationships.map((r, i) => (
                    <div key={i} className="p-2 bg-gray-50 rounded text-xs font-mono">
                      <span className="text-blue-600">{r.patent_id}</span> → 
                      {r.inventor_id ? <span className="text-green-600 ml-1">{r.inventor_id}</span> : ''}
                      {r.company_id ? <span className="text-rose-600 ml-1">{r.company_id}</span> : ''}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-sm italic">No relationships found</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================= REPORT VIEW ================= */}
      {activeTab === "reports" && report && report.status === "success" && (
        <div className="space-y-8 animate-fade-in">
          {/* STATS OVERVIEW */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <p className="text-sm text-gray-500 font-medium uppercase tracking-wider mb-1">Total Patents</p>
              <p className="text-3xl font-extrabold text-indigo-600">{report.total_patents?.toLocaleString() || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <p className="text-sm text-gray-500 font-medium uppercase tracking-wider mb-1">Total Companies</p>
              <p className="text-3xl font-extrabold text-rose-500">{report.total_companies?.toLocaleString() || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <p className="text-sm text-gray-500 font-medium uppercase tracking-wider mb-1">Top Inventors</p>
              <p className="text-3xl font-extrabold text-emerald-500">{report.top_inventors?.length || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <p className="text-sm text-gray-500 font-medium uppercase tracking-wider mb-1">Countries</p>
              <p className="text-3xl font-extrabold text-amber-500">{report.countries?.length || 0}</p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* TOP COMPANIES */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h2 className="font-bold mb-6 text-gray-800 text-xl border-b pb-3">
                🏢 Q2: Top Companies
              </h2>
              <div className="space-y-4">
                {report.top_companies?.length > 0 ? (
                  report.top_companies.map((comp, i) => (
                    <div key={i} className="flex items-center group">
                      <div className="w-8 h-8 flex-shrink-0 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center font-bold text-sm mr-4 group-hover:bg-rose-600 group-hover:text-white transition-colors">
                        {i+1}
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between items-end mb-1">
                          <span className="font-medium text-gray-800 truncate pr-4">{comp.name}</span>
                          <span className="font-bold text-rose-600">{comp.patent_count}</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-1.5">
                          <div className="bg-rose-500 h-1.5 rounded-full" style={{ width: `${(comp.patent_count / report.top_companies[0].patent_count) * 100}%` }}></div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-sm italic">No data available</p>
                )}
              </div>
            </div>

            {/* TOP INVENTORS */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h2 className="font-bold mb-6 text-gray-800 text-xl border-b pb-3">
                🏆 Q1: Top Inventors
              </h2>
              <div className="space-y-4">
                {report.top_inventors?.length > 0 ? (
                  report.top_inventors.map((inv, i) => (
                    <div key={i} className="flex items-center group">
                      <div className="w-8 h-8 flex-shrink-0 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-sm mr-4 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                        {i+1}
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between items-end mb-1">
                          <span className="font-medium text-gray-800 truncate pr-4">{inv.name}</span>
                          <span className="font-bold text-blue-600">{inv.patent_count}</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-1.5">
                          <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${(inv.patent_count / report.top_inventors[0].patent_count) * 100}%` }}></div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-sm italic">No data available</p>
                )}
              </div>
            </div>

            {/* TRENDS */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h2 className="font-bold mb-6 text-gray-800 text-xl border-b pb-3">
                📅 Q4: Patent Trends Over Time
              </h2>
              <div className="space-y-3 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
                {report.trends?.length > 0 ? (
                  (() => {
                    const maxTotal = Math.max(...report.trends.map(t => t.total || 0));
                    return report.trends.map((t, i) => (
                      <div key={i} className="flex items-center gap-4 text-sm">
                        <span className="w-12 font-bold text-gray-600">{t.year || 'N/A'}</span>
                        <div className="flex-1 bg-gray-100 rounded-r-md h-6 flex items-center">
                          <div 
                            className="bg-gradient-to-r from-indigo-400 to-indigo-600 h-full rounded-r-md shadow-sm" 
                            style={{ width: `${maxTotal ? (t.total / maxTotal) * 100 : 0}%`, minWidth: '4px' }}
                          />
                        </div>
                        <span className="w-12 text-right font-medium text-indigo-700">{t.total}</span>
                      </div>
                    ));
                  })()
                ) : (
                  <p className="text-gray-400 text-sm italic">No trends available</p>
                )}
              </div>
            </div>

            {/* COUNTRIES */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h2 className="font-bold mb-6 text-gray-800 text-xl border-b pb-3">
                🌍 Q3: Top Countries
              </h2>
              <div className="grid grid-cols-2 gap-4">
                {report.countries?.length > 0 ? (
                  report.countries.map((c, i) => (
                    <div key={i} className="bg-gray-50 p-4 rounded-xl flex flex-col justify-center items-center text-center border border-gray-100 hover:border-emerald-200 hover:bg-emerald-50 transition-colors">
                      <span className="text-2xl font-black text-gray-800 mb-1">{c.country}</span>
                      <span className="text-sm font-medium text-emerald-600">{c.total} patents</span>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-sm italic col-span-2">No data available</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================= SQL QUERIES VIEW ================= */}
      {activeTab === "sql" && report && report.status === "success" && (
        <div className="space-y-8 animate-fade-in">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="font-bold mb-4 text-gray-800 text-xl border-b pb-3 flex justify-between items-center">
              <span>🔗 Q5: JOIN Query</span>
              <span className="text-sm font-normal text-gray-500 bg-gray-100 px-3 py-1 rounded-full">Patents + Inventors + Companies</span>
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-600 uppercase tracking-wider text-xs font-semibold">
                  <tr>
                    <th className="px-4 py-3 rounded-tl-lg">Patent ID</th>
                    <th className="px-4 py-3">Title</th>
                    <th className="px-4 py-3">Inventor</th>
                    <th className="px-4 py-3">Company</th>
                    <th className="px-4 py-3">Country</th>
                    <th className="px-4 py-3 rounded-tr-lg">Year</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {report.joined_data?.slice(0, 15).map((row, i) => (
                    <tr key={i} className="hover:bg-blue-50/50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-blue-600">{row.patent_id}</td>
                      <td className="px-4 py-3 text-gray-800 font-medium">{row.title?.substring(0, 40)}...</td>
                      <td className="px-4 py-3 text-gray-600">{row.inventor_name || '-'}</td>
                      <td className="px-4 py-3 text-rose-600 font-medium">{row.company_name || '-'}</td>
                      <td className="px-4 py-3 text-gray-500">{row.country || '-'}</td>
                      <td className="px-4 py-3 text-gray-500">{row.year || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h2 className="font-bold mb-4 text-gray-800 text-xl border-b pb-3 flex justify-between items-center">
                <span>📊 Q6: CTE Query</span>
                <span className="text-sm font-normal text-gray-500 bg-gray-100 px-3 py-1 rounded-full">WITH statement</span>
              </h2>
              <div className="space-y-3">
                {report.cte_results?.map((row, i) => (
                  <div key={i} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <span className="font-bold text-gray-700">{row.country}</span>
                    <span className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-sm font-semibold">{row.total} patents</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h2 className="font-bold mb-4 text-gray-800 text-xl border-b pb-3 flex justify-between items-center">
                <span>🎯 Q7: Ranking Query</span>
                <span className="text-sm font-normal text-gray-500 bg-gray-100 px-3 py-1 rounded-full">Window Functions</span>
              </h2>
              <div className="space-y-3 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
                {report.ranked_inventors?.map((inv, i) => (
                  <div key={i} className="flex flex-col p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-gray-800">{inv.name}</span>
                      <span className="text-orange-600 font-bold">{inv.patent_count} patents</span>
                    </div>
                    <div className="flex gap-3 text-xs text-gray-500">
                      <span className="bg-white px-2 py-1 rounded shadow-sm border border-gray-200">Rank: #{inv.rank_position}</span>
                      <span className="bg-white px-2 py-1 rounded shadow-sm border border-gray-200">Dense Rank: #{inv.dense_rank}</span>
                      <span className="bg-white px-2 py-1 rounded shadow-sm border border-gray-200">{inv.country}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* EMPTY STATE */}
      {!report && !sampleData && !loading && (
        <div className="text-center mt-20 text-gray-500 bg-white p-10 rounded-2xl shadow-sm border border-gray-100 max-w-2xl mx-auto animate-fade-in">
          <div className="text-5xl mb-4">🚀</div>
          <h3 className="text-xl font-bold text-gray-800 mb-2">Ready to analyze patent data</h3>
          <p className="mb-6">Click <b>Run Pipeline</b> to parse and load the latest TSV files, or <b>Load Reports</b> to view existing analytics from the database.</p>
          <button 
            onClick={runPipeline}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-xl font-medium transition-colors shadow-md hover:shadow-lg"
          >
            Start Pipeline
          </button>
        </div>
      )}
    </div>
  );
}

export default Home;