"""
Virtual Doctor Application with Decorator-based Menu System
Core concept: Decorators handle menu registration, routing, and execution
"""

# Dictionary to store registered services/menu options
menu_options = {}
current_menu = "main"

def virtual_doctor_service(description, menu="main", requires_input=False):
    """
    Main decorator for registering Virtual Doctor services
    - Registers functions as menu options
    - Handles user input collection if needed
    - Controls execution flow between services
    """
    def decorator(func):
        # Create menu if it doesn't exist
        if menu not in menu_options:
            menu_options[menu] = {}
        
        # Register function in the menu
        menu_options[menu][func.__name__] = {
            'function': func,
            'description': description,
            'requires_input': requires_input
        }
        
        def wrapper(*args, **kwargs):
            print(f"\n{'='*50}")
            print(f"Virtual Doctor Service: {description}")
            print(f"{'='*50}")
            
            # If function requires input, prompt user
            if requires_input:
                user_input = input("Please describe your concern: ")
                return func(user_input)
            return func()
        
        return wrapper
    return decorator

def show_menu():
    """Display current menu options using decorator-registered functions"""
    global current_menu
    
    print(f"\n{'='*50}")
    print(f"VIRTUAL DOCTOR - MAIN MENU")
    print(f"{'='*50}")
    
    if current_menu not in menu_options:
        print("No services available. Returning to main menu.")
        current_menu = "main"
        return
    
    # Get services from current menu
    services = menu_options[current_menu]
    
    # Display numbered options
    for idx, (name, service) in enumerate(services.items(), 1):
        print(f"{idx}. {service['description']}")
    
    print(f"{len(services) + 1}. Back to Main Menu" if current_menu != "main" else "")
    print(f"{len(services) + (2 if current_menu != 'main' else 1)}. Exit System")
    
    return services

def execute_service(choice):
    """Execute selected service using decorator-wrapped function"""
    global current_menu
    
    services = menu_options[current_menu]
    service_list = list(services.items())
    
    if 1 <= choice <= len(service_list):
        service_name, service = service_list[choice - 1]
        service['function']()
        return True
    elif choice == len(service_list) + 1 and current_menu != "main":
        current_menu = "main"
        return True
    elif choice == len(service_list) + (2 if current_menu != "main" else 1):
        return False  # Exit signal
    else:
        print("Invalid choice. Please try again.")
        return True

# ========== VIRTUAL DOCTOR SERVICES (Registered via decorators) ==========

@virtual_doctor_service("Symptom Checker", requires_input=True)
def symptom_checker(user_input):
    """Analyze symptoms and provide general guidance"""
    symptoms = user_input.lower()
    
    print("\n--- Symptom Analysis ---")
    
    # Simple keyword-based symptom analysis
    if "headache" in symptoms or "migraine" in symptoms:
        print("For headaches:")
        print("- Rest in a quiet, dark room")
        print("- Stay hydrated")
        print("- Consider over-the-counter pain relief if appropriate")
        print("- If severe or persistent, consult a doctor")
    
    if "fever" in symptoms or "temperature" in symptoms:
        print("\nFor fever:")
        print("- Rest and stay hydrated")
        print("- Monitor temperature regularly")
        print("- Use fever-reducing medication if needed")
        print("- Seek medical help if fever exceeds 103°F (39.4°C)")
    
    if "cough" in symptoms or "cold" in symptoms:
        print("\nFor cough/cold:")
        print("- Drink warm fluids")
        print("- Use honey for cough relief")
        print("- Rest and avoid irritants")
        print("- Consult doctor if symptoms worsen")
    
    if "stomach" in symptoms or "nausea" in symptoms:
        print("\nFor stomach issues:")
        print("- Stick to bland foods (BRAT diet)")
        print("- Stay hydrated with small sips")
        print("- Avoid spicy/fatty foods")
        print("- Seek help for severe pain or vomiting")
    
    print("\n⚠️ Disclaimer: This is general guidance only.")
    print("For medical emergencies, call emergency services immediately.")
    input("\nPress Enter to continue...")

@virtual_doctor_service("Basic Health Guidance", menu="guidance")
def health_guidance():
    """Provide general health advice"""
    print("\n--- General Health Guidelines ---")
    
    guidelines = [
        "1. Stay hydrated: Drink at least 8 glasses of water daily",
        "2. Balanced diet: Include fruits, vegetables, and whole grains",
        "3. Regular exercise: 30 minutes most days of the week",
        "4. Adequate sleep: 7-9 hours per night for adults",
        "5. Stress management: Practice relaxation techniques",
        "6. Regular check-ups: Annual health screenings recommended",
        "7. Hand hygiene: Wash hands frequently to prevent illness",
        "8. Vaccinations: Keep immunizations up to date"
    ]
    
    for guideline in guidelines:
        print(f"• {guideline}")
    
    print("\nRemember: Prevention is better than cure!")
    input("\nPress Enter to continue...")

@virtual_doctor_service("Exercise & Fitness Tips", menu="guidance")
def fitness_tips():
    """Provide exercise recommendations"""
    print("\n--- Exercise Recommendations ---")
    
    tips = [
        "Cardio: 150 minutes moderate or 75 minutes vigorous weekly",
        "Strength training: 2+ days per week for all major muscle groups",
        "Flexibility: Stretch major muscle groups regularly",
        "Balance exercises: Especially important for older adults",
        "Start slow: Gradually increase intensity and duration",
        "Listen to your body: Rest when needed",
        "Stay consistent: Regular activity is key",
        "Consult professional: Before starting new exercise programs"
    ]
    
    for tip in tips:
        print(f"✓ {tip}")
    
    input("\nPress Enter to continue...")

