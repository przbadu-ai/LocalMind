from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional, Any
from utils.web_scraper import fetch_and_extract
from database.models import Message, ToolCallData
from database.repositories.message_repository import MessageRepository

router = APIRouter()
logger = logging.getLogger(__name__)
message_repo = MessageRepository()

class ApproveToolCallRequest(BaseModel):
    conversation_id: str
    tool_call_id: str
    approved: bool
    tool_name: str
    tool_args: dict[str, Any]

@router.post("/chat/tool/approve")
async def approve_tool_call(request: ApproveToolCallRequest):
    """
    Approve or deny a tool call.
    If approved, executes the tool (fetch_url) and returns the result.
    If denied, returns an error message.
    """
    logger.info(f"Tool approval request: {request.conversation_id}, {request.tool_call_id}, {request.approved}")
    
    if not request.approved:
        # Update status to 'error' in DB for persistence
        messages = message_repo.get_recent_by_chat_id(request.conversation_id, limit=20)
        found_msg = False
        for msg in reversed(messages):
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc.id == request.tool_call_id:
                        logger.info(f"Persisting denial for tool call {tc.id} in message {msg.id}")
                        tc.status = "error"
                        tc.error = "User denied permission"
                        message_repo.update(msg)
                        found_msg = True
                        break
            if found_msg:
                break
        
        if not found_msg:
            logger.warning(f"Could not find message containing tool call {request.tool_call_id} to persist denial")
        
        return {
            "success": False, 
            "result": {"error": "User denied permission"}
        }
        
    if request.tool_name == "fetch_url":
        url = request.tool_args.get("url")
        if not url:
             return {
                 "success": False, 
                 "result": {"error": "No URL provided"}
             }
             
        # Execute
        try:
            content = fetch_and_extract(url)
            
            # Update DB persistence
            messages = message_repo.get_recent_by_chat_id(request.conversation_id, limit=20)
            found_msg = False
            for msg in reversed(messages):
                if msg.tool_calls:
                    updated = False
                    for tc in msg.tool_calls:
                        if tc.id == request.tool_call_id:
                            logger.info(f"Persisting success for tool call {tc.id} in message {msg.id}")
                            tc.status = "completed"
                            tc.result = content
                            updated = True
                            break
                    if updated:
                        message_repo.update(msg)
                        found_msg = True
                        break
            
            if not found_msg:
                 logger.warning(f"Could not find message containing tool call {request.tool_call_id} to persist success")

            return {
                "success": True,
                "result": content,
                # We return the data needed to Resume
                "resume_data": {
                    "id": request.tool_call_id,
                    "name": "fetch_url",
                    "arguments": request.tool_args,
                    "result": content 
                }
            }
        except Exception as e:
            # Update status to error in DB
            messages = message_repo.get_recent_by_chat_id(request.conversation_id, limit=20)
            for msg in reversed(messages):
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        if tc.id == request.tool_call_id:
                            tc.status = "error"
                            tc.error = str(e)
                            message_repo.update(msg)
                            break
            
            return {
                "success": False, 
                "result": {"error": str(e)}
            }

            
    return {
        "success": False, 
        "result": {"error": f"Unknown tool: {request.tool_name}"}
    }


