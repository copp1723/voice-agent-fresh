import { io, Socket } from 'socket.io-client'
import { WebSocketEvent, WSEventType } from '@types/index'

class WebSocketService {
  private socket: Socket | null = null
  private listeners: Map<string, Set<(data: any) => void>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(): void {
    if (this.socket?.connected) {
      return
    }

    const wsUrl = import.meta.env.VITE_WS_URL || window.location.origin
    const apiKey = import.meta.env.VITE_API_KEY || localStorage.getItem('apiKey')

    this.socket = io(wsUrl, {
      transports: ['websocket', 'polling'],
      auth: {
        apiKey,
        token: localStorage.getItem('authToken'),
      },
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    })

    this.setupEventHandlers()
  }

  private setupEventHandlers(): void {
    if (!this.socket) return

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
      this.emit('connection:status', { connected: true })
    })

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
      this.emit('connection:status', { connected: false })
    })

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
      this.emit('connection:error', error)
    })

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      this.reconnectAttempts = attemptNumber
      console.log(`WebSocket reconnection attempt ${attemptNumber}`)
    })

    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed')
      this.emit('connection:failed', {
        message: 'Failed to reconnect to server',
      })
    })

    // Listen for all WebSocket events
    Object.values(WSEventType).forEach((eventType) => {
      this.socket!.on(eventType, (data) => {
        const event: WebSocketEvent = {
          type: eventType,
          data,
          timestamp: new Date().toISOString(),
        }
        this.handleEvent(event)
      })
    })
  }

  private handleEvent(event: WebSocketEvent): void {
    // Notify all listeners for this event type
    const listeners = this.listeners.get(event.type)
    if (listeners) {
      listeners.forEach((callback) => callback(event.data))
    }

    // Notify wildcard listeners
    const wildcardListeners = this.listeners.get('*')
    if (wildcardListeners) {
      wildcardListeners.forEach((callback) => callback(event))
    }
  }

  on(eventType: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType)!.add(callback)

    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(eventType)
      if (listeners) {
        listeners.delete(callback)
        if (listeners.size === 0) {
          this.listeners.delete(eventType)
        }
      }
    }
  }

  off(eventType: string, callback?: (data: any) => void): void {
    if (!callback) {
      // Remove all listeners for this event type
      this.listeners.delete(eventType)
    } else {
      // Remove specific listener
      const listeners = this.listeners.get(eventType)
      if (listeners) {
        listeners.delete(callback)
        if (listeners.size === 0) {
          this.listeners.delete(eventType)
        }
      }
    }
  }

  emit(eventType: string, data?: any): void {
    if (this.socket?.connected) {
      this.socket.emit(eventType, data)
    } else {
      console.warn('Cannot emit event: WebSocket not connected')
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.listeners.clear()
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }

  getSocket(): Socket | null {
    return this.socket
  }
}

// Create singleton instance
const wsService = new WebSocketService()

// Export singleton instance and class for testing
export default wsService
export { WebSocketService }