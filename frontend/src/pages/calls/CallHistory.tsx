import { useState, useCallback } from 'react'
import {
  Box,
  Typography,
  Paper,
  TextField,
  InputAdornment,
  IconButton,
  Button,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tooltip,
  LinearProgress,
  Menu,
  Divider,
} from '@mui/material'
import {
  Search,
  FilterList,
  Download,
  Phone,
  Visibility,
  PlayArrow,
  Message,
  MoreVert,
  CalendarToday,
  Clear,
  CheckCircle,
  Cancel,
  Warning,
  Schedule,
} from '@mui/icons-material'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { useApiQuery, useApiMutation } from '@hooks/useApi'
import { callService } from '@services/endpoints'
import { Call, CallStatus, AgentType, CallFilters } from '@types'
import { formatDuration, formatDateTime, formatPhoneNumber } from '@utils/format'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'

interface CallRowProps {
  call: Call
  onView: (call: Call) => void
  onPlayRecording: (call: Call) => void
}

function CallRow({ call, onView, onPlayRecording }: CallRowProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const navigate = useNavigate()

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const getStatusIcon = (status: CallStatus) => {
    switch (status) {
      case CallStatus.COMPLETED:
        return <CheckCircle color="success" fontSize="small" />
      case CallStatus.FAILED:
        return <Cancel color="error" fontSize="small" />
      case CallStatus.IN_PROGRESS:
        return <Schedule color="primary" fontSize="small" />
      default:
        return <Warning color="warning" fontSize="small" />
    }
  }

  const getStatusColor = (status: CallStatus) => {
    switch (status) {
      case CallStatus.COMPLETED:
        return 'success'
      case CallStatus.FAILED:
        return 'error'
      case CallStatus.IN_PROGRESS:
        return 'primary'
      default:
        return 'warning'
    }
  }

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive':
        return 'success'
      case 'negative':
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <TableRow hover>
      <TableCell>
        <Box display="flex" alignItems="center" gap={1}>
          <Phone fontSize="small" color="action" />
          <Typography variant="body2">
            {formatPhoneNumber(call.phoneNumber)}
          </Typography>
        </Box>
      </TableCell>
      <TableCell>
        <Chip
          label={call.agentType}
          size="small"
          variant="outlined"
        />
      </TableCell>
      <TableCell>
        <Typography variant="body2">
          {formatDateTime(call.startTime)}
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2">
          {formatDuration(call.duration || 0)}
        </Typography>
      </TableCell>
      <TableCell>
        <Box display="flex" alignItems="center" gap={0.5}>
          {getStatusIcon(call.status)}
          <Chip
            label={call.status}
            size="small"
            color={getStatusColor(call.status) as any}
          />
        </Box>
      </TableCell>
      <TableCell>
        {call.summary && (
          <Chip
            label={call.summary.sentiment}
            size="small"
            variant="outlined"
            color={getSentimentColor(call.summary.sentiment) as any}
          />
        )}
      </TableCell>
      <TableCell align="right">
        <Box display="flex" justifyContent="flex-end" gap={1}>
          <Tooltip title="View Details">
            <IconButton size="small" onClick={() => onView(call)}>
              <Visibility fontSize="small" />
            </IconButton>
          </Tooltip>
          {call.status === CallStatus.COMPLETED && (
            <Tooltip title="Play Recording">
              <IconButton size="small" onClick={() => onPlayRecording(call)}>
                <PlayArrow fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          <IconButton size="small" onClick={handleMenuOpen}>
            <MoreVert fontSize="small" />
          </IconButton>
        </Box>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={() => {
            navigate(`/calls/${call.id}`)
            handleMenuClose()
          }}>
            View Full Details
          </MenuItem>
          <MenuItem onClick={() => {
            navigate(`/customers?phone=${call.phoneNumber}`)
            handleMenuClose()
          }}>
            View Customer
          </MenuItem>
          {call.smsStatus && (
            <MenuItem onClick={handleMenuClose}>
              View SMS Status
            </MenuItem>
          )}
          <Divider />
          <MenuItem onClick={handleMenuClose}>
            Download Recording
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            Export Transcript
          </MenuItem>
        </Menu>
      </TableCell>
    </TableRow>
  )
}

export default function CallHistory() {
  const navigate = useNavigate()
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [selectedCall, setSelectedCall] = useState<Call | null>(null)
  const [detailsDialog, setDetailsDialog] = useState(false)
  const [recordingDialog, setRecordingDialog] = useState(false)
  const [exportDialog, setExportDialog] = useState(false)
  
  const [filters, setFilters] = useState<CallFilters>({
    searchTerm: '',
    agentType: undefined,
    status: undefined,
    dateFrom: undefined,
    dateTo: undefined,
  })

  const [showFilters, setShowFilters] = useState(false)

  const { data: calls, isLoading } = useApiQuery(
    ['calls', 'history', page, rowsPerPage, filters],
    () => callService.getCallHistory({
      page: page + 1,
      pageSize: rowsPerPage,
      ...filters,
    }),
    {
      keepPreviousData: true,
    }
  )

  const exportMutation = useApiMutation(
    (params: any) => callService.exportCalls(params),
    {
      onSuccess: (response) => {
        // Handle file download
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `calls-export-${format(new Date(), 'yyyy-MM-dd')}.csv`)
        document.body.appendChild(link)
        link.click()
        link.remove()
      },
    }
  )

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const handleSearch = useCallback((searchTerm: string) => {
    setFilters(prev => ({ ...prev, searchTerm }))
    setPage(0)
  }, [])

  const handleClearFilters = () => {
    setFilters({
      searchTerm: '',
      agentType: undefined,
      status: undefined,
      dateFrom: undefined,
      dateTo: undefined,
    })
    setPage(0)
  }

  const handleExport = () => {
    exportMutation.mutate(filters)
    setExportDialog(false)
  }

  const handleViewCall = (call: Call) => {
    setSelectedCall(call)
    setDetailsDialog(true)
  }

  const handlePlayRecording = (call: Call) => {
    setSelectedCall(call)
    setRecordingDialog(true)
  }

  const callsData = calls?.data || { data: [], total: 0 }
  const hasActiveFilters = filters.searchTerm || filters.agentType || filters.status || filters.dateFrom || filters.dateTo

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Call History
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Search and manage all historical calls
            </Typography>
          </Box>
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={() => setExportDialog(true)}
            >
              Export
            </Button>
          </Box>
        </Box>

        {/* Search and Filters */}
        <Paper sx={{ mb: 3, p: 2 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search by phone number, agent, or transcript..."
                value={filters.searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                  endAdornment: filters.searchTerm && (
                    <InputAdornment position="end">
                      <IconButton
                        size="small"
                        onClick={() => handleSearch('')}
                      >
                        <Clear />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box display="flex" justifyContent="flex-end" gap={2}>
                <Button
                  variant={showFilters ? 'contained' : 'outlined'}
                  startIcon={<FilterList />}
                  onClick={() => setShowFilters(!showFilters)}
                >
                  Filters
                  {hasActiveFilters && (
                    <Chip
                      label={Object.values(filters).filter(Boolean).length}
                      size="small"
                      color="primary"
                      sx={{ ml: 1 }}
                    />
                  )}
                </Button>
                {hasActiveFilters && (
                  <Button
                    variant="text"
                    onClick={handleClearFilters}
                  >
                    Clear All
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>

          {/* Filter Controls */}
          {showFilters && (
            <>
              <Divider sx={{ my: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Agent Type</InputLabel>
                    <Select
                      value={filters.agentType || ''}
                      onChange={(e) => setFilters({ ...filters, agentType: e.target.value as AgentType || undefined })}
                    >
                      <MenuItem value="">All</MenuItem>
                      {Object.values(AgentType).map(type => (
                        <MenuItem key={type} value={type}>{type}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Status</InputLabel>
                    <Select
                      value={filters.status || ''}
                      onChange={(e) => setFilters({ ...filters, status: e.target.value as CallStatus || undefined })}
                    >
                      <MenuItem value="">All</MenuItem>
                      {Object.values(CallStatus).map(status => (
                        <MenuItem key={status} value={status}>{status}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <DatePicker
                    label="From Date"
                    value={filters.dateFrom ? new Date(filters.dateFrom) : null}
                    onChange={(date) => setFilters({ ...filters, dateFrom: date ? format(date, 'yyyy-MM-dd') : undefined })}
                    slotProps={{ textField: { size: 'small', fullWidth: true } }}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <DatePicker
                    label="To Date"
                    value={filters.dateTo ? new Date(filters.dateTo) : null}
                    onChange={(date) => setFilters({ ...filters, dateTo: date ? format(date, 'yyyy-MM-dd') : undefined })}
                    slotProps={{ textField: { size: 'small', fullWidth: true } }}
                  />
                </Grid>
              </Grid>
            </>
          )}
        </Paper>

        {/* Calls Table */}
        <Paper>
          {isLoading && <LinearProgress />}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Phone Number</TableCell>
                  <TableCell>Agent</TableCell>
                  <TableCell>Date & Time</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Sentiment</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {callsData.data.map((call) => (
                  <CallRow
                    key={call.id}
                    call={call}
                    onView={handleViewCall}
                    onPlayRecording={handlePlayRecording}
                  />
                ))}
                {callsData.data.length === 0 && !isLoading && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Box py={4}>
                        <Phone sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                        <Typography variant="body1" color="text.secondary">
                          No calls found matching your criteria
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={callsData.total}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </Paper>

        {/* Call Details Dialog */}
        <Dialog
          open={detailsDialog}
          onClose={() => setDetailsDialog(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Call Details - {selectedCall && formatPhoneNumber(selectedCall.phoneNumber)}
          </DialogTitle>
          <DialogContent dividers>
            {selectedCall && (
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Call ID
                  </Typography>
                  <Typography variant="body1">{selectedCall.callSid}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Duration
                  </Typography>
                  <Typography variant="body1">
                    {formatDuration(selectedCall.duration || 0)}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Start Time
                  </Typography>
                  <Typography variant="body1">
                    {formatDateTime(selectedCall.startTime)}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    End Time
                  </Typography>
                  <Typography variant="body1">
                    {selectedCall.endTime ? formatDateTime(selectedCall.endTime) : 'N/A'}
                  </Typography>
                </Grid>
                {selectedCall.summary && (
                  <>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Summary
                      </Typography>
                      <Typography variant="body1">
                        {selectedCall.summary.summary}
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Keywords
                      </Typography>
                      <Box display="flex" gap={1} flexWrap="wrap" mt={1}>
                        {selectedCall.summary.keywords.map((keyword, idx) => (
                          <Chip key={idx} label={keyword} size="small" />
                        ))}
                      </Box>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Action Items
                      </Typography>
                      <Box mt={1}>
                        {selectedCall.summary.actionItems.map((item, idx) => (
                          <Typography key={idx} variant="body2">
                            • {item}
                          </Typography>
                        ))}
                      </Box>
                    </Grid>
                  </>
                )}
              </Grid>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDetailsDialog(false)}>Close</Button>
            <Button
              variant="contained"
              onClick={() => navigate(`/calls/${selectedCall?.id}`)}
            >
              View Full Details
            </Button>
          </DialogActions>
        </Dialog>

        {/* Export Dialog */}
        <Dialog open={exportDialog} onClose={() => setExportDialog(false)}>
          <DialogTitle>Export Calls</DialogTitle>
          <DialogContent>
            <Typography variant="body2" paragraph>
              Export the current filtered call list to CSV format.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {callsData.total} calls will be exported based on current filters.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setExportDialog(false)}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleExport}
              disabled={exportMutation.isLoading}
            >
              Export to CSV
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  )
}