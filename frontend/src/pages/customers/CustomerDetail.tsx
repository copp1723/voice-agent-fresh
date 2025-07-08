import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Avatar,
  IconButton,
  Button,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Tab,
  Tabs,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineDot,
  TimelineContent,
  TimelineConnector,
} from '@mui/lab'
import {
  Person,
  Phone,
  Email,
  Edit,
  Tag,
  Notes,
  History,
  Message,
  PlayArrow,
  Download,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  AccessTime,
  ArrowBack,
  Send,
} from '@mui/icons-material'
import { useApiQuery, useApiMutation } from '@hooks/useApi'
import { customerService, callService } from '@services/endpoints'
import { Customer, Call, SMSConversation, CallStatus } from '@types'
import { formatPhoneNumber, formatDateTime, formatDuration } from '@utils/format'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [tabValue, setTabValue] = useState(0)
  const [editDialog, setEditDialog] = useState(false)
  const [smsDialog, setSmsDialog] = useState(false)
  const [smsMessage, setSmsMessage] = useState('')
  const [notes, setNotes] = useState('')

  const customerId = parseInt(id!, 10)

  const { data: customer, isLoading: isLoadingCustomer, refetch: refetchCustomer } = useApiQuery(
    ['customer', customerId],
    () => customerService.getCustomer(customerId),
    {
      enabled: !!customerId,
    }
  )

  const { data: customerCalls, isLoading: isLoadingCalls } = useApiQuery(
    ['customer', customerId, 'calls'],
    () => customerService.getCustomerCalls(customerId),
    {
      enabled: !!customerId,
    }
  )

  const { data: customerSMS, isLoading: isLoadingSMS } = useApiQuery(
    ['customer', customerId, 'sms'],
    () => customerService.getCustomerSMS(customerId),
    {
      enabled: !!customerId,
    }
  )

  const updateMutation = useApiMutation(
    (data: { notes: string }) => customerService.updateCustomer(customerId, data),
    {
      onSuccess: () => {
        refetchCustomer()
        setEditDialog(false)
      },
    }
  )

  const sendSMSMutation = useApiMutation(
    (message: string) => 
      // This would be a real SMS endpoint
      Promise.resolve({ success: true }),
    {
      onSuccess: () => {
        setSmsDialog(false)
        setSmsMessage('')
      },
    }
  )

  const handleUpdateNotes = () => {
    updateMutation.mutate({ notes })
  }

  const handleSendSMS = () => {
    if (smsMessage.trim()) {
      sendSMSMutation.mutate(smsMessage)
    }
  }

  const getCallStatusIcon = (status: CallStatus) => {
    switch (status) {
      case CallStatus.COMPLETED:
        return <CheckCircle color="success" />
      case CallStatus.FAILED:
        return <ErrorIcon color="error" />
      default:
        return <Warning color="warning" />
    }
  }

  if (isLoadingCustomer) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (!customer?.data) {
    return (
      <Box>
        <Alert severity="error">Customer not found</Alert>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/customers')} sx={{ mt: 2 }}>
          Back to Customers
        </Button>
      </Box>
    )
  }

  const customerData = customer.data
  const calls = customerCalls?.data || []
  const smsConversation = customerSMS?.data
  const getInitials = (firstName?: string, lastName?: string) => {
    if (!firstName && !lastName) return '?'
    return `${firstName?.[0] || ''}${lastName?.[0] || ''}`.toUpperCase()
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <IconButton onClick={() => navigate('/customers')}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4">Customer Profile</Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Customer Info Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" flexDirection="column" alignItems="center" mb={3}>
                <Avatar
                  sx={{ width: 80, height: 80, bgcolor: 'primary.main', mb: 2 }}
                >
                  {getInitials(customerData.firstName, customerData.lastName)}
                </Avatar>
                <Typography variant="h5">
                  {customerData.firstName || customerData.lastName
                    ? `${customerData.firstName || ''} ${customerData.lastName || ''}`.trim()
                    : 'Unknown Customer'}
                </Typography>
                <Box display="flex" gap={0.5} mt={1}>
                  {customerData.tags.map((tag, idx) => (
                    <Chip key={idx} label={tag} size="small" icon={<Tag />} />
                  ))}
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Phone color="action" />
                <Typography>{formatPhoneNumber(customerData.phoneNumber)}</Typography>
              </Box>

              {customerData.email && (
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <Email color="action" />
                  <Typography>{customerData.email}</Typography>
                </Box>
              )}

              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <History color="action" />
                <Typography variant="body2" color="text.secondary">
                  Customer since {formatDateTime(customerData.createdAt)}
                </Typography>
              </Box>

              <Box display="flex" alignItems="center" gap={1}>
                <AccessTime color="action" />
                <Typography variant="body2" color="text.secondary">
                  Last call: {customerData.lastCallDate ? formatDateTime(customerData.lastCallDate) : 'N/A'}
                </Typography>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="subtitle2">Notes</Typography>
                  <IconButton size="small" onClick={() => {
                    setNotes(customerData.notes)
                    setEditDialog(true)
                  }}>
                    <Edit fontSize="small" />
                  </IconButton>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {customerData.notes || 'No notes added yet'}
                </Typography>
              </Box>

              <Box mt={3}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<Message />}
                  onClick={() => setSmsDialog(true)}
                >
                  Send SMS
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Activity and History */}
        <Grid item xs={12} md={8}>
          <Paper>
            <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
              <Tab label={`Call History (${calls.length})`} />
              <Tab label="SMS Conversations" />
              <Tab label="Activity Timeline" />
            </Tabs>

            <TabPanel value={tabValue} index={0}>
              {isLoadingCalls ? (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              ) : calls.length === 0 ? (
                <Box p={3} textAlign="center">
                  <Phone sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                  <Typography color="text.secondary">No call history</Typography>
                </Box>
              ) : (
                <List>
                  {calls.map((call) => (
                    <ListItem key={call.id} divider>
                      <ListItemAvatar>
                        {getCallStatusIcon(call.status)}
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="body1">
                              {call.agentType} Agent
                            </Typography>
                            <Chip label={call.status} size="small" />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {formatDateTime(call.startTime)} • Duration: {formatDuration(call.duration || 0)}
                            </Typography>
                            {call.summary && (
                              <Typography variant="body2" sx={{ mt: 1 }}>
                                {call.summary.summary}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          onClick={() => navigate(`/calls/${call.id}`)}
                        >
                          <PlayArrow />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              {isLoadingSMS ? (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              ) : !smsConversation || smsConversation.messages.length === 0 ? (
                <Box p={3} textAlign="center">
                  <Message sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                  <Typography color="text.secondary">No SMS conversations</Typography>
                </Box>
              ) : (
                <List>
                  {smsConversation.messages.map((message) => (
                    <ListItem
                      key={message.id}
                      sx={{
                        flexDirection: message.direction === 'outbound' ? 'row-reverse' : 'row',
                      }}
                    >
                      <Box
                        sx={{
                          maxWidth: '70%',
                          p: 2,
                          borderRadius: 2,
                          bgcolor: message.direction === 'outbound' ? 'primary.main' : 'grey.200',
                          color: message.direction === 'outbound' ? 'white' : 'text.primary',
                        }}
                      >
                        <Typography variant="body2">{message.content}</Typography>
                        <Typography
                          variant="caption"
                          sx={{
                            display: 'block',
                            mt: 0.5,
                            opacity: 0.7,
                          }}
                        >
                          {formatDateTime(message.timestamp)}
                        </Typography>
                      </Box>
                    </ListItem>
                  ))}
                </List>
              )}
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <Timeline>
                <TimelineItem>
                  <TimelineSeparator>
                    <TimelineDot color="primary">
                      <Person />
                    </TimelineDot>
                    <TimelineConnector />
                  </TimelineSeparator>
                  <TimelineContent>
                    <Typography variant="subtitle2">
                      Customer created
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {formatDateTime(customerData.createdAt)}
                    </Typography>
                  </TimelineContent>
                </TimelineItem>

                {calls.slice(0, 5).map((call, idx) => (
                  <TimelineItem key={call.id}>
                    <TimelineSeparator>
                      <TimelineDot color={call.status === CallStatus.COMPLETED ? 'success' : 'error'}>
                        <Phone />
                      </TimelineDot>
                      {idx < 4 && <TimelineConnector />}
                    </TimelineSeparator>
                    <TimelineContent>
                      <Typography variant="subtitle2">
                        {call.agentType} Agent Call
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {formatDateTime(call.startTime)} • {formatDuration(call.duration || 0)}
                      </Typography>
                      {call.summary && (
                        <Chip
                          label={call.summary.sentiment}
                          size="small"
                          sx={{ mt: 1 }}
                        />
                      )}
                    </TimelineContent>
                  </TimelineItem>
                ))}
              </Timeline>
            </TabPanel>
          </Paper>
        </Grid>
      </Grid>

      {/* Edit Notes Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Customer Notes</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Notes"
            fullWidth
            multiline
            rows={4}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleUpdateNotes}
            disabled={updateMutation.isLoading}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Send SMS Dialog */}
      <Dialog open={smsDialog} onClose={() => setSmsDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Send SMS to {formatPhoneNumber(customerData.phoneNumber)}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Message"
            fullWidth
            multiline
            rows={4}
            value={smsMessage}
            onChange={(e) => setSmsMessage(e.target.value)}
            helperText={`${smsMessage.length}/160 characters`}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSmsDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            startIcon={<Send />}
            onClick={handleSendSMS}
            disabled={!smsMessage.trim() || sendSMSMutation.isLoading}
          >
            Send SMS
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}