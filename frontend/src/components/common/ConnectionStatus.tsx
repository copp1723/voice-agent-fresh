import { Chip } from '@mui/material'
import { Circle } from '@mui/icons-material'
import { useSystemStore } from '@store/index'

export default function ConnectionStatus() {
  const wsConnected = useSystemStore((state) => state.wsConnected)
  const health = useSystemStore((state) => state.health)

  const getStatus = () => {
    if (!wsConnected) return { label: 'Disconnected', color: 'error' as const }
    if (health?.status === 'error') return { label: 'Error', color: 'error' as const }
    if (health?.status === 'degraded') return { label: 'Degraded', color: 'warning' as const }
    return { label: 'Connected', color: 'success' as const }
  }

  const status = getStatus()

  return (
    <Chip
      icon={<Circle />}
      label={status.label}
      color={status.color}
      size="small"
      sx={{ mr: 2 }}
    />
  )
}