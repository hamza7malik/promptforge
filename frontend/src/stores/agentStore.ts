import { create } from "zustand";
import { Agent, AgentCreate, AgentUpdate } from "@/types";
import { apiClient } from "@/api";

interface AgentStore {
  agents: Agent[];
  currentAgent: Agent | null;
  loading: boolean;
  error: string | null;

  fetchAgents: () => Promise<void>;
  fetchAgent: (agentId: string) => Promise<void>;
  createAgent: (data: AgentCreate) => Promise<Agent>;
  updateAgent: (agentId: string, data: AgentUpdate) => Promise<Agent>;
  deleteAgent: (agentId: string) => Promise<void>;
  setCurrentAgent: (agent: Agent | null) => void;
}

export const useAgentStore = create<AgentStore>((set) => ({
  agents: [],
  currentAgent: null,
  loading: false,
  error: null,

  fetchAgents: async () => {
    set({ loading: true, error: null });
    try {
      const agents = await apiClient.listAgents();
      set({ agents, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  fetchAgent: async (agentId: string) => {
    set({ loading: true, error: null });
    try {
      const agent = await apiClient.getAgent(agentId);
      set({ currentAgent: agent, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  createAgent: async (data: AgentCreate) => {
    set({ loading: true, error: null });
    try {
      const agent = await apiClient.createAgent(data);
      set((state) => ({
        agents: [...state.agents, agent],
        loading: false,
      }));
      return agent;
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  updateAgent: async (agentId: string, data: AgentUpdate) => {
    set({ loading: true, error: null });
    try {
      const agent = await apiClient.updateAgent(agentId, data);
      set((state) => ({
        agents: state.agents.map((a) => (a.id === agentId ? agent : a)),
        currentAgent:
          state.currentAgent?.id === agentId ? agent : state.currentAgent,
        loading: false,
      }));
      return agent;
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  deleteAgent: async (agentId: string) => {
    set({ loading: true, error: null });
    try {
      await apiClient.deleteAgent(agentId);
      set((state) => ({
        agents: state.agents.filter((a) => a.id !== agentId),
        currentAgent:
          state.currentAgent?.id === agentId ? null : state.currentAgent,
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  setCurrentAgent: (agent: Agent | null) => {
    set({ currentAgent: agent });
  },
}));
