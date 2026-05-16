import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const PlantVisionApp());
}

class PlantVisionApp extends StatelessWidget {
  const PlantVisionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PlantVision AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2C5F2D),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}