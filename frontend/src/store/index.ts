import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { User, Notification, SystemHealth } from '@types/index'

// Auth store
interface AuthState {
  user: User | null
  isAuthenticated: boolean
  token: string | null
  setAuth: (user: User, token: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        isAuthenticated: false,
        token: null,
        setAuth: (user, token) =>
          set({
            user,
            token,
            isAuthenticated: true,
          }),
        logout: () =>
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          }),
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          token: state.token,
        }),
      },
    ),
  ),
)

// UI store
interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  notifications: Notification[]
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markNotificationRead: (id: string) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set) => ({
        sidebarOpen: true,
        theme: 'light',
        notifications: [],
        toggleSidebar: () =>
          set((state) => ({
            sidebarOpen: !state.sidebarOpen,
          })),
        setTheme: (theme) => set({ theme }),
        addNotification: (notification) =>
          set((state) => ({
            notifications: [
              {
                ...notification,
                id: crypto.randomUUID(),
                timestamp: new Date().toISOString(),
                read: false,
              },
              ...state.notifications,
            ].slice(0, 50), // Keep only last 50 notifications
          })),
        markNotificationRead: (id) =>
          set((state) => ({
            notifications: state.notifications.map((n) =>
              n.id === id ? { ...n, read: true } : n,
            ),
          })),
        removeNotification: (id) =>
          set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
          })),
        clearNotifications: () => set({ notifications: [] }),
      }),
      {
        name: 'ui-storage',
        partialize: (state) => ({
          theme: state.theme,
          sidebarOpen: state.sidebarOpen,
        }),
      },
    ),
  ),
)

// System store
interface SystemState {
  health: SystemHealth | null
  wsConnected: boolean
  lastUpdate: string | null
  setHealth: (health: SystemHealth) => void
  setWsConnected: (connected: boolean) => void
}

export const useSystemStore = create<SystemState>()(
  devtools((set) => ({
    health: null,
    wsConnected: false,
    lastUpdate: null,
    setHealth: (health) =>
      set({
        health,
        lastUpdate: new Date().toISOString(),
      }),
    setWsConnected: (wsConnected) => set({ wsConnected }),
  })),
)

// Active calls store (for real-time updates)
interface ActiveCallsState {
  activeCalls: Map<string, any>
  addCall: (callSid: string, call: any) => void
  updateCall: (callSid: string, updates: any) => void
  removeCall: (callSid: string) => void
  clearCalls: () => void
}

export const useActiveCallsStore = create<ActiveCallsState>()(
  devtools((set) => ({
    activeCalls: new Map(),
    addCall: (callSid, call) =>
      set((state) => {
        const newCalls = new Map(state.activeCalls)
        newCalls.set(callSid, call)
        return { activeCalls: newCalls }
      }),
    updateCall: (callSid, updates) =>
      set((state) => {
        const newCalls = new Map(state.activeCalls)
        const existingCall = newCalls.get(callSid)
        if (existingCall) {
          newCalls.set(callSid, { ...existingCall, ...updates })
        }
        return { activeCalls: newCalls }
      }),
    removeCall: (callSid) =>
      set((state) => {
        const newCalls = new Map(state.activeCalls)
        newCalls.delete(callSid)
        return { activeCalls: newCalls }
      }),
    clearCalls: () => set({ activeCalls: new Map() }),
  })),
)