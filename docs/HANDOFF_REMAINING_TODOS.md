# Developer Handoff: Remaining TODOs

## Overview
This document provides detailed guidance for completing the remaining two features in the voice agent customization system. The core infrastructure is complete and tested - these features will enhance usability and intelligence.

## TODO #1: Domain Knowledge System

### Current State
- Database schema exists (`domain_knowledge` table in `enhanced_models.py`)
- Agent-domain linking implemented (`agent_domains` table)
- Placeholder for knowledge injection in `agent_builder.py`

### What Needs to Be Built

#### 1.1 Knowledge Base Service (`/server/services/knowledge_base.py`)
```python
class KnowledgeBase:
    """
    Manages domain-specific knowledge for agents
    
    Required functionality:
    1. CRUD operations for knowledge entries
    2. Vector embeddings for semantic search
    3. Context injection during conversations
    4. Version management for knowledge updates
    """
    
    def __init__(self):
        # Initialize vector database (Pinecone, Weaviate, or pgvector)
        # Set up embedding model (sentence-transformers recommended)
        pass
    
    def add_knowledge(self, domain: str, content: str, metadata: dict):
        # Store knowledge with embedding
        # Update version if exists
        pass
    
    def search_relevant(self, query: str, domain: str, top_k: int = 5):
        # Semantic search using embeddings
        # Filter by domain and active status
        pass
    
    def get_context_for_conversation(self, agent_id: int, conversation_text: str):
        # Find relevant knowledge based on conversation
        # Format for prompt injection
        pass
```

#### 1.2 API Endpoints (`/server/routes/knowledge_management.py`)
```python
# Knowledge CRUD
POST   /api/knowledge                    # Add knowledge entry
GET    /api/knowledge?domain={domain}    # List knowledge by domain
PUT    /api/knowledge/{id}              # Update knowledge
DELETE /api/knowledge/{id}              # Deactivate knowledge

# Bulk operations
POST   /api/knowledge/import            # Import from CSV/JSON
POST   /api/knowledge/generate-embeddings # Regenerate all embeddings

# Domain management
GET    /api/domains                     # List all domains
POST   /api/domains                     # Create new domain
```

#### 1.3 Integration Points

**In `call_processor.py` (or equivalent):**
```python
# During conversation processing
def process_message(call_id: str, message: str):
    # Get agent configuration
    agent = get_agent_for_call(call_id)
    
    # Inject relevant knowledge
    knowledge_context = knowledge_base.get_context_for_conversation(
        agent.id, 
        message
    )
    
    # Add to prompt
    enhanced_prompt = f"{agent.system_prompt}\n\nRelevant Information:\n{knowledge_context}"
```

**In `agent_builder.py`:**
```python
def compile_system_prompt(self, db: Session, agent_id: int):
    # ... existing code ...
    
    # Add knowledge domain references
    domains = self._get_agent_domains(db, agent_id)
    if domains:
        prompt_parts.append("\n## Knowledge Base Access:")
        prompt_parts.append("You have access to information about:")
        for domain in domains:
            prompt_parts.append(f"- {domain['name']}")
        prompt_parts.append("Use this knowledge to provide accurate, detailed responses.")
```

#### 1.4 Implementation Steps

1. **Set up vector database**
   ```bash
   # Option 1: PostgreSQL with pgvector
   CREATE EXTENSION vector;
   ALTER TABLE domain_knowledge ADD COLUMN embedding vector(384);
   
   # Option 2: External service
   pip install pinecone-client
   # or
   pip install weaviate-client
   ```

2. **Install embedding model**
   ```bash
   pip install sentence-transformers
   ```

3. **Create embedding service**
   ```python
   from sentence_transformers import SentenceTransformer
   
   class EmbeddingService:
       def __init__(self):
           self.model = SentenceTransformer('all-MiniLM-L6-v2')
       
       def embed_text(self, text: str) -> np.ndarray:
           return self.model.encode(text)
   ```

4. **Implement search functionality**
   ```python
   # Using pgvector
   SELECT content, metadata, 
          1 - (embedding <-> %s) as similarity
   FROM domain_knowledge
   WHERE domain_name = %s AND active = true
   ORDER BY similarity DESC
   LIMIT %s
   ```

