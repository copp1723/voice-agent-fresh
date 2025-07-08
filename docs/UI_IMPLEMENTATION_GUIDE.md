# UI Implementation Technical Guide

## Overview

This guide provides technical specifications for implementing the Voice Agent Dashboard UI based on the UI/UX requirements. It includes component structures, API endpoints, state management patterns, and code examples.

## Tech Stack Recommendation

### Frontend Framework: React 18+ with TypeScript

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@mui/material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "axios": "^1.6.0",
    "socket.io-client": "^4.7.0",
    "react-query": "^3.39.0",
    "recharts": "^2.10.0",
    "date-fns": "^2.30.0",
    "react-hook-form": "^7.48.0",
    "notistack": "^3.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0"
  }
}
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Layout/
│   │   │   ├── Navigation/
│   │   │   ├── LoadingStates/
│   │   │   └── ErrorBoundary/
│   │   ├── dashboard/
│   │   │   ├── DashboardOverview/
│   │   │   ├── MetricsCards/
│   │   │   ├── ActiveCallsWidget/
│   │   │   └── RecentCallsList/
│   │   ├── calls/
│   │   │   ├── ActiveCallsMonitor/
│   │   │   ├── CallHistory/
│   │   │   ├── CallDetails/
│   │   │   └── CallTranscription/
│   │   ├── agents/
│   │   │   ├── AgentList/
│   │   │   ├── AgentConfig/
│   │   │   ├── AgentPerformance/
│   │   │   └── KeywordManager/
│   │   └── reports/
│   │       ├── ReportBuilder/
│   │       ├── Charts/
│   │       └── ExportOptions/
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useAuth.ts
│   │   ├── useCallData.ts
│   │   └── useNotifications.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── auth.ts
│   ├── store/
│   │   ├── callStore.ts
│   │   ├── agentStore.ts
│   │   └── userStore.ts
│   ├── types/
│   │   ├── call.types.ts
│   │   ├── agent.types.ts
│   │   └── user.types.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── theme/
│   │   └── theme.ts
│   ├── App.tsx
│   └── main.tsx
```

## API Integration

### Base API Configuration

```typescript
// src/services/api.ts
import axios from 'axios';

const API_BASE_URL = process.env.VITE_API_URL || 'https://api.akillionvoice.xyz';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('api_key');
  if (token) {
    config.headers['X-API-Key'] = token;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### API Endpoints Mapping

```typescript
// src/services/endpoints.ts
export const endpoints = {
  // Health & Status
  health: '/health',
  
  // Calls
  calls: {
    list: '/api/calls',
    active: '/api/calls/active',
    details: (id: string) => `/api/calls/${id}`,
    transcription: (id: string) => `/api/calls/${id}/transcription`,
  },
  
  // Agents
  agents: {
    list: '/api/agents',
    config: (type: string) => `/api/agents/${type}`,
    update: (type: string) => `/api/agents/${type}`,
    performance: (type: string) => `/api/agents/${type}/performance`,
  },
  
  // SMS
  sms: {
    logs: '/api/sms/logs',
    send: '/api/sms/send',
  },
  
  // Reports
  reports: {
    daily: '/api/reports/daily',
    custom: '/api/reports/custom',
    export: '/api/reports/export',
  },
  
  // WebSocket
  ws: {
    calls: 'wss://api.akillionvoice.xyz/ws/calls',
  },
};
```

## Real-time Updates with WebSocket

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef } from 'react';
import io, { Socket } from 'socket.io-client';

export const useWebSocket = (onMessage: (data: any) => void) => {
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    socketRef.current = io(process.env.VITE_WS_URL || 'wss://api.akillionvoice.xyz', {
      transports: ['websocket'],
      auth: {
        token: localStorage.getItem('api_key'),
      },
    });

    socketRef.current.on('call:update', onMessage);
    socketRef.current.on('call:new', onMessage);
    socketRef.current.on('call:end', onMessage);

    return () => {
      socketRef.current?.disconnect();
    };
  }, [onMessage]);

  return socketRef.current;
};
```

## Key Component Examples

### Dashboard Overview Component

```typescript
// src/components/dashboard/DashboardOverview.tsx
import React from 'react';
import { Grid, Paper, Typography, Box } from '@mui/material';
import { useQuery } from 'react-query';
import { MetricsCard } from './MetricsCards';
import { ActiveCallsWidget } from './ActiveCallsWidget';
import { RecentCallsList } from './RecentCallsList';
import { api } from '../../services/api';

