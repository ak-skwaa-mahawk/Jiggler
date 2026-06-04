// lib/clients/intent_client.dart

import 'package:grpc/grpc.dart';
import '../generated/issttoft.pb.dart';
import '../generated/issttoft.pbgrpc.dart';

class IntentClient {
  late final ClientChannel _channel;
  late final InferenceServiceClient _stub;

  IntentClient({String host = 'localhost', int port = 50051}) {
    _channel = ClientChannel(
      host,
      port: port,
      options: const ChannelOptions(
        credentials: ChannelCredentials.insecure(),
        idleTimeout: Duration(minutes: 5),
      ),
    );
    _stub = InferenceServiceClient(_channel);
  }

  // === Existing methods (getAllIntentBands, getIntentBand, etc.) remain the same ===

  /// Streaming intent updates (real-time)
  Stream<IntentUpdate> streamIntentUpdates() {
    return _stub.streamIntentUpdates(Empty());
  }

  Future<void> close() async {
    await _channel.shutdown();
  }
}