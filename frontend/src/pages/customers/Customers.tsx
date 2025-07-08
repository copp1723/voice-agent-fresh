import { useState } from 'react'
import {
  Box,
  Typography,
  Paper,
  TextField,
  InputAdornment,
  IconButton,
  Button,
  Chip,
  Avatar,
  Grid,
  Card,
  CardContent,
  CardActions,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Badge,
  Tooltip,
  LinearProgress,
  Autocomplete,
} from '@mui/material'
import {
  Search,
  Add,
  Person,
  Phone,
  Email,
  Tag,
  Notes,
  History,
  Message,
  TrendingUp,
  TrendingDown,
  Clear,
  Edit,
  FilterList,
} from '@mui/icons-material'
import { useApiQuery, useApiMutation } from '@hooks/useApi'
import { customerService } from '@services/endpoints'
import { Customer, CustomerFormData, Call, SMSConversation, Sentiment } from '@types'
import { formatPhoneNumber, formatDateTime } from '@utils/format'
import { useNavigate } from 'react-router-dom'

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
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  )
}

interface CustomerCardProps {
  customer: Customer
  onEdit: (customer: Customer) => void
  onView: (customer: Customer) => void
}

function CustomerCard({ customer, onEdit, onView }: CustomerCardProps) {
  const getSentimentIcon = (sentiment?: Sentiment) => {
    if (!sentiment) return null
    switch (sentiment) {
      case Sentiment.POSITIVE:
        return <TrendingUp color="success" fontSize="small" />
      case Sentiment.NEGATIVE:
        return <TrendingDown color="error" fontSize="small" />
      default:
        return null
    }
  }

  const getInitials = (firstName?: string, lastName?: string) => {
    if (!firstName && !lastName) return '?'
    return `${firstName?.[0] || ''}${lastName?.[0] || ''}`.toUpperCase()
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Avatar sx={{ width: 56, height: 56, bgcolor: 'primary.main' }}>
            {getInitials(customer.firstName, customer.lastName)}
          </Avatar>
          <Box flex={1}>
            <Typography variant="h6">
              {customer.firstName || customer.lastName
                ? `${customer.firstName || ''} ${customer.lastName || ''}`.trim()
                : 'Unknown Customer'}
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <Phone fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {formatPhoneNumber(customer.phoneNumber)}
              </Typography>
            </Box>
          </Box>
          {customer.averageSentiment && (
            <Tooltip title={`Average sentiment: ${customer.averageSentiment}`}>
              <Box>{getSentimentIcon(customer.averageSentiment)}</Box>
            </Tooltip>
          )}
        </Box>

        {customer.email && (
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <Email fontSize="small" color="action" />
            <Typography variant="body2">{customer.email}</Typography>
          </Box>
        )}

        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <History fontSize="small" color="action" />
          <Typography variant="body2" color="text.secondary">
            {customer.totalCalls} total calls
            {customer.lastCallDate && ` • Last: ${formatDateTime(customer.lastCallDate)}`}
          </Typography>
        </Box>

        {customer.tags.length > 0 && (
          <Box display="flex" gap={0.5} flexWrap="wrap" mb={1}>
            {customer.tags.map((tag, idx) => (
              <Chip
                key={idx}
                label={tag}
                size="small"
                icon={<Tag fontSize="small" />}
              />
            ))}
          </Box>
        )}

        {customer.notes && (
          <Box display="flex" alignItems="flex-start" gap={1}>
            <Notes fontSize="small" color="action" />
            <Typography variant="body2" color="text.secondary" noWrap>
              {customer.notes}
            </Typography>
          </Box>
        )}
      </CardContent>
      <CardActions>
        <Button size="small" onClick={() => onView(customer)}>
          View Details
        </Button>
        <Button size="small" onClick={() => onEdit(customer)}>
          Edit
        </Button>
      </CardActions>
    </Card>
  )
}

