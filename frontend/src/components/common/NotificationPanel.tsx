import {
  Drawer,
  Box,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
  Chip,
  Badge,
} from '@mui/material'
import {
  Close,
  Info,
  Warning,
  Error,
  CheckCircle,
  Delete,
  MarkEmailRead,
} from '@mui/icons-material'
import { useUIStore } from '@store/index'
import { NotificationType } from '@types/index'
import { formatRelativeTime } from '@utils/format'

interface NotificationPanelProps {
  open: boolean
  onClose: () => void
}

export default function NotificationPanel({ open, onClose }: NotificationPanelProps) {
  const { notifications, markNotificationRead, removeNotification, clearNotifications } = useUIStore()

  const unreadCount = notifications.filter((n) => !n.read).length

  const getIcon = (type: NotificationType) => {
    switch (type) {
      case NotificationType.INFO:
        return <Info color="info" />
      case NotificationType.WARNING:
        return <Warning color="warning" />
      case NotificationType.ERROR:
        return <Error color="error" />
      case NotificationType.SUCCESS:
        return <CheckCircle color="success" />
      default:
        return <Info />
    }
  }

  const getColor = (type: NotificationType) => {
    switch (type) {
      case NotificationType.INFO:
        return 'info'
      case NotificationType.WARNING:
        return 'warning'
      case NotificationType.ERROR:
        return 'error'
      case NotificationType.SUCCESS:
        return 'success'
      default:
        return 'default'
    }
  }

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: { width: 400 },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">
            Notifications
            {unreadCount > 0 && (
              <Chip
                label={unreadCount}
                color="primary"
                size="small"
                sx={{ ml: 1 }}
              />
            )}
          </Typography>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>
      </Box>

      <Divider />

      {notifications.length === 0 ? (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">No notifications</Typography>
        </Box>
      ) : (
        <>
          <List sx={{ flex: 1, overflow: 'auto' }}>
            {notifications.map((notification) => (
              <ListItem
                key={notification.id}
                sx={{
                  backgroundColor: notification.read ? 'transparent' : 'action.hover',
                  '&:hover': {
                    backgroundColor: 'action.hover',
                  },
                }}
                secondaryAction={
                  <Box>
                    {!notification.read && (
                      <IconButton
                        edge="end"
                        size="small"
                        onClick={() => markNotificationRead(notification.id)}
                      >
                        <MarkEmailRead fontSize="small" />
                      </IconButton>
                    )}
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={() => removeNotification(notification.id)}
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </Box>
                }
              >
                <ListItemIcon>{getIcon(notification.type)}</ListItemIcon>
                <ListItemText
                  primary={notification.title}
                  secondary={
                    <>
                      <Typography variant="body2" component="span">
                        {notification.message}
                      </Typography>
                      <Typography variant="caption" display="block" color="text.secondary">
                        {formatRelativeTime(notification.timestamp)}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>

          <Divider />

          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Button
              size="small"
              onClick={() => {
                notifications.filter((n) => !n.read).forEach((n) => markNotificationRead(n.id))
              }}
              disabled={unreadCount === 0}
            >
              Mark all as read
            </Button>
            <Button size="small" color="error" onClick={clearNotifications}>
              Clear all
            </Button>
          </Box>
        </>
      )}
    </Drawer>
  )
}