import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import { ApiError, ApiResponse } from '@types/index'

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    // Add API key if available
    const apiKey = import.meta.env.VITE_API_KEY || localStorage.getItem('apiKey')
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey
    }

    // Add auth token if available
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    // Wrap response in standard format
    return {
      data: response.data,
      status: response.status,
      message: response.data.message,
    } as ApiResponse<any>
  },
  (error: AxiosError<ApiError>) => {
    // Handle network errors
    if (!error.response) {
      const apiError: ApiError = {
        status: 0,
        message: 'Network error. Please check your connection.',
        code: 'NETWORK_ERROR',
      }
      return Promise.reject(apiError)
    }

    // Handle API errors
    const apiError: ApiError = {
      status: error.response.status,
      message: error.response.data?.message || 'An error occurred',
      code: error.response.data?.code,
      details: error.response.data?.details,
    }

    // Handle authentication errors
    if (error.response.status === 401) {
      localStorage.removeItem('authToken')
      window.location.href = '/login'
    }

    return Promise.reject(apiError)
  },
)

// Generic request function
export async function request<T>(
  method: string,
  url: string,
  data?: any,
  config?: AxiosRequestConfig,
): Promise<ApiResponse<T>> {
  try {
    const response = await api.request<T>({
      method,
      url,
      data,
      ...config,
    })
    return response as any
  } catch (error) {
    throw error
  }
}

// Convenience methods
export const apiClient = {
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    request<T>('GET', url, undefined, config),

  post: <T>(url: string, data?: any, config?: AxiosRequestConfig) =>
    request<T>('POST', url, data, config),

  put: <T>(url: string, data?: any, config?: AxiosRequestConfig) =>
    request<T>('PUT', url, data, config),

  patch: <T>(url: string, data?: any, config?: AxiosRequestConfig) =>
    request<T>('PATCH', url, data, config),

  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    request<T>('DELETE', url, undefined, config),
}

export default apiClient