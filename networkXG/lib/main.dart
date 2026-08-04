// lib/main.dart
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'sovereign_vault.dart';
import 'sovereign_handshake.dart';           // ← from networkXG
import 'package:networkxg/relational_mesh_bridge.dart'; // new bridge (below)

late List<CameraDescription> cameras;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  cameras = await availableCameras();
  await SovereignVault().initialize();
  await RelationalMeshBridge().initialize(); // boots Python relational_mesh + soliton pulse

  runApp(const SovereignFloorApp());
}

class SovereignFloorApp extends StatefulWidget {
  const SovereignFloorApp({super.key});
  @override
  State<SovereignFloorApp> createState() => _SovereignFloorAppState();
}

class _SovereignFloorAppState extends State<SovereignFloorApp> {
  late CameraController _controller;
  final Vault = SovereignVault();
  final Mesh = RelationalMeshBridge();

  @override
  void initState() {
    super.initState();
    _controller = CameraController(cameras[0], ResolutionPreset.high);
    _controller.initialize().then((_) {
      _controller.startImageStream((image) async {
        await for (final metric in Vault.processFrame(image)) {
          // Pass derived metrics to living mesh for soliton propagation
          await Mesh.propagateMetric(metric);
          setState(() {}); // Bloom + HUD update
        }
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        body: Stack(
          children: [
            CameraPreview(_controller),
            const BloomPainter(),
            const ResonanceHUD(),
            // Sovereign handshake ritual overlay — always present
            const Positioned(
              bottom: 40,
              left: 40,
              child: SovereignHandshake(
                onGrip: (success) {
                  if (success) {
                    RelationalMeshBridge().triggerConstellationHandshake();
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}