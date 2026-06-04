// lib/clients/intent_client.dart
// Simple helper client for the Sovereign Intent Engine

import 'package:grpc/grpc.dart';
import 'package:protobuf/protobuf.dart'; // for Empty

// Import your generated protobuf files
// Run: protoc --dart_out=grpc:lib/generated -Iproto proto/isst_toft.proto
import '../generated/issttoft.pb.dart';
import '../generated/issttoft.pbgrpc.dart';

class IntentClient {
  late final InferenceServiceClient _client;
  late final ClientChannel _channel;

  IntentClient({
    String host = 'localhost',
    int port = 50051,
  }) {
    _channel = ClientChannel(
      host,
      port: port,
      options: const ChannelOptions(
        credentials: ChannelCredentials.insecure(),
        idleTimeout: Duration(minutes: 5),
      ),
    );
    _client = InferenceServiceClient(_channel);
  }

  /// Get all current intent bands
  Future<List<IntentBand>> getAllIntentBands() async {
    try {
      final response = await _client.getAllIntentBands(Empty());
      return response.bands;
    } catch (e) {
      print('Error fetching intent bands: $e');
      rethrow;
    }
  }

  /// Get a specific intent band by ID and mode
  Future<IntentBand?> getIntentBand(String bandId, {int mode = 0}) async {
    try {
      final request = GetIntentBandRequest()
        ..bandId = bandId
        ..mode = mode;

      return await _client.getIntentBand(request);
    } on GrpcError catch (e) {
      if (e.code == StatusCode.notFound) {
        return null; // Band doesn't exist
      }
      print('gRPC error: ${e.message}');
      rethrow;
    } catch (e) {
      print('Unexpected error: $e');
      rethrow;
    }
  }

  /// Close the connection
  Future<void> close() async {
    await _channel.shutdown();
  }
}