export const DashboardOverview: React.FC = () => {
  const { data: metrics, isLoading } = useQuery(
    'dashboardMetrics',
    () => api.get('/api/metrics/today').then(res => res.data),
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  if (isLoading) return <LoadingState />;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard Overview
      </Typography>
      
      <Grid container spacing={3}>
        {/* Metrics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <MetricsCard
            title="Total Calls Today"
            value={metrics?.totalCalls || 0}
            trend={metrics?.callsTrend}
            icon="phone"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricsCard
            title="Average Duration"
            value={`${metrics?.avgDuration || 0}s`}
            trend={metrics?.durationTrend}
            icon="timer"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricsCard
            title="SMS Sent"
            value={metrics?.smsSent || 0}
            trend={metrics?.smsTrend}
            icon="message"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricsCard
            title="Routing Accuracy"
            value={`${metrics?.routingAccuracy || 0}%`}
            trend={metrics?.accuracyTrend}
            icon="target"
          />
        </Grid>

        {/* Active Calls */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '400px' }}>
            <ActiveCallsWidget />
          </Paper>
        </Grid>

        {/* Recent Calls */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '400px' }}>
            <RecentCallsList limit={10} />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
```

### Active Call Monitor Component

```typescript
// src/components/calls/ActiveCallsMonitor.tsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  Button,
  LinearProgress,
} from '@mui/material';
import { useWebSocket } from '../../hooks/useWebSocket';
import { Call } from '../../types/call.types';

export const ActiveCallsMonitor: React.FC = () => {
  const [activeCalls, setActiveCalls] = useState<Call[]>([]);

  const handleCallUpdate = (data: any) => {
    if (data.type === 'call:new') {
      setActiveCalls(prev => [...prev, data.call]);
    } else if (data.type === 'call:update') {
      setActiveCalls(prev =>
        prev.map(call => call.id === data.call.id ? data.call : call)
      );
    } else if (data.type === 'call:end') {
      setActiveCalls(prev => prev.filter(call => call.id !== data.callId));
    }
  };

  useWebSocket(handleCallUpdate);

  return (
    <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))' }}>
      {activeCalls.map(call => (
        <CallCard key={call.id} call={call} />
      ))}
    </Box>
  );
};

const CallCard: React.FC<{ call: Call }> = ({ call }) => {
  const duration = Math.floor((Date.now() - new Date(call.startTime).getTime()) / 1000);

  return (
    <Card sx={{ position: 'relative' }}>
      <LinearProgress
        variant="determinate"
        value={(call.messageCount / 20) * 100}
        sx={{ position: 'absolute', top: 0, left: 0, right: 0 }}
      />
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">
            {call.fromNumber}
          </Typography>
          <Chip
            label={call.agentType}
            color="primary"
            size="small"
          />
        </Box>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Duration: {formatDuration(duration)}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Confidence: {(call.routingConfidence * 100).toFixed(0)}%
        </Typography>
        
        <Box sx={{ mt: 2 }}>
          <Button size="small" variant="outlined" sx={{ mr: 1 }}>
            Monitor
          </Button>
          <Button size="small" variant="contained" color="warning">
            Take Over
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};
```

### Agent Configuration Component

```typescript
// src/components/agents/AgentConfig.tsx
import React from 'react';
import {
  Paper,
  TextField,
  Button,
  Box,
  Typography,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { useMutation, useQueryClient } from 'react-query';
import { api } from '../../services/api';

interface AgentConfigProps {
  agentType: string;
  config: AgentConfig;
}

export const AgentConfigForm: React.FC<AgentConfigProps> = ({ agentType, config }) => {
  const queryClient = useQueryClient();
  const { control, handleSubmit, watch } = useForm({
    defaultValues: config,
  });

  const mutation = useMutation(
    (data: AgentConfig) => api.put(`/api/agents/${agentType}`, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['agents']);
        // Show success notification
      },
    }
  );

  const onSubmit = (data: AgentConfig) => {
    mutation.mutate(data);
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Configure {config.name}
      </Typography>
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Agent Name"
                fullWidth
              />
            )}
          />
          
          <Controller
            name="systemPrompt"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="System Prompt"
                multiline
                rows={4}
                fullWidth
                helperText="Define how the agent should behave"
              />
            )}
          />
          
          <Controller
            name="keywords"
            control={control}
            render={({ field }) => (
              <KeywordInput
                value={field.value}
                onChange={field.onChange}
                label="Routing Keywords"
              />
            )}
          />
          
          <Controller
            name="voiceModel"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth>
                <InputLabel>Voice Model</InputLabel>
                <Select {...field}>
                  <MenuItem value="alloy">Alloy (Neutral)</MenuItem>
                  <MenuItem value="echo">Echo (Calm)</MenuItem>
                  <MenuItem value="fable">Fable (Warm)</MenuItem>
                  <MenuItem value="nova">Nova (Friendly)</MenuItem>
                  <MenuItem value="shimmer">Shimmer (Gentle)</MenuItem>
                </Select>
              </FormControl>
            )}
          />
          
          <Controller
            name="smsTemplate"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="SMS Template"
                multiline
                rows={3}
                fullWidth
                helperText="Use {summary} to insert call summary"
              />
            )}
          />
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              type="submit"
              variant="contained"
              disabled={mutation.isLoading}
            >
              Save Configuration
            </Button>
            <Button variant="outlined">
              Test Agent
            </Button>
          </Box>
        </Box>
      </form>
    </Paper>
  );
};
```

## State Management

### Using Zustand for Global State

```typescript
// src/store/callStore.ts
import { create } from 'zustand';
import { Call } from '../types/call.types';

