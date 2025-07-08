import { apiClient } from './api'
import {
  Agent,
  AgentFormData,
  AgentMetrics,
  Call,
  CallFilters,
  Customer,
  CustomerFormData,
  CustomerFilters,
  DashboardMetrics,
  PaginatedResponse,
  ReportFilters,
  SMSLog,
  SMSConversation,
  SystemHealth,
  User,
  UserFormData,
} from '@types/index'

// Dashboard endpoints
export const dashboardService = {
  getMetrics: () => apiClient.get<DashboardMetrics>('/dashboard/metrics'),
  getHealth: () => apiClient.get<SystemHealth>('/health'),
}

// Call endpoints
export const callService = {
  getActiveCalls: () => apiClient.get<Call[]>('/calls/active'),
  
  getCallHistory: (params: CallFilters & { page?: number; pageSize?: number }) => {
    const queryParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        queryParams.append(key, value.toString())
      }
    })
    return apiClient.get<PaginatedResponse<Call>>(`/calls?${queryParams}`)
  },
  
  getCalls: (filters?: CallFilters, page = 1, pageSize = 20) => {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString(),
    })
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          params.append(key, value.toString())
        }
      })
    }
    
    return apiClient.get<PaginatedResponse<Call>>(`/calls?${params}`)
  },
  
  getCall: (id: number) => apiClient.get<Call>(`/calls/${id}`),
  
  endCall: (callId: number) => apiClient.post(`/calls/${callId}/end`),
  
  transferCall: (callSid: string, agentType: string) =>
    apiClient.post(`/calls/${callSid}/transfer`, { agentType }),
    
  addNote: (callId: number, note: string) =>
    apiClient.post(`/calls/${callId}/notes`, { note }),
    
  exportCalls: (filters: CallFilters) =>
    apiClient.post('/calls/export', filters, { responseType: 'blob' }),
}

// Agent endpoints
export const agentService = {
  getAgents: () => apiClient.get<Agent[]>('/agents'),
  
  getAgent: (agentType: string) => apiClient.get<Agent>(`/agents/${agentType}`),
  
  createAgent: (data: AgentFormData) => apiClient.post<Agent>('/agents', data),
  
  updateAgent: (agentType: string, data: Partial<AgentFormData>) =>
    apiClient.put<Agent>(`/agents/${agentType}`, data),
  
  deleteAgent: (id: number) => apiClient.delete(`/agents/${id}`),
  
  getAgentMetrics: (agentType: string, dateFrom?: string, dateTo?: string) => {
    const params = new URLSearchParams()
    if (dateFrom) params.append('dateFrom', dateFrom)
    if (dateTo) params.append('dateTo', dateTo)
    
    return apiClient.get<AgentMetrics>(`/agents/${agentType}/metrics?${params}`)
  },
  
  testAgent: (agentType: string, phoneNumber: string) =>
    apiClient.post<{ success: boolean; message: string }>(`/agents/${agentType}/test`, { phoneNumber }),
}

// SMS endpoints
export const smsService = {
  getSMSLogs: (page = 1, pageSize = 20) =>
    apiClient.get<PaginatedResponse<SMSLog>>(`/sms?page=${page}&pageSize=${pageSize}`),
  
  getSMSLog: (id: number) => apiClient.get<SMSLog>(`/sms/${id}`),
  
  retrySMS: (id: number) => apiClient.post(`/sms/${id}/retry`),
}

// User endpoints
export const userService = {
  getUsers: () => apiClient.get<User[]>('/users'),
  
  getUser: (id: number) => apiClient.get<User>(`/users/${id}`),
  
  createUser: (data: UserFormData) => apiClient.post<User>('/users', data),
  
  updateUser: (id: number, data: Partial<UserFormData>) =>
    apiClient.put<User>(`/users/${id}`, data),
  
  deleteUser: (id: number) => apiClient.delete(`/users/${id}`),
  
  getCurrentUser: () => apiClient.get<User>('/users/me'),
}

// Report endpoints
export const reportService = {
  generateReport: (filters: ReportFilters) =>
    apiClient.post<{ reportUrl: string }>('/reports/generate', filters),
  
  getReportTemplates: () =>
    apiClient.get<Array<{ id: string; name: string; description: string }>>('/reports/templates'),
  
  exportReport: (reportId: string, format: 'pdf' | 'csv' | 'excel') =>
    apiClient.get(`/reports/${reportId}/export?format=${format}`, {
      responseType: 'blob',
    }),
}

// Customer endpoints
export const customerService = {
  getCustomers: (filters?: CustomerFilters) => {
    const params = new URLSearchParams()
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }
    return apiClient.get<Customer[]>(`/customers?${params}`)
  },
  
  getCustomer: (id: number) => apiClient.get<Customer>(`/customers/${id}`),
  
  createCustomer: (data: CustomerFormData) => apiClient.post<Customer>('/customers', data),
  
  updateCustomer: (id: number, data: Partial<CustomerFormData>) =>
    apiClient.put<Customer>(`/customers/${id}`, data),
    
  deleteCustomer: (id: number) => apiClient.delete(`/customers/${id}`),
  
  getCustomerCalls: (id: number) => apiClient.get<Call[]>(`/customers/${id}/calls`),
  
  getCustomerSMS: (id: number) => apiClient.get<SMSConversation>(`/customers/${id}/sms`),
  
  getTags: () => apiClient.get<string[]>('/customers/tags'),
}

// Auth endpoints
export const authService = {
  login: (username: string, password: string) =>
    apiClient.post<{ token: string; user: User }>('/auth/login', { username, password }),
  
  logout: () => apiClient.post('/auth/logout'),
  
  refreshToken: () => apiClient.post<{ token: string }>('/auth/refresh'),
  
  forgotPassword: (email: string) => apiClient.post('/auth/forgot-password', { email }),
  
  resetPassword: (token: string, newPassword: string) =>
    apiClient.post('/auth/reset-password', { token, newPassword }),
}