#### 1.5 Testing Strategy
```python
# tests/test_knowledge_base.py
def test_knowledge_crud():
    # Test adding, updating, retrieving knowledge

def test_semantic_search():
    # Test that relevant knowledge is found
    
def test_context_injection():
    # Test that knowledge appears in prompts

def test_domain_filtering():
    # Test that only relevant domains are searched
```

### Expected Deliverables
1. Working knowledge base with semantic search
2. API endpoints for knowledge management
3. Integration with conversation flow
4. Import/export functionality
5. Performance metrics (search latency < 100ms)

---

## TODO #2: Agent Customization UI

### Current State
- Backend API fully implemented (`/server/routes/agent_management.py`)
- Agent builder service complete (`/server/services/agent_builder.py`)
- Frontend structure exists (React + TypeScript)

### What Needs to Be Built

#### 2.1 React Components Structure
```
/client/src/components/AgentBuilder/
├── index.tsx                 # Main container
├── AgentForm.tsx            # Core agent details
├── TemplateSelector.tsx     # Choose starting template
├── GoalConfiguration.tsx    # Assign and configure goals
├── InstructionEditor.tsx    # Manage do's and don'ts
├── DomainSelector.tsx       # Choose knowledge domains
├── VoiceConfiguration.tsx   # Voice settings and testing
├── TestingConsole.tsx       # Live agent testing
└── AgentList.tsx           # View/manage existing agents
```

#### 2.2 Main Agent Builder Component
```typescript
// /client/src/components/AgentBuilder/index.tsx
import React, { useState, useEffect } from 'react';
import { AgentForm } from './AgentForm';
import { GoalConfiguration } from './GoalConfiguration';
import { InstructionEditor } from './InstructionEditor';
import { VoiceConfiguration } from './VoiceConfiguration';
import { TestingConsole } from './TestingConsole';
import { agentService } from '../../services/agentService';

export const AgentBuilder: React.FC = () => {
    const [currentStep, setCurrentStep] = useState(1);
    const [agentConfig, setAgentConfig] = useState<AgentConfig>({
        name: '',
        templateId: null,
        goals: [],
        instructions: { dos: [], donts: [] },
        voice: { provider: 'chatterbox', baseEmotion: 'friendly' }
    });
    
    const steps = [
        { id: 1, name: 'Basic Info', component: AgentForm },
        { id: 2, name: 'Goals', component: GoalConfiguration },
        { id: 3, name: 'Instructions', component: InstructionEditor },
        { id: 4, name: 'Voice', component: VoiceConfiguration },
        { id: 5, name: 'Test', component: TestingConsole }
    ];
    
    // Render current step with navigation
};
```

#### 2.3 Goal Configuration Component
```typescript
// /client/src/components/AgentBuilder/GoalConfiguration.tsx
interface GoalConfigProps {
    selectedGoals: AgentGoal[];
    availableGoals: ConversationGoal[];
    onChange: (goals: AgentGoal[]) => void;
}

export const GoalConfiguration: React.FC<GoalConfigProps> = ({
    selectedGoals,
    availableGoals,
    onChange
}) => {
    return (
        <div className="space-y-4">
            <h3>Configure Agent Goals</h3>
            
            {/* Available goals with drag-and-drop */}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <h4>Available Goals</h4>
                    {availableGoals.map(goal => (
                        <GoalCard
                            key={goal.id}
                            goal={goal}
                            onAdd={() => handleAddGoal(goal)}
                        />
                    ))}
                </div>
                
                <div>
                    <h4>Selected Goals</h4>
                    <DragDropContext onDragEnd={handleDragEnd}>
                        <Droppable droppableId="selected-goals">
                            {(provided) => (
                                <div {...provided.droppableProps} ref={provided.innerRef}>
                                    {selectedGoals.map((goal, index) => (
                                        <Draggable key={goal.id} draggableId={goal.id} index={index}>
                                            {(provided) => (
                                                <SelectedGoalCard
                                                    goal={goal}
                                                    onRemove={() => handleRemoveGoal(goal.id)}
                                                    onToggleRequired={() => handleToggleRequired(goal.id)}
                                                    provided={provided}
                                                />
                                            )}
                                        </Draggable>
                                    ))}
                                    {provided.placeholder}
                                </div>
                            )}
                        </Droppable>
                    </DragDropContext>
                </div>
            </div>
        </div>
    );
};
```

