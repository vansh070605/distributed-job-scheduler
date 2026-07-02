import React, { createContext, useContext, useState, useEffect } from "react";
import api from "../services/api";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

interface Organization {
  id: string;
  name: string;
  slug: string;
}

interface Project {
  id: string;
  name: string;
  slug: string;
  org_id: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  organizations: Organization[];
  projects: Project[];
  activeOrg: Organization | null;
  activeProject: Project | null;
  setActiveOrg: (org: Organization) => void;
  setActiveProject: (proj: Project) => void;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshContext: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeOrg, setActiveOrgState] = useState<Organization | null>(null);
  const [activeProject, setActiveProjectState] = useState<Project | null>(null);

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("active_org_id");
    localStorage.removeItem("active_project_id");
    setIsAuthenticated(false);
    setUser(null);
    setOrganizations([]);
    setProjects([]);
    setActiveOrgState(null);
    setActiveProjectState(null);
    setLoading(false);
  };

  const refreshContext = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      logout();
      return;
    }

    try {
      setIsAuthenticated(true);
      // Fetch me
      const meRes = await api.get<User>("/auth/me");
      setUser(meRes.data);

      // Fetch orgs
      const orgsRes = await api.get<Organization[]>("/orgs");
      const orgs = orgsRes.data;
      setOrganizations(orgs);

      if (orgs.length > 0) {
        const savedOrgId = localStorage.getItem("active_org_id");
        const defaultOrg = orgs.find(o => o.id === savedOrgId) || orgs[0];
        setActiveOrgState(defaultOrg);
        localStorage.setItem("active_org_id", defaultOrg.id);

        // Fetch projects for this org
        const projsRes = await api.get<Project[]>(`/projects?org_id=${defaultOrg.id}`);
        const projs = projsRes.data;
        setProjects(projs);

        if (projs.length > 0) {
          const savedProjId = localStorage.getItem("active_project_id");
          const defaultProj = projs.find(p => p.id === savedProjId) || projs[0];
          setActiveProjectState(defaultProj);
          localStorage.setItem("active_project_id", defaultProj.id);
        } else {
          setActiveProjectState(null);
        }
      }
    } catch (err) {
      console.error("Failed to load user session context", err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (token: string) => {
    localStorage.setItem("access_token", token);
    await refreshContext();
  };

  const setActiveOrg = async (org: Organization) => {
    setActiveOrgState(org);
    localStorage.setItem("active_org_id", org.id);
    try {
      const projsRes = await api.get<Project[]>(`/projects?org_id=${org.id}`);
      const projs = projsRes.data;
      setProjects(projs);
      if (projs.length > 0) {
        setActiveProjectState(projs[0]);
        localStorage.setItem("active_project_id", projs[0].id);
      } else {
        setActiveProjectState(null);
        localStorage.removeItem("active_project_id");
      }
    } catch (err) {
      console.error("Failed to swap projects context", err);
    }
  };

  const setActiveProject = (proj: Project) => {
    setActiveProjectState(proj);
    localStorage.setItem("active_project_id", proj.id);
  };

  useEffect(() => {
    refreshContext();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        loading,
        organizations,
        projects,
        activeOrg,
        activeProject,
        setActiveOrg,
        setActiveProject,
        login,
        logout,
        refreshContext,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
