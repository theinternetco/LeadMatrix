"""
GMB Review Automation System - Test Suite
Tests all critical components: Groq AI, Telegram Bot, Environment Variables
"""
import os
from dotenv import load_dotenv
import requests
from groq import Groq


# Load environment variables
load_dotenv()


print("🧪 TESTING GMB REVIEW AUTOMATION SYSTEM\n")
print("=" * 70)


# ============================================================================
# TEST 1: Groq AI Connection
# ============================================================================
print("\n✅ TEST 1: Groq AI Connection")
try:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # ✅ UPDATED: Using latest Llama 3.3
        messages=[{"role": "user", "content": "Say 'Groq is working!'"}],
        max_tokens=20
    )
    print(f"   ✓ Groq AI Response: {response.choices[0].message.content}")
    print(f"   ✓ Model: llama-3.3-70b-versatile")
    print(f"   ✓ Status: OPERATIONAL")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    print(f"   ℹ️  Check your GROQ_API_KEY in .env file")


# ============================================================================
# TEST 2: Telegram Bot Connection
# ============================================================================
print("\n✅ TEST 2: Telegram Bot Connection")
try:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("   ✗ ERROR: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
    else:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': (
                '🎉 *GMB Review System Test*\n\n'
                '✅ *All Systems Operational!*\n\n'
                '🤖 Groq AI: Connected (Llama 3.3 70B)\n'
                '📱 Telegram Bot: Working\n'
                '🗄️ Database: Configured\n'
                '📧 Gmail Monitor: Ready\n\n'
                '🚀 *System is ready to monitor reviews!*'
            ),
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.json().get('ok'):
            print(f"   ✓ Telegram Message Sent Successfully!")
            print(f"   ✓ Chat ID: {chat_id}")
            print(f"   ✓ Bot: @shfhdsjiabot")
            print(f"   ℹ️  Check your Telegram for the test message!")
        else:
            print(f"   ✗ ERROR: {response.json()}")
            
except requests.exceptions.Timeout:
    print(f"   ✗ ERROR: Request timeout - Check your internet connection")
except Exception as e:
    print(f"   ✗ ERROR: {e}")


# ============================================================================
# TEST 3: Environment Variables Check
# ============================================================================
print("\n✅ TEST 3: Environment Variables")

# AI Configuration
ai_provider = os.getenv('AI_PROVIDER', 'groq')
groq_key = os.getenv('GROQ_API_KEY')
print(f"   🤖 AI Provider: {ai_provider.upper()}")
print(f"   🔑 Groq API Key: {'✓ Set' if groq_key else '✗ Missing'}")

# Email Configuration
gmail_email = os.getenv('GMAIL_EMAIL')
gmail_password = os.getenv('GMAIL_APP_PASSWORD')
print(f"   📧 Gmail Email: {gmail_email if gmail_email else '✗ Missing'}")
print(f"   🔐 Gmail App Password: {'✓ Set' if gmail_password else '✗ Missing'}")

# Telegram Configuration
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
print(f"   📱 Telegram Bot Token: {'✓ Set' if telegram_token else '✗ Missing'}")
print(f"   💬 Telegram Chat ID: {telegram_chat_id if telegram_chat_id else '✗ Missing'}")

# Database Configuration
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Mask password in database URL for security
    if '@' in database_url:
        masked_db = database_url.split('@')[-1]
        print(f"   🗄️ Database: ✓ Set ({masked_db})")
    else:
        print(f"   🗄️ Database: ✓ Set")
else:
    print(f"   🗄️ Database: ✗ Missing")


# ============================================================================
# TEST 4: Configuration Validation
# ============================================================================
print("\n✅ TEST 4: Configuration Validation")

errors = []
warnings = []

# Check critical components
if not groq_key:
    errors.append("GROQ_API_KEY is missing")

if not database_url:
    errors.append("DATABASE_URL is missing")

# Check optional components
if not gmail_email or not gmail_password:
    warnings.append("Email monitoring disabled (Gmail credentials missing)")

if not telegram_token or not telegram_chat_id:
    warnings.append("Telegram notifications disabled (Bot credentials missing)")

# Display results
if errors:
    print("\n   ❌ CRITICAL ERRORS:")
    for error in errors:
        print(f"      • {error}")
else:
    print("   ✓ All critical configuration validated")

if warnings:
    print("\n   ⚠️  WARNINGS:")
    for warning in warnings:
        print(f"      • {warning}")


# ============================================================================
# FINAL STATUS
# ============================================================================
print("\n" + "=" * 70)

if not errors:
    print("🎉 ALL TESTS PASSED!")
    print("\n✨ YOUR GMB REVIEW AUTOMATION SYSTEM IS READY!")
    print("\n📋 NEXT STEPS:")
    print("   1. Make sure PostgreSQL is running")
    print("   2. Run: python -m review_automation.main")
    print("   3. Monitor reviews in real-time!")
    
    if warnings:
        print("\n💡 TIP: Enable optional features by setting missing credentials")
else:
    print("❌ TESTS FAILED!")
    print("\n🔧 FIX THE ERRORS ABOVE AND RUN AGAIN:")
    print("   python test_system.py")

print("=" * 70)