export default function Customers() {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [createDialog, setCreateDialog] = useState(false)
  const [editDialog, setEditDialog] = useState(false)
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [tabValue, setTabValue] = useState(0)
  
  const [formData, setFormData] = useState<CustomerFormData>({
    phoneNumber: '',
    firstName: '',
    lastName: '',
    email: '',
    tags: [],
    notes: '',
  })

  const { data: customers, isLoading, refetch } = useApiQuery(
    ['customers', searchTerm, selectedTags],
    () => customerService.getCustomers({
      searchTerm,
      tags: selectedTags,
    })
  )

  const { data: allTags } = useApiQuery(
    ['customers', 'tags'],
    () => customerService.getTags()
  )

  const createMutation = useApiMutation(
    (data: CustomerFormData) => customerService.createCustomer(data),
    {
      onSuccess: () => {
        refetch()
        setCreateDialog(false)
        resetForm()
      },
    }
  )

  const updateMutation = useApiMutation(
    ({ id, data }: { id: number; data: CustomerFormData }) =>
      customerService.updateCustomer(id, data),
    {
      onSuccess: () => {
        refetch()
        setEditDialog(false)
        resetForm()
      },
    }
  )

  const resetForm = () => {
    setFormData({
      phoneNumber: '',
      firstName: '',
      lastName: '',
      email: '',
      tags: [],
      notes: '',
    })
    setSelectedCustomer(null)
  }

  const handleCreate = () => {
    createMutation.mutate(formData)
  }

  const handleUpdate = () => {
    if (selectedCustomer) {
      updateMutation.mutate({ id: selectedCustomer.id, data: formData })
    }
  }

  const handleEdit = (customer: Customer) => {
    setSelectedCustomer(customer)
    setFormData({
      phoneNumber: customer.phoneNumber,
      firstName: customer.firstName || '',
      lastName: customer.lastName || '',
      email: customer.email || '',
      tags: customer.tags,
      notes: customer.notes,
    })
    setEditDialog(true)
  }

  const handleView = (customer: Customer) => {
    navigate(`/customers/${customer.id}`)
  }

  const customersData = customers?.data || []
  const tagsData = allTags?.data || []

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Customer Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage customer profiles and interaction history
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setCreateDialog(true)}
        >
          Add Customer
        </Button>
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ mb: 3, p: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search by name, phone, or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
                endAdornment: searchTerm && (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={() => setSearchTerm('')}>
                      <Clear />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Autocomplete
              multiple
              options={tagsData}
              value={selectedTags}
              onChange={(_, value) => setSelectedTags(value)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  placeholder="Filter by tags"
                  InputProps={{
                    ...params.InputProps,
                    startAdornment: (
                      <>
                        <InputAdornment position="start">
                          <FilterList />
                        </InputAdornment>
                        {params.InputProps.startAdornment}
                      </>
                    ),
                  }}
                />
              )}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip
                    variant="outlined"
                    label={option}
                    size="small"
                    {...getTagProps({ index })}
                  />
                ))
              }
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Customer Grid */}
      {isLoading ? (
        <LinearProgress />
      ) : customersData.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Person sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No customers found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {searchTerm || selectedTags.length > 0
              ? 'Try adjusting your search criteria'
              : 'Add your first customer to get started'}
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {customersData.map((customer) => (
            <Grid item xs={12} sm={6} md={4} key={customer.id}>
              <CustomerCard
                customer={customer}
                onEdit={handleEdit}
                onView={handleView}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog
        open={createDialog || editDialog}
        onClose={() => {
          setCreateDialog(false)
          setEditDialog(false)
          resetForm()
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {editDialog ? 'Edit Customer' : 'Add New Customer'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Phone Number"
                value={formData.phoneNumber}
                onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
                required
                disabled={editDialog}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="First Name"
                value={formData.firstName}
                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Last Name"
                value={formData.lastName}
                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <Autocomplete
                multiple
                freeSolo
                options={tagsData}
                value={formData.tags}
                onChange={(_, value) => setFormData({ ...formData, tags: value })}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Tags"
                    placeholder="Add tags..."
                  />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      variant="outlined"
                      label={option}
                      size="small"
                      {...getTagProps({ index })}
                    />
                  ))
                }
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setCreateDialog(false)
              setEditDialog(false)
              resetForm()
            }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={editDialog ? handleUpdate : handleCreate}
            disabled={createMutation.isLoading || updateMutation.isLoading}
          >
            {editDialog ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}