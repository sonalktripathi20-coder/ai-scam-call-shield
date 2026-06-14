import hashlib
import sys
import os

# Add parent directory to path so database module imports properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, SavedContact, is_known_number, init_db

def test_whitelist():
    print("Initializing test database...")
    init_db()
    
    db = SessionLocal()
    try:
        # Clear existing test entries
        db.query(SavedContact).delete()
        db.commit()
        
        # Test Contact Number
        raw_number = "+91 98765 43210"
        normalized_number = "9876543210" # last 10 digits
        hashed_number = hashlib.sha256(normalized_number.encode('utf-8')).hexdigest()
        
        # Add hash to whitelisted contacts
        db.add(SavedContact(phone_hash=hashed_number))
        db.commit()
        print(f"Added hash: {hashed_number} for number: {raw_number}")
        
        # Verify matching logic
        test_numbers = [
            ("+919876543210", True),
            ("9876543210", True),
            ("09876543210", True),
            ("919876543210", True),
            ("98765-43210", True),
            ("+91 98765 43210", True),
            ("9876543211", False),  # Off by one
            ("1234567890", False),  # Completely unknown
        ]
        
        passed = 0
        for num, expected in test_numbers:
            result = is_known_number(db, num)
            status = "PASSED" if result == expected else "FAILED"
            print(f"Testing: {num:<18} | Expected: {str(expected):<5} | Got: {str(result):<5} | Result: {status}")
            if result == expected:
                passed += 1
                
        print(f"\nTest results: {passed}/{len(test_numbers)} passed.")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_whitelist()
