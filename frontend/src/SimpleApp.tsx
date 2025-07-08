import { useState } from 'react'
import { ThemeProvider, CssBaseline, Container, Paper, Typography, Button, Box } from '@mui/material'
import { lightTheme } from './styles/theme'

export default function SimpleApp() {
  const [page, setPage] = useState('dashboard')
  
  const renderPage = () => {
    switch(page) {
      case 'dashboard':
        return (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>Voice Agent Dashboard</Typography>
            <Typography variant="body1" paragraph>
              Welcome to the Voice Agent Dashboard. This is a simplified version to verify the UI works.
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Button variant="contained" onClick={() => setPage('calls')} sx={{ mr: 1 }}>
                View Calls
              </Button>
              <Button variant="outlined" onClick={() => setPage('agents')}>
                Configure Agents
              </Button>
            </Box>
          </Paper>
        )
      
      case 'calls':
        return (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>Active Calls</Typography>
            <Typography variant="body1">No active calls at the moment.</Typography>
            <Button onClick={() => setPage('dashboard')} sx={{ mt: 2 }}>Back to Dashboard</Button>
          </Paper>
        )
      
      case 'agents':
        return (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>Agent Configuration</Typography>
            <Typography variant="body1">5 agents configured: General, Billing, Support, Sales, Scheduling</Typography>
            <Button onClick={() => setPage('dashboard')} sx={{ mt: 2 }}>Back to Dashboard</Button>
          </Paper>
        )
      
      default:
        return <Typography>Page not found</Typography>
    }
  }
  
  return (
    <ThemeProvider theme={lightTheme}>
      <CssBaseline />
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Voice Agent System
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Simplified UI (Backend: {window.location.port === '3000' ? 'http://localhost:10000' : 'Connected'})
          </Typography>
        </Box>
        {renderPage()}
      </Container>
    </ThemeProvider>
  )
}