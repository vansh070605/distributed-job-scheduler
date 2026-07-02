import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  Layers,
  Play,
  Cpu,
  Trash2,
  LogOut,
  FolderKanban,
  Building2,
  ChevronDown
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const {
    user,
    organizations,
    projects,
    activeOrg,
    activeProject,
    setActiveOrg,
    setActiveProject,
    logout
  } = useAuth();

  const [orgDropdown, setOrgDropdown] = useState(false);
  const [projDropdown, setProjDropdown] = useState(false);

  const menuItems = [
    { name: "Dashboard", path: "/", icon: LayoutDashboard },
    { name: "Queues", path: "/queues", icon: Layers },
    { name: "Jobs", path: "/jobs", icon: Play },
    { name: "Workers", path: "/workers", icon: Cpu },
    { name: "Dead Letter Queue", path: "/dlq", icon: Trash2 },
  ];

  return (
    <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen">
      {/* Brand Logo */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
        <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center font-bold text-white shadow-lg shadow-brand-500/25">
          Ω
        </div>
        <div>
          <h1 className="font-bold text-sm leading-tight text-white">Antigravity</h1>
          <span className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">Job Scheduler</span>
        </div>
      </div>

      {/* Orgs and Projects Pickers */}
      <div className="p-4 border-b border-slate-800 flex flex-col gap-3">
        {/* Org Selector */}
        <div className="relative">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Organization</label>
          <button
            onClick={() => setOrgDropdown(!orgDropdown)}
            className="w-full flex items-center justify-between bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-semibold text-slate-200 hover:border-slate-700 transition"
          >
            <span className="flex items-center gap-2 truncate">
              <Building2 size={14} className="text-slate-400" />
              {activeOrg?.name || "Select Org"}
            </span>
            <ChevronDown size={14} className="text-slate-400" />
          </button>
          {orgDropdown && (
            <div className="absolute left-0 right-0 mt-1 bg-slate-950 border border-slate-850 rounded-lg shadow-2xl z-50 py-1 overflow-hidden">
              {organizations.map((org) => (
                <button
                  key={org.id}
                  onClick={() => {
                    setActiveOrg(org);
                    setOrgDropdown(false);
                  }}
                  className="w-full text-left px-3 py-2 text-xs hover:bg-slate-900 text-slate-300 font-medium transition"
                >
                  {org.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Project Selector */}
        <div className="relative">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Project</label>
          <button
            onClick={() => setProjDropdown(!projDropdown)}
            className="w-full flex items-center justify-between bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-semibold text-slate-200 hover:border-slate-700 transition"
          >
            <span className="flex items-center gap-2 truncate">
              <FolderKanban size={14} className="text-slate-400" />
              {activeProject?.name || "No Projects"}
            </span>
            <ChevronDown size={14} className="text-slate-400" />
          </button>
          {projDropdown && (
            <div className="absolute left-0 right-0 mt-1 bg-slate-950 border border-slate-850 rounded-lg shadow-2xl z-50 py-1 overflow-hidden">
              {projects.map((proj) => (
                <button
                  key={proj.id}
                  onClick={() => {
                    setActiveProject(proj);
                    setProjDropdown(false);
                  }}
                  className="w-full text-left px-3 py-2 text-xs hover:bg-slate-900 text-slate-300 font-medium transition"
                >
                  {proj.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Menu Links */}
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition ${
                isActive
                  ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent"
              }`}
            >
              <Icon size={16} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User Info & Logout */}
      <div className="p-4 border-t border-slate-800 bg-slate-950 flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-brand-400">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-xs font-bold text-slate-200 truncate">{user?.full_name}</h4>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{user?.role}</span>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 border border-slate-800 hover:border-red-500/30 hover:bg-red-500/5 hover:text-red-400 transition rounded-lg py-2 text-xs font-semibold text-slate-400"
        >
          <LogOut size={14} />
          Sign Out
        </button>
      </div>
    </div>
  );
};
