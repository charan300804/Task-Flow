import axios from 'axios';
import { Job, JobCreate, WorkerNode, Schedule, ScheduleCreate, SystemMetricsResponse } from '../types';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor for JWT auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('taskflow_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: async (username: string, password: str) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const res = await axios.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    if (res.data.access_token) {
      localStorage.setItem('taskflow_token', res.data.access_token);
    }
    return res.data;
  },
  getMe: async () => {
    const res = await api.get('/auth/me');
    return res.data;
  },
  logout: () => {
    localStorage.removeItem('taskflow_token');
  }
};

export const jobsApi = {
  submitJob: async (jobData: JobCreate, idempotencyKey?: string): Promise<Job> => {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    const res = await api.post('/jobs', jobData, { headers });
    return res.data;
  },
  getJobs: async (page = 1, size = 20, status?: string, jobType?: string) => {
    const params: Record<string, any> = { page, size };
    if (status) params.status = status;
    if (jobType) params.job_type = jobType;
    const res = await api.get('/jobs', { params });
    return res.data;
  },
  getJobDetail: async (id: string): Promise<Job> => {
    const res = await api.get(`/jobs/${id}`);
    return res.data;
  },
  cancelJob: async (id: string): Promise<Job> => {
    const res = await api.post(`/jobs/${id}/cancel`);
    return res.data;
  },
  retryJob: async (id: string): Promise<Job> => {
    const res = await api.post(`/jobs/${id}/retry`);
    return res.data;
  },
  deleteJob: async (id: string): Promise<void> => {
    await api.delete(`/jobs/${id}`);
  },
  getJobResult: async (id: string) => {
    const res = await api.get(`/jobs/${id}/result`);
    return res.data;
  }
};

export const workersApi = {
  getWorkers: async (): Promise<WorkerNode[]> => {
    const res = await api.get('/workers');
    return res.data;
  },
  getWorkerDetail: async (id: string): Promise<WorkerNode> => {
    const res = await api.get(`/workers/${id}`);
    return res.data;
  }
};

export const schedulesApi = {
  getSchedules: async (): Promise<Schedule[]> => {
    const res = await api.get('/schedules');
    return res.data;
  },
  createSchedule: async (data: ScheduleCreate): Promise<Schedule> => {
    const res = await api.post('/schedules', data);
    return res.data;
  },
  updateSchedule: async (id: string, data: Partial<ScheduleCreate>): Promise<Schedule> => {
    const res = await api.patch(`/schedules/${id}`, data);
    return res.data;
  },
  deleteSchedule: async (id: string): Promise<void> => {
    await api.delete(`/schedules/${id}`);
  }
};

export const metricsApi = {
  getOverviewMetrics: async (): Promise<SystemMetricsResponse> => {
    const res = await api.get('/metrics/overview');
    return res.data;
  }
};

export const adminApi = {
  getDeadLetterJobs: async (page = 1, size = 20) => {
    const res = await api.get('/admin/dead-letter', { params: { page, size } });
    return res.data;
  },
  retryDeadLetterJob: async (id: string): Promise<Job> => {
    const res = await api.post(`/admin/dead-letter/${id}/retry`);
    return res.data;
  },
  deleteDeadLetterJob: async (id: string): Promise<void> => {
    await api.delete(`/admin/dead-letter/${id}`);
  }
};

export default api;
