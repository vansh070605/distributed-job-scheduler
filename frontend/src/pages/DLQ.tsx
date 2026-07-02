import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
import { Trash2, RefreshCw, RefreshCcw, HelpCircle } from "lucide-react";

interface DLQItem {
  id: string;
  job_id: string;
  reason: string;
  failed_at: string;
  original_payload: any;
}

interface Job {
  id: string;
  name: string;
}

export const DLQ: React.FC = () => {
  const { activeProject } = useAuth();
  const [dlqItems, setDlqItems] = useState<DLQItem[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchDLQ = async () => {
    if (!activeProject) return;
    setLoading(true);
    try {
      // Fetch all project jobs to map names
      const jobRes = await api.get<Job[]>(`/projects/${activeProject.id}/jobs`);
      setJobs(jobRes.data);

      const res = await api.get<DLQItem[]>(`/projects/${activeProject.id}/dlq`);
      setDlqItems(res.data);
    } catch (err) {
      console.error("Failed to load DLQ records", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (item: DLQItem) => {
    if (!activeProject) return;
    setActionLoading(item.id);
    try {
      await api.post(`/projects/${activeProject.id}/dlq/${item.id}/retry`);
      fetchDLQ();
    } catch (err) {
      alert("Failed to re-enqueue job from DLQ.");
    } finally {
      setActionLoading(null);
    }
  };

  useEffect(() => {
    fetchDLQ();
  }, [activeProject]);

  return (
    <div className="flex flex-col gap-8 w-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-900 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white font-sans flex items-center gap-2">
            <Trash2 className="text-rose-500" size={22} />
            Dead Letter Queue (DLQ)
          </h2>
          <p className="text-slate-400 text-xs font-semibold mt-1">Audit failed jobs and re-run executions</p>
        </div>
        <div>
          <button
            onClick={fetchDLQ}
            disabled={loading}
            className="flex items-center gap-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-300 transition"
          >
            <RefreshCcw size={14} className={loading ? "animate-spin" : ""} />
            Sync
          </button>
        </div>
      </div>

      {/* DLQ List */}
      <div className="glass rounded-xl overflow-hidden">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider bg-slate-900/40">
              <th className="p-4">Job Info</th>
              <th className="p-4">Failure Reason</th>
              <th className="p-4">Payload Parameters</th>
              <th className="p-4">Failed Time</th>
              <th className="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs font-medium text-slate-350">
            {dlqItems.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-8 text-center text-slate-500 font-semibold">
                  Excellent! The Dead Letter Queue is currently empty.
                </td>
              </tr>
            ) : (
              dlqItems.map((item) => {
                const job = jobs.find(j => j.id === item.job_id);
                return (
                  <tr key={item.id} className="hover:bg-slate-900/10 transition align-top">
                    <td className="p-4">
                      <h4 className="font-bold text-white">{job?.name || "Job Run"}</h4>
                      <span className="text-[9px] text-slate-500 block mt-0.5">Job: {item.job_id.substring(0, 13)}...</span>
                    </td>
                    <td className="p-4 max-w-[250px]">
                      <span className="text-red-400 font-mono text-[10px] whitespace-pre-wrap leading-relaxed block">
                        {item.reason}
                      </span>
                    </td>
                    <td className="p-4">
                      <pre className="p-2.5 bg-slate-950/60 border border-slate-850 rounded-lg text-[9px] font-mono text-indigo-350 overflow-x-auto max-w-[180px]">
                        {JSON.stringify(item.original_payload, null, 2)}
                      </pre>
                    </td>
                    <td className="p-4 text-slate-400">
                      {new Date(item.failed_at).toLocaleString()}
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => handleRetry(item)}
                        disabled={actionLoading === item.id}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold bg-emerald-500/15 border border-emerald-500/25 hover:bg-emerald-500/20 text-emerald-400 transition"
                      >
                        <RefreshCw size={10} className={actionLoading === item.id ? "animate-spin" : ""} />
                        {actionLoading === item.id ? "Retrying..." : "Re-enqueue"}
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
