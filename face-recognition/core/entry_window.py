import time
from typing import Callable, Optional

class EntryWindowManager:    
    def __init__(self, window_duration: float = 120.0):
        self.window_duration = window_duration
        self.window_active = False
        self.window_start_time: Optional[float] = None
        self.expected_count = 0
        self.actual_count = 0
    
    def open_entry_window(self, expected_count: int) -> bool:
        if self.window_active:
            print("⚠️  Entry window already open")
            return False
        self.window_active = True
        self.window_start_time = time.time()
        self.expected_count = expected_count
        self.actual_count = 0
        print(f"🔓 DOOR UNLOCKED - Entry window open for {self.window_duration}s")
        print(f"   Expected persons: {expected_count}")
        return True
    
    def is_window_open(self) -> bool:
        if not self.window_active:
            return False
        
        elapsed = time.time() - self.window_start_time
        
        if elapsed >= self.window_duration:
            self.window_active = False
            return False
        
        return True
    
    def record_person_crossing(self) -> int:
        if self.is_window_open():
            self.actual_count += 1
            elapsed = time.time() - self.window_start_time
            print(f"   [+{elapsed:.1f}s] Person {self.actual_count} crossing...")
            return self.actual_count
        return self.actual_count
    
    def close_entry_window(self) -> dict:
        final_expected = self.expected_count
        final_actual = self.actual_count
        if not self.window_active and final_expected == 0:
            return {
                'expected': 0,
                'actual': 0,
                'is_valid': False,
                'tailgating': False,
                'message': 'Entry window was not open'
            }
        self.window_active = False
        elapsed = time.time() - self.window_start_time
        result = {
            'expected': final_expected,
            'actual': final_actual,
            'duration': elapsed,
            'tailgating': False,
            'is_valid': False,
            'message': ''
        }
        print(f"\n🔒 DOOR LOCKED - Entry window closed after {elapsed:.1f}s")
        print(f"   Expected: {final_expected} persons")
        print(f"   Actual: {final_actual} persons")
        if final_actual == final_expected:
            result['is_valid'] = True
            result['message'] = f"✅ VALID ENTRY: {final_actual} authorized persons entered"
            print(result['message'])
        elif final_actual > final_expected:
            result['tailgating'] = True
            unauthorized = final_actual - final_expected
            result['message'] = f"🚨 TAILGATING DETECTED: {unauthorized} unauthorized person(s) entered!"
            print(result['message'])
        elif final_actual < final_expected:
            result['message'] = f"⚠️  INCOMPLETE ENTRY: Expected {final_expected}, only {final_actual} entered"
            print(result['message'])
        else:
            result['message'] = f"❌ UNAUTHORIZED ENTRY: Person entered without authorization!"
            print(result['message'])
        return result
    
    def get_window_status(self) -> dict:
        """Get current entry window status."""
        if not self.window_active:
            return {
                'active': False,
                'elapsed': 0,
                'remaining': 0,
                'expected': 0,
                'actual': 0
            }
        
        elapsed = time.time() - self.window_start_time
        remaining = max(0, self.window_duration - elapsed)
        
        return {
            'active': True,
            'elapsed': elapsed,
            'remaining': remaining,
            'expected': self.expected_count,
            'actual': self.actual_count
        }
