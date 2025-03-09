import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

class SalesforceClient:
    """Client for interacting with the Salesforce API to retrieve CRM data"""
    
    def __init__(self, 
                 client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 security_token: Optional[str] = None):
        self.client_id = client_id or os.getenv("SALESFORCE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SALESFORCE_CLIENT_SECRET")
        self.username = username or os.getenv("SALESFORCE_USERNAME")
        self.password = password or os.getenv("SALESFORCE_PASSWORD")
        self.security_token = security_token or os.getenv("SALESFORCE_SECURITY_TOKEN")
        self.instance_url = None
        self.access_token = None
        self.token_expiry = None
        
        if not all([self.client_id, self.client_secret, self.username, self.password]):
            logger.warning("Salesforce API credentials not fully configured")
    
    async def _get_access_token(self) -> str:
        """Get an access token from the Salesforce API"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
            
        try:
            url = "https://login.salesforce.com/services/oauth2/token"
            payload = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": f"{self.password}{self.security_token}" if self.security_token else self.password
            }
            
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.instance_url = token_data["instance_url"]
            self.token_expiry = datetime.now() + timedelta(seconds=3600)  # Typically 1 hour
            
            return self.access_token
        except Exception as e:
            logger.error(f"Error getting Salesforce access token: {str(e)}")
            raise
    
    async def get_opportunities(self, days_back: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent opportunities"""
        try:
            token = await self._get_access_token()
            
            # Calculate date filter
            from_date = datetime.now() - timedelta(days=days_back)
            date_str = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # SOQL query for opportunities
            query = (f"SELECT Id, Name, StageName, Amount, CloseDate, AccountId, Account.Name, "
                     f"LastModifiedDate, OwnerId, Owner.Name "
                     f"FROM Opportunity "
                     f"WHERE LastModifiedDate >= {date_str} "
                     f"ORDER BY LastModifiedDate DESC "
                     f"LIMIT {limit}")
            
            # URL encode the query
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            
            url = f"{self.instance_url}/services/data/v56.0/query?q={encoded_query}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json().get("records", [])
        except Exception as e:
            logger.error(f"Error getting opportunities from Salesforce: {str(e)}")
            return []
    
    async def get_accounts(self, search_term: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get accounts, optionally filtered by search term"""
        try:
            token = await self._get_access_token()
            
            # SOQL query for accounts
            if search_term:
                query = (f"SELECT Id, Name, Type, Industry, Website, Phone, Description, "
                         f"BillingAddress, LastModifiedDate "
                         f"FROM Account "
                         f"WHERE Name LIKE '%{search_term}%' "
                         f"ORDER BY LastModifiedDate DESC "
                         f"LIMIT {limit}")
            else:
                query = (f"SELECT Id, Name, Type, Industry, Website, Phone, Description, "
                         f"BillingAddress, LastModifiedDate "
                         f"FROM Account "
                         f"ORDER BY LastModifiedDate DESC "
                         f"LIMIT {limit}")
            
            # URL encode the query
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            
            url = f"{self.instance_url}/services/data/v56.0/query?q={encoded_query}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json().get("records", [])
        except Exception as e:
            logger.error(f"Error getting accounts from Salesforce: {str(e)}")
            return []
            
    async def get_contacts(self, account_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get contacts, optionally filtered by account ID"""
        try:
            token = await self._get_access_token()
            
            # SOQL query for contacts
            if account_id:
                query = (f"SELECT Id, FirstName, LastName, Email, Phone, AccountId, Account.Name, "
                         f"Title, Department, LastModifiedDate "
                         f"FROM Contact "
                         f"WHERE AccountId = '{account_id}' "
                         f"ORDER BY LastModifiedDate DESC "
                         f"LIMIT {limit}")
            else:
                query = (f"SELECT Id, FirstName, LastName, Email, Phone, AccountId, Account.Name, "
                         f"Title, Department, LastModifiedDate "
                         f"FROM Contact "
                         f"ORDER BY LastModifiedDate DESC "
                         f"LIMIT {limit}")
            
            # URL encode the query
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            
            url = f"{self.instance_url}/services/data/v56.0/query?q={encoded_query}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json().get("records", [])
        except Exception as e:
            logger.error(f"Error getting contacts from Salesforce: {str(e)}")
            return []