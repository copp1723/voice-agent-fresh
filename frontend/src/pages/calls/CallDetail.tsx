import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  IconButton,
  Button,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  LinearProgress,
  Slider,
  CircularProgress,
  Alert,
  Tooltip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import {
  ArrowBack,
  Phone,
  Person,
  AccessTime,
  PlayArrow,
  Pause,
  VolumeUp,
  Download,
  Share,
  CheckCircle,
  Warning,
  TrendingUp,
  Message,
  Notes,
  ContentCopy,
  Replay10,
  Forward10,
} from '@mui/icons-material'
import { useApiQuery, useApiMutation } from '@hooks/useApi'
import { callService } from '@services/endpoints'
import { Call, CallStatus, MessageRole, Sentiment } from '@types'
import { formatPhoneNumber, formatDateTime, formatDuration, formatTime } from '@utils/format'

export default function CallDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [volume, setVolume] = useState(70)
  const [selectedMessage, setSelectedMessage] = useState<number | null>(null)
  const [shareDialog, setShareDialog] = useState(false)
  const [noteDialog, setNoteDialog] = useState(false)
  const [note, setNote] = useState('')
  const audioRef = useRef<HTMLAudioElement>(null)

  const callId = parseInt(id!, 10)

  const { data: call, isLoading, refetch } = useApiQuery(
    ['call', callId],
    () => callService.getCall(callId),
    {
      enabled: !!callId,
    }
  )

  const addNoteMutation = useApiMutation(
    (note: string) => callService.addNote(callId, note),
    {
      onSuccess: () => {
        refetch()
        setNoteDialog(false)
        setNote('')
      },
    }
  )

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume / 100
    }
  }, [volume])

  const handlePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const handleSeek = (newValue: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = newValue
      setCurrentTime(newValue)
    }
  }

  const handleRewind = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 10)
    }
  }

  const handleForward = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.min(
        audioRef.current.duration,
        audioRef.current.currentTime + 10
      )
    }
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime)
    }
  }

  const handleCopyTranscript = () => {
    if (call?.data.messages) {
      const transcript = call.data.messages
        .map(msg => `${msg.role === MessageRole.USER ? 'Customer' : 'Agent'}: ${msg.content}`)
        .join('\n\n')
      navigator.clipboard.writeText(transcript)
    }
  }

  const handleDownloadRecording = () => {
    // TODO: Implement download functionality
    console.log('Downloading recording...')
  }

  const handleAddNote = () => {
    if (note.trim()) {
      addNoteMutation.mutate(note)
    }
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (!call?.data) {
    return (
      <Box>
        <Alert severity="error">Call not found</Alert>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/calls')} sx={{ mt: 2 }}>
          Back to Calls
        </Button>
      </Box>
    )
  }

  const callData = call.data
  const duration = callData.duration || 0
  const getSentimentColor = (sentiment?: Sentiment) => {
    switch (sentiment) {
      case Sentiment.POSITIVE:
        return 'success'
      case Sentiment.NEGATIVE:
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <IconButton onClick={() => navigate('/calls')}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4">Call Details</Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Call Information */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Call Information
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Phone color="action" />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Phone Number
                  </Typography>
                  <Typography>{formatPhoneNumber(callData.phoneNumber)}</Typography>
                </Box>
              </Box>

              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Person color="action" />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Agent Type
                  </Typography>
                  <Chip label={callData.agentType} size="small" />
                </Box>
              </Box>

              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <AccessTime color="action" />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Start Time
                  </Typography>
                  <Typography>{formatDateTime(callData.startTime)}</Typography>
                </Box>
              </Box>

              {callData.endTime && (
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <AccessTime color="action" />
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      End Time
                    </Typography>
                    <Typography>{formatDateTime(callData.endTime)}</Typography>
                  </Box>
                </Box>
              )}

              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <AccessTime color="action" />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Duration
                  </Typography>
                  <Typography variant="h6" color="primary">
                    {formatDuration(duration)}
                  </Typography>
                </Box>
              </Box>

              <Box display="flex" alignItems="center" gap={1} mb={2}>
                {callData.status === CallStatus.COMPLETED ? (
                  <CheckCircle color="success" />
                ) : (
                  <Warning color="warning" />
                )}
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip
                    label={callData.status}
                    color={callData.status === CallStatus.COMPLETED ? 'success' : 'warning'}
                    size="small"
                  />
                </Box>
              </Box>

              <Box display="flex" alignItems="center" gap={1}>
                <TrendingUp color="action" />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Routing Confidence
                  </Typography>
                  <Typography>{Math.round(callData.routingConfidence * 100)}%</Typography>
                </Box>
              </Box>

              {callData.smsStatus && (
                <Box mt={2}>
                  <Divider sx={{ mb: 2 }} />
                  <Box display="flex" alignItems="center" gap={1}>
                    <Message color="action" />
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        SMS Status
                      </Typography>
                      <Chip
                        label={callData.smsStatus}
                        color={callData.smsStatus === 'delivered' ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Call Summary */}
          {callData.summary && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Call Summary
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Typography variant="body2" paragraph>
                  {callData.summary.summary}
                </Typography>

                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Sentiment
                  </Typography>
                  <Chip
                    label={callData.summary.sentiment}
                    color={getSentimentColor(callData.summary.sentiment) as any}
                    size="small"
                  />
                </Box>

                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Keywords
                  </Typography>
                  <Box display="flex" gap={0.5} flexWrap="wrap">
                    {callData.summary.keywords.map((keyword, idx) => (
                      <Chip key={idx} label={keyword} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Box>

                {callData.summary.actionItems.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Action Items
                    </Typography>
                    {callData.summary.actionItems.map((item, idx) => (
                      <Typography key={idx} variant="body2">
                        • {item}
                      </Typography>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Recording and Transcript */}
        <Grid item xs={12} md={8}>
          {/* Audio Player */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Call Recording</Typography>
              <Box display="flex" gap={1}>
                <Tooltip title="Add Note">
                  <IconButton onClick={() => setNoteDialog(true)}>
                    <Notes />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Share">
                  <IconButton onClick={() => setShareDialog(true)}>
                    <Share />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Download">
                  <IconButton onClick={handleDownloadRecording}>
                    <Download />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>

            <Box mb={2}>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <IconButton onClick={handleRewind}>
                  <Replay10 />
                </IconButton>
                <IconButton onClick={handlePlayPause} color="primary">
                  {isPlaying ? <Pause /> : <PlayArrow />}
                </IconButton>
                <IconButton onClick={handleForward}>
                  <Forward10 />
                </IconButton>
                <Typography variant="body2">
                  {formatDuration(Math.floor(currentTime))} / {formatDuration(duration)}
                </Typography>
              </Box>

              <Slider
                value={currentTime}
                max={duration}
                onChange={(_, value) => handleSeek(value as number)}
                sx={{ mb: 2 }}
              />

              <Box display="flex" alignItems="center" gap={2}>
                <VolumeUp />
                <Slider
                  value={volume}
                  onChange={(_, value) => setVolume(value as number)}
                  sx={{ width: 120 }}
                />
              </Box>
            </Box>

            <audio
              ref={audioRef}
              src={`/api/calls/${callId}/recording`}
              onTimeUpdate={handleTimeUpdate}
            />
          </Paper>

          {/* Transcript */}
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Call Transcript</Typography>
              <Tooltip title="Copy Transcript">
                <IconButton onClick={handleCopyTranscript}>
                  <ContentCopy />
                </IconButton>
              </Tooltip>
            </Box>

            <List>
              {callData.messages.map((message, idx) => (
                <ListItem
                  key={idx}
                  sx={{
                    bgcolor: selectedMessage === idx ? 'action.selected' : 'transparent',
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'action.hover' },
                  }}
                  onClick={() => setSelectedMessage(idx)}
                >
                  <ListItemAvatar>
                    <Avatar
                      sx={{
                        bgcolor: message.role === MessageRole.USER ? 'primary.main' : 'secondary.main',
                      }}
                    >
                      {message.role === MessageRole.USER ? <Person /> : <Phone />}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="subtitle1">
                          {message.role === MessageRole.USER ? 'Customer' : 'Agent'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatTime(message.timestamp)}
                        </Typography>
                      </Box>
                    }
                    secondary={message.content}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>

      {/* Add Note Dialog */}
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
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNoteDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleAddNote}
            disabled={!note.trim() || addNoteMutation.isLoading}
          >
            Add Note
          </Button>
        </DialogActions>
      </Dialog>

      {/* Share Dialog */}
      <Dialog open={shareDialog} onClose={() => setShareDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Share Call Recording</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Share Link"
            value={`${window.location.origin}/calls/${callId}/share`}
            InputProps={{
              readOnly: true,
              endAdornment: (
                <IconButton
                  onClick={() => {
                    navigator.clipboard.writeText(`${window.location.origin}/calls/${callId}/share`)
                  }}
                >
                  <ContentCopy />
                </IconButton>
              ),
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShareDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}