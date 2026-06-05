import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import 'result_screen.dart';
import 'disease_result_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ImagePicker _picker = ImagePicker();
  bool _loading = false;
  String _loadingMessage = "Identifying plant...";

  bool get _isMobile => !kIsWeb && (Platform.isAndroid || Platform.isIOS);

  Future<void> _pickAndIdentify(ImageSource source) async {
    final List<XFile> images = await _picker.pickMultiImage();
    if (images.isEmpty) return;

    setState(() {
      _loading = true;
      _loadingMessage = "Identifying plant...";
    });

    try {
      final result = await ApiService.identifyPlant(
        images.map((x) => File(x.path)).toList(),
      );
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => ResultScreen(data: result)),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _capturePhoto() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.camera);
    if (image == null) return;

    setState(() {
      _loading = true;
      _loadingMessage = "Identifying plant...";
    });

    try {
      final result = await ApiService.identifyPlant([File(image.path)]);
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => ResultScreen(data: result)),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _detectDiseaseFromCamera() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.camera);
    if (image == null) return;
    await _runDiseaseDetection(File(image.path));
  }

  Future<void> _detectDiseaseFromGallery() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
    if (image == null) return;
    await _runDiseaseDetection(File(image.path));
  }

  Future<void> _runDiseaseDetection(File imageFile) async {
    setState(() {
      _loading = true;
      _loadingMessage = "Analyzing leaf health...";
    });

    try {
      final result = await ApiService.detectDisease(imageFile);
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => DiseaseResultScreen(data: result, image: imageFile),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF1F8E9),
      body: SafeArea(
        child: _loading
            ? Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const CircularProgressIndicator(color: Color(0xFF2C5F2D)),
                    const SizedBox(height: 16),
                    Text(
                      _loadingMessage,
                      style: const TextStyle(
                          fontSize: 16, color: Color(0xFF2C5F2D)),
                    ),
                  ],
                ),
              )
            : SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    const SizedBox(height: 40),

                    // Logo
                    Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        color: const Color(0xFF2C5F2D),
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: const Icon(Icons.local_florist,
                          size: 60, color: Colors.white),
                    ),
                    const SizedBox(height: 20),
                    const Text(
                      "PlantVision AI",
                      style: TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF2C5F2D),
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      "Identify any plant instantly\nwith AI-powered recognition",
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 15, color: Colors.grey),
                    ),
                    const SizedBox(height: 40),

                    // ── Section: Plant Identification ────────────────────
                    _SectionLabel(
                      icon: Icons.local_florist,
                      label: "Plant Identification",
                    ),
                    const SizedBox(height: 12),

                    if (_isMobile) ...[
                      _ActionButton(
                        icon: Icons.camera_alt,
                        label: "Take Photo",
                        subtitle: "Capture a real-time photo",
                        color: const Color(0xFF2C5F2D),
                        onTap: _capturePhoto,
                      ),
                      const SizedBox(height: 12),
                    ],

                    _ActionButton(
                      icon: Icons.photo_library,
                      label: "Upload from Gallery",
                      subtitle: "Select saved images",
                      color: const Color(0xFF558B2F),
                      onTap: () => _pickAndIdentify(ImageSource.gallery),
                    ),

                    const SizedBox(height: 32),

                    // ── Divider ──────────────────────────────────────────
                    const Row(children: [
                      Expanded(child: Divider(color: Color(0xFFBDBDBD))),
                      Padding(
                        padding: EdgeInsets.symmetric(horizontal: 12),
                        child: Text("or",
                            style:
                                TextStyle(color: Colors.grey, fontSize: 13)),
                      ),
                      Expanded(child: Divider(color: Color(0xFFBDBDBD))),
                    ]),

                    const SizedBox(height: 32),

                    // ── Section: Disease Detection ───────────────────────
                    _SectionLabel(
                      icon: Icons.coronavirus_outlined,
                      label: "Disease Detection",
                    ),
                    const SizedBox(height: 12),

                    if (_isMobile) ...[
                      _ActionButton(
                        icon: Icons.camera_alt_outlined,
                        label: "Scan Leaf (Camera)",
                        subtitle: "Check for diseases in real-time",
                        color: const Color(0xFFB85C00),
                        onTap: _detectDiseaseFromCamera,
                      ),
                      const SizedBox(height: 12),
                    ],

                    _ActionButton(
                      icon: Icons.image_search,
                      label: "Scan from Gallery",
                      subtitle: "Upload a leaf image to analyze",
                      color: const Color(0xFFD4761A),
                      onTap: _detectDiseaseFromGallery,
                    ),

                    const SizedBox(height: 32),
                    const Text(
                      "Supports leaves, flowers, fruits & bark",
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
      ),
    );
  }
}

// ── Section label widget ──────────────────────────────────────────────────────
class _SectionLabel extends StatelessWidget {
  final IconData icon;
  final String label;

  const _SectionLabel({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Row(
        children: [
          Icon(icon, size: 18, color: const Color(0xFF2C5F2D)),
          const SizedBox(width: 8),
          Text(
            label,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: Color(0xFF2C5F2D),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Reusable action button ────────────────────────────────────────────────────
class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
                color: color.withOpacity(0.3),
                blurRadius: 12,
                offset: const Offset(0, 4))
          ],
        ),
        child: Row(
          children: [
            Icon(icon, color: Colors.white, size: 36),
            const SizedBox(width: 16),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold)),
                Text(subtitle,
                    style: const TextStyle(
                        color: Colors.white70, fontSize: 13)),
              ],
            )
          ],
        ),
      ),
    );
  }
}