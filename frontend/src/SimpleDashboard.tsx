import { useState, useEffect } from 'react'
import { 
  ThemeProvider, CssBaseline, Container, Paper, Typography, 
  Button, Box, Grid, Card, CardContent, List, ListItem,
  ListItemText, Chip, AppBar, Toolbar, Tab, Tabs,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TextField, Alert
} from '@mui/material'
import { lightTheme } from './styles/theme'

// Simple dashboard without complex routing or authentication
export default function SimpleDashboard() {
  const [currentTab, setCurrentTab] = useState(0)
  const [calls, setCalls] = useState<any[]>([])
  const [agents, setAgents] = useState([
    { type: 'general', name: 'General Assistant', status: 'active', keywords: ['hello', 'help', 'information'] },
    { type: 'billing', name: 'Billing Specialist', status: 'active', keywords: ['bill', 'payment', 'invoice'] },
    { type: 'support', name: 'Support Agent', status: 'active', keywords: ['problem', 'issue', 'broken'] },
    { type: 'sales', name: 'Sales Representative', status: 'active', keywords: ['buy', 'purchase', 'price'] },
    { type: 'scheduling', name: 'Scheduling Assistant', status: 'active', keywords: ['appointment', 'schedule', 'book'] }
  ])
  const [apiStatus, setApiStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking')

  // Check API connection with error handling
  useEffect(() => {
    const checkApi = async () => {
      try {
        const res = await fetch('http://localhost:10000/health', { 
          method: 'GET',
          mode: 'cors',
          credentials: 'omit'
        })
        setApiStatus(res.ok ? 'connected' : 'disconnected')
      } catch (err) {
        setApiStatus('disconnected')
      }
    }
    checkApi()
    
    // Recheck every 30 seconds
    const interval = setInterval(checkApi, 30000)
    return () => clearInterval(interval)
  }, [])

  // Fetch calls if API is connected
  useEffect(() => {
    if (apiStatus === 'connected') {
      fetch('http://localhost:10000/api/calls')
        .then(res => res.json())
        .then(data => setCalls(Array.isArray(data) ? data : []))
        .catch(err => console.log('Could not fetch calls:', err))
    }
  }, [apiStatus])

  const renderDashboard = () => (
    <Grid container spacing={3}>
      {/* Status Cards */}
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>Active Calls</Typography>
            <Typography variant="h3">{calls.filter(c => c.status === 'active').length}</Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>Total Calls Today</Typography>
            <Typography variant="h3">{calls.length}</Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>Active Agents</Typography>
            <Typography variant="h3">{agents.length}</Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>API Status</Typography>
            <Chip 
              label={apiStatus} 
              color={apiStatus === 'connected' ? 'success' : 'error'}
              size="small"
            />
          </CardContent>
        </Card>
      </Grid>

      {/* Recent Calls */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Recent Calls</Typography>
          {calls.length > 0 ? (
            <List>
              {calls.slice(0, 5).map((call, idx) => (
                <ListItem key={idx}>
                  <ListItemText 
                    primary={`Call from ${call.from_number || 'Unknown'}`}
                    secondary={`Routed to: ${call.agent_type || 'general'} | Status: ${call.status}`}
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography color="textSecondary">No calls yet. {apiStatus !== 'connected' && 'Connect to API to see calls.'}</Typography>
          )}
        </Paper>
      </Grid>
    </Grid>
  )

  const renderAgents = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Agent Type</TableCell>
            <TableCell>Name</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Keywords</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {agents.map((agent) => (
            <TableRow key={agent.type}>
              <TableCell>{agent.type}</TableCell>
              <TableCell>{agent.name}</TableCell>
              <TableCell>
                <Chip label={agent.status} color="success" size="small" />
              </TableCell>
              <TableCell>
                {agent.keywords.map(kw => (
                  <Chip key={kw} label={kw} size="small" sx={{ mr: 0.5 }} />
                ))}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )

  const renderSettings = () => (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>API Configuration</Typography>
      <Box sx={{ mb: 3 }}>
        <Alert severity={apiStatus === 'connected' ? 'success' : 'warning'}>
          Backend API: {apiStatus === 'connected' 
            ? 'Connected to http://localhost:10000' 
            : 'Not connected. Run: python3 start_simple.py'}
        </Alert>
      </Box>
      
      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Environment Settings</Typography>
      <TextField
        fullWidth
        label="Twilio Phone Number"
        defaultValue="+19786432034"
        margin="normal"
        helperText="Configure in .env file"
      />
      <TextField
        fullWidth
        label="OpenRouter API Key"
        type="password"
        defaultValue="your-key-here"
        margin="normal"
        helperText="Required for AI responses"
      />
    </Paper>
  )

  return (
    <ThemeProvider theme={lightTheme}>
      <CssBaseline />
      
      {/* App Bar */}
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Voice Agent Dashboard (Simplified)
          </Typography>
          <Typography variant="caption">
            {new Date().toLocaleString()}
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={currentTab} onChange={(_, v) => setCurrentTab(v)}>
          <Tab label="Dashboard" />
          <Tab label="Agents" />
          <Tab label="Settings" />
        </Tabs>
      </Box>

      {/* Content */}
      <Container maxWidth="lg" sx={{ mt: 3, mb: 3 }}>
        {currentTab === 0 && renderDashboard()}
        {currentTab === 1 && renderAgents()}
        {currentTab === 2 && renderSettings()}
      </Container>
    </ThemeProvider>
  )
}