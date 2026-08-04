import socket
import threading
import time
import numpy as np
from typing import Any

# Import our previously designed secure serialization class
# (Assuming SecureStateSerializer from the previous step is accessible here)
SHARED_SECRET = b"tgs_manifold_ultra_secure_secret_key_32bytes_long"
serializer = SecureStateSerializer(secret_key=SHARED_SECRET)

# Define network binding profiles
HOST = "127.0.0.1"
PORT = 9988

# ==============================================================================
# 1. BACKUP SERVER RECEIVER LOOP (Thread-Isolated)
# ==============================================================================
def run_backup_receiver_server(stop_event: threading.Event):
    """
    A network server simulating a secondary dual-ring node. 
    Listens for inbound state transfers, validates authenticity, and hot-boots state arrays.
    """
    # Create an IPv4 TCP streaming socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow prompt port reuse after close to avoid socket bind blocks
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(1)
    server_sock.settimeout(0.2)  # Short timeout to allow clean check of stop_event
    
    print(f"[BACKUP-NODE] Server listening on tcp://{HOST}:{PORT}")
    
    while not stop_event.is_set():
        try:
            conn, addr = server_sock.accept()
        except socket.timeout:
            continue  # Check stop_event again
            
        print(f"\n[BACKUP-NODE] Connection inbound accepted from endpoint: {addr}")
        try:
            # Accumulate inbound string buffers over network socket stream
            received_data = []
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                received_data.append(chunk)
            
            envelope_str = b"".join(received_data).decode('utf-8')
            
            if envelope_str:
                print(f"[BACKUP-NODE] Inbound payload packet received ({len(envelope_str)} bytes). Checking signatures...")
                
                # Verify cryptographic footprint and unpack state values natively
                restored_state = serializer.deserialize_agent_state(envelope_str)
                
                print("✅ [BACKUP-NODE] CRYPTOGRAPHIC SIGNATURE VALIDATED!")
                print(f"[BACKUP-NODE] Resuming Loop for Target Agent ID: {restored_state['agent_id']}")
                print(f"[BACKUP-NODE] Extracted EKF State Map Vector:\n{restored_state['ekf_x'].flatten()}")
                
                # Send confirmation payload receipt handshake acknowledgement
                conn.close()
                print("[BACKUP-NODE] State integration successful. Hot takeover mode complete.")
                break
                
        except Exception as e:
            print(f"❌ [BACKUP-NODE ERROR] Compromised or corrupt packet drop: {e}")
            if 'conn' in locals():
                conn.close()
                
    server_sock.close()
    print("[BACKUP-NODE] Server thread disengaged.")


# ==============================================================================
# 2. ACTIVE NETWORK TRANSMISSION HOOK
# ==============================================================================
def execute_network_failover(agent_id: str, ekf_x: np.ndarray, ekf_P: np.ndarray, pid_integral: np.ndarray) -> bool:
    """
    Serializes and opens a stream to transmit state vectors to the target backup socket.
    """
    print(f"\n[AGENT-{agent_id}] Initializing socket failover protocol...")
    
    # 1. Package active memory matrix frames safely
    serialized_packet = serializer.serialize_agent_state(
        agent_id=agent_id,
        ekf_state=ekf_x,
        ekf_covariance=ekf_P,
        pid_integral=pid_integral
    )
    
    try:
        # 2. Connect directly to the local server port
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((HOST, PORT))
        
        # 3. Stream data package string down network tube
        print(f"[AGENT-{agent_id}] Streaming encrypted state envelope to backup receiver...")
        client_sock.sendall(serialized_packet.encode('utf-8'))
        client_sock.close()
        
        print(f"✅ [AGENT-{agent_id}] Network streaming complete. Local state successfully transferred.")
        return True
    except ConnectionRefusedError:
        print("❌ [FAILOVER FAILURE] Connection refused! Target backup receiver server is offline.")
        return False
    except Exception as e:
        print(f"❌ [FAILOVER FAILURE] Transmit error encountered: {e}")
        return False


# ==============================================================================
# 3. INTEGRATION DEMO HARNESS
# ==============================================================================
if __name__ == "__main__":
    # Create thread event controls
    stop_signal = threading.Event()
    
    # 1. Fire up background backup receiver server thread
    backup_thread = threading.Thread(target=run_backup_receiver_server, args=(stop_signal,))
    backup_thread.start()
    
    # Give server a brief window to bind the network port securely
    time.sleep(0.2)
    
    # 2. Generate mock runtime data simulating an agent experiencing a drift spike
    mock_ekf_x = np.array([[2.34], [-1.02], [0.55]])  # 3D drift state estimate
    mock_ekf_P = np.eye(3) * 0.04                      # Filter uncertainty
    mock_pid_int = np.array([0.1, -0.05, 0.02])        # PID error history cache
    
    # 3. Trigger early-warning transmission event
    print("\n[SIMULATION MASTER] Structural threshold threat predicted! Executing failover hook...")
    success = execute_network_failover(
        agent_id="Sovereign-TGS-Agent-01", 
        ekf_x=mock_ekf_x, 
        ekf_P=mock_ekf_P, 
        pid_integral=mock_pid_int
    )
    
    # 4. Cleanup and thread teardown handling
    time.sleep(0.5)  # Let server process print logs before stopping
    stop_signal.set()
    backup_thread.join()
    print("\n[SIMULATION MASTER] All local network verification routines finalized.")
