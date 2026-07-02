import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
import { Plus, Terminal, RefreshCcw, Search, ChevronRight, X, Clock, HelpCircle } from "lucide-react";

interface Queue {
  id: string;
  name: string;
}

interface Job {
  id: string;
  queue_id: string;
  name: string;
  payload: any;
  status: string;
  priority_override: number | null;
  retry_count: number;
  max_retries: number;
  cron_expression: string | null;
  next_run_at: string | null;
  idempotency_key: string | null;
  last_worker_id: string | null;
  created_at: string;
}

interface JobExecution {
  id: string;
  worker_id: string | null;
  status: string;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
  duration: number | null;
}

interface JobLog {
  id: string;
  level: string;
  message: string;
  timestamp: string;
}

export const Jobs: React.FC = () => {
  const { activeProject } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [queues, setQueues] = useState<Queue[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedQueue, setSelectedQueue] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");

  // Create Job form states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [jobName, setJobName] = useState("");
  const [targetQueueId, setTargetQueueId] = useState("");
  const [jobPayload, setJobPayload] = useState('{\n  "duration": 2,\n  "should_fail": false\n}');
  const [priorityOverride, setPriorityOverride] = useState("");
  const [maxRetries, setMaxRetries] = useState(3);
  const [delaySeconds, setDelaySeconds] = useState("");
  const [cronExpression, setCronExpression] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState("");

  // Detailed Drawer states
  const [inspectJob, setInspectJob] = useState<Job | null>(null);
  const [executions, setExecutions] = useState<JobExecution[]>([]);
  const [logs, setLogs] = useState<JobLog[]>([]);
  const [drawerLoading, setDrawerLoading] = useState(false);

  const fetchJobs = async () => {
    if (!activeProject) return;
    setLoading(true);
    try {
      const qRes = await api.get<Queue[]>(`/projects/${activeProject.id}/queues`);
      setQueues(qRes.data);
      if (qRes.data.length > 0 && !targetQueueId) {
        setTargetQueueId(qRes.data[0].id);
      }

      let url = `/projects/${activeProject.id}/jobs?`;
      if (selectedQueue) url += `queue_id=${selectedQueue}&`;
      if (selectedStatus) url += `status=${selectedStatus}&`;
      if (searchQuery) url += `search=${searchQuery}&`;

      const jRes = await api.get<Job[]>(url);
      setJobs(jRes.data);
    } catch (err) {
      console.error("Failed to fetch jobs list", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    try {
      let parsedPayload = {};
      try {
        parsedPayload = JSON.parse(jobPayload);
      } catch {
        alert("Invalid JSON payload format");
        return;
      }

      await api.post(`/projects/${activeProject.id}/jobs`, {
        queue_id: targetQueueId,
        name: jobName,
        payload: parsedPayload,
        priority_override: priorityOverride ? parseInt(priorityOverride) : null,
        max_retries: maxRetries,
        delay_seconds: delaySeconds ? parseInt(delaySeconds) : null,
        cron_expression: cronExpression || null,
        idempotency_key: idempotencyKey || null,
      });

      setShowCreateModal(false);
      setJobName("");
      setPriorityOverride("");
      setDelaySeconds("");
      setCronExpression("");
      setIdempotencyKey("");
      fetchJobs();
    } catch (err) {
      alert("Failed to submit job.");
    }
  };

  const handleInspectJob = async (job: Job) => {
    setInspectJob(job);
    setDrawerLoading(true);
    try {
      const execRes = await api.get<JobExecution[]>(`/projects/${activeProject?.id}/jobs/${job.id}/executions`);
      setExecutions(execRes.data);

      const logRes = await api.get<JobLog[]>(`/projects/${activeProject?.id}/jobs/${job.id}/logs`);
      setLogs(logRes.data);
    } catch (err) {
      console.error("Failed to load details for job", err);
    } finally {
      setDrawerLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [activeProject, selectedQueue, selectedStatus]);

  return (
    <div className="flex flex-col gap-8 w-full relative">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-900 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Submitted Jobs</h2>
          <p className="text-slate-400 text-xs font-semibold mt-1">Audit execution runs and dynamic worker logs</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchJobs}
            className="flex items-center gap-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-300 transition"
          >
            <RefreshCcw size={14} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 rounded-lg px-3.5 py-2 text-xs font-bold text-white transition shadow-lg shadow-brand-500/25"
          >
            <Plus size={14} />
            Submit Job
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-wrap gap-4 items-center bg-slate-900/35 border border-slate-800/80 p-4 rounded-xl">
        <div className="flex-1 min-w-[200px] relative">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search by job name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && fetchJobs()}
            className="w-full bg-slate-950 border border-slate-850 focus:border-brand-500 outline-none rounded-lg pl-9 pr-3.5 py-2 text-xs text-slate-300 transition"
          />
        </div>

        <select
          value={selectedQueue}
          onChange={(e) => setSelectedQueue(e.target.value)}
          className="bg-slate-950 border border-slate-850 text-slate-300 rounded-lg px-3 py-2 text-xs focus:border-brand-500 outline-none transition"
        >
          <option value="">All Queues</option>
          {queues.map(q => (
            <option key={q.id} value={q.id}>{q.name}</option>
          ))}
        </select>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="bg-slate-950 border border-slate-850 text-slate-300 rounded-lg px-3 py-2 text-xs focus:border-brand-500 outline-none transition"
        >
          <option value="">All Statuses</option>
          <option value="queued">Queued</option>
          <option value="scheduled">Scheduled</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="dlq">DLQ</option>
        </select>
      </div>

      {/* Jobs List */}
      <div className="glass rounded-xl overflow-hidden">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider bg-slate-900/40">
              <th className="p-4">Job Details</th>
              <th className="p-4">Queue</th>
              <th className="p-4">Status</th>
              <th className="p-4">Retry Stats</th>
              <th className="p-4">Scheduled For</th>
              <th className="p-4 text-right">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs font-medium text-slate-300">
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-slate-500 font-semibold">
                  No submitted jobs matching selected filters.
                </td>
              </tr>
            ) : (
              jobs.map((job) => {
                const qName = queues.find(q => q.id === job.queue_id)?.name || "Default";
                const isFailed = job.status === "failed" || job.status === "dlq";
                const isSuccess = job.status === "completed";
                const isRunning = job.status === "running";
                
                return (
                  <tr key={job.id} className="hover:bg-slate-900/20 transition">
                    <td className="p-4">
                      <h4 className="font-bold text-white">{job.name}</h4>
                      <span className="text-[10px] text-slate-500 font-bold block mt-0.5">{job.id}</span>
                    </td>
                    <td className="p-4">{qName}</td>
                    <td className="p-4">
                      <span className={`px-2.5 py-1 rounded-full text-[9px] font-bold tracking-wide uppercase ${
                        isSuccess ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/25" :
                        isFailed ? "bg-red-500/10 text-red-400 border border-red-500/25" :
                        isRunning ? "bg-blue-500/10 text-blue-400 border border-blue-500/25" :
                        "bg-amber-500/10 text-amber-400 border border-amber-500/25"
                      }`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="p-4 text-slate-400">
                      {job.retry_count} / {job.max_retries}
                    </td>
                    <td className="p-4 text-slate-400">
                      {job.next_run_at ? new Date(job.next_run_at).toLocaleString() : "Immediate / Runs"}
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => handleInspectJob(job)}
                        className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition"
                      >
                        <ChevronRight size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Inspect Drawer Panel */}
      {inspectJob && (
        <div className="fixed inset-y-0 right-0 w-[550px] bg-slate-900 border-l border-slate-800 shadow-2xl z-50 flex flex-col h-full transform transition duration-300">
          <div className="h-16 flex items-center justify-between px-6 border-b border-slate-800 bg-slate-950">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Job Inspection</h3>
              <span className="text-[10px] text-slate-500 font-bold block mt-0.5">{inspectJob.id}</span>
            </div>
            <button
              onClick={() => setInspectJob(null)}
              className="p-1 hover:bg-slate-850 rounded-lg text-slate-400 hover:text-white transition"
            >
              <X size={18} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Status & Metadata info */}
            <div className="grid grid-cols-2 gap-4 bg-slate-950 p-4 border border-slate-850 rounded-xl text-xs">
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">State</span>
                <span className="font-bold text-white">{inspectJob.status.toUpperCase()}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Worker Assigned</span>
                <span className="font-bold text-slate-400">{inspectJob.last_worker_id || "None"}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Idempotency Key</span>
                <span className="font-mono text-[10px] text-slate-400">{inspectJob.idempotency_key || "None"}</span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Cron Expression</span>
                <span className="font-bold text-slate-400">{inspectJob.cron_expression || "None"}</span>
              </div>
            </div>

            {/* Payload JSON */}
            <div>
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">Job Payload Parameters</h4>
              <pre className="p-4 bg-slate-950 border border-slate-850 rounded-xl text-[11px] font-mono text-indigo-350 overflow-x-auto">
                {JSON.stringify(inspectJob.payload, null, 2)}
              </pre>
            </div>

            {/* Executions Section */}
            <div>
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-3">Job Run History</h4>
              {executions.length === 0 ? (
                <div className="text-xs text-slate-500 font-semibold py-4 text-center border border-dashed border-slate-850 rounded-xl">
                  No execution runs completed yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {executions.map(exec => (
                    <div key={exec.id} className="p-4 bg-slate-950/60 border border-slate-850/80 rounded-xl flex items-center justify-between text-xs">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${exec.status === 'completed' ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                          <span className="font-bold text-slate-200">{exec.status.toUpperCase()}</span>
                        </div>
                        <span className="text-[10px] text-slate-500 block mt-1">{new Date(exec.started_at).toLocaleString()}</span>
                      </div>
                      <div className="text-right">
                        <span className="font-bold text-slate-300 block">{exec.duration ? `${exec.duration.toFixed(2)}s` : "0.0s"}</span>
                        <span className="text-[9px] text-slate-500 block font-semibold mt-1">Worker: {exec.worker_id || "scheduler"}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Logs console */}
            <div>
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-3">Execution Console Logs</h4>
              {logs.length === 0 ? (
                <div className="text-xs text-slate-500 font-semibold py-4 text-center border border-dashed border-slate-850 rounded-xl">
                  Console logs empty.
                </div>
              ) : (
                <div className="p-4 bg-slate-950 border border-slate-850 rounded-xl font-mono text-[10px] text-slate-350 space-y-2 overflow-x-auto leading-relaxed">
                  {logs.map(log => (
                    <div key={log.id} className="flex gap-2">
                      <span className="text-slate-600">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                      <span className={log.level === 'error' ? 'text-red-400' : log.level === 'warning' ? 'text-amber-400' : 'text-slate-300'}>
                        [{log.level.toUpperCase()}]
                      </span>
                      <span>{log.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create Job Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 w-full max-w-lg flex flex-col gap-4">
            <h3 className="text-sm font-bold text-white">Submit New Job</h3>
            <form onSubmit={handleCreateJob} className="flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Job Name</label>
                  <input
                    type="text"
                    required
                    value={jobName}
                    onChange={(e) => setJobName(e.target.value)}
                    placeholder="e.g. sync-user-profiles"
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Target Queue</label>
                  <select
                    value={targetQueueId}
                    onChange={(e) => setTargetQueueId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  >
                    {queues.map(q => (
                      <option key={q.id} value={q.id}>{q.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Payload JSON Parameter</label>
                <textarea
                  rows={4}
                  required
                  value={jobPayload}
                  onChange={(e) => setJobPayload(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 font-mono outline-none rounded-lg px-3 py-2.5 text-xs text-indigo-250"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Priority Override</label>
                  <input
                    type="number"
                    value={priorityOverride}
                    onChange={(e) => setPriorityOverride(e.target.value)}
                    placeholder="Null"
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Delay Seconds</label>
                  <input
                    type="number"
                    value={delaySeconds}
                    onChange={(e) => setDelaySeconds(e.target.value)}
                    placeholder="Immediate"
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Max Retries</label>
                  <input
                    type="number"
                    required
                    value={maxRetries}
                    onChange={(e) => setMaxRetries(parseInt(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Cron Expression (recurring)</label>
                  <input
                    type="text"
                    value={cronExpression}
                    onChange={(e) => setCronExpression(e.target.value)}
                    placeholder="*/5 * * * *"
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Idempotency Key</label>
                  <input
                    type="text"
                    value={idempotencyKey}
                    onChange={(e) => setIdempotencyKey(e.target.value)}
                    placeholder="Unique transaction hash"
                    className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 outline-none rounded-lg px-3 py-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-800 hover:bg-slate-850 rounded-lg text-xs font-semibold text-slate-400 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-500 hover:bg-brand-600 rounded-lg text-xs font-bold text-white transition"
                >
                  Submit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
