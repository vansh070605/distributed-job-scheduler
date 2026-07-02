import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from "recharts";
import { Layers, Play, CheckCircle, AlertTriangle, RefreshCcw, Building2 } from "lucide-react";

interface Metric {
  queue_id: string;
  queued_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  avg_execution_time_ms: number;
  throughput_1h: number;
  success_rate: number;
}

interface Queue {
  id: string;
  name: string;
}

export const Dashboard: React.FC = () => {
  const { activeProject } = useAuth();
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [queues, setQueues] = useState<Queue[]>([]);
  const [loading, setLoading] = useState(false);
  const [setupLoading, setSetupLoading] = useState(false);

  const fetchMetrics = async () => {
    if (!activeProject) return;
    setLoading(true);
    try {
      const qRes = await api.get<Queue[]>(`/projects/${activeProject.id}/queues`);
      setQueues(qRes.data);

      const res = await api.get<Metric[]>(`/metrics/projects/${activeProject.id}`);
      setMetrics(res.data);
    } catch (err) {
      console.error("Failed to load metrics", err);
    } finally {
      setLoading(false);
    }
  };

  const handleBootstrap = async () => {
    // Helper to bootstrap a test project structure easily
    setSetupLoading(true);
    try {
      // 1. Create default org if not exists
      let orgId = "";
      try {
        const orgRes = await api.post("/orgs/", { name: "Default Organization", slug: "default-org" });
        orgId = orgRes.data.id;
      } catch {
        const listRes = await api.get<any[]>("/orgs/");
        orgId = listRes.data[0]?.id;
      }

      // 2. Create project
      let projId = "";
      try {
        const projRes = await api.post(`/projects/?org_id=${orgId}`, { name: "Default Project", slug: "default-project" });
        projId = projRes.data.id;
      } catch {
        const listRes = await api.get<any[]>(`/projects/?org_id=${orgId}`);
        projId = listRes.data[0]?.id;
      }

      // 3. Create default queue
      try {
        await api.post(`/projects/${projId}/queues`, {
          name: "default-queue",
          priority: 1,
          concurrency: 5,
        });
      } catch {}

      window.location.reload();
    } catch (err) {
      console.error("Failed to bootstrap system structures", err);
    } finally {
      setSetupLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, [activeProject]);

  // Aggregate metrics
  const totalQueues = queues.length;
  const totalQueued = metrics.reduce((acc, m) => acc + m.queued_jobs, 0);
  const totalRunning = metrics.reduce((acc, m) => acc + m.running_jobs, 0);
  const totalCompleted = metrics.reduce((acc, m) => acc + m.completed_jobs, 0);
  const totalFailed = metrics.reduce((acc, m) => acc + m.failed_jobs, 0);

  const pieData = [
    { name: "Queued", value: totalQueued, color: "#7abeff" },
    { name: "Running", value: totalRunning, color: "#339eff" },
    { name: "Completed", value: totalCompleted, color: "#10b981" },
    { name: "Failed", value: totalFailed, color: "#ef4444" },
  ].filter(p => p.value > 0);

  // Prepare chart details
  const barChartData = metrics.map((m) => {
    const queueName = queues.find((q) => q.id === m.queue_id)?.name || m.queue_id.substring(0, 8);
    return {
      name: queueName,
      Queued: m.queued_jobs,
      Running: m.running_jobs,
      Completed: m.completed_jobs,
      Failed: m.failed_jobs,
    };
  });

  return (
    <div className="flex flex-col gap-8 w-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-900 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white">System Dashboard</h2>
          <p className="text-slate-400 text-xs font-semibold mt-1">Real-time scheduling performance updates</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="flex items-center gap-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-300 transition"
          >
            <RefreshCcw size={14} className={loading ? "animate-spin" : ""} />
            Sync
          </button>
        </div>
      </div>

      {!activeProject ? (
        <div className="flex flex-col items-center justify-center py-20 bg-slate-900/50 border border-slate-800 rounded-xl p-8 gap-4">
          <div className="w-12 h-12 bg-brand-500/10 rounded-lg flex items-center justify-center">
            <Building2 size={24} className="text-brand-400" />
          </div>
          <div className="text-center">
            <h3 className="text-sm font-bold text-white">Initialize Project Structure</h3>
            <p className="text-xs text-slate-400 max-w-sm mt-1">No active organizations or projects were detected. Boostrap a default workspace environment to test runs.</p>
          </div>
          <button
            onClick={handleBootstrap}
            disabled={setupLoading}
            className="bg-brand-500 hover:bg-brand-600 px-4 py-2 rounded-lg text-xs font-bold text-white transition mt-2 shadow-lg shadow-brand-500/20"
          >
            {setupLoading ? "BOOTSTRAPPING..." : "BOOTSTRAP TEST ENVIRONMENT"}
          </button>
        </div>
      ) : (
        <>
          {/* Metrics summary cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl glass flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Queues Registered</span>
                <span className="text-2xl font-bold text-white mt-2 block">{totalQueues}</span>
              </div>
              <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg"><Layers size={20} /></div>
            </div>

            <div className="p-5 rounded-xl glass flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Pending / Running</span>
                <span className="text-2xl font-bold text-brand-400 mt-2 block">{totalQueued + totalRunning}</span>
              </div>
              <div className="p-3 bg-brand-500/10 text-brand-400 rounded-lg"><Play size={20} /></div>
            </div>

            <div className="p-5 rounded-xl glass flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Successful Jobs</span>
                <span className="text-2xl font-bold text-emerald-400 mt-2 block">{totalCompleted}</span>
              </div>
              <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg"><CheckCircle size={20} /></div>
            </div>

            <div className="p-5 rounded-xl glass flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Failed Executions</span>
                <span className="text-2xl font-bold text-rose-400 mt-2 block">{totalFailed}</span>
              </div>
              <div className="p-3 bg-rose-500/10 text-rose-400 rounded-lg"><AlertTriangle size={20} /></div>
            </div>
          </div>

          {/* Charts area */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Bar Chart of Queues */}
            <div className="lg:col-span-2 p-6 rounded-xl glass flex flex-col gap-4">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Queue Workload Allocations</h3>
              <div className="h-80 w-full">
                {barChartData.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-slate-500 font-semibold">No metrics logs collected yet.</div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={barChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                      <YAxis stroke="#64748b" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc", borderRadius: "8px", fontSize: "12px" }} />
                      <Legend wrapperStyle={{ fontSize: "11px", fontWeight: "600" }} />
                      <Bar dataKey="Queued" fill="#f59e0b" />
                      <Bar dataKey="Running" fill="#3b82f6" />
                      <Bar dataKey="Completed" fill="#10b981" />
                      <Bar dataKey="Failed" fill="#ef4444" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* Pie Chart of States */}
            <div className="p-6 rounded-xl glass flex flex-col gap-4">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Overall Job Status Ratios</h3>
              <div className="h-80 w-full flex items-center justify-center relative">
                {pieData.length === 0 ? (
                  <div className="text-xs text-slate-500 font-semibold">No active jobs to trace.</div>
                ) : (
                  <>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={90}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {pieData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc", borderRadius: "8px", fontSize: "12px" }} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="absolute flex flex-col items-center justify-center">
                      <span className="text-2xl font-bold text-white">
                        {totalQueued + totalRunning + totalCompleted + totalFailed}
                      </span>
                      <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Total Runs</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
