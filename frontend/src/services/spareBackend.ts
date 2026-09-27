/**
 * Spare Backend Service
 * Connects to the AI agent analysis backend running on WSL
 */

const SPARE_API_URL = import.meta.env.VITE_SPARE_API_URL || "http://localhost:8000/api";

export interface AnalysisResponse {
  status: string;
  message: string;
  user_id: string;
  analysis_started: string;
  estimated_completion_minutes: number;
}

export interface AnalysisStatus {
  user_id: string;
  status: "in_progress" | "completed" | "failed";
  agents_completed: number;
  total_agents: number;
  last_updated: string;
}

export interface HealthCheck {
  status: string;
  service: string;
  agents: Record<string, string>;
  database: string;
  timestamp: string;
}

export interface AgentLog {
  log_id: string;
  user_id: string;
  agent_name: string;
  execution_timestamp: string;
  input_data: any;
  output_data: any;
  confidence_score?: number;
  execution_time_ms?: number;
  success: boolean;
  error_message?: string;
  model_version?: string;
  created_at: string;
}

export interface AgentLogsResponse {
  user_id: string;
  logs: AgentLog[];
  total_count: number;
}

/**
 * Spare Backend API Service
 * Handles communication with the 9-agent analysis system
 */
export const spareBackendService = {
  /**
   * Trigger complete financial analysis for a user
   * All 9 agents will analyze and push results to database
   */
  triggerAnalysis: async (user_id: string): Promise<AnalysisResponse> => {
    console.log(`[Spare Backend] Triggering analysis for user ${user_id}`);

    const response = await fetch(`${SPARE_API_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Analysis failed: ${response.status}`);
    }

    const data = await response.json();
    console.log(`[Spare Backend] Analysis started:`, data);
    return data;
  },

  /**
   * Check the current status of analysis for a user
   */
  getAnalysisStatus: async (user_id: string): Promise<AnalysisStatus> => {
    const response = await fetch(`${SPARE_API_URL}/status/${user_id}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("No analysis found for this user");
      }
      throw new Error(`Status check failed: ${response.status}`);
    }

    const data = await response.json();
    console.log(`[Spare Backend] Status:`, data);
    return data;
  },

  /**
   * Check if the spare backend is healthy and running
   */
  checkHealth: async (): Promise<HealthCheck> => {
    const response = await fetch(`${SPARE_API_URL}/health`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get detailed agent execution logs for a user
   */
  getAgentLogs: async (user_id: string): Promise<AgentLogsResponse> => {
    console.log(`[Spare Backend] Fetching agent logs for user ${user_id}`);
    
    const response = await fetch(`${SPARE_API_URL}/agent-logs/${user_id}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch agent logs: ${response.status}`);
    }

    const data = await response.json();
    console.log(`[Spare Backend] Retrieved ${data.total_count} agent logs`);
    return data;
  },

  /**
   * Poll for analysis completion
   * Returns a promise that resolves when analysis is complete
   */
  waitForCompletion: async (
    user_id: string,
    onProgress?: (status: AnalysisStatus) => void,
    timeout_ms: number = 600000 // 10 minutes default
  ): Promise<AnalysisStatus> => {
    const startTime = Date.now();
    const pollInterval = 5000; // 5 seconds

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await spareBackendService.getAnalysisStatus(user_id);

          // Call progress callback if provided
          if (onProgress) {
            onProgress(status);
          }

          // Check if completed
          if (status.status === "completed") {
            console.log(`[Spare Backend] Analysis completed!`);
            resolve(status);
            return;
          }

          if (status.status === "failed") {
            reject(new Error("Analysis failed"));
            return;
          }

          // Check timeout
          if (Date.now() - startTime > timeout_ms) {
            reject(new Error("Analysis timeout"));
            return;
          }

          // Continue polling
          setTimeout(poll, pollInterval);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  },
};

export default spareBackendService;
