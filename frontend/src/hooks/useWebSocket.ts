import { useEffect, useCallback, useRef } from 'react'
import wsService from '@services/websocket'
import { useSystemStore, useActiveCallsStore, useUIStore } from '@store/index'
import { WSEventType, NotificationType } from '@types/index'

export function useWebSocket() {
  const setWsConnected = useSystemStore((state) => state.setWsConnected)
  const { addCall, updateCall, removeCall } = useActiveCallsStore()
  const addNotification = useUIStore((state) => state.addNotification)
  const cleanupRef = useRef<(() => void)[]>([])

  const handleCallStarted = useCallback(
    (data: any) => {
      addCall(data.callSid, data)
      addNotification({
        type: NotificationType.INFO,
        title: 'New Call',
        message: `Incoming call from ${data.phoneNumber}`,
      })
    },
    [addCall, addNotification],
  )

  const handleCallUpdated = useCallback(
    (data: any) => {
      updateCall(data.callSid, data)
    },
    [updateCall],
  )

  const handleCallEnded = useCallback(
    (data: any) => {
      removeCall(data.callSid)
      if (data.error) {
        addNotification({
          type: NotificationType.WARNING,
          title: 'Call Ended',
          message: `Call ended with error: ${data.error}`,
        })
      }
    },
    [removeCall, addNotification],
  )

  const handleSystemAlert = useCallback(
    (data: any) => {
      addNotification({
        type: data.severity || NotificationType.WARNING,
        title: 'System Alert',
        message: data.message,
      })
    },
    [addNotification],
  )

  const handleConnectionStatus = useCallback(
    (data: { connected: boolean }) => {
      setWsConnected(data.connected)
      if (!data.connected) {
        addNotification({
          type: NotificationType.WARNING,
          title: 'Connection Lost',
          message: 'WebSocket connection lost. Attempting to reconnect...',
        })
      }
    },
    [setWsConnected, addNotification],
  )

  useEffect(() => {
    // Connect to WebSocket
    wsService.connect()

    // Subscribe to events
    cleanupRef.current = [
      wsService.on(WSEventType.CALL_STARTED, handleCallStarted),
      wsService.on(WSEventType.CALL_UPDATED, handleCallUpdated),
      wsService.on(WSEventType.CALL_ENDED, handleCallEnded),
      wsService.on(WSEventType.SYSTEM_ALERT, handleSystemAlert),
      wsService.on('connection:status', handleConnectionStatus),
    ]

    // Initial connection status
    setWsConnected(wsService.isConnected())

    return () => {
      // Cleanup subscriptions
      cleanupRef.current.forEach((cleanup) => cleanup())
      cleanupRef.current = []
    }
  }, [
    handleCallStarted,
    handleCallUpdated,
    handleCallEnded,
    handleSystemAlert,
    handleConnectionStatus,
    setWsConnected,
  ])

  return {
    isConnected: wsService.isConnected(),
    emit: wsService.emit.bind(wsService),
    on: wsService.on.bind(wsService),
    off: wsService.off.bind(wsService),
  }
}

// Hook for subscribing to specific WebSocket events
export function useWebSocketEvent(
  eventType: string,
  handler: (data: any) => void,
  deps: React.DependencyList = [],
) {
  useEffect(() => {
    const unsubscribe = wsService.on(eventType, handler)
    return unsubscribe
  }, [eventType, ...deps])
}