import { Paper, Box, Typography, Chip, Grid } from '@mui/material'
import { CheckCircle, Warning, Error, Circle } from '@mui/icons-material'
import { useApiQuery } from '@hooks/useApi'
import { dashboardService } from '@services/endpoints'
import { useSystemStore } from '@store/index'

export default function SystemHealthIndicator() {
  const { data: healthData } = useApiQuery(
    ['system', 'health'],
    () => dashboardService.getHealth(),
    {
      refetchInterval: 60000, // Check every minute
    },
  )

  const wsConnected = useSystemStore((state) => state.wsConnected)
  const health = healthData?.data

  const getStatusIcon = (status: boolean | undefined) => {
    if (status === undefined) return <Circle color="disabled" />
    return status ? <CheckCircle color="success" /> : <Error color="error" />
  }

  const getOverallStatus = () => {
    if (!health) return { icon: <Warning />, label: 'Unknown', color: 'warning' as const }
    if (health.status === 'healthy') return { icon: <CheckCircle />, label: 'All Systems Operational', color: 'success' as const }
    if (health.status === 'degraded') return { icon: <Warning />, label: 'Degraded Performance', color: 'warning' as const }
    return { icon: <Error />, label: 'System Error', color: 'error' as const }
  }

  const overallStatus = getOverallStatus()

  return (
    <Paper sx={{ p: 2 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h6">System Health</Typography>
        <Chip
          icon={overallStatus.icon}
          label={overallStatus.label}
          color={overallStatus.color}
          size="small"
        />
      </Box>

      <Grid container spacing={2}>
        <Grid item xs={6} sm={3}>
          <Box display="flex" alignItems="center" gap={1}>
            {getStatusIcon(health?.twilioStatus)}
            <Typography variant="body2">Twilio API</Typography>
          </Box>
        </Grid>
        
        <Grid item xs={6} sm={3}>
          <Box display="flex" alignItems="center" gap={1}>
            {getStatusIcon(health?.openrouterStatus)}
            <Typography variant="body2">OpenRouter AI</Typography>
          </Box>
        </Grid>
        
        <Grid item xs={6} sm={3}>
          <Box display="flex" alignItems="center" gap={1}>
            {getStatusIcon(health?.databaseStatus)}
            <Typography variant="body2">Database</Typography>
          </Box>
        </Grid>
        
        <Grid item xs={6} sm={3}>
          <Box display="flex" alignItems="center" gap={1}>
            {getStatusIcon(wsConnected)}
            <Typography variant="body2">WebSocket</Typography>
          </Box>
        </Grid>
      </Grid>

      {health?.activeSessions !== undefined && (
        <Box mt={2} display="flex" justifyContent="space-between">
          <Typography variant="caption" color="text.secondary">
            Active Sessions: {health.activeSessions}
          </Typography>
          {health.uptime && (
            <Typography variant="caption" color="text.secondary">
              Uptime: {Math.floor(health.uptime / 3600)}h {Math.floor((health.uptime % 3600) / 60)}m
            </Typography>
          )}
        </Box>
      )}
    </Paper>
  )
}