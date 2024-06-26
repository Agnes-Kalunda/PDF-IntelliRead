import os
import openai
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from .forms import PDFUploadForm
from django.conf import settings
import fitz  # PyMuPDF
import pdfplumber
from dotenv import load_dotenv



load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def index(request):
    return render(request, 'index.html')


def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF file: {e}")
    return text

def upload_pdf(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['pdf_file']
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)
            pdf_text = extract_text_from_pdf(file_path)
            request.session['pdf_text'] = pdf_text  # Store PDF text in session
            return redirect('ask_question')
    else:
        form = PDFUploadForm()
    return render(request, 'upload.html', {'form': form})



@csrf_exempt
def ask_question(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        pdf_text = request.session.get('pdf_text', '')
        if question and pdf_text:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an assistant."},
                        {"role": "user", "content": f"Based on the following information from the PDF: {pdf_text}. {question}"}
                    ],
                    max_tokens=150,
                    temperature=0.5
                )
                answer = response['choices'][0]['message']['content'].strip()
                return JsonResponse({'answer': answer})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
    elif request.method == 'GET':
        return render(request, 'ask.html')
    return HttpResponseBadRequest('Invalid request method')
