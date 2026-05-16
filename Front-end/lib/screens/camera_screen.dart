import 'package:flutter/material.dart';
// Real-time camera is handled via image_picker in home_screen.dart
// This screen is reserved for future live viewfinder feature

class CameraScreen extends StatelessWidget {
  const CameraScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Camera")),
      body: const Center(
        child: Text("Live camera coming soon"),
      ),
    );
  }
}