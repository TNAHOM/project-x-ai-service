import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Any, cast
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.core.logger import logging



logger = logging.getLogger(__name__)

TOKEN_PATH = Path(__file__).parent / 'tokens' / 'slack_token.json'

logger.info(f"Using TOKEN_PATH: {TOKEN_PATH}")


# Load environment variables from a local .env if present
def _load_env_file() -> None:
    env_file = Path(__file__).parent / ".env"
    try:
        from dotenv import load_dotenv  # type: ignore
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=False)
    except Exception:
        # Fallback simple parser if python-dotenv isn't installed
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    if k and k not in os.environ:
                        os.environ[k] = v
            except Exception:
                pass


_load_env_file()


class SlackService:
    """Handles Slack API operations with token-based authentication"""
    
    def __init__(self):
        self.client: Optional[WebClient] = None
        self.token: Optional[str] = None
        self.bot_user_id: Optional[str] = None

    def _get_token_from_env(self) -> Optional[str]:
        """Get token from environment variable"""
        return os.environ.get("SLACK_BOT_TOKEN") or os.environ.get("SLACK_TOKEN")

    def _get_token_from_file(self) -> Optional[str]:
        """Load token from token file"""
        if TOKEN_PATH.exists():
            try:
                with open(TOKEN_PATH, 'r') as f:
                    data = json.load(f)
                    return data.get('token')
            except Exception as e:
                logger.warning(f"Failed to load token from file: {e}")
        return None

    def _save_token(self, token: str) -> None:
        """Save token to file for persistence"""
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(TOKEN_PATH, 'w') as f:
                json.dump({'token': token, 'saved_at': datetime.now().isoformat()}, f)
            logger.info("Slack token saved successfully")
        except Exception as e:
            logger.warning(f"Failed to save token: {e}")
        
    def authenticate(self) -> bool:
        """
        Authenticate with Slack using Bot Token.
        
        Priority:
        1. SLACK_BOT_TOKEN or SLACK_TOKEN environment variable
        2. Token from slack_token.json file
        
        Returns True if authentication successful.
        """
        # Try to get token from env first
        self.token = self._get_token_from_env()
        
        # Fall back to file
        if not self.token:
            self.token = self._get_token_from_file()
        
        if not self.token:
            raise ValueError(
                "Slack token not found. Please set SLACK_BOT_TOKEN environment variable "
                f"or save token to {TOKEN_PATH}. "
                "See setup instructions for how to obtain a token."
            )
        
        # Initialize Slack client
        self.client = WebClient(token=self.token)
        if self.client is None:
            raise Exception("Failed to initialize Slack WebClient.")
        
        # Test authentication and get bot info
        try:
            response = self.client.auth_test()
            self.bot_user_id = response['user_id']
            logger.info(f"Authenticated as bot: {response['user']} in team: {response['team']}")
            
            # Save token to file if it came from env (for future use)
            if self._get_token_from_env() and not TOKEN_PATH.exists():
                self._save_token(self.token)
            
            return True
        except SlackApiError as e:
            raise Exception(f"Failed to authenticate with Slack: {e.response['error']}")
    
    def _require_client(self) -> WebClient:
        """Return initialized Slack WebClient or raise a helpful error."""
        if self.client is None:
            raise Exception("Slack client is not initialized. Call 'authenticate()' before using this method.")
        return cast(WebClient, self.client)

    def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict]] = None
    ) -> dict:
        """Send a message to a Slack channel or user"""
        try:
            client = self._require_client()
            response = client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts,
                blocks=blocks
            )
            data: Any = response.data
            
            return {
                'ok': data.get('ok'),
                'channel': data.get('channel'),
                'ts': data.get('ts'),
                'message': data.get('message'),
                'status': 'Message sent successfully'
            }
        except SlackApiError as e:
            raise Exception(f"Failed to send message: {e.response['error']}")
    
    def list_channels(
        self,
        types: str = "public_channel,private_channel",
        limit: int = 100
    ) -> dict:
        """List Slack channels"""
        try:
            client = self._require_client()
            response = client.conversations_list(
                types=types,
                limit=limit
            )
            data: Any = response.data
            channels = data.get('channels') or []
            
            return {
                'count': len(channels),
                'channels': [
                    {
                        'id': ch['id'],
                        'name': ch['name'],
                        'is_channel': ch.get('is_channel', False),
                        'is_private': ch.get('is_private', False),
                        'is_member': ch.get('is_member', False),
                        'num_members': ch.get('num_members', 0),
                        'topic': ch.get('topic', {}).get('value', ''),
                        'purpose': ch.get('purpose', {}).get('value', '')
                    }
                    for ch in channels
                ]
            }
        except SlackApiError as e:
            raise Exception(f"Failed to list channels: {e.response['error']}")
    
    def get_channel_history(
        self,
        channel: str,
        limit: int = 10,
        oldest: Optional[str] = None,
        latest: Optional[str] = None
    ) -> dict:
        """Get message history from a channel"""
        try:
            client = self._require_client()
            response = client.conversations_history(
                channel=channel,
                limit=limit,
                oldest=oldest,
                latest=latest
            )
            data: Any = response.data
            messages = data.get('messages') or []
            
            return {
                'channel': channel,
                'count': len(messages),
                'messages': [
                    {
                        'type': msg.get('type'),
                        'user': msg.get('user'),
                        'text': msg.get('text'),
                        'ts': msg.get('ts'),
                        'thread_ts': msg.get('thread_ts'),
                        'reply_count': msg.get('reply_count', 0),
                        'reactions': msg.get('reactions', [])
                    }
                    for msg in messages
                ]
            }
        except SlackApiError as e:
            raise Exception(f"Failed to get channel history: {e.response['error']}")
    
    def get_thread_replies(
        self,
        channel: str,
        thread_ts: str,
        limit: int = 100
    ) -> dict:
        """Get replies in a thread"""
        try:
            client = self._require_client()
            response = client.conversations_replies(
                channel=channel,
                ts=thread_ts,
                limit=limit
            )
            data: Any = response.data
            messages = data.get('messages') or []
            
            return {
                'channel': channel,
                'thread_ts': thread_ts,
                'count': len(messages),
                'messages': [
                    {
                        'type': msg.get('type'),
                        'user': msg.get('user'),
                        'text': msg.get('text'),
                        'ts': msg.get('ts'),
                        'thread_ts': msg.get('thread_ts')
                    }
                    for msg in messages
                ]
            }
        except SlackApiError as e:
            raise Exception(f"Failed to get thread replies: {e.response['error']}")
    
    def search_messages(
        self,
        query: str,
        count: int = 20,
        sort: str = "timestamp",
        sort_dir: str = "desc"
    ) -> dict:
        """Search for messages across workspace"""
        try:
            client = self._require_client()
            response = client.search_messages(
                query=query,
                count=count,
                sort=sort,
                sort_dir=sort_dir
            )
            data: Any = response.data
            messages_section = data.get('messages') or {}
            matches = messages_section.get('matches') or []
            
            return {
                'query': query,
                'total': messages_section.get('total', 0),
                'count': len(matches),
                'messages': [
                    {
                        'type': msg.get('type'),
                        'user': msg.get('user'),
                        'username': msg.get('username'),
                        'text': msg.get('text'),
                        'ts': msg.get('ts'),
                        'channel': msg.get('channel', {}).get('name'),
                        'channel_id': msg.get('channel', {}).get('id'),
                        'permalink': msg.get('permalink')
                    }
                    for msg in matches
                ]
            }
        except SlackApiError as e:
            raise Exception(f"Failed to search messages: {e.response['error']}")
    
    def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[List[Dict]] = None
    ) -> dict:
        """Update an existing message"""
        try:
            client = self._require_client()
            response = client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                blocks=blocks
            )
            data: Any = response.data
            return {
                'ok': data.get('ok'),
                'channel': data.get('channel'),
                'ts': data.get('ts'),
                'text': data.get('text'),
                'status': 'Message updated successfully'
            }
        except SlackApiError as e:
            raise Exception(f"Failed to update message: {e.response['error']}")
    
    def delete_message(
        self,
        channel: str,
        ts: str
    ) -> dict:
        """Delete a message"""
        try:
            client = self._require_client()
            response = client.chat_delete(
                channel=channel,
                ts=ts
            )
            data: Any = response.data
            return {
                'ok': data.get('ok'),
                'channel': data.get('channel'),
                'ts': data.get('ts'),
                'status': 'Message deleted successfully'
            }
        except SlackApiError as e:
            raise Exception(f"Failed to delete message: {e.response['error']}")
    
    def add_reaction(
        self,
        channel: str,
        timestamp: str,
        name: str
    ) -> dict:
        """Add emoji reaction to a message"""
        try:
            client = self._require_client()
            response = client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=name
            )
            data: Any = response.data
            return {
                'ok': data.get('ok'),
                'status': f'Reaction :{name}: added successfully'
            }
        except SlackApiError as e:
            raise Exception(f"Failed to add reaction: {e.response['error']}")
    
    def list_users(
        self,
        limit: int = 100
    ) -> dict:
        """List users in the workspace"""
        try:
            client = self._require_client()
            response = client.users_list(limit=limit)
            data: Any = response.data
            members = data.get('members') or []
            
            return {
                'count': len(members),
                'users': [
                    {
                        'id': user['id'],
                        'name': user.get('name'),
                        'real_name': user.get('real_name'),
                        'display_name': user.get('profile', {}).get('display_name'),
                        'email': user.get('profile', {}).get('email'),
                        'is_bot': user.get('is_bot', False),
                        'is_admin': user.get('is_admin', False),
                        'is_owner': user.get('is_owner', False),
                        'deleted': user.get('deleted', False)
                    }
                    for user in members
                    if not user.get('deleted', False)
                ]
            }
        except SlackApiError as e:
            raise Exception(f"Failed to list users: {e.response['error']}")
    
    def get_user_info(
        self,
        user_id: str
    ) -> dict:
        """Get information about a specific user"""
        try:
            if self.client is None:
                raise Exception("Slack client is not initialized. Call 'authenticate()' before using this method.")
            response = self.client.users_info(user=user_id)
            
            user = response.get('user')
            if not user:
                raise Exception("User not found in response")
            
            return {
                'id': user['id'],
                'name': user.get('name'),
                'real_name': user.get('real_name'),
                'display_name': user.get('profile', {}).get('display_name'),
                'email': user.get('profile', {}).get('email'),
                'phone': user.get('profile', {}).get('phone'),
                'title': user.get('profile', {}).get('title'),
                'status_text': user.get('profile', {}).get('status_text'),
                'status_emoji': user.get('profile', {}).get('status_emoji'),
                'is_bot': user.get('is_bot', False),
                'is_admin': user.get('is_admin', False),
                'is_owner': user.get('is_owner', False),
                'timezone': user.get('tz')
            }
        except SlackApiError as e:
            raise Exception(f"Failed to get user info: {e.response['error']}")
    
    def upload_file(
        self,
        channels: str,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        filename: Optional[str] = None,
        title: Optional[str] = None,
        initial_comment: Optional[str] = None
    ) -> dict:
        """Upload a file to Slack"""
        try:
            kwargs = {
                'channels': channels,
                'title': title,
                'initial_comment': initial_comment
            }
            
            if file_path:
                kwargs['file'] = file_path
            elif content:
                kwargs['content'] = content
                if filename:
                    kwargs['filename'] = filename
            else:
                raise ValueError("Either file_path or content must be provided")
            
            client = self._require_client()
            response = client.files_upload(**kwargs)
            data: Any = response.data
            file_info = data.get('file')
            if not file_info:
                raise Exception("File upload failed: No file info returned in response")
            
            return {
                'ok': data.get('ok'),
                'file_id': file_info['id'],
                'name': file_info['name'],
                'title': file_info.get('title'),
                'mimetype': file_info.get('mimetype'),
                'url_private': file_info.get('url_private'),
                'permalink': file_info.get('permalink'),
                'status': 'File uploaded successfully'
            }
        except SlackApiError as e:
            raise Exception(f"Failed to upload file: {e.response['error']}")
    
    def create_channel(
        self,
        name: str,
        is_private: bool = False
    ) -> dict:
        """Create a new channel"""
        try:
            client = self._require_client()
            response = client.conversations_create(
                name=name,
                is_private=is_private
            )
            data: Any = response.data
            channel = data.get('channel') or {}
            
            return {
                'ok': data.get('ok'),
                'channel_id': channel.get('id'),
                'channel_name': channel.get('name'),
                'is_private': channel.get('is_private', False),
                'status': 'Channel created successfully'
            }
        except SlackApiError as e:
            raise Exception(f"Failed to create channel: {e.response['error']}")
    
    def invite_to_channel(
        self,
        channel: str,
        users: List[str]
    ) -> dict:
        """Invite users to a channel"""
        try:
            client = self._require_client()
            response = client.conversations_invite(
                channel=channel,
                users=','.join(users)
            )
            data: Any = response.data
            return {
                'ok': data.get('ok'),
                'channel': (data.get('channel') or {}).get('id'),
                'status': f'Successfully invited {len(users)} user(s) to channel'
            }
        except SlackApiError as e:
            raise Exception(f"Failed to invite users: {e.response['error']}")
    
    def set_channel_topic(
        self,
        channel: str,
        topic: str
    ) -> dict:
        """Set the topic for a channel"""
        try:
            client = self._require_client()
            response = client.conversations_setTopic(
                channel=channel,
                topic=topic
            )
            data: Any = response.data
            return {
                'ok': data.get('ok'),
                'channel': data.get('channel'),
                'topic': data.get('topic'),
                'status': 'Channel topic updated successfully'
            }
        except SlackApiError as e:
            raise Exception(f"Failed to set channel topic: {e.response['error']}")