import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Button,
  Chip,
  Avatar,
  LinearProgress,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  Collapse,
  Alert,
} from '@mui/material'
import {
  Phone,
  PhoneDisabled,
  Visibility,
  PlayArrow,
  Pause,
  Stop,
  Notes,
  SwapHoriz,
  ExpandMore,
  ExpandLess,
  VolumeUp,
  Person,
  AccessTime,
  TrendingUp,
  Message,
} from '@mui/icons-material'
import { useApiQuery, useApiMutation } from '@hooks/useApi'
import { useWebSocket } from '@hooks/useWebSocket'
import { callService } from '@services/endpoints'
import { Call, CallStatus, AgentType, WSEventType } from '@types'
import { formatDuration, formatTime } from '@utils/format'

interface ActiveCallCardProps {
  call: Call
  onViewTranscript: (call: Call) => void
  onEndCall: (callId: number) => void
  onTransferCall: (callId: number) => void
  onAddNote: (callId: number, note: string) => void
}

function ActiveCallCard({
  call,
  onViewTranscript,
  onEndCall,
  onTransferCall,
  onAddNote,
}: ActiveCallCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [isPlaying, setIsPlaying] = useState(true)
  const [noteDialog, setNoteDialog] = useState(false)
  const [note, setNote] = useState('')

  const duration = call.startTime
    ? Math.floor((Date.now() - new Date(call.startTime).getTime()) / 1000)
    : 0

  const handleAddNote = () => {
    if (note.trim()) {
      onAddNote(call.id, note)
      setNote('')
      setNoteDialog(false)
    }
  }

  const getAgentColor = (agentType: AgentType) => {
    const colors = {
      [AgentType.GENERAL]: 'primary',
      [AgentType.BILLING]: 'warning',
      [AgentType.SUPPORT]: 'info',
      [AgentType.SALES]: 'success',
      [AgentType.SCHEDULING]: 'secondary',
    }
    return colors[agentType] || 'default'
  }

  return (
    <>
      <Card sx={{ mb: 2, position: 'relative' }}>
        <LinearProgress
          variant="indeterminate"
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 2,
          }}
        />
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <Box display="flex" alignItems="center" gap={1}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <Phone />
                </Avatar>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Customer
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {call.phoneNumber}
                  </Typography>
                </Box>
              </Box>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Box display="flex" alignItems="center" gap={1}>
                <Avatar sx={{ bgcolor: getAgentColor(call.agentType) }}>
                  <Person />
                </Avatar>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Agent Type
                  </Typography>
                  <Chip
                    label={call.agentType}
                    size="small"
                    color={getAgentColor(call.agentType) as any}
                  />
                </Box>
              </Box>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Box display="flex" alignItems="center" gap={1}>
                <AccessTime color="action" />
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Duration
                  </Typography>
                  <Typography variant="h6" color="primary">
                    {formatDuration(duration)}
                  </Typography>
                </Box>
              </Box>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Box display="flex" alignItems="center" gap={1}>
                <TrendingUp color="success" />
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Confidence
                  </Typography>
                  <Typography variant="body1">
                    {Math.round(call.routingConfidence * 100)}%
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>

          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Box mt={2} p={2} bgcolor="background.default" borderRadius={1}>
              <Typography variant="subtitle2" gutterBottom>
                Latest Transcript
              </Typography>
              {call.messages.slice(-3).map((msg, idx) => (
                <Box key={idx} mb={1}>
                  <Typography variant="caption" color="text.secondary">
                    {msg.role === 'user' ? 'Customer' : 'Agent'} •{' '}
                    {formatTime(msg.timestamp)}
                  </Typography>
                  <Typography variant="body2">{msg.content}</Typography>
                </Box>
              ))}
            </Box>
          </Collapse>
        </CardContent>

        <CardActions sx={{ justifyContent: 'space-between' }}>
          <Box>
            <Tooltip title={isPlaying ? 'Pause' : 'Resume'}>
              <IconButton
                size="small"
                onClick={() => setIsPlaying(!isPlaying)}
              >
                {isPlaying ? <Pause /> : <PlayArrow />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Add Note">
              <IconButton size="small" onClick={() => setNoteDialog(true)}>
                <Notes />
              </IconButton>
            </Tooltip>
            <Tooltip title="Transfer Call">
              <IconButton
                size="small"
                onClick={() => onTransferCall(call.id)}
              >
                <SwapHoriz />
              </IconButton>
            </Tooltip>
            <Tooltip title="View Full Transcript">
              <IconButton size="small" onClick={() => onViewTranscript(call)}>
                <Visibility />
              </IconButton>
            </Tooltip>
          </Box>

          <Box>
            <IconButton
              size="small"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
            <Button
              color="error"
              size="small"
              startIcon={<PhoneDisabled />}
              onClick={() => onEndCall(call.id)}
            >
              End Call
            </Button>
          </Box>
        </CardActions>
      </Card>

      <Dialog open={noteDialog} onClose={() => setNoteDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Note to Call</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Note"
            fullWidth
            multiline
            rows={4}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <Box mt={2} display="flex" justifyContent="flex-end" gap={1}>
            <Button onClick={() => setNoteDialog(false)}>Cancel</Button>
            <Button variant="contained" onClick={handleAddNote}>
              Add Note
            </Button>
          </Box>
        </DialogContent>
      </Dialog>
    </>
  )
}

