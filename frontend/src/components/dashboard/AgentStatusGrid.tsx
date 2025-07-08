import { Paper, Typography, Grid, Card, CardContent, Box, Skeleton } from '@mui/material'
import { SmartToy, TrendingUp } from '@mui/icons-material'
import { useApiQuery } from '@hooks/useApi'
import { agentService } from '@services/endpoints'
import { formatNumber, formatPercent } from '@utils/format'

export default function AgentStatusGrid() {
  const { data: agentsData, isLoading } = useApiQuery(
    ['agents'],
    () => agentService.getAgents(),
  )

  const agents = agentsData?.data || []

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Agent Performance
      </Typography>
      
      <Grid container spacing={2}>
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <Grid item xs={12} key={i}>
              <Skeleton variant="rectangular" height={80} />
            </Grid>
          ))
        ) : (
          agents.map((agent) => (
            <Grid item xs={12} key={agent.id}>
              <Card variant="outlined">
                <CardContent sx={{ py: 1.5 }}>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box display="flex" alignItems="center" gap={1}>
                      <SmartToy color="primary" />
                      <Box>
                        <Typography variant="subtitle2">{agent.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Priority: {agent.priority}
                        </Typography>
                      </Box>
                    </Box>
                    <Box textAlign="right">
                      <Typography variant="body2">
                        {agent.keywords.length} keywords
                      </Typography>
                      <Typography variant="caption" color={agent.isActive ? 'success.main' : 'text.disabled'}>
                        {agent.isActive ? 'Active' : 'Inactive'}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>
    </Paper>
  )
}