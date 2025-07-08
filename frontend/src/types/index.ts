// Core domain types for the Voice Agent Dashboard

export interface User {
  id: number
  username: string
  email: string
  role: UserRole
  createdAt: string
  updatedAt: string
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  ADVISOR = 'advisor',
  VIEWER = 'viewer',
}

export interface Agent {
  id: number
  agentType: AgentType
  name: string
  description: string
  systemPrompt: string
  keywords: string[]
  priority: number
  smsTemplate: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export enum AgentType {
  GENERAL = 'general',
  BILLING = 'billing',
  SUPPORT = 'support',
  SALES = 'sales',
  SCHEDULING = 'scheduling',
}

export interface Call {
  id: number
  callSid: string
  phoneNumber: string
  agentType: AgentType
  startTime: string
  endTime?: string
  duration?: number
  status: CallStatus
  routingConfidence: number
  messages: Message[]
  summary?: CallSummary
  smsStatus?: SMSStatus
}

export enum CallStatus {
  INITIATED = 'initiated',
  IN_PROGRESS = 'in-progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  BUSY = 'busy',
  NO_ANSWER = 'no-answer',
}

export interface Message {
  id: number
  callId: number
  role: MessageRole
  content: string
  timestamp: string
}

export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
}

export interface CallSummary {
  summary: string
  keywords: string[]
  sentiment: Sentiment
  actionItems: string[]
}

export enum Sentiment {
  POSITIVE = 'positive',
  NEUTRAL = 'neutral',
  NEGATIVE = 'negative',
}

export interface SMSLog {
  id: number
  callId: number
  toNumber: string
  message: string
  status: SMSStatus
  sentAt: string
  deliveredAt?: string
  error?: string
}

export enum SMSStatus {
  PENDING = 'pending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  FAILED = 'failed',
}

export interface DashboardMetrics {
  totalCalls: number
  activeCalls: number
  avgCallDuration: number
  routingAccuracy: number
  smsDeliveryRate: number
  agentDistribution: Record<AgentType, number>
  callsPerHour: Array<{
    hour: string
    count: number
  }>
}

export interface AgentMetrics {
  agentType: AgentType
  totalCalls: number
  avgDuration: number
  avgConfidence: number
  successRate: number
  sentiment: {
    positive: number
    neutral: number
    negative: number
  }
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'error'
  twilioStatus: boolean
  openrouterStatus: boolean
  databaseStatus: boolean
  activeSessions: number
  uptime: number
  lastError?: string
}

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  timestamp: string
  read: boolean
  actionUrl?: string
}

export enum NotificationType {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  SUCCESS = 'success',
}

// API Response types
export interface ApiResponse<T> {
  data: T
  status: number
  message?: string
}

export interface ApiError {
  status: number
  message: string
  code?: string
  details?: Record<string, any>
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

// WebSocket event types
export interface WebSocketEvent {
  type: WSEventType
  data: any
  timestamp: string
}

export enum WSEventType {
  CALL_STARTED = 'call:started',
  CALL_UPDATED = 'call:updated',
  CALL_ENDED = 'call:ended',
  AGENT_STATUS_CHANGED = 'agent:status_changed',
  SYSTEM_ALERT = 'system:alert',
  METRICS_UPDATED = 'metrics:updated',
}

// Form types
export interface AgentFormData {
  name: string
  description: string
  systemPrompt: string
  keywords: string
  priority: number
  smsTemplate: string
  isActive: boolean
}

export interface UserFormData {
  username: string
  email: string
  role: UserRole
  password?: string
}

// Customer types
export interface Customer {
  id: number
  phoneNumber: string
  firstName?: string
  lastName?: string
  email?: string
  tags: string[]
  notes: string
  totalCalls: number
  lastCallDate?: string
  averageSentiment?: Sentiment
  createdAt: string
  updatedAt: string
}

export interface CustomerFormData {
  firstName?: string
  lastName?: string
  email?: string
  phoneNumber: string
  tags: string[]
  notes: string
}

export interface SMSConversation {
  id: number
  customerId: number
  messages: SMSMessage[]
  lastMessageAt: string
}

export interface SMSMessage {
  id: number
  content: string
  direction: 'inbound' | 'outbound'
  timestamp: string
  status: SMSStatus
}

// Filter types
export interface CallFilters {
  agentType?: AgentType
  status?: CallStatus
  dateFrom?: string
  dateTo?: string
  phoneNumber?: string
  searchTerm?: string
}

export interface CustomerFilters {
  searchTerm?: string
  tags?: string[]
  hasNotes?: boolean
  minCalls?: number
  maxCalls?: number
}

export interface ReportFilters {
  dateFrom: string
  dateTo: string
  agentTypes?: AgentType[]
  metrics?: string[]
  groupBy?: 'hour' | 'day' | 'week' | 'month'
}