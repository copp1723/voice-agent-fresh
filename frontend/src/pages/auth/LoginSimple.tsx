import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Paper, TextField, Button, Typography, Alert } from '@mui/material'
import { useAuthStore } from '@store/index'

export default function LoginSimple() {
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)
  const [showAlert, setShowAlert] = useState(false)

  const handleBypassLogin = () => {
    // For testing, bypass authentication
    login({
      id: '1',
      email: 'test@example.com',
      username: 'Test User',
      role: 'admin',
    }, 'fake-token')
    
    navigate('/dashboard')
  }

  const handleRealLogin = () => {
    setShowAlert(true)
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f5f5',
      }}
    >
      <Paper elevation={3} sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Typography variant="h4" align="center" gutterBottom>
          Voice Agent Dashboard
        </Typography>
        
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
          Login to access the dashboard
        </Typography>

        {showAlert && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Backend authentication not connected. Use bypass login for testing.
          </Alert>
        )}

        <TextField
          fullWidth
          label="Email"
          defaultValue="admin@akillionvoice.xyz"
          margin="normal"
        />
        
        <TextField
          fullWidth
          label="Password"
          type="password"
          defaultValue="admin123"
          margin="normal"
        />
        
        <Button
          fullWidth
          variant="contained"
          size="large"
          onClick={handleRealLogin}
          sx={{ mt: 2, mb: 1 }}
        >
          Login (Requires Backend)
        </Button>
        
        <Button
          fullWidth
          variant="outlined"
          size="large"
          onClick={handleBypassLogin}
          color="secondary"
        >
          Bypass Login (For Testing)
        </Button>
        
        <Typography variant="caption" display="block" align="center" sx={{ mt: 2 }}>
          Use "Bypass Login" to test the dashboard without backend authentication
        </Typography>
      </Paper>
    </Box>
  )
}