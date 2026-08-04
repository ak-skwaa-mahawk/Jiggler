cat > \~/sovereign/grpc/six_cylinder_grpc_client.py << 'PYEOF'
import grpc
import issttoft_pb2
import issttoft_pb2_grpc

class SixCylinderGrpcClient:
    def __init__(self, host="localhost", port=50051):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = issttoft_pb2_grpc.InferenceServiceStub(self.channel)

    def compute_six_face_boundary(self, spin=1.5, pressure=1.0, temp=0.15, belt_mod=1.0):
        req = issttoft_pb2.SixFaceRequest(
            spin=spin, pressure=pressure, temp=temp, belt_mod=belt_mod
        )
        resp = self.stub.ComputeSixFaceBoundary(req)
        return {
            "core_curvature": resp.core_curvature,
            "belt_curvature": resp.belt_curvature,
            "cap_curvature": resp.cap_curvature,
            "closed_loop_delta": resp.closed_loop_delta,
            "gs_density": resp.gs_density,
            "closed_loop_stability": resp.closed_loop_stability,
            "regime": resp.regime,
        }

    def get_closed_loop_delta(self, spin=1.5, pressure=1.0, temp=0.15, belt_mod=1.0):
        req = issttoft_pb2.SixFaceRequest(
            spin=spin, pressure=pressure, temp=temp, belt_mod=belt_mod
        )
        resp = self.stub.GetClosedLoopDelta(req)
        return resp.delta

    def run_tracking_form_proof(self, spin=1.5, pressure=1.0, temp=0.15, belt_mod=1.0):
        req = issttoft_pb2.SixFaceRequest(
            spin=spin, pressure=pressure, temp=temp, belt_mod=belt_mod
        )
        resp = self.stub.RunTrackingFormProof(req)
        return {
            "all_pillars_hold": resp.all_pillars_hold,
            "details": resp.details,
        }

    def is_geometry_valid(self, spin=1.5, pressure=1.0, temp=0.15, belt_mod=1.0):
        proof = self.run_tracking_form_proof(spin, pressure, temp, belt_mod)
        return proof["all_pillars_hold"]

    def close(self):
        self.channel.close()
PYEOF