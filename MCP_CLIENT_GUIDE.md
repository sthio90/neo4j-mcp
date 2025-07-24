# Building an MCP Client Web Application

This guide covers building a custom MCP (Model Context Protocol) client as a web application with database access, AI model integration, custom UIs, and automated testing.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Implementation Plan](#implementation-plan)
5. [Core Components](#core-components)
6. [Web Application Setup](#web-application-setup)
7. [MCP Client Implementation](#mcp-client-implementation)
8. [Database Integration](#database-integration)
9. [AI Model Integration](#ai-model-integration)
10. [Custom UI Components](#custom-ui-components)
11. [Automated Testing](#automated-testing)
12. [Deployment](#deployment)

## Overview

An MCP client is a program that can:
- Start and manage MCP server processes
- Communicate with servers via JSON-RPC 2.0
- Discover and invoke tools provided by servers
- Handle responses and errors gracefully

### Benefits of a Web-Based MCP Client

- **Universal Access**: Use from any device with a browser
- **Multi-User Support**: Multiple users can access different MCP servers
- **Rich UI**: Build interactive dashboards and visualizations
- **API Gateway**: Expose MCP tools as REST/GraphQL APIs
- **Integration Hub**: Connect multiple AI models and services

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │   Backend API   │     │   MCP Servers   │
│   (React/Vue)   │────▶│   (Node/Python) │────▶│   (Multiple)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
   ┌──────────┐           ┌──────────────┐       ┌──────────────┐
   │    UI    │           │ MCP Manager  │       │ Neo4j Server │
   │Components│           │   Service    │       │ Other Server │
   └──────────┘           └──────────────┘       └──────────────┘
```

### Key Components

1. **Frontend**: Interactive web interface
2. **Backend API**: Manages MCP connections and provides REST/WebSocket APIs
3. **MCP Manager**: Handles server lifecycle and communication
4. **Database**: Stores configurations, logs, and results
5. **AI Integration**: Connects to various AI providers

## Technology Stack

### Recommended Stack

**Frontend:**
- **Framework**: React with TypeScript (or Vue.js)
- **UI Library**: Material-UI, Ant Design, or Tailwind UI
- **State Management**: Redux Toolkit or Zustand
- **Real-time**: Socket.io client for live updates

**Backend:**
- **Runtime**: Node.js with TypeScript
- **Framework**: Express.js or Fastify
- **WebSocket**: Socket.io for real-time communication
- **Process Management**: node-pty for spawning MCP servers
- **Database**: PostgreSQL with Prisma ORM

**Testing:**
- **Unit Tests**: Jest
- **Integration Tests**: Supertest
- **E2E Tests**: Playwright or Cypress
- **MCP Mocking**: Custom mock servers

## Implementation Plan

### Phase 1: Core MCP Client (Week 1-2)

1. Set up project structure
2. Implement MCP client class
3. Handle JSON-RPC communication
4. Process management (start/stop servers)
5. Basic CLI for testing

### Phase 2: Web API Layer (Week 2-3)

1. REST API design
2. WebSocket implementation
3. Authentication & authorization
4. Server configuration management
5. API documentation (OpenAPI)

### Phase 3: Frontend Development (Week 3-4)

1. UI framework setup
2. Dashboard layout
3. Tool exploration interface
4. Real-time updates
5. Response visualization

### Phase 4: Advanced Features (Week 4-6)

1. AI model integration
2. Custom UI components for tools
3. Workflow automation
4. Advanced testing framework
5. Performance optimization

## Core Components

### MCP Client Class (TypeScript)

```typescript
// src/mcp/MCPClient.ts
import { spawn, ChildProcess } from 'child_process';
import { EventEmitter } from 'events';

interface MCPRequest {
  jsonrpc: '2.0';
  method: string;
  params?: any;
  id: number | string;
}

interface MCPResponse {
  jsonrpc: '2.0';
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
  id: number | string;
}

export class MCPClient extends EventEmitter {
  private process: ChildProcess | null = null;
  private requestId = 0;
  private pendingRequests = new Map<number, {
    resolve: (value: any) => void;
    reject: (error: any) => void;
  }>();

  constructor(private command: string, private args: string[] = []) {
    super();
  }

  async connect(): Promise<void> {
    this.process = spawn(this.command, this.args, {
      stdio: ['pipe', 'pipe', 'pipe']
    });

    this.process.stdout?.on('data', (data) => {
      this.handleResponse(data.toString());
    });

    this.process.stderr?.on('data', (data) => {
      console.error('MCP Server Error:', data.toString());
    });

    this.process.on('exit', (code) => {
      this.emit('exit', code);
    });

    // Initialize connection
    await this.request('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {}
    });
  }

  private async request(method: string, params?: any): Promise<any> {
    const id = ++this.requestId;
    const request: MCPRequest = {
      jsonrpc: '2.0',
      method,
      params,
      id
    };

    return new Promise((resolve, reject) => {
      this.pendingRequests.set(id, { resolve, reject });
      this.process?.stdin?.write(JSON.stringify(request) + '\n');
    });
  }

  private handleResponse(data: string): void {
    try {
      const response: MCPResponse = JSON.parse(data);
      const pending = this.pendingRequests.get(response.id as number);
      
      if (pending) {
        if (response.error) {
          pending.reject(response.error);
        } else {
          pending.resolve(response.result);
        }
        this.pendingRequests.delete(response.id as number);
      }
    } catch (error) {
      console.error('Failed to parse MCP response:', error);
    }
  }

  async listTools() {
    return this.request('tools/list');
  }

  async callTool(name: string, arguments: any) {
    return this.request('tools/call', { name, arguments });
  }

  async disconnect(): Promise<void> {
    this.process?.kill();
    this.process = null;
  }
}
```

### Server Manager

```typescript
// src/mcp/ServerManager.ts
export interface ServerConfig {
  id: string;
  name: string;
  command: string;
  args?: string[];
  env?: Record<string, string>;
  autoStart?: boolean;
}

export class ServerManager {
  private servers = new Map<string, MCPClient>();
  private configs = new Map<string, ServerConfig>();

  async addServer(config: ServerConfig): Promise<void> {
    this.configs.set(config.id, config);
    
    if (config.autoStart) {
      await this.startServer(config.id);
    }
  }

  async startServer(id: string): Promise<MCPClient> {
    const config = this.configs.get(id);
    if (!config) throw new Error(`Server ${id} not found`);

    const client = new MCPClient(config.command, config.args);
    
    // Set environment variables
    if (config.env) {
      process.env = { ...process.env, ...config.env };
    }

    await client.connect();
    this.servers.set(id, client);
    
    return client;
  }

  async stopServer(id: string): Promise<void> {
    const client = this.servers.get(id);
    if (client) {
      await client.disconnect();
      this.servers.delete(id);
    }
  }

  getServer(id: string): MCPClient | undefined {
    return this.servers.get(id);
  }

  listServers(): ServerConfig[] {
    return Array.from(this.configs.values());
  }
}
```

## Web Application Setup

### Backend API Structure

```typescript
// src/api/server.ts
import express from 'express';
import { Server } from 'socket.io';
import { ServerManager } from '../mcp/ServerManager';

const app = express();
const io = new Server(server, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:3000'
  }
});

const serverManager = new ServerManager();

// REST API Routes
app.post('/api/servers', async (req, res) => {
  try {
    await serverManager.addServer(req.body);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/servers/:id/tools', async (req, res) => {
  try {
    const server = serverManager.getServer(req.params.id);
    if (!server) return res.status(404).json({ error: 'Server not found' });
    
    const tools = await server.listTools();
    res.json(tools);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/servers/:id/tools/:toolName', async (req, res) => {
  try {
    const server = serverManager.getServer(req.params.id);
    if (!server) return res.status(404).json({ error: 'Server not found' });
    
    const result = await server.callTool(req.params.toolName, req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// WebSocket for real-time updates
io.on('connection', (socket) => {
  socket.on('subscribe-server', (serverId) => {
    socket.join(`server:${serverId}`);
  });

  socket.on('call-tool', async (data) => {
    const { serverId, toolName, arguments } = data;
    const server = serverManager.getServer(serverId);
    
    if (server) {
      try {
        const result = await server.callTool(toolName, arguments);
        socket.emit('tool-result', { toolName, result });
      } catch (error) {
        socket.emit('tool-error', { toolName, error: error.message });
      }
    }
  });
});
```

### Frontend Components

```tsx
// src/components/MCPDashboard.tsx
import React, { useState, useEffect } from 'react';
import { ServerList } from './ServerList';
import { ToolExplorer } from './ToolExplorer';
import { ResultViewer } from './ResultViewer';
import { useMCPClient } from '../hooks/useMCPClient';

export const MCPDashboard: React.FC = () => {
  const { servers, tools, results, callTool } = useMCPClient();
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<string | null>(null);

  return (
    <div className="mcp-dashboard">
      <div className="sidebar">
        <ServerList
          servers={servers}
          selectedServer={selectedServer}
          onSelectServer={setSelectedServer}
        />
      </div>
      
      <div className="main-content">
        {selectedServer && (
          <ToolExplorer
            tools={tools[selectedServer] || []}
            selectedTool={selectedTool}
            onSelectTool={setSelectedTool}
            onCallTool={(toolName, args) => 
              callTool(selectedServer, toolName, args)
            }
          />
        )}
        
        <ResultViewer results={results} />
      </div>
    </div>
  );
};
```

## Database Integration

### Schema Design

```sql
-- PostgreSQL schema for MCP client
CREATE TABLE servers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  command VARCHAR(255) NOT NULL,
  args JSONB DEFAULT '[]',
  env JSONB DEFAULT '{}',
  auto_start BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tool_calls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  server_id UUID REFERENCES servers(id),
  tool_name VARCHAR(255) NOT NULL,
  arguments JSONB,
  result JSONB,
  error TEXT,
  duration_ms INTEGER,
  user_id UUID,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE workflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  steps JSONB NOT NULL,
  created_by UUID,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Prisma Integration

```typescript
// prisma/schema.prisma
model Server {
  id        String   @id @default(uuid())
  name      String
  command   String
  args      Json     @default("[]")
  env       Json     @default("{}")
  autoStart Boolean  @default(false)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  
  toolCalls ToolCall[]
}

model ToolCall {
  id         String   @id @default(uuid())
  serverId   String
  server     Server   @relation(fields: [serverId], references: [id])
  toolName   String
  arguments  Json?
  result     Json?
  error      String?
  durationMs Int?
  userId     String?
  createdAt  DateTime @default(now())
}
```

## AI Model Integration

### Multi-Model Support

```typescript
// src/ai/AIProvider.ts
interface AIProvider {
  name: string;
  generateCompletion(prompt: string, context?: any): Promise<string>;
  generateEmbedding(text: string): Promise<number[]>;
}

class OpenAIProvider implements AIProvider {
  name = 'openai';
  
  constructor(private apiKey: string) {}
  
  async generateCompletion(prompt: string, context?: any): Promise<string> {
    // Implementation using OpenAI API
  }
  
  async generateEmbedding(text: string): Promise<number[]> {
    // Implementation using OpenAI embeddings
  }
}

class AnthropicProvider implements AIProvider {
  name = 'anthropic';
  
  constructor(private apiKey: string) {}
  
  async generateCompletion(prompt: string, context?: any): Promise<string> {
    // Implementation using Claude API
  }
  
  async generateEmbedding(text: string): Promise<number[]> {
    // Implementation using Anthropic embeddings
  }
}

// AI-enhanced MCP tool calling
class AIEnhancedMCPClient {
  constructor(
    private mcpClient: MCPClient,
    private aiProvider: AIProvider
  ) {}
  
  async intelligentToolCall(userQuery: string): Promise<any> {
    // 1. Get available tools
    const tools = await this.mcpClient.listTools();
    
    // 2. Use AI to determine which tool to call
    const toolSelectionPrompt = `
      User Query: ${userQuery}
      Available Tools: ${JSON.stringify(tools)}
      
      Which tool should be called and with what arguments?
      Respond with JSON: { "tool": "tool_name", "arguments": {} }
    `;
    
    const aiResponse = await this.aiProvider.generateCompletion(toolSelectionPrompt);
    const { tool, arguments } = JSON.parse(aiResponse);
    
    // 3. Call the selected tool
    return this.mcpClient.callTool(tool, arguments);
  }
}
```

## Custom UI Components

### Tool-Specific UIs

```tsx
// src/components/tools/PatientViewer.tsx
import React from 'react';
import { Patient, Admission } from '../types';

interface PatientViewerProps {
  data: {
    patient: Patient;
    admissions?: Admission[];
  };
}

export const PatientViewer: React.FC<PatientViewerProps> = ({ data }) => {
  return (
    <div className="patient-viewer">
      <div className="patient-header">
        <h2>Patient {data.patient.subject_id}</h2>
        <div className="patient-demographics">
          <span>Gender: {data.patient.gender}</span>
          <span>Age: {data.patient.anchor_age}</span>
        </div>
      </div>
      
      {data.admissions && (
        <div className="admissions-timeline">
          <h3>Admissions Timeline</h3>
          {data.admissions.map(admission => (
            <div key={admission.hadm_id} className="admission-card">
              <h4>Admission {admission.hadm_id}</h4>
              <p>Type: {admission.admission_type}</p>
              <p>Admitted: {admission.admittime}</p>
              <p>Discharged: {admission.dischtime}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Tool UI Registry
export const toolUIRegistry = {
  'ehr_patient': PatientViewer,
  'ehr_search_notes': NoteSearchViewer,
  'ehr_list_diagnoses': DiagnosisListViewer,
  // ... other tool-specific components
};
```

### Dynamic Form Generation

```tsx
// src/components/DynamicToolForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';

interface ToolParameter {
  name: string;
  type: string;
  description?: string;
  required?: boolean;
  default?: any;
  enum?: string[];
}

interface DynamicToolFormProps {
  tool: {
    name: string;
    description: string;
    parameters: ToolParameter[];
  };
  onSubmit: (args: any) => void;
}

export const DynamicToolForm: React.FC<DynamicToolFormProps> = ({ 
  tool, 
  onSubmit 
}) => {
  const { register, handleSubmit } = useForm();

  const renderField = (param: ToolParameter) => {
    switch (param.type) {
      case 'string':
        if (param.enum) {
          return (
            <select {...register(param.name)} defaultValue={param.default}>
              {param.enum.map(value => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          );
        }
        return (
          <input
            type="text"
            {...register(param.name)}
            defaultValue={param.default}
          />
        );
      
      case 'boolean':
        return (
          <input
            type="checkbox"
            {...register(param.name)}
            defaultChecked={param.default}
          />
        );
      
      case 'number':
        return (
          <input
            type="number"
            {...register(param.name, { valueAsNumber: true })}
            defaultValue={param.default}
          />
        );
      
      default:
        return null;
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <h3>{tool.name}</h3>
      <p>{tool.description}</p>
      
      {tool.parameters.map(param => (
        <div key={param.name} className="form-field">
          <label>
            {param.name}
            {param.required && <span className="required">*</span>}
          </label>
          {renderField(param)}
          {param.description && (
            <small>{param.description}</small>
          )}
        </div>
      ))}
      
      <button type="submit">Execute Tool</button>
    </form>
  );
};
```

## Automated Testing

### Testing Strategy

```typescript
// src/tests/mcp-client.test.ts
import { MCPClient } from '../mcp/MCPClient';
import { MockMCPServer } from './mocks/MockMCPServer';

describe('MCPClient', () => {
  let client: MCPClient;
  let mockServer: MockMCPServer;

  beforeEach(async () => {
    mockServer = new MockMCPServer();
    await mockServer.start();
    
    client = new MCPClient('node', [mockServer.getPath()]);
    await client.connect();
  });

  afterEach(async () => {
    await client.disconnect();
    await mockServer.stop();
  });

  test('should list tools', async () => {
    const tools = await client.listTools();
    expect(tools).toHaveProperty('tools');
    expect(Array.isArray(tools.tools)).toBe(true);
  });

  test('should call tool successfully', async () => {
    const result = await client.callTool('test_tool', { 
      param1: 'value1' 
    });
    expect(result).toHaveProperty('success', true);
  });

  test('should handle tool errors', async () => {
    await expect(
      client.callTool('error_tool', {})
    ).rejects.toThrow('Tool execution failed');
  });
});
```

### Mock MCP Server

```typescript
// src/tests/mocks/MockMCPServer.ts
export class MockMCPServer {
  private server: any;
  private port: number;

  async start(): Promise<void> {
    // Create a mock server that responds to MCP protocol
    this.server = createMockServer({
      tools: [
        {
          name: 'test_tool',
          description: 'Test tool',
          parameters: [],
          handler: async (args) => ({ success: true, data: args })
        },
        {
          name: 'error_tool',
          description: 'Tool that errors',
          parameters: [],
          handler: async () => {
            throw new Error('Tool execution failed');
          }
        }
      ]
    });
    
    await this.server.listen(this.port);
  }

  getPath(): string {
    return path.join(__dirname, 'mock-mcp-server.js');
  }

  async stop(): Promise<void> {
    await this.server.close();
  }
}
```

### E2E Testing

```typescript
// src/tests/e2e/dashboard.test.ts
import { test, expect } from '@playwright/test';

test.describe('MCP Dashboard', () => {
  test('should add and connect to a server', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Add server
    await page.click('[data-testid="add-server-button"]');
    await page.fill('[name="name"]', 'Test Server');
    await page.fill('[name="command"]', 'mock-mcp-server');
    await page.click('[type="submit"]');
    
    // Verify server appears in list
    await expect(page.locator('[data-testid="server-list"]'))
      .toContainText('Test Server');
    
    // Connect to server
    await page.click('[data-testid="connect-button"]');
    await expect(page.locator('[data-testid="status"]'))
      .toContainText('Connected');
  });

  test('should execute a tool', async ({ page }) => {
    // ... setup server connection ...
    
    // Select tool
    await page.click('[data-testid="tool-ehr_patient"]');
    
    // Fill form
    await page.fill('[name="subject_id"]', '10000032');
    await page.check('[name="include_diagnoses"]');
    
    // Execute
    await page.click('[data-testid="execute-tool"]');
    
    // Verify results
    await expect(page.locator('[data-testid="results"]'))
      .toContainText('Patient 10000032');
  });
});
```

## Deployment

### Docker Configuration

```dockerfile
# Dockerfile
FROM node:18-alpine

# Install Python for MCP servers that need it
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy application
COPY . .

# Build frontend
RUN npm run build

EXPOSE 3000

CMD ["node", "dist/server.js"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-client:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/mcp
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./mcp-servers:/app/mcp-servers
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=mcp
    volumes:
      - postgres-data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    volumes:
      - redis-data:/data

volumes:
  postgres-data:
  redis-data:
```

### Production Considerations

1. **Security**:
   - Implement proper authentication (JWT, OAuth)
   - Sanitize tool inputs
   - Use environment-specific configurations
   - Enable HTTPS

2. **Scalability**:
   - Use Redis for session management
   - Implement horizontal scaling for API servers
   - Use message queues for long-running tools

3. **Monitoring**:
   - Add application metrics (Prometheus)
   - Log aggregation (ELK stack)
   - Error tracking (Sentry)

4. **Performance**:
   - Cache tool responses
   - Implement rate limiting
   - Use connection pooling

## Next Steps

1. **Start with the core MCP client implementation**
2. **Build a simple REST API**
3. **Create basic UI components**
4. **Add one AI provider integration**
5. **Implement automated tests**
6. **Deploy a minimal version**
7. **Iterate based on user feedback**

## Resources

- [MCP Specification](https://github.com/anthropics/mcp)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Socket.io Documentation](https://socket.io/docs/)
- [Playwright Testing](https://playwright.dev/)

This guide provides a foundation for building a production-ready MCP client web application. Start with the core components and gradually add features based on your specific needs.