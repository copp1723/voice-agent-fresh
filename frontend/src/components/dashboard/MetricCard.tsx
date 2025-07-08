import { Card, CardContent, Box, Typography, Skeleton, Chip } from '@mui/material'
import { TrendingUp, TrendingDown } from '@mui/icons-material'

interface MetricCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info'
  loading?: boolean
  trend?: 'up' | 'down'
  trendValue?: string
}

export default function MetricCard({
  title,
  value,
  icon,
  color = 'primary',
  loading = false,
  trend,
  trendValue,
}: MetricCardProps) {
  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box flex={1}>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            {loading ? (
              <Skeleton variant="text" width="60%" height={32} />
            ) : (
              <Typography variant="h4" component="div">
                {value}
              </Typography>
            )}
            {trend && !loading && (
              <Box display="flex" alignItems="center" gap={0.5} mt={1}>
                {trend === 'up' ? (
                  <TrendingUp color="success" fontSize="small" />
                ) : (
                  <TrendingDown color="error" fontSize="small" />
                )}
                {trendValue && (
                  <Typography variant="caption" color={trend === 'up' ? 'success.main' : 'error.main'}>
                    {trendValue}
                  </Typography>
                )}
              </Box>
            )}
          </Box>
          <Box
            sx={{
              backgroundColor: `${color}.light`,
              borderRadius: 2,
              p: 1.5,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Box sx={{ color: `${color}.main` }}>{icon}</Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}