export default function ActiveCalls() {
  const [selectedCall, setSelectedCall] = useState<Call | null>(null)
  const [transcriptDialog, setTranscriptDialog] = useState(false)

  const { data: activeCalls, isLoading, refetch } = useApiQuery(
    ['calls', 'active'],
    () => callService.getActiveCalls(),
    {
      refetchInterval: 5000, // Refresh every 5 seconds
    }
  )

  const endCallMutation = useApiMutation(
    (callId: number) => callService.endCall(callId),
    {
      onSuccess: () => {
        refetch()
      },
    }
  )

  const addNoteMutation = useApiMutation(
    ({ callId, note }: { callId: number; note: string }) =>
      callService.addNote(callId, note)
  )

  // WebSocket for real-time updates
  const { subscribe, unsubscribe } = useWebSocket()

  useEffect(() => {
    const handleCallUpdate = () => {
      refetch()
    }

    subscribe(WSEventType.CALL_STARTED, handleCallUpdate)
    subscribe(WSEventType.CALL_UPDATED, handleCallUpdate)
    subscribe(WSEventType.CALL_ENDED, handleCallUpdate)

    return () => {
      unsubscribe(WSEventType.CALL_STARTED, handleCallUpdate)
      unsubscribe(WSEventType.CALL_UPDATED, handleCallUpdate)
      unsubscribe(WSEventType.CALL_ENDED, handleCallUpdate)
    }
  }, [subscribe, unsubscribe, refetch])

  const handleViewTranscript = (call: Call) => {
    setSelectedCall(call)
    setTranscriptDialog(true)
  }

  const handleEndCall = (callId: number) => {
    if (window.confirm('Are you sure you want to end this call?')) {
      endCallMutation.mutate(callId)
    }
  }

  const handleTransferCall = (callId: number) => {
    // TODO: Implement call transfer dialog
    console.log('Transfer call:', callId)
  }

  const handleAddNote = (callId: number, note: string) => {
    addNoteMutation.mutate({ callId, note })
  }

  const calls = activeCalls?.data || []
  const activeCallsCount = calls.filter(
    (call) => call.status === CallStatus.IN_PROGRESS
  ).length

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Active Calls Monitor
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time monitoring of all active calls
          </Typography>
        </Box>
        <Box display="flex" alignItems="center" gap={2}>
          <Chip
            icon={<Phone />}
            label={`${activeCallsCount} Active`}
            color="success"
            variant={activeCallsCount > 0 ? 'filled' : 'outlined'}
          />
          <Button
            variant="outlined"
            startIcon={<VolumeUp />}
            size="small"
          >
            Audio Settings
          </Button>
        </Box>
      </Box>

      {isLoading ? (
        <LinearProgress />
      ) : calls.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Phone sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No Active Calls
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Active calls will appear here in real-time
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          <Grid item xs={12}>
            {calls.map((call) => (
              <ActiveCallCard
                key={call.id}
                call={call}
                onViewTranscript={handleViewTranscript}
                onEndCall={handleEndCall}
                onTransferCall={handleTransferCall}
                onAddNote={handleAddNote}
              />
            ))}
          </Grid>
        </Grid>
      )}

      {/* Transcript Dialog */}
      <Dialog
        open={transcriptDialog}
        onClose={() => setTranscriptDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Call Transcript - {selectedCall?.phoneNumber}
        </DialogTitle>
        <DialogContent>
          {selectedCall?.messages.map((msg, idx) => (
            <Box key={idx} mb={2}>
              <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                <Chip
                  label={msg.role === 'user' ? 'Customer' : 'Agent'}
                  size="small"
                  color={msg.role === 'user' ? 'default' : 'primary'}
                />
                <Typography variant="caption" color="text.secondary">
                  {formatTime(msg.timestamp)}
                </Typography>
              </Box>
              <Typography variant="body1">{msg.content}</Typography>
            </Box>
          ))}
        </DialogContent>
      </Dialog>
    </Box>
  )
}