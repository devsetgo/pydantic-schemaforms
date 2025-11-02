#!/usr/bin/env python3
"""
Test script for the FastAPI user registration form
"""
import requests
import threading
import time
import uvicorn
from fastapi_example import app

def start_server():
    uvicorn.run(app, host='127.0.0.1', port=8002, log_level='error')

def main():
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(3)  # Wait for server to start

    print('🧪 Testing form submission...')

    # Test GET request first
    try:
        response = requests.get('http://127.0.0.1:8002/user', timeout=5)
        print('✅ GET /user - Status:', response.status_code)
    except Exception as e:
        print('❌ GET /user failed:', e)
        return

    # Test POST request with form data
    try:
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'user'
        }
        
        response = requests.post('http://127.0.0.1:8002/user', data=form_data, timeout=5)
        print('📤 POST /user - Status:', response.status_code)
        
        if response.status_code == 200:
            print('✅ Form submission successful!')
            if 'Registration Success' in response.text:
                print('✅ Success page rendered correctly!')
            else:
                print('ℹ️  Form rendered (likely with validation errors)')
        else:
            print('❌ Form submission failed with status', response.status_code)
            print('Response:', response.text[:500] + '...')
            
    except Exception as e:
        print('❌ POST /user failed:', e)

    print('🎉 Test completed!')

if __name__ == '__main__':
    main()