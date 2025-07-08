#!/usr/bin/env python3
"""
Fresh Render Deployment Script - Creates completely new services
"""
import os
import requests
import json
import sys
from typing import Dict, Any

class FreshRenderDeployer:
    """
    Deploy fresh voice agent services to Render
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_fresh_database(self) -> Dict[str, Any]:
        """
        Create a fresh PostgreSQL database
        """
        print("🗄️ Creating fresh PostgreSQL database...")
        
        db_config = {
            "type": "postgresql",
            "name": "voice-agent-db-fresh",
            "plan": "starter",
            "region": "oregon",
            "databaseName": "voice_agent_fresh",
            "databaseUser": "voice_agent_user"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/postgres",
                headers=self.headers,
                json=db_config
            )
            
            if response.status_code == 201:
                database = response.json()
                print(f"✅ Fresh database created: {database['name']}")
                print(f"📊 Database URL: {database['databaseUrl']}")
                return database
            else:
                print(f"❌ Failed to create database: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return None
    
    def create_fresh_web_service(self, repo_url: str, database_url: str, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """
        Create a fresh web service
        """
        print("🚀 Creating fresh web service...")
        
        service_config = {
            "type": "web_service",
            "name": "voice-agent-fresh",
            "repo": repo_url,
            "plan": "starter",
            "region": "oregon",
            "branch": "main",
            "buildCommand": "pip install --upgrade pip && pip install -r requirements.txt",
            "startCommand": "python src/main.py",
            "healthCheckPath": "/health",
            "envVars": [
                # Core Flask settings
                {"key": "FLASK_ENV", "value": "production"},
                {"key": "SECRET_KEY", "generateValue": True},
                {"key": "PORT", "value": "10000"},
                {"key": "DATABASE_URL", "value": database_url},
                
                # Voice agent settings
                {"key": "VOICE_PROVIDER", "value": "openai"},
                {"key": "DEFAULT_VOICE", "value": "alloy"},
                {"key": "COMPANY_NAME", "value": "Voice Agent Fresh"},
                {"key": "MAX_CONVERSATION_TURNS", "value": "20"},
                {"key": "RESPONSE_TIMEOUT", "value": "30"},
            ]
        }
        
        # Add user-provided environment variables
        for key, value in env_vars.items():
            service_config["envVars"].append({"key": key, "value": value})
        
        try:
            response = requests.post(
                f"{self.base_url}/services",
                headers=self.headers,
                json=service_config
            )
            
            if response.status_code == 201:
                service = response.json()
                print(f"✅ Fresh web service created: {service['name']}")
                print(f"🌐 Service URL: {service['serviceDetails']['url']}")
                return service
            else:
                print(f"❌ Failed to create web service: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating web service: {e}")
            return None
    
    def deploy_fresh_voice_agent(self, repo_url: str, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """
        Deploy complete fresh voice agent system for A Killion Voice
        """
        print("🎯 Deploying A Killion Voice Agent to Production")
        print("=" * 50)
        
        # Step 1: Create fresh database
        database = self.create_fresh_database()
        if not database:
            print("❌ Database creation failed - aborting deployment")
            return None
        
        # Step 2: Create fresh web service
        service = self.create_fresh_web_service(
            repo_url, 
            database["databaseUrl"], 
            env_vars
        )
        if not service:
            print("❌ Web service creation failed")
            return None
        
        # Step 3: Return deployment info
        deployment_info = {
            "database": database,
            "service": service,
            "urls": {
                "app": service["serviceDetails"]["url"],
                "health": f"{service['serviceDetails']['url']}/health",
                "twilio_webhook": f"{service['serviceDetails']['url']}/api/twilio/inbound",
                "status_webhook": f"{service['serviceDetails']['url']}/api/twilio/status"
            },
            "production_details": {
                "domain": "akillionvoice.xyz",
                "phone": "(978) 643-2034",
                "company": "A Killion Voice"
            }
        }
        
        print("\n🎉 A Killion Voice Deployment Complete!")
        print("=" * 50)
        print(f"🌐 App URL: {deployment_info['urls']['app']}")
        print(f"❤️ Health Check: {deployment_info['urls']['health']}")
        print(f"📞 Twilio Webhook: {deployment_info['urls']['twilio_webhook']}")
        print(f"📊 Status Webhook: {deployment_info['urls']['status_webhook']}")
        print(f"☎️ Phone Number: (978) 643-2034")
        print(f"🌍 Domain: akillionvoice.xyz")
        
        return deployment_info

def main():
    """
    Deploy A Killion Voice to Production
    """
    print("🎯 A Killion Voice - Production Deployment")
    print("Deploying to akillionvoice.xyz with (978) 643-2034")
    print("=" * 50)
    
    # Get credentials from environment or user input
    api_key = os.getenv('RENDER_API_KEY')
    if not api_key:
        api_key = input("Enter your Render API key: ").strip()
        if not api_key:
            print("❌ Render API key is required")
            return False
    
    # Get repository URL
    repo_url = input("Enter your GitHub repository URL (or press Enter for default): ").strip()
    if not repo_url:
        repo_url = "https://github.com/copp1723/voice-agent-fresh"
        print(f"Using default repo: {repo_url}")
    
    # Get OpenRouter API key
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_key:
        openrouter_key = input("Enter your OpenRouter API key: ").strip()
        if not openrouter_key:
            print("❌ OpenRouter API key is required")
            return False
    
    # Production environment variables (no hard-coded secrets)
    env_vars = {
        "OPENROUTER_API_KEY": openrouter_key,
        "COMPANY_NAME": "A Killion Voice",
        "DOMAIN": "akillionvoice.xyz",
        "API_BASE_URL": "https://api.akillionvoice.xyz",
        "TWILIO_PHONE_NUMBER": "+19786432034",
        "FLASK_ENV": "production"
    }
    
    # Optional Twilio credentials (can be added later in Render dashboard)
    print("\n📝 Twilio Configuration:")
    print("You can add these later in the Render dashboard if not available now:")
    
    twilio_sid = input("Twilio Account SID (optional): ").strip()
    if twilio_sid:
        env_vars["TWILIO_ACCOUNT_SID"] = twilio_sid
    
    twilio_token = input("Twilio Auth Token (optional): ").strip()
    if twilio_token:
        env_vars["TWILIO_AUTH_TOKEN"] = twilio_token
    
    # Deploy
    deployer = FreshRenderDeployer(api_key)
    result = deployer.deploy_fresh_voice_agent(repo_url, env_vars)
    
    if result:
        print("\n📋 Next Steps:")
        print("1. Test the health endpoint")
        print("2. Add Twilio credentials in Render dashboard if not provided")
        print("3. Configure Twilio webhook URLs:")
        print(f"   - Incoming calls: {result['urls']['twilio_webhook']}")
        print(f"   - Status updates: {result['urls']['status_webhook']}")
        print("4. Test by calling (978) 643-2034")
        print("5. Monitor logs in Render dashboard")
        print("\n🎉 A Killion Voice is ready for production!")
    else:
        print("\n❌ Deployment failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

