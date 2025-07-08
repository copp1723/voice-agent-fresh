import { Grid, Paper, Box, Typography, Card, CardContent } from '@mui/material'
import {
  Phone,
  PhoneInTalk,
  AccessTime,
  TrendingUp,
  Message,
  CheckCircle,
} from '@mui/icons-material'
import { useApiQuery } from '@hooks/useApi'
import { dashboardService } from '@services/endpoints'
import MetricCard from '@components/dashboard/MetricCard'
import CallDistributionChart from '@components/dashboard/CallDistributionChart'
import CallVolumeChart from '@components/dashboard/CallVolumeChart'
import RecentCallsList from '@components/dashboard/RecentCallsList'
import AgentStatusGrid from '@components/dashboard/AgentStatusGrid'
import SystemHealthIndicator from '@components/dashboard/SystemHealthIndicator'
import { formatNumber, formatPercent, formatDuration } from '@utils/format'

export default function Dashboard() {
  const { data: metrics, isLoading } = useApiQuery(
    ['dashboard', 'metrics'],
    () => dashboardService.getMetrics(),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    },
  )

  const metricsData = metrics?.data

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard Overview
      </Typography>
      
      <Grid container spacing={3}>
        {/* Metric Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Calls Today"
            value={formatNumber(metricsData?.totalCalls || 0)}
            icon={<Phone />}
            color="primary"
            loading={isLoading}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Calls"
            value={formatNumber(metricsData?.activeCalls || 0)}
            icon={<PhoneInTalk />}
            color="success"
            loading={isLoading}
            trend={metricsData?.activeCalls ? 'up' : undefined}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Avg Call Duration"
            value={formatDuration(metricsData?.avgCallDuration || 0)}
            icon={<AccessTime />}
            color="info"
            loading={isLoading}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Routing Accuracy"
            value={formatPercent(metricsData?.routingAccuracy || 0)}
            icon={<TrendingUp />}
            color="warning"
            loading={isLoading}
          />
        </Grid>

        {/* System Health */}
        <Grid item xs={12}>
          <SystemHealthIndicator />
        </Grid>

        {/* Charts Row */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Call Volume (Last 24 Hours)
            </Typography>
            <CallVolumeChart data={metricsData?.callsPerHour || []} />
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Agent Distribution
            </Typography>
            <CallDistributionChart data={metricsData?.agentDistribution || {}} />
          </Paper>
        </Grid>

        {/* Agent Status Grid */}
        <Grid item xs={12} md={6}>
          <AgentStatusGrid />
        </Grid>

        {/* Recent Calls */}
        <Grid item xs={12} md={6}>
          <RecentCallsList />
        </Grid>

        {/* SMS Stats */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    SMS Sent Today
                  </Typography>
                  <Typography variant="h5">
                    {formatNumber(metricsData?.totalCalls || 0)}
                  </Typography>
                </Box>
                <Message color="action" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    SMS Delivery Rate
                  </Typography>
                  <Typography variant="h5">
                    {formatPercent(metricsData?.smsDeliveryRate || 0)}
                  </Typography>
                </Box>
                <CheckCircle color="success" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}