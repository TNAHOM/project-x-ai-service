## Folder structure

```

ai_agent_service/
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI entry point
│   ├── config.py                   # Environment configs (dotenv / settings)
│   ├── container.py                # Dependency injection setup
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── agent_router.py     # Endpoints for AI Agent interactions
│   │   │   └── mcp_router.py       # Endpoints for MCP server operations
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── agent_schema.py     # Request/Response models for agents
│   │       └── mcp_schema.py       # Request/Response models for MCP
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py           # Custom exception classes
│   │   ├── logger.py               # Central logging configuration
│   │   ├── utils.py                # Shared helper functions
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agent_service.py        # LangChain agent management logic
│   │   ├── mcp_service.py          # MCP server interactions
│   │   └── registry.py             # For registering & managing multiple agents
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── agent_model.py          # Data models for agent definitions
│   │   ├── mcp_model.py            # Data models for MCP context
│   │   └── base_model.py           # Shared domain base classes
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── db.py                   # If you add a DB (e.g., for logs/state)
│   │   ├── http_client.py          # Async external API/MCP HTTP calls
│   │   └── langchain_setup.py      # LangChain tool & LLM initialization
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_agents.py
│       └── test_mcp.py
│
├── requirements.txt
├── .env
├── README.md
└── pyproject.toml  (optional if using Poetry)

```
