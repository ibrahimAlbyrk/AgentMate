"""
Gmail Fetcher for AgentMate

This module provides functionality for fetching emails from Gmail.
"""

from typing import Dict, Any, List, Optional

from Agents.LLM.llm_agent import LLMAgent
from Core.logger import LoggerCreator

class GmailFetcher:
    """
    Responsible for fetching emails from Gmail.
    
    This class encapsulates all the logic for retrieving emails from Gmail,
    including fetching email lists and individual emails.
    """
    
    def __init__(self, llm_agent: LLMAgent, include_labels: List[str] = None):
        """
        Initialize the Gmail fetcher.
        
        Args:
            llm_agent: The LLM agent to use for fetching emails
            include_labels: Labels to include when fetching emails (default: ['INBOX'])
        """
        self.llm = llm_agent
        self.include_labels = include_labels or ['INBOX']
        self.logger = LoggerCreator.create_advanced_console("GmailFetcher")
    
    async def get_emails(self, limit: int) -> Dict[str, Any]:
        """
        Get a list of emails.
        
        Args:
            limit: Maximum number of emails to fetch
            
        Returns:
            A dictionary containing the fetched emails
        """
        try:
            output = await self.llm.run_action("get_emails", max_results=limit, label_ids=self.include_labels)
            return output['data']
        except Exception as e:
            self.logger.error(f"Error fetching emails: {str(e)}")
            return {'messages': []}
    
    async def get_emails_subjects(self, limit: int) -> Dict[str, Any]:
        """
        Get a list of email subjects.
        
        Args:
            limit: Maximum number of emails to fetch
            
        Returns:
            A dictionary containing the fetched email subjects
        """
        try:
            output = await self.llm.run_action("get_emails_subjects", max_results=limit, label_ids=self.include_labels)
            return output['data']
        except Exception as e:
            self.logger.error(f"Error fetching email subjects: {str(e)}")
            return {'messages': []}
    
    async def get_email_by_message_id(self, message_id: str) -> Dict[str, Any]:
        """
        Get a specific email by its message ID.
        
        Args:
            message_id: The ID of the message to fetch
            
        Returns:
            A dictionary containing the fetched email
        """
        try:
            output = await self.llm.run_action("get_email_by_message_id", message_id=message_id)
            return output['data']
        except Exception as e:
            self.logger.error(f"Error fetching email by message ID: {str(e)}")
            return {}