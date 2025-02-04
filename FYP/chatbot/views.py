import secrets
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json, requests
from FYP import settings
from datetime import datetime
from .models import chathistory
from .services import AstraService
from .models import chathistory
import requests
from typing import Optional

# Create your views here.

def run_flow(message, flow_id=settings.LANGFLOW_SETTINGS['FLOW_ID'], tweaks=None):
    """Send a request to Langflow API and return the response."""
    payload = {
        "input_value": message,
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": tweaks or {}
    }

    try:
        url = f"{settings.LANGFLOW_SETTINGS['BASE_API_URL']}/{flow_id}"
        print(f"Sending payload to Langflow: {payload}")
        response = requests.post(
            url,
            json=payload
        )
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Langflow API error: {str(e)}")
        raise Exception("Langflow API is unreachable or misconfigured.")


def index(request):
    """Serve the main page."""
    if 'session_id' not in request.session:
        request.session['session_id'] = secrets.token_hex(16)
    return render(request, 'index.html')


@csrf_exempt
@require_http_methods(["POST"])
def handle_flow(request):
    """Process user input and return Langflow response."""
    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        session_id = request.session.get('session_id', None)

        if not user_message:
            return JsonResponse({"error": "Message is required"}, status=400)

        if not session_id:
            return JsonResponse({"error": "Session ID is missing"}, status=400)

        print(f"User message: {user_message}, Session ID: {session_id}")

        # Run Langflow flow
        result = run_flow(user_message)
        # Extract bot response
        outputs = result.get("outputs", [])
        bot_response = outputs[0]["outputs"][0]["results"]["result"] if outputs else "No response."
        # Save to database
        chathistory.objects.create(
            session_id=session_id,
            user_message=user_message,
            bot_response=bot_response
        )

        return JsonResponse({"bot_response": bot_response})

    except Exception as e:
        print(f"Error in handle_flow: {e}")
        return JsonResponse({"error": str(e)}, status=500)

#------------------------------------------------------------------------------------------------#
@require_http_methods(["GET"])
def get_chats(request):
    """Retrieve chat history for the current session."""
    session_id = request.session.get('session_id')
    chats = chathistory.objects.filter(session_id=session_id).values(
        'user_message', 'bot_response', 'timestamp'
    )
    return JsonResponse({
        "session_id": session_id,
        "chats": list(chats)
    })


@csrf_exempt
@require_http_methods(["POST"])
def clear_session(request):
    """Clear the chat history for the current session."""
    session_id = request.session.get('session_id')
    chathistory.objects.filter(session_id=session_id).delete()
    if 'session_id' in request.session:
        del request.session['session_id']
    return JsonResponse({"message": "Session cleared successfully."})


def chathistory_panel(request):
    """Serve the admin panel with grouped chat history."""
    chats = chathistory.objects.all()
    grouped_chats = {}

    for chat in chats:
        if chat.session_id not in grouped_chats:
            grouped_chats[chat.session_id] = []
        grouped_chats[chat.session_id].append({
            'user_message': chat.user_message,
            'bot_response': chat.bot_response,
            'timestamp': chat.timestamp.isoformat()
        })

    return render(request, 'chathistory.html', {'grouped_chats': grouped_chats})




@csrf_exempt
@require_http_methods(["POST"])
def delete_session_chats(request, session_id):
    """Delete all chat records for a given session ID."""
    try:
        chathistory.objects.filter(session_id=session_id).delete()
        return JsonResponse({
            "success": True,
            "message": "All chats for the session have been deleted successfully!"
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Failed to delete chats: {str(e)}"
        }, status=500)
