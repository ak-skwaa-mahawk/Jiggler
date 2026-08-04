// lib/six_cylinder_grpc_client.dart
// Sovereign gRPC Client for SixCylinderBoundary GS Coupling
// Matches the hardened Rust / gRPC server in isst-toft-inference-backend

import 'package:grpc/grpc.dart';
import 'package:fixnum/fixnum.dart'; // if you use Int64

// Import your generated protobuf code
// Run: protoc --dart_out=grpc:lib/generated -Iproto proto/isst_toft.proto
import 'generated/issttoft.pb.dart';
import 'generated/issttoft.pbgrpc.dart';

class SixCylinderGrpcClient {
  late final InferenceServiceClient _client;

  SixCylinderGrpcClient({String host = 'localhost', int port = 50051}) {
    final channel = ClientChannel(
      host,
      port: port,
      options: const ChannelOptions(
        credentials: ChannelCredentials.insecure(),
        idleTimeout: Duration(minutes: 1),
      ),
    );
    _client = InferenceServiceClient(channel);
  }

  /// Compute full 6-face boundary state + toroidal metrics
  Future<SixFaceResponse> computeSixFaceBoundary({
    double spin = 1.5,
    double pressure = 1.0,
    double temp = 0.15,
    double beltMod = 1.0,
  }) async {
    final request = SixFaceRequest()
      ..spin = spin
      ..pressure = pressure
      ..temp = temp
      ..beltMod = beltMod;

    return await _client.computeSixFaceBoundary(request);
  }

  /// Quick closed-loop delta only
  Future<double> getClosedLoopDelta({
    double spin = 1.5,
    double pressure = 1.0,
    double temp = 0.15,
    double beltMod = 1.0,
  }) async {
    final request = SixFaceRequest()
      ..spin = spin
      ..pressure = pressure
      ..temp = temp
      ..beltMod = beltMod;

    final response = await _client.getClosedLoopDelta(request);
    return response.delta;
  }

  /// Run the four-pillar TrackingFormProof
  Future<ProofResponse> runTrackingFormProof({
    double spin = 1.5,
    double pressure = 1.0,
    double temp = 0.15,
    double beltMod = 1.0,
  }) async {
    final request = SixFaceRequest()
      ..spin = spin
      ..pressure = pressure
      ..temp = temp
      ..beltMod = beltMod;

    return await _client.runTrackingFormProof(request);
  }

  /// Convenience: returns true if all four pillars hold
  Future<bool> isGeometryValid({
    double spin = 1.5,
    double pressure = 1.0,
    double temp = 0.15,
    double beltMod = 1.0,
  }) async {
    final proof = await runTrackingFormProof(
      spin: spin,
      pressure: pressure,
      temp: temp,
      beltMod: beltMod,
    );
    return proof.allPillarsHold;
  }
}