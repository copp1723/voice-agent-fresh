# Voice Agent Dashboard Frontend

A modern, real-time dashboard for managing AI-powered voice agents built with React, TypeScript, and Material-UI.

## Architecture Overview

### Technology Stack

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI (MUI) v5
- **State Management**: Zustand (client state) + React Query (server state)
- **Real-time**: Socket.io Client
- **Routing**: React Router v6
- **Forms**: React Hook Form
- **Charts**: Chart.js with react-chartjs-2
- **Testing**: Vitest + React Testing Library

### Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── common/      # Shared components
│   │   ├── dashboard/   # Dashboard-specific components
│   │   ├── calls/       # Call-related components
│   │   ├── agents/      # Agent-related components
│   │   └── ...
│   ├── pages/           # Page components (routes)
│   ├── layouts/         # Layout components
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API and WebSocket services
│   ├── store/           # Zustand stores
│   ├── utils/           # Utility functions
│   ├── types/           # TypeScript type definitions
│   ├── styles/          # Theme and global styles
│   └── tests/           # Test files
├── public/              # Static assets
└── package.json
```

### Key Features

1. **Real-time Updates**: WebSocket integration for live call monitoring
2. **Type Safety**: Full TypeScript coverage
3. **Responsive Design**: Mobile-first approach with MUI
4. **State Management**: Efficient client/server state separation
5. **Performance**: Code splitting and lazy loading
6. **Testing**: Comprehensive test setup with Vitest

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend server running on port 5000

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Generate coverage report
- `npm run lint` - Run ESLint

## Development Guidelines

### Code Style

- Use functional components with hooks
- Follow React best practices
- Maintain consistent file naming (PascalCase for components)
- Use path aliases for imports (@components, @utils, etc.)

### State Management

- **Zustand**: UI state, user preferences, notifications
- **React Query**: Server data, caching, synchronization
- **Local State**: Component-specific state only

### API Integration

All API calls go through the centralized API service:

```typescript
import { apiClient } from '@services/api'

// Example usage
const response = await apiClient.get<User[]>('/users')
```

### WebSocket Events

Subscribe to real-time events using the WebSocket service:

```typescript
import { useWebSocket } from '@hooks/useWebSocket'

// In component
const { on, emit } = useWebSocket()

useEffect(() => {
  const unsubscribe = on('call:started', handleCallStarted)
  return unsubscribe
}, [])
```

### Component Development

1. Create component in appropriate directory
2. Add TypeScript types
3. Use MUI components and theme
4. Add loading and error states
5. Write tests

### Testing

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test -- --watch

# Run specific test file
npm run test format.test.ts
```

## Environment Variables

```env
VITE_API_BASE_URL=http://localhost:5000
VITE_API_KEY=your-api-key
VITE_WS_URL=ws://localhost:5000
VITE_ENABLE_ANALYTICS=true
VITE_ENV=development
```

## Building for Production

```bash
# Build the application
npm run build

# The build output will be in ../src/static/dashboard
# This integrates with the Flask backend
```

## Architecture Decisions

1. **Vite over Create React App**: Faster builds and better DX
2. **Material-UI**: Comprehensive component library with accessibility
3. **Zustand over Redux**: Simpler state management for this scale
4. **React Query**: Powerful server state management
5. **TypeScript**: Type safety and better IDE support

## Future Enhancements

1. Implement comprehensive error boundaries
2. Add performance monitoring
3. Implement progressive web app features
4. Add end-to-end testing with Playwright
5. Implement data visualization dashboards
6. Add voice recording playback features

## Contributing

1. Follow the established patterns
2. Write tests for new features
3. Update types when modifying API
4. Ensure responsive design
5. Document complex logic

## License

Proprietary - A Killion Voice