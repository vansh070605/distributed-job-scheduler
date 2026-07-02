import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
import { Plus, Pause, Play, Settings, ShieldAlert, ArrowRight } from "lucide-react";

interface Queue {
  id: string;
  name: string;
  priority: number;
  concurrency: number;
  is_paused: boolean;
  rate_limit: number | null;
  retry_policy_id: string | null;
}

interface RetryPolicy {
  id: string;
  name: string;
  strategy: string;
  max_retries: number;
  base_delay: number;
}

export const Queues: React.FC = () => {
  const { activeProject } = useAuth();
  const [queues, setQueues] = useState<Queue[]>([]);
  const [policies, setPolicies] = useState<RetryPolicy[]>([]);
  const [loading, setLoading] = useState(false);

  // Form states for creating a queue
  const [showQueueModal, setShowQueueModal] = useState(false);
  const [qName, setQName] = useState("");
  const [qPriority, setQPriority] = useState(1);
  const [qConcurrency, setQConcurrency] = useState(10);
  const [qRateLimit, setQRateLimit] = useState("");
  const [qPolicyId, setQPolicyId] = useState("");

  // Form states for creating a retry policy
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [pName, setPName] = useState("");
  const [pStrategy, setPStrategy] = useState("fixed");
  const [pMaxRetries, setPMaxRetries] = useState(3);
  const [pBaseDelay, setPBaseDelay] = useState(5);
  const [pFactor, setPFactor] = useState(2);

  const fetchData = async () => {
    if (!activeProject) return;
    setLoading(true);
    try {
      const qRes = await api.get<Queue[]>(`/projects/${activeProject.id}/queues`);
      setQueues(qRes.data);

      const pRes = await api.get<RetryPolicy[]>(`/projects/${activeProject.id}/retry-policies`);
      setPolicies(pRes.data);
    } catch (err) {
      console.error("Failed to load queues/policies", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateQueue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    try {
      await api.post(`/projects/${activeProject.id}/queues`, {
        name: qName,
        priority: qPriority,
        concurrency: qConcurrency,
        rate_limit: qRateLimit ? parseInt(qRateLimit) : null,
        retry_policy_id: qPolicyId || null,
      });
      setShowQueueModal(false);
      setQName("");
      setQPriority(1);
      setQConcurrency(10);
      setQRateLimit("");
      setQPolicyId("");
      fetchData();
    } catch (err) {
      alert("Failed to create queue. Please check your data.");
    }
  };

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    try {
      await api.post(`/projects/${activeProject.id}/retry-policies`, {
        name: pName,
        strategy: pStrategy,
        max_retries: pMaxRetries,
        base_delay: pBaseDelay,
        backoff_factor: pFactor
      });
      setShowPolicyModal(false);
      setPName("");
      setPStrategy("fixed");
      setPMaxRetries(3);
      setPBaseDelay(5);
      setPFactor(2);
      fetchData();
    } catch (err) {
      alert("Failed to create retry policy.");
    }
  };

  const togglePauseQueue = async (queue: Queue) => {
    if (!activeProject) return;
    try {
      await api.put(`/projects/${activeProject.id}/queues/${queue.id}`, {
        is_paused: !queue.is_paused
      });
      fetchData();
    } catch (err) {
      console.error("Failed to toggle queue execution state", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeProject]);

  return (
    <div className="flex flex-col gap-8 w-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-900 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Dynamic Queues</h2>
          <p className="text-slate-400 text-xs font-semibold mt-1">Configure priorities, concurrency, and retry limits</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowPolicyModal(true)}
            className="flex items-center gap-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg px-3.5 py-2 text-xs font-semibold text-slate-300 transition"
          >
            <ShieldAlert size={14} />
            Add Retry Policy
          </button>
          <button
            onClick={() => setShowQueueModal(true)}
            className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 rounded-lg px-3.5 py-2 text-xs font-bold text-white transition shadow-lg shadow-brand-500/25"
          >
            <Plus size={14} />
            Create Queue
          </button>
        </div>
      </div>

      {/* Queues List */}
      <div className="glass rounded-xl overflow-hidden">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider bg-slate-900/40">
              <th className="p-4">Queue Name</th>
              <th className="p-4">Priority</th>
              <th className="p-4">Concurrency Limit</th>
              <th className="p-4">Rate Limit</th>
              <th className="p-4">Retry Policy</th>
              <th className="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs font-medium text-slate-300">
            {queues.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-slate-500 font-semibold">
                  No active queues found. Create a queue to get started.
                </td>
              </tr>
            ) : (
              queues.map((queue) => {
                const policy = policies.find(p => p.id === queue.retry_policy_id);
                return (
                  <tr key={queue.id} className="hover:bg-slate-900/20 transition">
                    <td className="p-4 font-bold text-white flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${queue.is_paused ? 'bg-amber-500' : 'bg-emerald-500'}`}></div>
                      {queue.name}
                    </td>
                    <td className="p-4">{queue.priority}</td>
                    <td className="p-4">{queue.concurrency} workers</td>
                    <td className="p-4">{queue.rate_limit ? `${queue.rate_limit}/sec` : "Unlimited"}</td>
                    <td className="p-4">
                      {policy ? `${policy.name} (${policy.strategy})` : <span className="text-slate-500">None</span>}
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => togglePauseQueue(queue)}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold border transition ${
                          queue.is_paused
                            ? "bg-emerald-500/10 border-emerald-500/25 text-emerald-400 hover:bg-emerald-500/20"
                            : "bg-amber-500/10 border-amber-500/25 text-amber-400 hover:bg-amber-500/20"
                        }`}
                      >
                        {queue.is_paused ? <Play size={10} /> : <Pause size={10} />}
                        {queue.is_paused ? "Resume" : "Pause"}
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Queue Modal */}
      {showQueueModal && (
        <div className="fixed inset-0 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 w-full max-w-md flex flex-col gap-4">
            <h3 className="text-sm font-bold text-white">Create Queue</h3>
            <form onSubmit={handleCreateQueue} className="flex flex-col gap-4">
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Queue Name</label>
                <input
                  type="text"
                  required
                  value={qName}
                  onChange={(e) => setQName(e.target.value)}
                  placeholder="e.g. data-processing"
                  className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Priority</label>
                  <input
                    type="number"
                    required
                    value={qPriority}
                    onChange={(e) => setQPriority(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Concurrency</label>
                  <input
                    type="number"
                    required
                    value={qConcurrency}
                    onChange={(e) => setQConcurrency(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Rate Limit (jobs/sec, optional)</label>
                <input
                  type="number"
                  value={qRateLimit}
                  onChange={(e) => setQRateLimit(e.target.value)}
                  placeholder="Unlimited"
                  className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Retry Policy (optional)</label>
                <select
                  value={qPolicyId}
                  onChange={(e) => setQPolicyId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                >
                  <option value="">No retry policy</option>
                  {policies.map(p => (
                    <option key={p.id} value={p.id}>{p.name} ({p.strategy})</option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-2 mt-2">
                <button
                  type="button"
                  onClick={() => setShowQueueModal(false)}
                  className="px-4 py-2 border border-slate-800 hover:bg-slate-850 rounded-lg text-xs font-semibold text-slate-400 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-500 hover:bg-brand-600 rounded-lg text-xs font-bold text-white transition"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Retry Policy Modal */}
      {showPolicyModal && (
        <div className="fixed inset-0 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 w-full max-w-md flex flex-col gap-4">
            <h3 className="text-sm font-bold text-white">Create Retry Policy</h3>
            <form onSubmit={handleCreatePolicy} className="flex flex-col gap-4">
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Policy Name</label>
                <input
                  type="text"
                  required
                  value={pName}
                  onChange={(e) => setPName(e.target.value)}
                  placeholder="e.g. exponential-backoff"
                  className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Strategy</label>
                  <select
                    value={pStrategy}
                    onChange={(e) => setPStrategy(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  >
                    <option value="fixed">Fixed Delay</option>
                    <option value="linear">Linear Backoff</option>
                    <option value="exponential">Exponential Backoff</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Max Retries</label>
                  <input
                    type="number"
                    required
                    value={pMaxRetries}
                    onChange={(e) => setPMaxRetries(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Base Delay (sec)</label>
                  <input
                    type="number"
                    required
                    value={pBaseDelay}
                    onChange={(e) => setPBaseDelay(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Backoff Factor</label>
                  <input
                    type="number"
                    required
                    value={pFactor}
                    onChange={(e) => setPFactor(parseInt(e.target.value))}
                    disabled={pStrategy !== "exponential"}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200 disabled:opacity-50"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-2">
                <button
                  type="button"
                  onClick={() => setShowPolicyModal(false)}
                  className="px-4 py-2 border border-slate-800 hover:bg-slate-850 rounded-lg text-xs font-semibold text-slate-400 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-500 hover:bg-brand-600 rounded-lg text-xs font-bold text-white transition"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
