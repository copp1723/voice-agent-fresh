import { Paper, Typography, List, ListItem, ListItemText, Chip, Box } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useApiQuery } from '@hooks/useApi'
import { callService } from '@services/endpoints'
import { formatPhoneNumber, formatRelativeTime } from '@utils/format'
import { CallStatus } from '@types/index'

export default function RecentCallsList() {
  const navigate = useNavigate()
  const { data: callsData } = useApiQuery(
    ['calls', 'recent'],
    () => callService.getCalls(undefined, 1, 10),
  )

  const calls = callsData?.data.data || []

  const getStatusColor = (status: CallStatus) => {
    switch (status) {
      case CallStatus.COMPLETED:
        return 'success'
      case CallStatus.IN_PROGRESS:
        return 'primary'
      case CallStatus.FAILED:
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Recent Calls
      </Typography>
      
      <List>
        {calls.map((call) => (
          <ListItem
            key={call.id}
            button
            onClick={() => navigate(`/calls/${call.id}`)}
            sx={{ px: 0 }}
          >
            <ListItemText
              primary={formatPhoneNumber(call.phoneNumber)}
              secondary={
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="caption">
                    {formatRelativeTime(call.startTime)}
                  </Typography>
                  <Chip
                    label={call.agentType}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              }
            />
            <Chip
              label={call.status.replace('-', ' ')}
              size="small"
              color={getStatusColor(call.status)}
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  )
}