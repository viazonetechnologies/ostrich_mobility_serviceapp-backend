"""Dummy SMS service for demo mode"""

class SMSService:
    def __init__(self):
        self.client = None
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS - demo mode always returns True"""
        print(f"Demo SMS to {to_number}: {message}")
        return True

sms_service = SMSService()