from astrapy.db import AstraDB
from django.contrib import messages, auth
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.db import models
from FYP import settings
from .models import pdfdocument
import os
import asyncio
import aiohttp
from datetime import datetime
import numpy as np
from pypdf import PdfReader
from django.shortcuts import get_object_or_404
from django.conf import settings
# Create your views here.


#def register(request):

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot:chathistory_panel')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def is_superuser(user):
    return user.is_superuser


def logout_view(request):
    logout(request)
    return redirect('user:login')

@login_required(login_url='user:login')
@user_passes_test(is_superuser)
def register_staff(request):
    if request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('user:register_staff')
        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists, choose another one')
                return redirect('user:register_staff')
            else:
                User.objects.create_user(username=username, password=password1, is_staff=True)
                messages.success(request, 'Staff created successfully')
    return render(request, 'Admin/createstaff.html')

@login_required(login_url='user:login')
@user_passes_test(is_superuser)
def user_list(request):
    # Modified to only show staff users
    users = User.objects.filter(is_staff=True).exclude(is_superuser=True)
    return render(request, 'Admin/deletestaff.html', {'users': users})

@login_required(login_url='user:login')
@user_passes_test(is_superuser)
def delete_user(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id, is_staff=True)  # Only allow staff user deletion
            if user == request.user:
                messages.error(request, "You cannot delete your own account!")
                return redirect('user_list')
            user.delete()
            messages.success(request, f"Staff ID {user.username} was successfully deleted.")
        except User.DoesNotExist:
            messages.error(request, "Staff user not found.")
    return redirect('user:user_list')

@login_required(login_url='user:login')
def upload(request):
    return render(request, 'upload_file.html')

@login_required(login_url='user:login')
def upload_pdf(request):
    if request.method == "POST":
        # Handle file upload here
        return HttpResponse("File uploaded successfully")
    return render(request, "upload_file.html")



db = AstraDB(
    token="AstraCS:HzmvzXKaBnqCexRUyYHqSSit:d77b26aba8c032f483711f5ce445acbdcdccd52c4c5325f18d5adeafb9f450c8",
    api_endpoint="https://bb20db55-ad46-4cc0-bde5-349ac80533a3-us-east1.apps.astra.datastax.com"
)
collection = db.collection("pdf")

# Asynchronous embedding generator
# Updated asynchronous embedding generator with text splitting
async def generate_embeddings(text: str, chunk_size=1000):
    try:
        # Split the text into chunks
        text_chunks = split_text(text, chunk_size)

        # Prepare the payloads for each chunk
        url = "http://localhost:11434/api/embeddings"
        tasks = []
        async with aiohttp.ClientSession() as session:
            for chunk in text_chunks:
                payload = {"model": "nomic-embed-text", "prompt": chunk}
                tasks.append(session.post(url, json=payload))

            # Execute all tasks concurrently
            responses = await asyncio.gather(*tasks)

            # Extract embeddings from responses
            embeddings = []
            for response in responses:
                result = await response.json()
                embedding = result.get('embedding')
                if embedding:
                    embeddings.append(embedding)

            # Aggregate embeddings (e.g., by averaging them)
            if embeddings:
                aggregated_embedding = np.mean(embeddings, axis=0).tolist()
                return aggregated_embedding

        return None  # Return None if no embeddings were successfully generated

    except Exception as e:
        print(f"Embedding generation error: {str(e)}")
        return None



# Ensure vector dimensions match the target dimension
def ensure_vector_dimensions(vector, target_dimension=4096):
    if vector is None:
        return None
    vector = [float(x) for x in vector]
    if len(vector) > target_dimension:
        return vector[:target_dimension]
    elif len(vector) < target_dimension:
        return vector + [0.0] * (target_dimension - len(vector))
    return vector


# Validate if a vector is valid
def is_valid_vector(vector):
    if vector is None or len(vector) == 0:
        return False
    magnitude = np.linalg.norm(vector)
    return magnitude > 1e-6