#### 2.4 Instruction Editor Component
```typescript
// /client/src/components/AgentBuilder/InstructionEditor.tsx
interface InstructionEditorProps {
    instructions: AgentInstructions;
    onChange: (instructions: AgentInstructions) => void;
    suggestions?: InstructionSuggestions;
}

export const InstructionEditor: React.FC<InstructionEditorProps> = ({
    instructions,
    onChange,
    suggestions
}) => {
    const [newInstruction, setNewInstruction] = useState('');
    const [instructionType, setInstructionType] = useState<'do' | 'dont'>('do');
    
    return (
        <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
                {/* Do's Section */}
                <div className="bg-green-50 p-4 rounded">
                    <h4 className="text-green-800 mb-3">Things to DO ✓</h4>
                    {instructions.dos.map((instruction, index) => (
                        <InstructionItem
                            key={index}
                            instruction={instruction}
                            type="do"
                            onEdit={(text) => handleEdit('do', index, text)}
                            onDelete={() => handleDelete('do', index)}
                            onCategoryChange={(category) => handleCategoryChange('do', index, category)}
                        />
                    ))}
                </div>
                
                {/* Don'ts Section */}
                <div className="bg-red-50 p-4 rounded">
                    <h4 className="text-red-800 mb-3">Things NOT to do ✗</h4>
                    {instructions.donts.map((instruction, index) => (
                        <InstructionItem
                            key={index}
                            instruction={instruction}
                            type="dont"
                            onEdit={(text) => handleEdit('dont', index, text)}
                            onDelete={() => handleDelete('dont', index)}
                            onCategoryChange={(category) => handleCategoryChange('dont', index, category)}
                        />
                    ))}
                </div>
            </div>
            
            {/* Add new instruction */}
            <div className="flex gap-2">
                <select value={instructionType} onChange={(e) => setInstructionType(e.target.value as 'do' | 'dont')}>
                    <option value="do">DO</option>
                    <option value="dont">DON'T</option>
                </select>
                <input
                    type="text"
                    value={newInstruction}
                    onChange={(e) => setNewInstruction(e.target.value)}
                    placeholder="Add new instruction..."
                    className="flex-1"
                />
                <button onClick={handleAdd}>Add</button>
            </div>
            
            {/* Suggestions */}
            {suggestions && (
                <div className="mt-4">
                    <h5>Suggested instructions for {suggestions.agentType}:</h5>
                    <div className="flex flex-wrap gap-2">
                        {suggestions.items.map((suggestion, index) => (
                            <button
                                key={index}
                                onClick={() => handleAddSuggestion(suggestion)}
                                className="text-sm bg-gray-100 px-2 py-1 rounded"
                            >
                                {suggestion.text}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
```

#### 2.5 Voice Configuration Component
```typescript
// /client/src/components/AgentBuilder/VoiceConfiguration.tsx
export const VoiceConfiguration: React.FC<VoiceConfigProps> = ({
    voiceSettings,
    onChange,
    agentId
}) => {
    const [testPhrase, setTestPhrase] = useState('');
    const [isPlaying, setIsPlaying] = useState(false);
    const [audioSamples, setAudioSamples] = useState<File[]>([]);
    
    const handleTestVoice = async () => {
        const audio = await agentService.testVoice(agentId, testPhrase, voiceSettings.baseEmotion);
        playAudio(audio);
    };
    
    const handleUploadSamples = async () => {
        if (audioSamples.length >= 3) {
            const result = await agentService.createVoiceProfile(agentId, audioSamples);
            if (result.success) {
                toast.success('Voice profile created!');
            }
        }
    };
    
    return (
        <div className="space-y-6">
            {/* Emotion Selection */}
            <div>
                <label>Base Emotion</label>
                <select 
                    value={voiceSettings.baseEmotion} 
                    onChange={(e) => onChange({ ...voiceSettings, baseEmotion: e.target.value })}
                >
                    <option value="neutral">Neutral</option>
                    <option value="friendly">Friendly</option>
                    <option value="professional">Professional</option>
                    <option value="empathetic">Empathetic</option>
                    <option value="excited">Excited</option>
                    <option value="calm">Calm</option>
                </select>
            </div>
            
            {/* Voice Testing */}
            <div className="bg-gray-50 p-4 rounded">
                <h4>Test Voice</h4>
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={testPhrase}
                        onChange={(e) => setTestPhrase(e.target.value)}
                        placeholder="Enter test phrase..."
                        className="flex-1"
                    />
                    <button onClick={handleTestVoice} disabled={!testPhrase || isPlaying}>
                        {isPlaying ? 'Playing...' : 'Test'}
                    </button>
                </div>
                
                {/* Quick test phrases */}
                <div className="mt-2">
                    <span className="text-sm text-gray-600">Quick tests:</span>
                    {['Hello! How can I help you?', 'Let me check that for you.', 'Is there anything else?'].map(phrase => (
                        <button
                            key={phrase}
                            onClick={() => setTestPhrase(phrase)}
                            className="ml-2 text-sm text-blue-600 hover:underline"
                        >
                            {phrase}
                        </button>
                    ))}
                </div>
            </div>
            
            {/* Voice Cloning */}
            <div className="bg-blue-50 p-4 rounded">
                <h4>Custom Voice (Optional)</h4>
                <p className="text-sm text-gray-600 mb-3">
                    Upload 3-5 audio samples (10-30 seconds each) to create a custom voice
                </p>
                <input
                    type="file"
                    multiple
                    accept="audio/*"
                    onChange={(e) => setAudioSamples(Array.from(e.target.files || []))}
                />
                {audioSamples.length > 0 && (
                    <div className="mt-2">
                        <p>{audioSamples.length} files selected</p>
                        <button 
                            onClick={handleUploadSamples} 
                            disabled={audioSamples.length < 3}
                            className="mt-2"
                        >
                            Create Voice Profile
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};
```

