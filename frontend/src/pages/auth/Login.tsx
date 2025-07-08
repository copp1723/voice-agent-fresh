import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
} from '@mui/material'
import { Visibility, VisibilityOff, Phone } from '@mui/icons-material'
import { useForm } from 'react-hook-form'
import { useAuthStore } from '@store/index'
import { authService } from '@services/endpoints'
import { useApiMutation } from '@hooks/useApi'

interface LoginFormData {
  username: string
  password: string
}

export default function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [showPassword, setShowPassword] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>()

  const loginMutation = useApiMutation(
    (data: LoginFormData) => authService.login(data.username, data.password),
    {
      onSuccess: (response) => {
        const { token, user } = response.data
        setAuth(user, token)
        localStorage.setItem('authToken', token)
        navigate('/dashboard')
      },
    },
  )

  const onSubmit = (data: LoginFormData) => {
    loginMutation.mutate(data)
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ mb: 3, textAlign: 'center' }}>
        <Phone sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography component="h1" variant="h5">
          Voice Agent Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Sign in to manage your voice agents
        </Typography>
      </Box>

      {loginMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {loginMutation.error?.message || 'Invalid username or password'}
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <TextField
          {...register('username', { required: 'Username is required' })}
          fullWidth
          label="Username"
          margin="normal"
          error={!!errors.username}
          helperText={errors.username?.message}
          disabled={loginMutation.isPending}
        />

        <TextField
          {...register('password', { required: 'Password is required' })}
          fullWidth
          label="Password"
          type={showPassword ? 'text' : 'password'}
          margin="normal"
          error={!!errors.password}
          helperText={errors.password?.message}
          disabled={loginMutation.isPending}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  aria-label="toggle password visibility"
                  onClick={() => setShowPassword(!showPassword)}
                  edge="end"
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <Button
          type="submit"
          fullWidth
          variant="contained"
          sx={{ mt: 3, mb: 2 }}
          disabled={loginMutation.isPending}
        >
          {loginMutation.isPending ? (
            <CircularProgress size={24} color="inherit" />
          ) : (
            'Sign In'
          )}
        </Button>

        {/* For demo purposes - remove in production */}
        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
          <Typography variant="caption" display="block" gutterBottom>
            Demo Credentials:
          </Typography>
          <Typography variant="caption" display="block">
            Username: admin / Password: admin123
          </Typography>
        </Box>
      </form>
    </Box>
  )
}