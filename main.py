"""
Unified Dual-Person Access Control System
Combines authentication (face-recognition) and monitoring (corner camera)
Run from root directory: python main.py
"""

import cv2
import sys
import importlib.util
from pathlib import Path


# Load face-recognition access control module
face_rec_path = Path(__file__).parent / "face-recognition"
sys.path.insert(0, str(face_rec_path))

from core.access_control import DualPersonAccessControl

# Load corner monitor module directly
corner_monitor_path = Path(__file__).parent / "strong-room-ai" / "core" / "corner_monitor.py"
spec = importlib.util.spec_from_file_location("corner_monitor", corner_monitor_path)
corner_monitor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corner_monitor_module)
CornerCameraMonitor = corner_monitor_module.CornerCameraMonitor


class DualPersonAccessControlSystem:
    
    def __init__(self):
        print("\n" + "="*70)
        print("DUAL-PERSON ACCESS CONTROL SYSTEM")
        print("="*70)
        print("Version: 2.0 - Unified with Live Monitoring")
        print("="*70)
        self.access_control = DualPersonAccessControl()
        self.corner_monitor = CornerCameraMonitor(expected_count=2)
        print("✅ System initialized")
        print("="*70 + "\n")
    
    def run_authentication_phase(self) -> bool:
        """Phase 1: Two-person face authentication at terminal"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ ERROR: Could not open camera!")
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
                    print("❌ ERROR: Failed to read frame")
                    break
                
                display_frame, queue_complete = self.access_control.process_authentication_frame(frame)
                person_count = len(self.access_control.auth_terminal.get_queue_status()['persons'])
                window_title = f"Authentication Terminal - Person #{person_count + 1}"
                
                cv2.imshow(window_title, display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n❌ Authentication cancelled")
                    cap.release()
                    cv2.destroyAllWindows()
                    return False
                elif key == 32:  # SPACE
                    is_auth, person_id, conf = self.access_control.authenticate_face_from_frame(frame)
                    if is_auth:
                        queue_complete = self.access_control.auth_terminal.add_authenticated_person(person_id)
                        if queue_complete:
                            print(f"\n✅ BOTH PERSONS AUTHENTICATED!")
                            print(f"   Authenticated: {self.access_control.auth_terminal.get_queue_status()['persons']}")
                            cap.release()
                            cv2.destroyAllWindows()
                            return True
                    else:
                        print(f"❌ Authentication failed (confidence: {conf:.2f})")
        
        except KeyboardInterrupt:
            print("\n❌ Authentication interrupted by user")
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        return False
    
    def run_monitoring_phase(self, duration_seconds=30):
        """Phase 2: Continuous corner camera monitoring with live alerts"""
        print("\n" + "="*70)
        print("PHASE 2: CONTINUOUS MONITORING")
        print("="*70)
        print("🚪 DOOR UNLOCKED - Persons authenticated")
        print(f"📹 Corner camera monitoring for {duration_seconds}s")
        print("🚨 Live alerts for:")
        print("   - TAILGATING: More persons than expected")
        print("   - UNDERCOUNTING: Fewer persons than expected")
        print("="*70 + "\n")
        
        # Run monitoring with specified duration
        monitoring_log = self.corner_monitor.run_monitoring(
            camera_index=0,
            duration_seconds=duration_seconds
        )
        
        # Analyze monitoring results
        if monitoring_log:
            # Count different alert types
            tailgate_frames = sum(1 for log in monitoring_log if log.get('alert_type') == 'TAILGATING')
            undercount_frames = sum(1 for log in monitoring_log if log.get('alert_type') == 'UNDERCOUNTING')
            alert_count = tailgate_frames + undercount_frames
            
            print(f"\n{'='*70}")
            print("MONITORING COMPLETE - ANALYSIS")
            print(f"{'='*70}")
            print(f"Total frames monitored: {len(monitoring_log)}")
            print(f"Alert frames: {alert_count}")
            print(f"  - Tailgating alerts: {tailgate_frames}")
            print(f"  - Undercounting alerts: {undercount_frames}")
            
            if alert_count > 0:
                print(f"\n⚠️  ALERTS DETECTED during monitoring")
            else:
                print(f"\n✅ All monitored frames normal - exactly 2 persons detected")
            
            print(f"{'='*70}\n")
            
            return {
                'monitored': True,
                'total_alerts': alert_count,
                'tailgate_alerts': tailgate_frames,
                'undercount_alerts': undercount_frames,
                'log': monitoring_log
            }
        
        return {
            'monitored': False,
            'total_alerts': 0,
            'tailgate_alerts': 0,
            'undercount_alerts': 0,
            'log': []
        }
    
    def run_full_cycle(self):
        """Execute complete access control cycle"""
        print("\n" + "="*70)
        print("FULL CYCLE - AUTHENTICATION + MONITORING")
        print("="*70 + "\n")
        
        # Phase 1: Authentication
        auth_success = self.run_authentication_phase()
        if not auth_success:
            print("\n❌ Authentication failed - System reset")
            self.access_control.reset_system()
            return
        
        # Phase 2: Monitoring
        monitoring_result = self.run_monitoring_phase(duration_seconds=30)
        
        # Final summary
        print("="*70)
        print("CYCLE COMPLETE - FINAL REPORT")
        print("="*70)
        print(f"✅ Phase 1 (Authentication): PASSED")
        print(f"   Authenticated: {self.access_control.auth_terminal.get_queue_status()['persons']}")
        print(f"\n📹 Phase 2 (Monitoring): {'✅ NORMAL' if monitoring_result['total_alerts'] == 0 else '⚠️  COMPROMISED'}")
        print(f"   Total Alerts: {monitoring_result['total_alerts']}")
        print(f"   Tailgating: {monitoring_result['tailgate_alerts']}")
        print(f"   Undercounting: {monitoring_result['undercount_alerts']}")
        print("="*70 + "\n")
        
        # Reset for next cycle
        self.access_control.reset_system()
    
    def show_menu(self):
        """Interactive menu system"""
        while True:
            print("\n" + "="*70)
            print("DUAL-PERSON ACCESS CONTROL SYSTEM - MENU")
            print("="*70)
            print("1. Run full access control cycle")
            print("2. Run authentication only")
            print("3. Run monitoring only (demo)")
            print("4. Exit")
            print("="*70)
            
            choice = input("Select option: ").strip()
            
            if choice == "1":
                self.run_full_cycle()
            
            elif choice == "2":
                auth_success = self.run_authentication_phase()
                if auth_success:
                    print("\n✅ Authentication phase completed successfully!")
                    self.access_control.reset_system()
                else:
                    print("\n❌ Authentication phase failed")
            
            elif choice == "3":
                print("\nStarting monitoring demo (30 seconds)...")
                self.run_monitoring_phase(duration_seconds=30)
            
            elif choice == "4":
                print("\n✅ System shutdown - Goodbye!")
                break
            
            else:
                print("❌ Invalid option - Please select 1-4")


def main():
    """Main entry point"""
    try:
        system = DualPersonAccessControlSystem()
        system.show_menu()
    except KeyboardInterrupt:
        print("\n\n❌ System interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
