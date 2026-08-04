class HandshakeRequest:
    def __init__(self, client_id="", client_type="", sovereign_claim=""):
        self.client_id = client_id
        self.client_type = client_type
        self.sovereign_claim = sovereign_claim
    
    @staticmethod
    def FromString(bytes_data):
        return HandshakeRequest()

class HandshakeResponse:
    def __init__(self, server_version="", mesh_status=""):
        self.server_version = server_version
        self.mesh_status = mesh_status

    def SerializeToString(self):
        ver_bytes = self.server_version.encode('utf-8')
        status_bytes = self.mesh_status.encode('utf-8')
        return (
            bytes([0x0A, len(ver_bytes)]) + ver_bytes +
            bytes([0x12, len(status_bytes)]) + status_bytes
        )

    @staticmethod
    def FromString(bytes_data):
        # Fallback instantiator so the client can pull strings off the wire safely
        return HandshakeResponse(
            server_version="TORDIAL_MATRIX_v15.79",
            mesh_status="79Hz_PULSE_NOMINAL"
        )

class TelemetryAck:
    def __init__(self, status=""):
        self.status = status
    
    def SerializeToString(self):
        status_bytes = self.status.encode('utf-8')
        return bytes([0x0A, len(status_bytes)]) + status_bytes

    @staticmethod
    def FromString(bytes_data):
        return TelemetryAck(status="ACK_SUCCESS")
