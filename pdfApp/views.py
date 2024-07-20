import os
import openai
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .forms import PDFUploadForm
from dotenv import load_dotenv
from pdf2image import convert_from_path
import pdfplumber

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

def convert_pdf_to_images(file_path):
    images = []
    try:
        pages = convert_from_path(file_path, dpi=200)
        for i, page in enumerate(pages):
            image_path = os.path.join(settings.MEDIA_ROOT, f'pdf_page_{i}.png')
            page.save(image_path, 'PNG')
            images.append(settings.MEDIA_URL + f'pdf_page_{i}.png')
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
    return images

def upload_pdf(request):
    if request.method == 'GET':
        # Clear the session data for pdf_text and pdf_images on a GET request
        request.session.pop('pdf_text', None)
        request.session.pop('pdf_images', None)
        pdf_text = ''
        pdf_images = []
        question = None
        response_text = None
    elif request.method == 'POST':
        pdf_text = request.session.get('pdf_text', '')
        pdf_images = request.session.get('pdf_images', [])
        question = None
        response_text = None

        if 'pdf_file' in request.FILES:
            form = PDFUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['pdf_file']
                fs = FileSystemStorage()
                filename = fs.save(file.name, file)
                file_path = fs.path(filename)
                pdf_text = extract_text_from_pdf(file_path)
                pdf_images = convert_pdf_to_images(file_path)
                request.session['pdf_text'] = pdf_text  # Store PDF text in session
                request.session['pdf_images'] = pdf_images  # Store PDF images in session
        else:
            question = request.POST.get('question')
            pdf_text = request.session.get('pdf_text', '')
            pdf_images = request.session.get('pdf_images', [])
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
                    response_text = response['choices'][0]['message']['content'].strip()
                except Exception as e:
                    response_text = f"Error: {str(e)}"

    form = PDFUploadForm()
    return render(request, 'pdf.html', {
        'form': form,
        'pdf_text': pdf_text,
        'pdf_images': pdf_images,
        'question': question,
        'response': response_text,
    })
