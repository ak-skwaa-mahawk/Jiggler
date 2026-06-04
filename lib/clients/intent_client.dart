// lib/clients/intent_client.dart
// Sovereign Intent + SixCylinderBoundary Client
// Features: Auto-reconnect, caching, retry logic, and full method support

import 'package:grpc/grpc.dart';
import 'package:protobuf/protobuf.dart';

import '../generated/issttoft.pb.dart';
import '../generated/issttoft.pbgrpc.dart';

class IntentClient {
  late ClientChannel _channel;
  late InferenceServiceClient _stub;

  final String host;
  final int port;
  final double cacheTtlSeconds;
  final int maxRetries;

  // Simple in-memory cache: key -> (timestamp, data)
  final Map<String, (DateTime, dynamic)> _cache = {};

  IntentClient({
    this.host = 'localhost',
    this.port = 50051,
    this.cacheTtlSeconds = 8.0,
    this.maxRetries = 3,
  }) {
    _connect();
  }

  void _connect() {
    _channel = ClientChannel(
      host,
      port: port,
      options: const ChannelOptions(
        credentials: ChannelCredentials.insecure(),
        idleTimeout: Duration(minutes: 5),
      ),
    );
    _stub = InferenceServiceClient(_channel);
    print('[IntentClient] Connected to $host:$port');
  }

  Future<void> _ensureConnected() async {
    try {
      await _channel.getConnection().channelReady;
    } catch (_) {
      print('[IntentClient] Connection lost. Reconnecting...');
      _connect();
    }
  }

  // ====================== INTENT ENGINE ======================

  Future<List<IntentBand>> getAllIntentBands({bool useCache = true}) async {
    const cacheKey = 'all_bands';

    if (useCache && _cache.containsKey(cacheKey)) {
      final (timestamp, data) = _cache[cacheKey]!;
      if (DateTime.now().difference(timestamp).inSeconds < cacheTtlSeconds) {
        return data as List<IntentBand>;
      }
    }

    for (int attempt = 0; attempt < maxRetries; attempt++) {
      try {
        await _ensureConnected();
        final response = await _stub.getAllIntentBands(Empty());
        final bands = response.bands;

        _cache[cacheKey] = (DateTime.now(), bands);
        return bands;
      } on GrpcError catch (e) {
        print('[IntentClient] getAllIntentBands error (attempt ${attempt + 1}): ${e.message}');
        if (attempt == maxRetries - 1) rethrow;
        await Future.delayed(Duration(milliseconds: 400 * (attempt + 1)));
        _connect();
      }
    }
    throw Exception('Failed to fetch intent bands after $maxRetries attempts');
  }

  Future<IntentBand?> getIntentBand(String bandId, {int mode = 0}) async {
    for (int attempt = 0; attempt < maxRetries; attempt++) {
      try {
        await _ensureConnected();
        final request = GetIntentBandRequest()
          ..bandId = bandId
          ..mode = mode;

        return await _stub.getIntentBand(request);
      } on GrpcError catch (e) {
        if (e.code == StatusCode.notFound) return null;
        if (attempt == maxRetries - 1) rethrow;
        await Future.delayed(Duration(milliseconds: 300));
        _connect();
      }
    }
    return null;
  }

  // ====================== SIXCYLINDERBOUNDARY METHODS ======================

  Future<SixFaceResponse> computeSixFaceBoundary({
    double spin = 1.5,
    double pressure = 1.0,
    double temp = 0.15,
    double beltMod = 1.0,
  }) async {
    for (int attempt = 0; attempt < maxRetries; attempt++) {
      try {
        await _ensureConnected();
        final req = SixFaceRequest()
          ..spin = spin
          ..pressure = pressure
          ..temp = temp
          ..beltMod = beltMod;

        return await _stub.computeSixFaceBoundary(req);
      } on GrpcError {
        if (attempt == maxRetries - 1) rethrow;
        await Future.delayed(Duration(milliseconds: 300));
        _connect();
      }
    }
    throw Exception('computeSixFaceBoundary failed');
  }

  Future<double> getClosedLoopDelta({
    double spin = 1.5,
    double pressure = 1.0,
    double temp = 0.15,
    double beltMod = 1.0,
  }) async {
    for (int attempt = 0; attempt < maxRetries; attempt++) {
      try {
        await _ensureConnected();
        final req = SixFaceRequest()
          ..spin = spin
          ..pressure = pressure
          ..temp = temp
          ..beltMod = beltMod;

        final response = await _stub.getClosedLoopDelta(req);
        return response.delta;
      } on GrpcError {
        if (attempt == maxRetries - 1) rethrow;
        await Future.delayed(Duration(milliseconds: 300));
        _connect();
      }
    }
    throw Exception('getClosedLoopDelta failed');
  }

  Future<ProofResponse> runTrackingFormProof({
    double spin = 1.5,
    double pressure = 1.0,
    double temp = 0.15,
    double beltMod = 1.0,
  }) async {
    for (int attempt = 0; attempt < maxRetries; attempt++) {
      try {
        await _ensureConnected();
        final req = SixFaceRequest()
          ..spin = spin
          ..pressure = pressure
          ..temp = temp
          ..beltMod = beltMod;

        return await _stub.runTrackingFormProof(req);
      } on GrpcError {
        if (attempt == maxRetries - 1) rethrow;
        await Future.delayed(Duration(milliseconds: 300));
        _connect();
      }
    }
    throw Exception('runTrackingFormProof failed');
  }

  // ====================== STREAMING (Future) ======================

  // Placeholder for future streaming RPC
  // Stream<IntentUpdate> streamIntentUpdates() async* {
  //   // Once we add a streaming method in the .proto
  // }

  Future<void> close() async {
    await _channel.shutdown();
  }
}