import { useLocation, useNavigate } from 'react-router-dom'
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Collapse,
} from '@mui/material'
import {
  Dashboard,
  Phone,
  PhoneInTalk,
  History,
  SmartToy,
  People,
  Assessment,
  Settings,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material'
import { useState } from 'react'

interface MenuItem {
  text: string
  icon: React.ReactNode
  path: string
  children?: MenuItem[]
}

const menuItems: MenuItem[] = [
  {
    text: 'Dashboard',
    icon: <Dashboard />,
    path: '/dashboard',
  },
  {
    text: 'Calls',
    icon: <Phone />,
    path: '/calls',
    children: [
      {
        text: 'Active Calls',
        icon: <PhoneInTalk />,
        path: '/calls/active',
      },
      {
        text: 'Call History',
        icon: <History />,
        path: '/calls/history',
      },
    ],
  },
  {
    text: 'Agents',
    icon: <SmartToy />,
    path: '/agents',
  },
  {
    text: 'Customers',
    icon: <People />,
    path: '/customers',
  },
  {
    text: 'Reports',
    icon: <Assessment />,
    path: '/reports',
  },
  {
    text: 'Settings',
    icon: <Settings />,
    path: '/settings',
  },
]

export default function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({
    '/calls': true, // Default open
  })

  const handleItemClick = (item: MenuItem) => {
    if (item.children) {
      setOpenItems((prev) => ({
        ...prev,
        [item.path]: !prev[item.path],
      }))
    } else {
      navigate(item.path)
    }
  }

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  return (
    <Box sx={{ width: '100%', height: '100%', overflow: 'auto' }}>
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
          A Killion Voice
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Voice Agent System
        </Typography>
      </Box>
      
      <Divider />
      
      <List>
        {menuItems.map((item) => (
          <Box key={item.path}>
            <ListItem disablePadding>
              <ListItemButton
                selected={isActive(item.path) && !item.children}
                onClick={() => handleItemClick(item)}
              >
                <ListItemIcon
                  sx={{
                    color: isActive(item.path) ? 'primary.main' : 'inherit',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
                {item.children && (
                  openItems[item.path] ? <ExpandLess /> : <ExpandMore />
                )}
              </ListItemButton>
            </ListItem>
            
            {item.children && (
              <Collapse in={openItems[item.path]} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {item.children.map((child) => (
                    <ListItem key={child.path} disablePadding>
                      <ListItemButton
                        sx={{ pl: 4 }}
                        selected={isActive(child.path)}
                        onClick={() => navigate(child.path)}
                      >
                        <ListItemIcon
                          sx={{
                            color: isActive(child.path) ? 'primary.main' : 'inherit',
                          }}
                        >
                          {child.icon}
                        </ListItemIcon>
                        <ListItemText primary={child.text} />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            )}
          </Box>
        ))}
      </List>
    </Box>
  )
}