@virtual_doctor_service("Mental Wellness", menu="guidance")
def mental_wellness():
    """Provide mental health guidance"""
    print("\n--- Mental Wellness Tips ---")
    
    tips = [
        "Practice mindfulness or meditation daily",
        "Maintain social connections",
        "Set realistic goals and priorities",
        "Take breaks and practice self-care",
        "Get sunlight exposure regularly",
        "Limit screen time before bed",
        "Seek professional help when needed",
        "Practice gratitude daily"
    ]
    
    for tip in tips:
        print(f"✨ {tip}")
    
    input("\nPress Enter to continue...")

@virtual_doctor_service("Common Medicine Suggestions", requires_input=True)
def medicine_suggestions(user_input):
    """Provide general medicine information (non-diagnostic)"""
    print("\n--- General Medicine Information ---")
    print(f"Based on your concern: {user_input}")
    
    print("\n⚠️ Important: Always consult a doctor or pharmacist before taking any medication.")
    print("Do not self-medicate without professional advice.\n")
    
    common_medicines = {
        "pain": [
            "Acetaminophen (Tylenol) - for mild pain/fever",
            "Ibuprofen (Advil) - for inflammation/pain",
            "Aspirin - for pain/fever (adults only)",
            "Follow dosage instructions carefully"
        ],
        "fever": [
            "Acetaminophen - fever reducer",
            "Ibuprofen - fever and inflammation",
            "Stay hydrated",
            "Monitor temperature regularly"
        ],
        "cold": [
            "Antihistamines - for runny nose/sneezing",
            "Decongestants - for nasal congestion",
            "Cough suppressants - for dry cough",
            "Expectorants - for productive cough"
        ],
        "allergy": [
            "Antihistamines (loratadine, cetirizine)",
            "Nasal corticosteroids",
            "Avoid known allergens",
            "Consult allergist for persistent symptoms"
        ]
    }
    
    found = False
    for key, medicines in common_medicines.items():
        if key in user_input.lower():
            found = True
            print(f"\nFor {key} relief (general information):")
            for medicine in medicines:
                print(f"  • {medicine}")
    
    if not found:
        print("\nGeneral medicine safety tips:")
        print("• Read labels carefully")
        print("• Check expiration dates")
        print("• Be aware of interactions")
        print("• Store medications properly")
        print("• Never share prescription medications")
    
    print("\n📞 Contact a healthcare professional for personalized advice.")
    input("\nPress Enter to continue...")

@virtual_doctor_service("First Aid Guidance", menu="first_aid")
def first_aid_basics():
    """Provide basic first aid information"""
    print("\n--- Basic First Aid Guidelines ---")
    
    first_aid = [
        "Burns: Cool with running water for 20 minutes",
        "Cuts: Clean with water, apply pressure, bandage",
        "Choking: Perform Heimlich maneuver if trained",
        "CPR: Call emergency services first, then begin compressions",
        "Sprains: RICE method (Rest, Ice, Compression, Elevation)",
        "Nosebleed: Sit up, lean forward, pinch nostrils",
        "Poisoning: Call poison control immediately",
        "Heat stroke: Move to cool area, hydrate, seek help"
    ]
    
    for aid in first_aid:
        print(f"🚑 {aid}")
    
    print("\n💡 Take a certified first aid course for proper training.")
    input("\nPress Enter to continue...")

@virtual_doctor_service("Emergency Contacts", menu="first_aid")
def emergency_contacts():
    """Display emergency contact information"""
    print("\n--- Emergency Contacts ---")
    
    contacts = [
        "Emergency Services: 911 or 1122 (US) or 112 (EU)",
        "Poison Control: 1-800-222-1222 (US)",
        "National Suicide Prevention: 988 (US)",
        "Local Hospital: [Your nearest hospital]",
        "Primary Doctor: [Your doctor's contact]",
        "Pharmacy: [Your pharmacy contact]"
    ]
    
    for contact in contacts:
        print(f"📞 {contact}")
    
    print("\nSave these numbers in your phone!")
    input("\nPress Enter to continue...")

@virtual_doctor_service("Health Guidance Menu")
def guidance_menu():
    """Navigate to health guidance submenu"""
    global current_menu
    current_menu = "guidance"
    return True

@virtual_doctor_service("First Aid Information")
def first_aid_menu():
    """Navigate to first aid submenu"""
    global current_menu
    current_menu = "first_aid"
    return True

@virtual_doctor_service("Exit System")
def exit_system():
    """Exit the application"""
    print("\nThank you for using Virtual Doctor!")
    print("Remember: This is not a substitute for professional medical care.")
    print("For emergencies, call 911 or your local emergency number.")
    return False

def main():
    """Main application loop"""
    print("="*60)
    print("VIRTUAL DOCTOR APPLICATION")
    print("="*60)
    print("Note: This provides general health information only.")
    print("Always consult healthcare professionals for medical advice.\n")
    
    running = True
    
    while running:
        services = show_menu()
        
        try:
            choice = int(input(f"\nEnter your choice (1-{len(services) + (2 if current_menu != 'main' else 1)}): "))
            running = execute_service(choice)
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nExiting Virtual Doctor...")
            running = False
    
    print("\nTake care and stay healthy! 👨‍⚕️👩‍⚕️")

if __name__ == "__main__":
    main()