def extract_text(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# 2. Split text into chunks
def split_text(text, chunk_size=1000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


# Upload PDF view
@login_required(login_url='user:login')
def upload_pdf(request):
    if request.method == "POST" and request.FILES.get('file'):
        file = request.FILES['file']
        file_name = file.name
        file_dir = settings.MEDIA_ROOT  # Save in MEDIA_ROOT
        file_path = os.path.join(file_dir, file_name)  # Full path to save the file

        # Ensure directory exists
        os.makedirs(file_dir, exist_ok=True)

        # Save the file locally
        with open(file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)

        # Generate the public URL
        public_file_path = os.path.join(settings.MEDIA_URL, file_name)  # Public path for serving the file

        # Extract text from the PDF
        try:
            text = extract_text(file_path)
            if not text.strip():
                messages.error(request, "The content of the uploaded file is empty or unreadable.")
                return render(request, "upload_file.html")
        except Exception as e:
            messages.error(request, f"Error reading file content: {str(e)}")
            return render(request, "upload_file.html")

        # Truncate content to fit within size limits
        MAX_CONTENT_SIZE = 1000000  # 1 MB limit
        truncated_content = text[:MAX_CONTENT_SIZE]

        # Generate embeddings
        try:
            embeddings = asyncio.run(generate_embeddings(truncated_content))
            if embeddings is None:
                messages.error(request, "Failed to generate embeddings.")
                return render(request, "upload_file.html")
            vector = ensure_vector_dimensions(embeddings)
            if not is_valid_vector(vector):
                messages.error(request, "Generated vector is invalid. Please check the input content.")
                return render(request, "upload_file.html")
        except Exception as e:
            messages.error(request, f"Embedding generation error: {str(e)}")
            return render(request, "upload_file.html")

        # Prepare the document for Astra DB
        document = {
            "filename": file_name,
            "content": truncated_content,
            "$vector": vector,
            "metadata": {
                "file_path": file_path,
                "upload_date": datetime.now().isoformat()
            }
        }

        # Insert document into Astra DB
        try:
            result = collection.insert_one(document)  # Insert the document
            if result:
                # Extract the document ID from the nested structure
                inserted_ids = result.get('status', {}).get('insertedIds', [])
                if inserted_ids:
                    doc_id = inserted_ids[0]  # Get the first inserted ID

                    # Insert into local database
                    try:
                        pdfdocument.objects.create(
                            file_name=file_name,
                            file_path=public_file_path,  # Save public file path
                            upload_date=datetime.now(),
                            astra_id=doc_id
                        )
                        messages.success(request, "File uploaded successfully!")
                        return render(request, "upload_file.html")
                    except Exception as e:
                        messages.error(request, f"Local database insertion error: {str(e)}")
                        return render(request, "upload_file.html")
                else:
                    raise Exception(f"No inserted IDs found in result: {result}")
            else:
                raise Exception("Insert operation failed.")
        except Exception as e:
            messages.error(request, f"Astra DB insertion error: {str(e)}")
            return render(request, "upload_file.html")

    return render(request, "upload_file.html")



#-------------------------------------------------------------------#
@login_required(login_url='user:login')
def view_pdfs(request):
    pdfs = pdfdocument.objects.all()
    print("Fetched PDFs:", pdfs)  # Debug: print the queryset
    return render(request, "delete_file.html", {"pdfs": pdfs})

@login_required(login_url='user:login')
def delete_pdf(request, id):
    pdf = get_object_or_404(pdfdocument, id=id)
    if request.method == "POST":
        try:
            # Delete from AstraDB
            result = collection.delete_one(pdf.astra_id)
            if not result:
                return HttpResponse(f"Failed to delete from AstraDB. ID: {pdf.astra_id}")

            # Delete the file from the local file system
            if os.path.exists(pdf.file_path):
                os.remove(pdf.file_path)

            # Delete the record from the local database
            pdf.delete()

            return redirect('user:view_pdfs')
        except Exception as e:
            return HttpResponse(f"Error deleting file: {str(e)}")
    return HttpResponse("Invalid request method.")

