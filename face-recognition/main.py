import cv2
import sys
from pathlib import Path
from core.access_control import DualPersonAccessControl

class DualPersonAccessControlDemo:
    def __init__(self):
        print("\n" + "="*70)
        print("DUAL-PERSON ACCESS CONTROL SYSTEM")
        print("="*70)
        self.access_control = DualPersonAccessControl()
        print("✅ System initialized")
        print("="*70 + "\n")
    
    def run_authentication_phase(self) -> bool:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("ERROR: Could not open camera!")
            return False
        print("\n" + "="*70)
        print("PHASE 1: AUTHENTICATION")
        print("="*70)
        print("Two people must authenticate sequentially at the terminal.")
        print("Controls:")
        print("  SPACE - Authenticate person (detects face in frame)")
        print("  Q - Quit")
        print("="*70 + "\n")
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("ERROR: Failed to read frame")
                    break
                display_frame, queue_complete = self.access_control.process_authentication_frame(frame)
                cv2.imshow("Authentication Terminal - Person #" + 
                          str(len(self.access_control.auth_terminal.get_queue_status()['persons'])+1), 
                          display_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Authentication cancelled")
                    cap.release()
                    cv2.destroyAllWindows()
                    return False
                elif key == 32:
                    is_auth, person_id, conf = self.access_control.authenticate_face_from_frame(frame)
                    if is_auth:
                        queue_complete = self.access_control.auth_terminal.add_authenticated_person(person_id)
                        if queue_complete:
                            print(f"\n✅ BOTH PERSONS AUTHENTICATED!")
                            print(f"   {self.access_control.auth_terminal.get_queue_status()['persons']}")
                            cap.release()
                            cv2.destroyAllWindows()
                            return True
                    else:
                        print(f"❌ Authentication failed (confidence: {conf:.2f})")
        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        return False
    
    def run_entry_phase(self) -> dict:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("ERROR: Could not open camera!")
            return {'is_valid': False, 'message': 'Camera error'}
        print("\n" + "="*70)
        print("PHASE 2: ENTRY WINDOW")
        print("="*70)
        print("Door is now UNLOCKED for 10 minutes.")
        print("Authorized persons may enter while camera counts.")
        print("="*70 + "\n")
        self.access_control.unlock_door()
        entry_result = None
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                display_frame, result = self.access_control.process_entry_frame(frame)
                cv2.imshow("Entry Monitor - Counting", display_frame)
                if result is not None:
                    entry_result = result
                    break
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Interrupted")
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()
        return entry_result or {'is_valid': False, 'message': 'Window closed'}
    
    def run_full_cycle(self):
        print("\n" + "="*70)
        print("DUAL-PERSON ACCESS CONTROL - FULL CYCLE")
        print("="*70 + "\n")
        auth_success = self.run_authentication_phase()
        if not auth_success:
            print("\n❌ Authentication failed. System reset.")
            self.access_control.reset_system()
            return
        entry_result = self.run_entry_phase()
        print("\n" + "="*70)
        print("CYCLE COMPLETE - FINAL RESULT")
        print("="*70)
        print(f"Entry Result: {entry_result['message']}")
        print(f"Valid: {entry_result['is_valid']}")
        print(f"Tailgating: {entry_result['tailgating']}")
        print("="*70 + "\n")
        self.access_control.reset_system()
    
    def demo_interactive(self):
        """Interactive demo mode."""
        while True:
            print("\n" + "="*70)
            print("DUAL-PERSON ACCESS CONTROL - DEMO")
            print("="*70)
            print("1. Run full access control cycle")
            print("2. Exit")
            print("="*70)
            
            choice = input("Select: ").strip()
            
            if choice == "1":
                self.run_full_cycle()
            elif choice == "2":
                print("Goodbye!")
                break
            else:
                print("Invalid option")


if __name__ == "__main__":
    demo = DualPersonAccessControlDemo()
    demo.demo_interactive()
