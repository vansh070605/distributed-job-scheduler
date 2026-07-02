import React, { useEffect, useState } from "react";
import api from "../services/api";
import { RefreshCcw, Cpu, Wifi, WifiOff } from "lucide-react";

interface QueueAssignment {
  queue_id: string;
}

interface Worker {
  id: string;
  hostname: string | null;
  status: string;
  concurrency: number;
  last_heartbeat: string;
  created_at: string;
  queue_assignments: QueueAssignment[];
}

interface Queue {
  id: string;
  name: string;
}

export const Workers: React.FC = () => {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [queues, setQueues] = useState<Queue[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      // For simple queue lookup, we'll fetch assignments.
      // To map assignments to names, we can look up project queues
      const listRes = await api.get<any[]>("/orgs/");
      if (listRes.data.length > 0) {
        const orgId = listRes.data[0].id;
        const projRes = await api.get<any[]>(`/projects?org_id=${orgId}`);
        if (projRes.data.length > 0) {
          const queuesRes = await api.get<Queue[]>(`/projects/${projRes.data[0].id}/queues`);
          setQueues(queuesRes.data);
        }
      }

      const res = await api.get<Worker[]>("/workers/");
      setWorkers(res.data);
    } catch (err) {
      console.error("Failed to load workers list", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col gap-8 w-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-900 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Active Workers</h2>
          <p className="text-slate-400 text-xs font-semibold mt-1">Monitor distributed node execution pools</p>
        </div>
        <div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-300 transition"
          >
            <RefreshCcw size={14} className={loading ? "animate-spin" : ""} />
            Sync
          </button>
        </div>
      </div>

      {/* Workers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workers.length === 0 ? (
          <div className="col-span-full py-16 text-center text-slate-500 font-semibold border border-dashed border-slate-850 rounded-xl">
            No workers currently registered. Start a worker node to connect.
          </div>
        ) : (
          workers.map((worker) => {
            const isOnline = worker.status === "active" && (new Date().getTime() - new Date(worker.last_heartbeat).getTime()) < 30000;
            return (
              <div key={worker.id} className="p-6 rounded-xl glass flex flex-col gap-4 relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-brand-500 to-indigo-500"></div>

                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-brand-500/10 text-brand-400 rounded-lg">
                      <Cpu size={20} />
                    </div>
                    <div>
                      <h3 className="text-xs font-bold text-white truncate max-w-[150px]" title={worker.id}>
                        {worker.id.substring(0, 16)}...
                      </h3>
                      <span className="text-[10px] text-slate-500 block font-semibold mt-0.5">{worker.hostname || "unknown"}</span>
                    </div>
                  </div>
                  <span className={`flex items-center gap-1 text-[9px] font-bold uppercase tracking-wide px-2 py-1 rounded-full ${
                    isOnline ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                  }`}>
                    {isOnline ? <Wifi size={10} /> : <WifiOff size={10} />}
                    {isOnline ? "online" : "offline"}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 bg-slate-950 p-3 rounded-lg border border-slate-850 text-xs">
                  <div>
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider block">Concurrency</span>
                    <span className="font-bold text-slate-200 mt-0.5 block">{worker.concurrency} threads</span>
                  </div>
                  <div>
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider block">Last Heartbeat</span>
                    <span className="font-bold text-slate-350 mt-0.5 block">
                      {new Date(worker.last_heartbeat).toLocaleTimeString()}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block mb-2">Assigned Queues</span>
                  {worker.queue_assignments.length === 0 ? (
                    <span className="text-[10px] text-slate-500 italic block font-semibold">No assignments</span>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {worker.queue_assignments.map((asg) => {
                        const qName = queues.find(q => q.id === asg.queue_id)?.name || asg.queue_id.substring(0, 8);
                        return (
                          <span key={asg.queue_id} className="bg-slate-900 border border-slate-800 rounded px-2 py-0.5 text-[9px] font-semibold text-slate-300">
                            {qName}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
