import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Card,
  CardContent,
  IconButton,
  Chip,
  Switch,
  FormControlLabel,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Tooltip,
} from '@mui/material'
import {
  Save,
  Cancel,
  Add,
  Delete,
  PlayArrow,
  Settings,
  Message,
  Psychology,
  Mic,
  Speed,
  VolumeUp,
  Edit,
  DragIndicator,
  ContentCopy,
  Check,
} from '@mui/icons-material'
import { useApiQuery, useApiMutation } from '@hooks/useApi'
import { agentService } from '@services/endpoints'
import { Agent, AgentType, AgentFormData } from '@types'
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'

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
      id={`agent-tabpanel-${index}`}
      aria-labelledby={`agent-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

interface KeywordItemProps {
  keyword: string
  index: number
  onEdit: (index: number, value: string) => void
  onDelete: (index: number) => void
}

function KeywordItem({ keyword, index, onEdit, onDelete }: KeywordItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(keyword)

  const handleSave = () => {
    onEdit(index, editValue)
    setIsEditing(false)
  }

  return (
    <Draggable draggableId={`keyword-${index}`} index={index}>
      {(provided) => (
        <ListItem
          ref={provided.innerRef}
          {...provided.draggableProps}
          sx={{
            bgcolor: 'background.paper',
            mb: 1,
            borderRadius: 1,
            border: 1,
            borderColor: 'divider',
          }}
        >
          <Box {...provided.dragHandleProps} mr={1}>
            <DragIndicator color="action" />
          </Box>
          {isEditing ? (
            <TextField
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={handleSave}
              onKeyPress={(e) => e.key === 'Enter' && handleSave()}
              size="small"
              autoFocus
              fullWidth
            />
          ) : (
            <ListItemText primary={keyword} />
          )}
          <ListItemSecondaryAction>
            <IconButton size="small" onClick={() => setIsEditing(true)}>
              <Edit fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              color="error"
              onClick={() => onDelete(index)}
            >
              <Delete fontSize="small" />
            </IconButton>
          </ListItemSecondaryAction>
        </ListItem>
      )}
    </Draggable>
  )
}

export default function AgentConfig() {
  const { agentType } = useParams<{ agentType: string }>()
  const navigate = useNavigate()
  const [tabValue, setTabValue] = useState(0)
  const [testDialog, setTestDialog] = useState(false)
  const [testPhone, setTestPhone] = useState('')
  const [testResult, setTestResult] = useState<any>(null)
  const [isSaved, setIsSaved] = useState(false)

  const { data: agent, isLoading } = useApiQuery(
    ['agents', agentType],
    () => agentService.getAgent(agentType!),
    {
      enabled: !!agentType,
    }
  )

  const [formData, setFormData] = useState<AgentFormData>({
    name: '',
    description: '',
    systemPrompt: '',
    keywords: '',
    priority: 5,
    smsTemplate: '',
    isActive: true,
  })

  const [keywords, setKeywords] = useState<string[]>([])
  const [newKeyword, setNewKeyword] = useState('')
  const [voiceSettings, setVoiceSettings] = useState({
    voice: 'alloy',
    speed: 1.0,
    pitch: 1.0,
    temperature: 0.7,
  })

  useEffect(() => {
    if (agent?.data) {
      const agentData = agent.data
      setFormData({
        name: agentData.name,
        description: agentData.description,
        systemPrompt: agentData.systemPrompt,
        keywords: agentData.keywords.join(', '),
        priority: agentData.priority,
        smsTemplate: agentData.smsTemplate,
        isActive: agentData.isActive,
      })
      setKeywords(agentData.keywords)
    }
  }, [agent])

  const updateMutation = useApiMutation(
    (data: AgentFormData) => agentService.updateAgent(agentType!, data),
    {
      onSuccess: () => {
        setIsSaved(true)
        setTimeout(() => setIsSaved(false), 3000)
      },
    }
  )

  const testMutation = useApiMutation(
    (phone: string) => agentService.testAgent(agentType!, phone),
    {
      onSuccess: (response) => {
        setTestResult(response.data)
      },
    }
  )

  const handleSave = () => {
    updateMutation.mutate({
      ...formData,
      keywords: keywords.join(', '),
    })
  }

  const handleAddKeyword = () => {
    if (newKeyword.trim() && !keywords.includes(newKeyword.trim())) {
      setKeywords([...keywords, newKeyword.trim()])
      setNewKeyword('')
    }
  }

  const handleEditKeyword = (index: number, value: string) => {
    const updated = [...keywords]
    updated[index] = value
    setKeywords(updated)
  }

  const handleDeleteKeyword = (index: number) => {
    setKeywords(keywords.filter((_, i) => i !== index))
  }

  const handleDragEnd = (result: any) => {
    if (!result.destination) return

    const items = Array.from(keywords)
    const [reorderedItem] = items.splice(result.source.index, 1)
    items.splice(result.destination.index, 0, reorderedItem)

    setKeywords(items)
  }

  const handleTest = () => {
    if (testPhone) {
      testMutation.mutate(testPhone)
    }
  }

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(formData.systemPrompt)
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Configure {agentType} Agent
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Customize behavior, keywords, and responses
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<Cancel />}
            onClick={() => navigate('/agents')}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            startIcon={isSaved ? <Check /> : <Save />}
            onClick={handleSave}
            disabled={updateMutation.isLoading}
            color={isSaved ? 'success' : 'primary'}
          >
            {isSaved ? 'Saved' : 'Save Changes'}
          </Button>
        </Box>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab icon={<Settings />} label="General" />
            <Tab icon={<Psychology />} label="Keywords" />
            <Tab icon={<Message />} label="Prompts & SMS" />
            <Tab icon={<Mic />} label="Voice Settings" />
          </Tabs>
        </Box>

        <Box sx={{ p: 3 }}>
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Agent Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  multiline
                  rows={3}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography gutterBottom>Priority Level</Typography>
                <Slider
                  value={formData.priority}
                  onChange={(_, value) => setFormData({ ...formData, priority: value as number })}
                  min={1}
                  max={10}
                  marks
                  valueLabelDisplay="auto"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.isActive}
                      onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                    />
                  }
                  label="Agent Active"
                />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Typography variant="h6" gutterBottom>
              Routing Keywords
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Add keywords that will route calls to this agent. Drag to reorder by priority.
            </Typography>

            <Box display="flex" gap={2} mb={3}>
              <TextField
                fullWidth
                label="Add Keyword"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
                size="small"
              />
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleAddKeyword}
                disabled={!newKeyword.trim()}
              >
                Add
              </Button>
            </Box>

            <DragDropContext onDragEnd={handleDragEnd}>
              <Droppable droppableId="keywords">
                {(provided) => (
                  <List {...provided.droppableProps} ref={provided.innerRef}>
                    {keywords.map((keyword, index) => (
                      <KeywordItem
                        key={index}
                        keyword={keyword}
                        index={index}
                        onEdit={handleEditKeyword}
                        onDelete={handleDeleteKeyword}
                      />
                    ))}
                    {provided.placeholder}
                  </List>
                )}
              </Droppable>
            </DragDropContext>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="h6">System Prompt</Typography>
                  <IconButton size="small" onClick={handleCopyPrompt}>
                    <ContentCopy fontSize="small" />
                  </IconButton>
                </Box>
                <TextField
                  fullWidth
                  multiline
                  rows={8}
                  value={formData.systemPrompt}
                  onChange={(e) => setFormData({ ...formData, systemPrompt: e.target.value })}
                  placeholder="Enter the system prompt that defines how this agent should behave..."
                  helperText="This prompt defines the agent's personality, knowledge, and behavior"
                />
              </Grid>
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom>
                  SMS Template
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  value={formData.smsTemplate}
                  onChange={(e) => setFormData({ ...formData, smsTemplate: e.target.value })}
                  placeholder="Enter SMS template with variables like {{customerName}}, {{callSummary}}..."
                  helperText="Use variables: {{customerName}}, {{callSummary}}, {{nextSteps}}"
                />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Voice Model</InputLabel>
                  <Select
                    value={voiceSettings.voice}
                    onChange={(e) => setVoiceSettings({ ...voiceSettings, voice: e.target.value })}
                  >
                    <MenuItem value="alloy">Alloy</MenuItem>
                    <MenuItem value="echo">Echo</MenuItem>
                    <MenuItem value="fable">Fable</MenuItem>
                    <MenuItem value="onyx">Onyx</MenuItem>
                    <MenuItem value="nova">Nova</MenuItem>
                    <MenuItem value="shimmer">Shimmer</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography gutterBottom>Response Temperature</Typography>
                <Slider
                  value={voiceSettings.temperature}
                  onChange={(_, value) => setVoiceSettings({ ...voiceSettings, temperature: value as number })}
                  min={0}
                  max={2}
                  step={0.1}
                  marks={[
                    { value: 0, label: 'Precise' },
                    { value: 1, label: 'Balanced' },
                    { value: 2, label: 'Creative' },
                  ]}
                  valueLabelDisplay="auto"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Box display="flex" alignItems="center" gap={2}>
                  <Speed />
                  <Box flex={1}>
                    <Typography gutterBottom>Speech Speed</Typography>
                    <Slider
                      value={voiceSettings.speed}
                      onChange={(_, value) => setVoiceSettings({ ...voiceSettings, speed: value as number })}
                      min={0.5}
                      max={2}
                      step={0.1}
                      valueLabelDisplay="auto"
                    />
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box display="flex" alignItems="center" gap={2}>
                  <VolumeUp />
                  <Box flex={1}>
                    <Typography gutterBottom>Voice Pitch</Typography>
                    <Slider
                      value={voiceSettings.pitch}
                      onChange={(_, value) => setVoiceSettings({ ...voiceSettings, pitch: value as number })}
                      min={0.5}
                      max={2}
                      step={0.1}
                      valueLabelDisplay="auto"
                    />
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Test Agent
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      Test this agent configuration with a phone call
                    </Typography>
                    <Button
                      variant="contained"
                      startIcon={<PlayArrow />}
                      onClick={() => setTestDialog(true)}
                    >
                      Test Agent
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>
        </Box>
      </Paper>

      {/* Test Agent Dialog */}
      <Dialog open={testDialog} onClose={() => setTestDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Test Agent Configuration</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Phone Number"
            value={testPhone}
            onChange={(e) => setTestPhone(e.target.value)}
            placeholder="+1234567890"
            margin="normal"
          />
          {testResult && (
            <Alert severity={testResult.success ? 'success' : 'error'} sx={{ mt: 2 }}>
              {testResult.message}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleTest}
            disabled={!testPhone || testMutation.isLoading}
            startIcon={testMutation.isLoading ? <CircularProgress size={20} /> : <PlayArrow />}
          >
            Start Test Call
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}