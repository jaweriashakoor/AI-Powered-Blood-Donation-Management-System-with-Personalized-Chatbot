# chatbot.py - improved responses for AI-Powered Blood project (stage 2)
blood_stock = {
    "A+": 25, "A-": 10, "B+": 20, "B-": 5,
    "AB+": 8, "AB-": 2, "O+": 35, "O-": 12,
}

def get_bot_response(user_message):
    msg = user_message.lower().strip()
    # 1. Check stock requests
    for bt in blood_stock.keys():
        if bt.lower() in msg and ("stock" in msg or "available" in msg):
            return f"Our current stock for {bt} is {blood_stock[bt]} units."
    # 2. Eligibility
    if "eligible" in msg or "eligibility" in msg:
        return "General eligibility: age 17-65, healthy, no recent major surgery or infectious disease. Please consult our centre for detailed checks."
    # 3. Donation / location
    if "donate" in msg or "location" in msg or "center" in msg:
        return "You can donate at our main center (123 Life St) Mon-Fri 9:00-17:00. Walk-ins welcome or book an appointment."
    # 4. Appointment / book
    if "appointment" in msg or "book" in msg:
        return "To book an appointment, sign up and go to the Dashboard → Book Appointment."
    # 5. Greetings
    if msg.startswith("hi") or "hello" in msg:
        return "Hello! I can tell you about blood stock, donation locations, eligibility, and donor/recipient actions."
    # 6. Thanks
    if "thank" in msg or "thanks" in msg:
        return "You're welcome! Happy to help."
    # 7. Help / commands
    if "help" in msg or "commands" in msg:
        return ("You can ask:\n- 'What is the stock of O+'\n- 'Am I eligible to donate?'\n- 'Where can I donate?'\n- 'How do I sign up?'\n- 'How do I book an appointment?'\n")
    # 8. Fallback
    return "Sorry, I didn't understand. Ask about stock, eligibility, or where to donate."

def enrich_bot_response(reply, user_row):
    # If user is logged in, add personalized note
    if user_row:
        name = user_row['name']
        role = user_row['role']
        bt = user_row['blood_type'] or ''
        extra = f"\n\nNote: Logged in as {name} ({role})."
        if bt:
            extra += f" Your blood type: {bt}."
        return reply + extra
    return reply
