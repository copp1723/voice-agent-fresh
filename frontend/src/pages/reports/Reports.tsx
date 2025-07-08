import { useState, useMemo } from 'react'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  IconButton,
  Tabs,
  Tab,
  Divider,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material'
import {
  TrendingUp,
  TrendingDown,
  Phone,
  AccessTime,
  Person,
  SentimentSatisfied,
  SentimentNeutral,
  SentimentDissatisfied,
  Download,
  Refresh,
  CalendarToday,
  ShowChart,
  PieChart as PieChartIcon,
  BarChart as BarChartIcon,
} from '@mui/icons-material'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js'
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2'
import { useApiQuery } from '@hooks/useApi'
import { reportService, callService, agentService } from '@services/endpoints'
import { AgentType, AgentMetrics } from '@types'
import { formatNumber, formatPercent, formatDuration } from '@utils/format'
import { startOfMonth, endOfMonth, subMonths, format } from 'date-fns'

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

interface MetricCardProps {
  title: string
  value: string | number
  change?: number
  icon: React.ReactNode
  color?: 'primary' | 'success' | 'warning' | 'error'
}

function MetricCard({ title, value, change, icon, color = 'primary' }: MetricCardProps) {
  const isPositive = change && change > 0
  const changeColor = isPositive ? 'success.main' : 'error.main'

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography color="text.secondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
            {change !== undefined && (
              <Box display="flex" alignItems="center" mt={1}>
                {isPositive ? (
                  <TrendingUp sx={{ color: changeColor, mr: 0.5, fontSize: 20 }} />
                ) : (
                  <TrendingDown sx={{ color: changeColor, mr: 0.5, fontSize: 20 }} />
                )}
                <Typography variant="body2" sx={{ color: changeColor }}>
                  {Math.abs(change)}% from last period
                </Typography>
              </Box>
            )}
          </Box>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              bgcolor: `${color}.light`,
              color: `${color}.main`,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

export default function Reports() {
  const [tabValue, setTabValue] = useState(0)
  const [dateRange, setDateRange] = useState({
    startDate: startOfMonth(new Date()),
    endDate: endOfMonth(new Date()),
  })
  const [selectedAgent, setSelectedAgent] = useState<AgentType | 'all'>('all')
  const [refreshKey, setRefreshKey] = useState(0)

  // Fetch analytics data
  const { data: callAnalytics, isLoading: isLoadingCalls } = useApiQuery(
    ['analytics', 'calls', dateRange, refreshKey],
    () => callService.getCalls({
      dateFrom: format(dateRange.startDate, 'yyyy-MM-dd'),
      dateTo: format(dateRange.endDate, 'yyyy-MM-dd'),
    }),
    {
      keepPreviousData: true,
    }
  )

  const { data: agentMetrics, isLoading: isLoadingMetrics } = useApiQuery(
    ['analytics', 'agents', selectedAgent, dateRange, refreshKey],
    () => {
      if (selectedAgent === 'all') {
        return Promise.all(
          Object.values(AgentType).map(type =>
            agentService.getAgentMetrics(
              type,
              format(dateRange.startDate, 'yyyy-MM-dd'),
              format(dateRange.endDate, 'yyyy-MM-dd')
            )
          )
        )
      }
      return agentService.getAgentMetrics(
        selectedAgent,
        format(dateRange.startDate, 'yyyy-MM-dd'),
        format(dateRange.endDate, 'yyyy-MM-dd')
      )
    }
  )

  const isLoading = isLoadingCalls || isLoadingMetrics

  // Calculate summary metrics
  const summaryMetrics = useMemo(() => {
    if (!callAnalytics?.data) {
      return {
        totalCalls: 0,
        avgDuration: 0,
        avgSatisfaction: 0,
        conversionRate: 0,
      }
    }

    const calls = callAnalytics.data.data
    const totalCalls = calls.length
    const avgDuration = calls.reduce((acc, call) => acc + (call.duration || 0), 0) / totalCalls
    const completedCalls = calls.filter(call => call.status === 'completed').length
    const conversionRate = (completedCalls / totalCalls) * 100

    return {
      totalCalls,
      avgDuration,
      avgSatisfaction: 85, // Mock data
      conversionRate,
    }
  }, [callAnalytics])

  // Chart configurations
  const callVolumeChartData = {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [
      {
        label: 'Call Volume',
        data: [650, 720, 810, 690],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
      },
    ],
  }

  const sentimentChartData = {
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [
      {
        data: [65, 25, 10],
        backgroundColor: [
          'rgba(76, 175, 80, 0.8)',
          'rgba(158, 158, 158, 0.8)',
          'rgba(244, 67, 54, 0.8)',
        ],
      },
    ],
  }

  const agentPerformanceData = {
    labels: Object.values(AgentType),
    datasets: [
      {
        label: 'Calls Handled',
        data: [120, 95, 180, 75, 110],
        backgroundColor: 'rgba(54, 162, 235, 0.8)',
      },
      {
        label: 'Avg Duration (min)',
        data: [8.5, 6.2, 9.1, 5.8, 7.3],
        backgroundColor: 'rgba(255, 206, 86, 0.8)',
      },
    ],
  }

  const responseTimeData = {
    labels: ['0-30s', '30-60s', '1-2min', '2-5min', '>5min'],
    datasets: [
      {
        label: 'Response Time Distribution',
        data: [245, 180, 95, 45, 20],
        backgroundColor: [
          'rgba(76, 175, 80, 0.8)',
          'rgba(139, 195, 74, 0.8)',
          'rgba(255, 235, 59, 0.8)',
          'rgba(255, 152, 0, 0.8)',
          'rgba(244, 67, 54, 0.8)',
        ],
      },
    ],
  }

  const chartOptions: ChartOptions<any> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
  }

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
  }

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting report...')
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Analytics Dashboard
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Comprehensive insights into call performance and agent metrics
            </Typography>
          </Box>
          <Box display="flex" gap={2}>
            <IconButton onClick={handleRefresh} disabled={isLoading}>
              <Refresh />
            </IconButton>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleExport}
            >
              Export Report
            </Button>
          </Box>
        </Box>

        {/* Date Range and Filters */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <DatePicker
                label="Start Date"
                value={dateRange.startDate}
                onChange={(date) => date && setDateRange({ ...dateRange, startDate: date })}
                slotProps={{ textField: { fullWidth: true, size: 'small' } }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <DatePicker
                label="End Date"
                value={dateRange.endDate}
                onChange={(date) => date && setDateRange({ ...dateRange, endDate: date })}
                slotProps={{ textField: { fullWidth: true, size: 'small' } }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Agent Type</InputLabel>
                <Select
                  value={selectedAgent}
                  onChange={(e) => setSelectedAgent(e.target.value as AgentType | 'all')}
                >
                  <MenuItem value="all">All Agents</MenuItem>
                  {Object.values(AgentType).map(type => (
                    <MenuItem key={type} value={type}>{type}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box display="flex" gap={1}>
                <Chip
                  icon={<CalendarToday fontSize="small" />}
                  label="Last 30 Days"
                  onClick={() => setDateRange({
                    startDate: subMonths(new Date(), 1),
                    endDate: new Date(),
                  })}
                  variant="outlined"
                  size="small"
                />
                <Chip
                  label="This Month"
                  onClick={() => setDateRange({
                    startDate: startOfMonth(new Date()),
                    endDate: endOfMonth(new Date()),
                  })}
                  variant="outlined"
                  size="small"
                />
              </Box>
            </Grid>
          </Grid>
        </Paper>

        {isLoading && <LinearProgress sx={{ mb: 2 }} />}

        {/* Summary Metrics */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Total Calls"
              value={formatNumber(summaryMetrics.totalCalls)}
              change={12.5}
              icon={<Phone />}
              color="primary"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Avg Call Duration"
              value={formatDuration(summaryMetrics.avgDuration)}
              change={-5.2}
              icon={<AccessTime />}
              color="warning"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Customer Satisfaction"
              value={formatPercent(summaryMetrics.avgSatisfaction / 100)}
              change={3.8}
              icon={<SentimentSatisfied />}
              color="success"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Conversion Rate"
              value={formatPercent(summaryMetrics.conversionRate / 100)}
              change={8.1}
              icon={<TrendingUp />}
              color="success"
            />
          </Grid>
        </Grid>

        {/* Detailed Analytics Tabs */}
        <Paper>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab icon={<ShowChart />} label="Trends" />
            <Tab icon={<PieChartIcon />} label="Distribution" />
            <Tab icon={<BarChartIcon />} label="Performance" />
            <Tab icon={<Person />} label="Agent Analytics" />
          </Tabs>
          <Divider />

          <Box p={3}>
            {/* Trends Tab */}
            {tabValue === 0 && (
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Call Volume Trends
                  </Typography>
                  <Box height={300}>
                    <Line data={callVolumeChartData} options={chartOptions} />
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    Response Time Distribution
                  </Typography>
                  <Box height={300}>
                    <Bar data={responseTimeData} options={chartOptions} />
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    Peak Hours Analysis
                  </Typography>
                  <Alert severity="info">
                    Peak call hours: 10 AM - 12 PM and 2 PM - 4 PM
                  </Alert>
                  <Box mt={2}>
                    {/* Add hourly heatmap here */}
                  </Box>
                </Grid>
              </Grid>
            )}

            {/* Distribution Tab */}
            {tabValue === 1 && (
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    Customer Sentiment Distribution
                  </Typography>
                  <Box height={300}>
                    <Pie data={sentimentChartData} options={chartOptions} />
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    Call Status Distribution
                  </Typography>
                  <Box height={300}>
                    <Doughnut
                      data={{
                        labels: ['Completed', 'Failed', 'No Answer', 'Busy'],
                        datasets: [{
                          data: [75, 10, 10, 5],
                          backgroundColor: [
                            'rgba(76, 175, 80, 0.8)',
                            'rgba(244, 67, 54, 0.8)',
                            'rgba(255, 152, 0, 0.8)',
                            'rgba(158, 158, 158, 0.8)',
                          ],
                        }],
                      }}
                      options={chartOptions}
                    />
                  </Box>
                </Grid>
              </Grid>
            )}

            {/* Performance Tab */}
            {tabValue === 2 && (
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Agent Performance Comparison
                  </Typography>
                  <Box height={400}>
                    <Bar data={agentPerformanceData} options={chartOptions} />
                  </Box>
                </Grid>
              </Grid>
            )}

            {/* Agent Analytics Tab */}
            {tabValue === 3 && (
              <Grid container spacing={3}>
                {Object.values(AgentType).map((agentType) => (
                  <Grid item xs={12} md={6} key={agentType}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {agentType} Agent
                        </Typography>
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Total Calls
                            </Typography>
                            <Typography variant="h5">120</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Success Rate
                            </Typography>
                            <Typography variant="h5">92%</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Avg Duration
                            </Typography>
                            <Typography variant="h5">8.5 min</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Routing Accuracy
                            </Typography>
                            <Typography variant="h5">95%</Typography>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </Box>
        </Paper>
      </Box>
    </LocalizationProvider>
  )
}