interface CallStore {
  activeCalls: Call[];
  callHistory: Call[];
  selectedCall: Call | null;
  setActiveCalls: (calls: Call[]) => void;
  updateCall: (callId: string, update: Partial<Call>) => void;
  selectCall: (call: Call | null) => void;
}

export const useCallStore = create<CallStore>((set) => ({
  activeCalls: [],
  callHistory: [],
  selectedCall: null,
  
  setActiveCalls: (calls) => set({ activeCalls: calls }),
  
  updateCall: (callId, update) => set((state) => ({
    activeCalls: state.activeCalls.map(call =>
      call.id === callId ? { ...call, ...update } : call
    ),
  })),
  
  selectCall: (call) => set({ selectedCall: call }),
}));
```

## Theme Configuration

```typescript
// src/theme/theme.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
    },
    success: {
      main: '#4caf50',
    },
    warning: {
      main: '#ff9800',
    },
    error: {
      main: '#f44336',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});
```

## Responsive Design Utilities

```typescript
// src/utils/responsive.ts
export const breakpoints = {
  mobile: '(max-width: 768px)',
  tablet: '(min-width: 769px) and (max-width: 1024px)',
  desktop: '(min-width: 1025px)',
};

export const useMediaQuery = (query: string) => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }
    const listener = () => setMatches(media.matches);
    media.addListener(listener);
    return () => media.removeListener(listener);
  }, [matches, query]);

  return matches;
};
```

## Error Handling

```typescript
// src/components/common/ErrorBoundary.tsx
import React, { Component, ReactNode } from 'react';
import { Box, Typography, Button } from '@mui/material';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Send to error tracking service
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Something went wrong
          </Typography>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            {this.state.error?.message}
          </Typography>
          <Button
            variant="contained"
            onClick={() => window.location.reload()}
            sx={{ mt: 2 }}
          >
            Reload Page
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}
```

## Performance Optimization

### Virtual Scrolling for Large Lists

```typescript
// src/components/common/VirtualList.tsx
import React from 'react';
import { FixedSizeList } from 'react-window';

interface VirtualListProps<T> {
  items: T[];
  height: number;
  itemSize: number;
  renderItem: (item: T, index: number) => React.ReactNode;
}

export function VirtualList<T>({ items, height, itemSize, renderItem }: VirtualListProps<T>) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      {renderItem(items[index], index)}
    </div>
  );

  return (
    <FixedSizeList
      height={height}
      itemCount={items.length}
      itemSize={itemSize}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

## Testing Strategy

```typescript
// src/components/dashboard/__tests__/DashboardOverview.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { DashboardOverview } from '../DashboardOverview';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('DashboardOverview', () => {
  it('renders metrics cards', async () => {
    render(<DashboardOverview />, { wrapper });
    
    await waitFor(() => {
      expect(screen.getByText('Total Calls Today')).toBeInTheDocument();
      expect(screen.getByText('Average Duration')).toBeInTheDocument();
    });
  });
});
```

## Deployment Configuration

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'https://api.akillionvoice.xyz',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

### Environment Variables

```env
# .env.example
VITE_API_URL=https://api.akillionvoice.xyz
VITE_WS_URL=wss://api.akillionvoice.xyz
VITE_GOOGLE_MAPS_KEY=your-key-here
VITE_SENTRY_DSN=your-sentry-dsn
```

## Security Considerations

1. **API Key Storage**: Use secure httpOnly cookies when possible
2. **XSS Prevention**: Sanitize all user inputs
3. **CSRF Protection**: Implement CSRF tokens
4. **Content Security Policy**: Configure CSP headers
5. **Regular Security Audits**: Use npm audit regularly

## Performance Checklist

- [ ] Implement code splitting with React.lazy()
- [ ] Use React.memo for expensive components
- [ ] Implement virtual scrolling for long lists
- [ ] Optimize bundle size with tree shaking
- [ ] Enable gzip compression
- [ ] Implement service worker for offline support
- [ ] Use CDN for static assets
- [ ] Implement proper caching strategies

## Accessibility Checklist

- [ ] All interactive elements have proper focus states
- [ ] ARIA labels for all icons and buttons
- [ ] Proper heading hierarchy (h1 → h2 → h3)
- [ ] Color contrast meets WCAG AA standards
- [ ] Keyboard navigation fully functional
- [ ] Screen reader announcements for updates
- [ ] Skip navigation links
- [ ] Form validation messages are accessible

This implementation guide provides the technical foundation for building the Voice Agent Dashboard UI. Follow these patterns and examples to ensure consistency and maintainability across the application.