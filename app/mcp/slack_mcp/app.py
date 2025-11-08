import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from app.mcp.slack_mcp.server import SlackService
    
# Initialize MCP server and Slack service
app = Server("slack-mcp")
slack = SlackService()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Slack tools"""
    return [
        Tool(
            name="send-message",
            description="Send a message to a Slack channel or user",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID or name (e.g., 'C1234567890' or '#general')"
                    },
                    "text": {
                        "type": "string",
                        "description": "Message text to send"
                    },
                    "threadTs": {
                        "type": "string",
                        "description": "Thread timestamp to reply in a thread (optional)"
                    }
                },
                "required": ["channel", "text"]
            }
        ),
        Tool(
            name="list-channels",
            description="List all Slack channels",
            inputSchema={
                "type": "object",
                "properties": {
                    "types": {
                        "type": "string",
                        "description": "Comma-separated list of channel types",
                        "default": "public_channel,private_channel"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of channels to return",
                        "default": 100
                    }
                }
            }
        ),
        Tool(
            name="get-channel-history",
            description="Get message history from a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of messages to retrieve",
                        "default": 10
                    },
                    "oldest": {
                        "type": "string",
                        "description": "Oldest timestamp to include (optional)"
                    },
                    "latest": {
                        "type": "string",
                        "description": "Latest timestamp to include (optional)"
                    }
                },
                "required": ["channel"]
            }
        ),
        Tool(
            name="get-thread-replies",
            description="Get all replies in a thread",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID"
                    },
                    "threadTs": {
                        "type": "string",
                        "description": "Thread timestamp"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of replies to retrieve",
                        "default": 100
                    }
                },
                "required": ["channel", "threadTs"]
            }
        ),
        Tool(
            name="search-messages",
            description="Search for messages across the workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 20
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["score", "timestamp"],
                        "description": "Sort by relevance or time",
                        "default": "timestamp"
                    },
                    "sortDir": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sort direction",
                        "default": "desc"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="update-message",
            description="Update an existing message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID"
                    },
                    "ts": {
                        "type": "string",
                        "description": "Message timestamp"
                    },
                    "text": {
                        "type": "string",
                        "description": "New message text"
                    }
                },
                "required": ["channel", "ts", "text"]
            }
        ),
        Tool(
            name="delete-message",
            description="Delete a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID"
                    },
                    "ts": {
                        "type": "string",
                        "description": "Message timestamp"
                    }
                },
                "required": ["channel", "ts"]
            }
        ),
        Tool(
            name="add-reaction",
            description="Add an emoji reaction to a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID"
                    },
                    "timestamp": {
                        "type": "string",
                        "description": "Message timestamp"
                    },
                    "name": {
                        "type": "string",
                        "description": "Emoji name (without colons, e.g., 'thumbsup')"
                    }
                },
                "required": ["channel", "timestamp", "name"]
            }
        ),
        Tool(
            name="list-users",
            description="List all users in the workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of users to return",
                        "default": 100
                    }
                }
            }
        ),
        Tool(
            name="get-user-info",
            description="Get information about a specific user",
            inputSchema={
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "User ID"
                    }
                },
                "required": ["userId"]
            }
        ),
        Tool(
            name="upload-file",
            description="Upload a file to Slack",
            inputSchema={
                "type": "object",
                "properties": {
                    "channels": {
                        "type": "string",
                        "description": "Comma-separated list of channel IDs"
                    },
                    "filePath": {
                        "type": "string",
                        "description": "Path to file to upload"
                    },
                    "content": {
                        "type": "string",
                        "description": "File content (alternative to filePath)"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Filename (required when using content)"
                    },
                    "title": {
                        "type": "string",
                        "description": "File title"
                    },
                    "initialComment": {
                        "type": "string",
                        "description": "Initial comment for the file"
                    }
                },
                "required": ["channels"]
            }
        ),
        Tool(
            name="create-channel",
            description="Create a new Slack channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Channel name (lowercase, no spaces)"
                    },
                    "isPrivate": {
                        "type": "boolean",
                        "description": "Whether the channel should be private",
                        "default": False
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="invite-to-channel",
            description="Invite users to a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID"
                    },
                    "users": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of user IDs to invite"
                    }
                },
                "required": ["channel", "users"]
            }
        ),
        Tool(
            name="set-channel-topic",
            description="Set the topic for a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID"
                    },
                    "topic": {
                        "type": "string",
                        "description": "New channel topic"
                    }
                },
                "required": ["channel", "topic"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    # Ensure user is authenticated
    if not slack.client:
        slack.authenticate()
    
    try:
        if name == "send-message":
            result = slack.send_message(
                channel=arguments['channel'],
                text=arguments['text'],
                thread_ts=arguments.get('threadTs')
            )
        elif name == "list-channels":
            result = slack.list_channels(
                types=arguments.get('types', 'public_channel,private_channel'),
                limit=arguments.get('limit', 100)
            )
        elif name == "get-channel-history":
            result = slack.get_channel_history(
                channel=arguments['channel'],
                limit=arguments.get('limit', 10),
                oldest=arguments.get('oldest'),
                latest=arguments.get('latest')
            )
        elif name == "get-thread-replies":
            result = slack.get_thread_replies(
                channel=arguments['channel'],
                thread_ts=arguments['threadTs'],
                limit=arguments.get('limit', 100)
            )
        elif name == "search-messages":
            result = slack.search_messages(
                query=arguments['query'],
                count=arguments.get('count', 20),
                sort=arguments.get('sort', 'timestamp'),
                sort_dir=arguments.get('sortDir', 'desc')
            )
        elif name == "update-message":
            result = slack.update_message(
                channel=arguments['channel'],
                ts=arguments['ts'],
                text=arguments['text']
            )
        elif name == "delete-message":
            result = slack.delete_message(
                channel=arguments['channel'],
                ts=arguments['ts']
            )
        elif name == "add-reaction":
            result = slack.add_reaction(
                channel=arguments['channel'],
                timestamp=arguments['timestamp'],
                name=arguments['name']
            )
        elif name == "list-users":
            result = slack.list_users(
                limit=arguments.get('limit', 100)
            )
        elif name == "get-user-info":
            result = slack.get_user_info(
                user_id=arguments['userId']
            )
        elif name == "upload-file":
            result = slack.upload_file(
                channels=arguments['channels'],
                file_path=arguments.get('filePath'),
                content=arguments.get('content'),
                filename=arguments.get('filename'),
                title=arguments.get('title'),
                initial_comment=arguments.get('initialComment')
            )
        elif name == "create-channel":
            result = slack.create_channel(
                name=arguments['name'],
                is_private=arguments.get('isPrivate', False)
            )
        elif name == "invite-to-channel":
            result = slack.invite_to_channel(
                channel=arguments['channel'],
                users=arguments['users']
            )
        elif name == "set-channel-topic":
            result = slack.set_channel_topic(
                channel=arguments['channel'],
                topic=arguments['topic']
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())