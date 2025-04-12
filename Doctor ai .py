import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import ResNet50, InceptionV3
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, Label, Button, Text, END, DISABLED, NORMAL, Frame, Scrollbar, RIGHT, Y, Toplevel
from tkinter import ttk
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import pytesseract
import re
import json
import urllib.request
from io import BytesIO
import threading

# Set pytesseract path if needed (modify this for your system if tesseract is not in PATH)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux/Mac

class MedicalAnalysisTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Medical Prescription & Tablet Analyzer")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f5f5f5")
        
        # Create medication database
        self.med_database = self.initialize_medication_database()
        
        # Initialize models
        self.initialize_models()
        
        # Create UI elements
        self.create_widgets()
        
    def initialize_models(self):
        """Initialize the necessary models for analysis"""
        self.status_label.config(text="Status: Loading models...")
        self.root.update()
        
        # Start loading models in a separate thread to prevent UI freezing
        threading.Thread(target=self.load_models, daemon=True).start()
    
    def load_models(self):
        """Load the pill classification model"""
        try:
            # Load ResNet50 model for pill identification
            self.pill_model = ResNet50(weights='imagenet')
            
            # Update status once models are loaded
            self.status_label.config(text="Status: Models loaded successfully! Ready to use.")
            self.upload_prescription_btn.config(state=NORMAL)
            self.upload_pill_btn.config(state=NORMAL)
            
            self.log_message("System initialized successfully.")
            self.log_message("Ready to analyze prescriptions and identify medications.")
        except Exception as e:
            self.status_label.config(text=f"Status: Error loading models - {str(e)}")
            self.log_message(f"Error loading models: {str(e)}")
    
    def initialize_medication_database(self):
        """Initialize a database of medications and their information"""
        # This would typically be loaded from a proper database or API
        # For demo purposes, we'll create a simple dictionary
        
        return {
            "aspirin": {
                "name": "Aspirin",
                "purpose": "Pain reliever and anti-inflammatory",
                "dosage": "Adults: 1-2 tablets every 4-6 hours",
                "side_effects": "Stomach irritation, heartburn, nausea",
                "warnings": "May cause bleeding. Avoid if allergic to NSAIDs.",
                "interactions": "Blood thinners, other NSAIDs"
            },
            "lisinopril": {
                "name": "Lisinopril",
                "purpose": "ACE inhibitor for high blood pressure and heart failure",
                "dosage": "Initially 10mg once daily, maintenance 20-40mg once daily",
                "side_effects": "Dry cough, dizziness, headache",
                "warnings": "May cause angioedema. Monitor kidney function.",
                "interactions": "Potassium supplements, diuretics"
            },
            "metformin": {
                "name": "Metformin",
                "purpose": "Treatment for type 2 diabetes",
                "dosage": "Start with 500mg twice daily, max 2550mg/day",
                "side_effects": "Nausea, diarrhea, stomach discomfort",
                "warnings": "May cause lactic acidosis in kidney dysfunction",
                "interactions": "Alcohol, contrast dyes"
            },
            "atorvastatin": {
                "name": "Atorvastatin",
                "purpose": "Statin medication to lower cholesterol",
                "dosage": "10-80mg once daily",
                "side_effects": "Muscle pain, liver enzyme elevations",
                "warnings": "Report unexplained muscle pain immediately",
                "interactions": "Grapefruit juice, certain antibiotics"
            },
            "amoxicillin": {
                "name": "Amoxicillin",
                "purpose": "Antibiotic for bacterial infections",
                "dosage": "250-500mg three times daily for 7-14 days",
                "side_effects": "Diarrhea, nausea, rash",
                "warnings": "May cause allergic reactions",
                "interactions": "Certain blood thinners, birth control pills"
            },
            "levothyroxine": {
                "name": "Levothyroxine",
                "purpose": "Thyroid hormone replacement",
                "dosage": "25-200mcg once daily on empty stomach",
                "side_effects": "Headache, insomnia, nervousness at high doses",
                "warnings": "Not for weight loss in normal thyroid function",
                "interactions": "Calcium/iron supplements, antacids"
            },
            "omeprazole": {
                "name": "Omeprazole",
                "purpose": "Proton pump inhibitor for acid reflux and ulcers",
                "dosage": "20mg once daily for 4-8 weeks",
                "side_effects": "Headache, abdominal pain, diarrhea",
                "warnings": "Long-term use may increase fracture risk",
                "interactions": "Clopidogrel, certain HIV medications"
            },
            "sertraline": {
                "name": "Sertraline",
                "purpose": "SSRI antidepressant",
                "dosage": "Start with 50mg once daily, maximum 200mg daily",
                "side_effects": "Nausea, diarrhea, insomnia, sexual dysfunction",
                "warnings": "May increase suicidal thoughts in young adults",
                "interactions": "MAO inhibitors, NSAIDs, blood thinners"
            },
            "paracetamol": {
                "name": "Paracetamol (Acetaminophen)",
                "purpose": "Pain reliever and fever reducer",
                "dosage": "Adults: 500-1000mg every 4-6 hours, max 4g/day",
                "side_effects": "Generally minimal at recommended doses",
                "warnings": "Overdose can cause severe liver damage",
                "interactions": "Alcohol, certain liver medications"
            },
            "ibuprofen": {
                "name": "Ibuprofen",
                "purpose": "NSAID pain reliever and anti-inflammatory",
                "dosage": "Adults: 200-400mg every 4-6 hours, max 3200mg/day",
                "side_effects": "Stomach pain, heartburn, dizziness",
                "warnings": "Long-term use increases risk of heart attack and stroke",
                "interactions": "Aspirin, blood pressure medications, diuretics"
            }
        }
        
    def create_widgets(self):
        """Create the UI elements"""
        # Title and description
        title_frame = Frame(self.root, bg="#f5f5f5")
        title_frame.pack(pady=(20, 10))
        
        title_label = Label(title_frame, text="Medical Prescription & Tablet Analyzer", 
                           font=("Helvetica", 22, "bold"), bg="#f5f5f5", fg="#2c3e50")
        title_label.pack()
        
        description = "Upload a doctor's prescription or medication image for analysis"
        desc_label = Label(title_frame, text=description, font=("Helvetica", 12), 
                          bg="#f5f5f5", fg="#34495e")
        desc_label.pack(pady=(5, 0))
        
        # Main content frame with tabs
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(pady=10, fill='both', expand=True)
        
        # Create tabs
        self.prescription_tab = Frame(self.tab_control, bg="#f5f5f5")
        self.pill_tab = Frame(self.tab_control, bg="#f5f5f5")
        
        self.tab_control.add(self.prescription_tab, text="Prescription Analysis")
        self.tab_control.add(self.pill_tab, text="Medication Identification")
        
        # Setup prescription tab
        self.setup_prescription_tab()
        
        # Setup pill identification tab
        self.setup_pill_tab()
        
        # Status bar at bottom
        status_frame = Frame(self.root, bg="#e0e0e0")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = Label(status_frame, text="Status: Initializing...", 
                                 font=("Helvetica", 10), bg="#e0e0e0", anchor="w", padx=10, pady=5)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
    def setup_prescription_tab(self):
        """Setup the prescription analysis tab"""
        # Left panel for image and controls
        left_panel = Frame(self.prescription_tab, bg="#f5f5f5", width=500)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Upload button
        self.upload_prescription_btn = Button(
            left_panel,
            text="Upload Prescription",
            command=self.upload_prescription,
            font=("Helvetica", 12),
            bg="#3498db",
            fg="white",
            padx=10,
            pady=5,
            state=DISABLED  # Disabled until models are loaded
        )
        self.upload_prescription_btn.pack(pady=(0, 10))
        
        # Image display
        self.prescription_image_frame = Frame(left_panel, bg="white", width=450, height=300,
                                            highlightbackground="#bdc3c7", highlightthickness=1)
        self.prescription_image_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.prescription_image_frame.pack_propagate(0)  # Prevent frame from shrinking
        
        self.prescription_image_label = Label(self.prescription_image_frame, bg="white")
        self.prescription_image_label.pack(fill=tk.BOTH, expand=True)
        
        # Process button
        self.process_prescription_btn = Button(
            left_panel,
            text="Analyze Prescription",
            command=self.analyze_prescription,
            font=("Helvetica", 12),
            bg="#2ecc71",
            fg="white",
            padx=10,
            pady=5,
            state=DISABLED
        )
        self.process_prescription_btn.pack(pady=10)
        
        # Right panel for results
        right_panel = Frame(self.prescription_tab, bg="#f5f5f5", width=500)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results label
        results_label = Label(right_panel, text="Prescription Analysis Results", 
                             font=("Helvetica", 14, "bold"), bg="#f5f5f5")
        results_label.pack(pady=(0, 10))
        
        # Text widget with scrollbar for results
        results_frame = Frame(right_panel, bg="#f5f5f5")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.prescription_result_text = Text(results_frame, height=20, width=50, 
                                           font=("Helvetica", 11), wrap=tk.WORD)
        scrollbar = Scrollbar(results_frame, command=self.prescription_result_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.prescription_result_text.configure(yscrollcommand=scrollbar.set)
        self.prescription_result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    
    def setup_pill_tab(self):
        """Setup the pill identification tab"""
        # Left panel for image and controls
        left_panel = Frame(self.pill_tab, bg="#f5f5f5", width=500)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Upload button
        self.upload_pill_btn = Button(
            left_panel,
            text="Upload Medication Image",
            command=self.upload_pill_image,
            font=("Helvetica", 12),
            bg="#3498db",
            fg="white",
            padx=10,
            pady=5,
            state=DISABLED  # Disabled until models are loaded
        )
        self.upload_pill_btn.pack(pady=(0, 10))
        
        # Image display
        self.pill_image_frame = Frame(left_panel, bg="white", width=450, height=300,
                                    highlightbackground="#bdc3c7", highlightthickness=1)
        self.pill_image_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.pill_image_frame.pack_propagate(0)  # Prevent frame from shrinking
        
        self.pill_image_label = Label(self.pill_image_frame, bg="white")
        self.pill_image_label.pack(fill=tk.BOTH, expand=True)
        
        # Process button
        self.identify_pill_btn = Button(
            left_panel,
            text="Identify Medication",
            command=self.identify_pill,
            font=("Helvetica", 12),
            bg="#2ecc71",
            fg="white",
            padx=10,
            pady=5,
            state=DISABLED
        )
        self.identify_pill_btn.pack(pady=10)
        
        # Right panel for results
        right_panel = Frame(self.pill_tab, bg="#f5f5f5", width=500)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results label
        results_label = Label(right_panel, text="Medication Information", 
                             font=("Helvetica", 14, "bold"), bg="#f5f5f5")
        results_label.pack(pady=(0, 10))
        
        # Text widget with scrollbar for results
        results_frame = Frame(right_panel, bg="#f5f5f5")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.pill_result_text = Text(results_frame, height=20, width=50, 
                                   font=("Helvetica", 11), wrap=tk.WORD)
        scrollbar = Scrollbar(results_frame, command=self.pill_result_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.pill_result_text.configure(yscrollcommand=scrollbar.set)
        self.pill_result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
    def upload_prescription(self):
        """Upload a prescription image"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if file_path:
            self.prescription_file_path = file_path
            self.status_label.config(text=f"Status: Prescription image loaded: {os.path.basename(file_path)}")
            
            # Display the image
            img = Image.open(file_path)
            img = self.resize_image(img, (450, 300))
            photo = ImageTk.PhotoImage(img)
            
            self.prescription_image_label.config(image=photo)
            self.prescription_image_label.image = photo
            
            # Enable the process button
            self.process_prescription_btn.config(state=NORMAL)
            
            self.log_message("Prescription image loaded. Click 'Analyze Prescription' to process.")
    
    def upload_pill_image(self):
        """Upload a pill/tablet image"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if file_path:
            self.pill_file_path = file_path
            self.status_label.config(text=f"Status: Medication image loaded: {os.path.basename(file_path)}")
            
            # Display the image
            img = Image.open(file_path)
            img = self.resize_image(img, (450, 300))
            photo = ImageTk.PhotoImage(img)
            
            self.pill_image_label.config(image=photo)
            self.pill_image_label.image = photo
            
            # Enable the identify button
            self.identify_pill_btn.config(state=NORMAL)
            
            self.log_message("Medication image loaded. Click 'Identify Medication' to process.")
    
    def resize_image(self, img, target_size):
        """Resize image while maintaining aspect ratio"""
        width, height = img.size
        ratio = min(target_size[0] / width, target_size[1] / height)
        new_size = (int(width * ratio), int(height * ratio))
        return img.resize(new_size, Image.LANCZOS)
    
    def preprocess_prescription_image(self, img_path):
        """Preprocess the prescription image for better OCR results"""
        # Open the image
        img = Image.open(img_path)
        
        # Convert to grayscale
        img = img.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # Apply some sharpening
        img = img.filter(ImageFilter.SHARPEN)
        
        # Denoise
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        # Increase size for better OCR
        width, height = img.size
        img = img.resize((width*2, height*2), Image.LANCZOS)
        
        # Save the preprocessed image temporarily
        temp_path = "temp_prescription.png"
        img.save(temp_path)
        
        return temp_path
    
    def analyze_prescription(self):
        """Analyze the prescription image"""
        if not hasattr(self, 'prescription_file_path'):
            self.status_label.config(text="Status: No prescription image loaded!")
            return
        
        self.status_label.config(text="Status: Analyzing prescription...")
        self.prescription_result_text.delete(1.0, END)
        self.prescription_result_text.insert(END, "Processing prescription image...\n\n")
        self.root.update()
        
        try:
            # Preprocess the image
            preprocessed_img_path = self.preprocess_prescription_image(self.prescription_file_path)
            
            # Perform OCR
            self.prescription_result_text.insert(END, "Extracting text from prescription...\n\n")
            self.root.update()
            
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(preprocessed_img_path)
            
            # Clean up the text
            text = self.clean_prescription_text(text)
            
            # Display the extracted text
            self.prescription_result_text.insert(END, "--- Raw Extracted Text ---\n")
            self.prescription_result_text.insert(END, text + "\n\n")
            
            # Analyze the prescription content
            self.analyze_prescription_content(text)
            
            # Clean up temp file
            if os.path.exists(preprocessed_img_path):
                os.remove(preprocessed_img_path)
            
            self.status_label.config(text="Status: Prescription analysis completed")
            
        except Exception as e:
            self.prescription_result_text.insert(END, f"Error analyzing prescription: {str(e)}\n")
            self.status_label.config(text="Status: Error in prescription analysis")
    
    def clean_prescription_text(self, text):
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove non-printable characters
        text = ''.join(c for c in text if c.isprintable() or c in ['\n', '\t'])
        
        # Split into lines and remove empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def analyze_prescription_content(self, text):
        """Analyze the prescription content for medications, dosages, etc."""
        self.prescription_result_text.insert(END, "--- Structured Analysis ---\n\n")
        
        # Try to identify patient information
        patient_info = self.extract_patient_info(text)
        if patient_info:
            self.prescription_result_text.insert(END, "Patient Information:\n")
            for key, value in patient_info.items():
                self.prescription_result_text.insert(END, f"- {key}: {value}\n")
            self.prescription_result_text.insert(END, "\n")
        
        # Try to identify doctor information
        doctor_info = self.extract_doctor_info(text)
        if doctor_info:
            self.prescription_result_text.insert(END, "Doctor Information:\n")
            for key, value in doctor_info.items():
                self.prescription_result_text.insert(END, f"- {key}: {value}\n")
            self.prescription_result_text.insert(END, "\n")
        
        # Try to identify medications
        medications = self.extract_medications(text)
        if medications:
            self.prescription_result_text.insert(END, "Medications:\n")
            for med in medications:
                self.prescription_result_text.insert(END, f"- Name: {med['name']}\n")
                if 'dosage' in med and med['dosage']:
                    self.prescription_result_text.insert(END, f"  Dosage: {med['dosage']}\n")
                if 'frequency' in med and med['frequency']:
                    self.prescription_result_text.insert(END, f"  Frequency: {med['frequency']}\n")
                if 'duration' in med and med['duration']:
                    self.prescription_result_text.insert(END, f"  Duration: {med['duration']}\n")
                if 'instructions' in med and med['instructions']:
                    self.prescription_result_text.insert(END, f"  Instructions: {med['instructions']}\n")
                
                # Look up medication information
                med_info = self.lookup_medication(med['name'])
                if med_info:
                    self.prescription_result_text.insert(END, f"  Information: {med_info['purpose']}\n")
                    
                self.prescription_result_text.insert(END, "\n")
        else:
            self.prescription_result_text.insert(END, "No medications clearly identified in the prescription.\n\n")
        
        # Add disclaimer
        self.prescription_result_text.insert(END, "DISCLAIMER: This analysis is for informational purposes only. "
                                             "Always consult with a healthcare professional for accurate "
                                             "interpretation of prescriptions.\n")
    
    def extract_patient_info(self, text):
        """Extract patient information from the prescription text"""
        patient_info = {}
        
        # Look for patient name pattern
        name_match = re.search(r'(?:Patient[:\s]+|Name[:\s]+)([A-Za-z\s.]+)', text, re.IGNORECASE)
        if name_match:
            patient_info['name'] = name_match.group(1).strip()
        
        # Look for age pattern
        age_match = re.search(r'(?:Age[:\s]+)(\d+)(?:\s+[Yy]ears?)?', text, re.IGNORECASE)
        if age_match:
            patient_info['age'] = age_match.group(1)
        
        # Look for date pattern
        date_match = re.search(r'(?:Date[:\s]+)([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})', text, re.IGNORECASE)
        if date_match:
            patient_info['date'] = date_match.group(1)
        
        return patient_info
    
    def extract_doctor_info(self, text):
        """Extract doctor information from the prescription text"""
        doctor_info = {}
        
        # Look for doctor name pattern
        dr_match = re.search(r'(?:Dr\.?|Doctor)[:\s]*([A-Za-z\s.]+)', text, re.IGNORECASE)
        if dr_match:
            doctor_info['name'] = dr_match.group(1).strip()
        
        # Look for credentials
        credentials_match = re.search(r'([A-Z.]+(?:\s*,\s*[A-Z.]+)*)', text)
        if credentials_match:
            credentials = credentials_match.group(1)
            if credentials != doctor_info.get('name', ''):
                doctor_info['credentials'] = credentials
        
        return doctor_info
    
    def extract_medications(self, text):
        """Extract medications from the prescription text"""
        medications = []
        
        # Split the text into lines for analysis
        lines = text.split('\n')
        
        # Common medication patterns
        rx_indicators = ['Rx', 'R/', '℞', 'Prescription']
        med_section_started = False
        
        for i, line in enumerate(lines):
            # Check if this line indicates the start of medications
            if any(indicator in line for indicator in rx_indicators) or 'medication' in line.lower():
                med_section_started = True
                continue
            
            if not med_section_started:
                continue
            
            # Skip lines that are likely not medications
            if len(line.strip()) < 3 or re.match(r'^[\d\s.,]+$', line):
                continue
            
            # Look for medication patterns
            # This is a simplified approach - real prescriptions would need more complex parsing
            parts = line.strip().split()
            if not parts:
                continue
            
            medication = {'name': parts[0]}
            
            # Try to extract dosage information
            dosage_pattern = r'(\d+\s*(?:mg|mcg|g|ml|IU|%|tablet|cap))'
            dosage_match = re.search(dosage_pattern, line, re.IGNORECASE)
            if dosage_match:
                medication['dosage'] = dosage_match.group(1)
            
            # Try to extract frequency
            freq_pattern = r'(\d+\s*(?:times|x)\s*(?:a|per)\s*day|daily|twice daily|once daily|every\s*\d+\s*hours?|morning|night)'
            freq_match = re.search(freq_pattern, line, re.IGNORECASE)
            if freq_match:
                medication['frequency'] = freq_match.group(1)
            
            # Try to extract duration
            duration_pattern = r'(?:for|duration|take)\s*(\d+\s*(?:days?|weeks?|months?))'
            duration_match = re.search(duration_pattern, line, re.IGNORECASE)
            if duration_match:
                medication['duration'] = duration_match.group(1)
            
            # Extract additional instructions
            if "after" in line.lower() or "before" in line.lower() or "with" in line.lower():
                medication['instructions'] = line
            
            # Check if this line is a continuation of the previous medication
            if medications and len(parts) < 3 and not dosage_match and not freq_match:
                # This might be additional instructions for the previous medication
                if 'instructions' in medications[-1]:
                    medications[-1]['instructions'] += " " + line
                else:
                    medications[-1]['instructions'] = line
            else:
                # This is a new medication
                medications.append(medication)
        
        return medications
    
    def identify_pill(self):
        """Identify the pill/tablet from the uploaded image"""
        if not hasattr(self, 'pill_file_path'):
            self.status_label.config(text="Status: No medication image loaded!")
            return
        
        self.status_label.config(text="Status: Identifying medication...")
        self.pill_result_text.delete(1.0, END)
        self.pill_result_text.insert(END, "Analyzing medication image...\n\n")
        self.root.update()
        
        try:
            # Load and preprocess the image
            img = image.load_img(self.pill_file_path, target_size=(224, 224))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)
            
            # Use the model to predict
            preds = self.pill_model.predict(x)
            predictions = decode_predictions(preds, top=5)[0]
            
            # Display results
            self.pill_result_text.insert(END, "Possible Medications Found:\n\n")
            
            # Flag to track if we found a medication
            found_medication = False
            
            # Check top predictions for medication-related terms
            med_terms = ['pill', 'capsule', 'tablet', 'medicine', 'drug', 'capsule', 'medicine', 'antibiotic']
            possible_meds = []
            
            for i, (imagenet_id, label, score) in enumerate(predictions):
                self.pill_result_text.insert(END, f"{i+1}. {label.replace('_', ' ').title()}: {score*100:.2f}%\n")
                
                # Check if any medication terms are in the prediction
                if any(term in label.lower() for term in med_terms):
                    found_medication = True
                
                # Check our database for similar names
                for med_name in self.med_database.keys():
                    # Simple string comparison for demo purposes
                    # A real system would use NLP and visual features
                    if med_name in label.lower() or label.lower() in med_name:
                        possible_meds.append(med_name)
            
            self.pill_result_text.insert(END, "\n")
            
            # For demonstration purposes, suggest a random medication from our database
            # In a real system, this would use proper image analysis specific to medications
            if not found_medication or not possible_meds:
                # For demo purposes, select a "simulated" match
                # In a real system, this would return "no match