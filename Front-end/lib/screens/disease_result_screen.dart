import 'dart:io';
import 'package:flutter/material.dart';

class DiseaseResultScreen extends StatelessWidget {
  final Map<String, dynamic> data;
  final File image;

  const DiseaseResultScreen({
    super.key,
    required this.data,
    required this.image,
  });

  @override
  Widget build(BuildContext context) {
    final bool isHealthy = data['healthy'] == true;
    final String disease = data['disease'] ?? 'Unknown';
    final double confidence = ((data['confidence'] ?? 0) * 100);
    final String displayName = data['display_name'] ?? disease;
    final String severity = data['severity'] ?? '';
    final String symptoms = data['symptoms'] ?? '';
    final String prevention = data['prevention'] ?? '';
    final List organicCures = data['organic_cures'] ?? [];
    final List chemicalCures = data['chemical_cures'] ?? [];

    final Color severityColor = isHealthy
        ? const Color(0xFF2C5F2D)
        : severity == 'high'
            ? Colors.red
            : severity == 'medium'
                ? Colors.orange
                : Colors.amber;

    return Scaffold(
      backgroundColor: const Color(0xFFF1F8E9),
      appBar: AppBar(
        title: const Text("Disease Analysis",
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF2C5F2D),
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Leaf image
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.file(image,
                  width: double.infinity, height: 220, fit: BoxFit.cover),
            ),
            const SizedBox(height: 16),

            // Health status card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: isHealthy
                    ? const Color(0xFFE8F5E9)
                    : const Color(0xFFFFF3E0),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: severityColor.withOpacity(0.4)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        isHealthy
                            ? Icons.check_circle
                            : Icons.warning_amber_rounded,
                        color: severityColor,
                        size: 28,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          isHealthy ? "Plant is Healthy!" : displayName,
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: severityColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      _Badge(
                        label:
                            "Confidence: ${confidence.toStringAsFixed(1)}%",
                        color: const Color(0xFF2C5F2D),
                      ),
                      if (!isHealthy && severity.isNotEmpty) ...[
                        const SizedBox(width: 8),
                        _Badge(
                          label:
                              "Severity: ${severity[0].toUpperCase()}${severity.substring(1)}",
                          color: severityColor,
                        ),
                      ]
                    ],
                  ),
                ],
              ),
            ),

            if (!isHealthy) ...[
              // Symptoms
              if (symptoms.isNotEmpty) ...[
                const SizedBox(height: 20),
                _SectionTitle(icon: Icons.info_outline, title: "Symptoms"),
                const SizedBox(height: 8),
                _InfoCard(text: symptoms),
              ],

              // Organic cures
              if (organicCures.isNotEmpty) ...[
                const SizedBox(height: 20),
                _SectionTitle(
                    icon: Icons.eco_outlined, title: "Organic Treatment"),
                const SizedBox(height: 8),
                ...organicCures
                    .map((cure) => _CureItem(text: cure, isOrganic: true)),
              ],

              // Chemical cures
              if (chemicalCures.isNotEmpty) ...[
                const SizedBox(height: 20),
                _SectionTitle(
                    icon: Icons.science_outlined,
                    title: "Chemical Treatment"),
                const SizedBox(height: 8),
                ...chemicalCures
                    .map((cure) => _CureItem(text: cure, isOrganic: false)),
              ],

              // Prevention
              if (prevention.isNotEmpty) ...[
                const SizedBox(height: 20),
                _SectionTitle(
                    icon: Icons.shield_outlined, title: "Prevention"),
                const SizedBox(height: 8),
                _InfoCard(text: prevention),
              ],
            ] else ...[
              const SizedBox(height: 24),
              const Center(
                child: Text(
                  "No disease detected. Keep up the good care!",
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 15, color: Colors.grey),
                ),
              ),
            ],

            const SizedBox(height: 32),

            // Scan again button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.refresh),
                label: const Text("Scan Another Leaf"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2C5F2D),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final IconData icon;
  final String title;
  const _SectionTitle({required this.icon, required this.title});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Icon(icon, size: 18, color: const Color(0xFF2C5F2D)),
      const SizedBox(width: 8),
      Text(title,
          style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Color(0xFF2C5F2D))),
    ]);
  }
}

class _InfoCard extends StatelessWidget {
  final String text;
  const _InfoCard({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Text(text, style: const TextStyle(fontSize: 14, height: 1.5)),
    );
  }
}

class _CureItem extends StatelessWidget {
  final String text;
  final bool isOrganic;
  const _CureItem({required this.text, required this.isOrganic});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          Icon(
            isOrganic ? Icons.eco : Icons.science,
            size: 18,
            color: isOrganic ? const Color(0xFF558B2F) : Colors.blueGrey,
          ),
          const SizedBox(width: 10),
          Expanded(
              child: Text(text, style: const TextStyle(fontSize: 14))),
        ],
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  final String label;
  final Color color;
  const _Badge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Text(label,
          style: TextStyle(
              fontSize: 12, color: color, fontWeight: FontWeight.w600)),
    );
  }
}