#### 2.6 Testing Console Component
```typescript
// /client/src/components/AgentBuilder/TestingConsole.tsx
export const TestingConsole: React.FC<TestingProps> = ({ agentId }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [goalProgress, setGoalProgress] = useState<GoalProgress[]>([]);
    
    const handleSendMessage = async () => {
        if (!input.trim()) return;
        
        // Add user message
        const userMessage = { role: 'user', content: input };
        setMessages([...messages, userMessage]);
        setInput('');
        setIsProcessing(true);
        
        try {
            // Get agent response
            const response = await agentService.testConversation(agentId, input);
            
            // Add agent response
            setMessages(prev => [...prev, { role: 'agent', content: response.message }]);
            
            // Update goal progress
            if (response.goalProgress) {
                setGoalProgress(response.goalProgress);
            }
        } finally {
            setIsProcessing(false);
        }
    };
    
    return (
        <div className="flex gap-4 h-96">
            {/* Chat Interface */}
            <div className="flex-1 flex flex-col border rounded">
                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                    {messages.map((msg, index) => (
                        <div key={index} className={`${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                            <div className={`inline-block p-2 rounded ${
                                msg.role === 'user' ? 'bg-blue-100' : 'bg-gray-100'
                            }`}>
                                {msg.content}
                            </div>
                        </div>
                    ))}
                    {isProcessing && <div className="text-center text-gray-500">Agent is thinking...</div>}
                </div>
                
                <div className="border-t p-2 flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        placeholder="Type your message..."
                        className="flex-1"
                    />
                    <button onClick={handleSendMessage} disabled={isProcessing}>Send</button>
                </div>
            </div>
            
            {/* Goal Progress Panel */}
            <div className="w-64 border rounded p-4">
                <h4 className="font-bold mb-2">Goal Progress</h4>
                {goalProgress.map(goal => (
                    <div key={goal.id} className="mb-3">
                        <div className="flex justify-between items-center">
                            <span className="text-sm">{goal.name}</span>
                            <span className="text-xs">{goal.percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded h-2 mt-1">
                            <div 
                                className="bg-blue-500 h-2 rounded" 
                                style={{ width: `${goal.percentage}%` }}
                            />
                        </div>
                        {goal.missingFields.length > 0 && (
                            <div className="text-xs text-gray-500 mt-1">
                                Missing: {goal.missingFields.join(', ')}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};
```

#### 2.7 Service Layer
```typescript
// /client/src/services/agentService.ts
import axios from 'axios';

export class AgentService {
    private baseURL = '/api/agents';
    
    async createAgent(config: AgentConfig): Promise<Agent> {
        const response = await axios.post(this.baseURL, config);
        return response.data;
    }
    
    async updateAgent(id: string, updates: Partial<AgentConfig>): Promise<Agent> {
        const response = await axios.put(`${this.baseURL}/${id}`, updates);
        return response.data;
    }
    
    async listAgents(filters?: AgentFilters): Promise<Agent[]> {
        const response = await axios.get(this.baseURL, { params: filters });
        return response.data.agents;
    }
    
    async testVoice(agentId: string, text: string, emotion: string): Promise<ArrayBuffer> {
        const response = await axios.post(
            `${this.baseURL}/${agentId}/test-voice`,
            { text, emotion },
            { responseType: 'arraybuffer' }
        );
        return response.data;
    }
    
    async testConversation(agentId: string, message: string): Promise<TestResponse> {
        const response = await axios.post(`${this.baseURL}/${agentId}/test`, { input: message });
        return response.data;
    }
    
    async createVoiceProfile(agentId: string, samples: File[]): Promise<VoiceProfileResult> {
        const formData = new FormData();
        samples.forEach((file, index) => {
            formData.append(`sample_${index}`, file);
        });
        
        const response = await axios.post(
            `${this.baseURL}/${agentId}/voice-profile`,
            formData,
            { headers: { 'Content-Type': 'multipart/form-data' } }
        );
        return response.data;
    }
}

export const agentService = new AgentService();
```

#### 2.8 Implementation Steps

1. **Set up component structure**
   ```bash
   cd client/src
   mkdir -p components/AgentBuilder
   # Create all component files
   ```

2. **Install required dependencies**
   ```bash
   npm install react-beautiful-dnd  # For drag-and-drop
   npm install react-hook-form      # For form management
   npm install @tanstack/react-query # For data fetching
   npm install react-hot-toast      # For notifications
   ```

3. **Add routing**
   ```typescript
   // In App.tsx or router config
   <Route path="/agents/new" element={<AgentBuilder />} />
   <Route path="/agents/:id/edit" element={<AgentBuilder editMode />} />
   <Route path="/agents" element={<AgentList />} />
   ```

4. **Style with Tailwind** (already configured)
   - Use existing UI components from `/client/src/components/ui/`
   - Follow the design system established in the project

5. **Add state management** (if needed)
   ```typescript
   // Using Zustand or Context API
   const useAgentBuilderStore = create((set) => ({
       currentAgent: null,
       isDirty: false,
       setAgent: (agent) => set({ currentAgent: agent, isDirty: true }),
       saveAgent: async () => {
           // Save logic
       }
   }));
   ```

#### 2.9 Testing Strategy
```typescript
// tests/components/AgentBuilder.test.tsx
describe('AgentBuilder', () => {
    it('should create agent from template', async () => {
        // Test template selection and customization
    });
    
    it('should validate required fields', () => {
        // Test form validation
    });
    
    it('should handle goal configuration', () => {
        // Test goal assignment and priority
    });
    
    it('should preview agent behavior', () => {
        // Test the testing console
    });
});
```

### Expected Deliverables
1. Complete AgentBuilder UI with all components
2. Integration with backend API
3. Voice testing functionality
4. Real-time conversation testing
5. Responsive design for desktop and tablet
6. Error handling and loading states
7. Form validation and user feedback

---

## Integration Notes

### Backend Considerations
1. Both features should work with existing authentication
2. Maintain backward compatibility with current agents
3. Add appropriate logging for debugging
4. Consider rate limiting for API endpoints

### Performance Requirements
1. Knowledge search: < 100ms latency
2. UI responsiveness: < 200ms for all interactions
3. Voice synthesis: < 500ms for test phrases
4. Agent creation: < 2 seconds total

### Security Considerations
1. Validate all user inputs
2. Sanitize knowledge content before storage
3. Implement proper access controls
4. Audit trail for agent modifications

## Resources
- Existing API documentation: `/server/routes/agent_management.py`
- Database schema: `/server/models/enhanced_models.py`
- Current UI components: `/client/src/components/ui/`
- Voice service: `/server/services/enhanced_chatterbox_service.py`

## Questions to Address
1. Should knowledge be shareable between agents?
2. Do we need approval workflow for agent changes?
3. Should we support agent versioning?
4. What analytics should we track for agent performance?

## Timeline Estimate
- Domain Knowledge System: 3-4 days
- Agent Customization UI: 4-5 days
- Integration and testing: 2 days
- Total: ~2 weeks for both features

Good luck! The foundation is solid - these features will make the system truly powerful and user-friendly.