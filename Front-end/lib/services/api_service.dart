import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';

class ApiService {
 static String get baseUrl {
  if (kIsWeb) return 'http://localhost:8000';
  if (Platform.isAndroid) return 'http://192.168.1.11:8000';
  if (Platform.isIOS) return 'http://192.168.1.11:8000';
  return 'http://localhost:8000';
}
  static Future<Map<String, dynamic>> identifyPlant(List<File> images) async {
    final uri     = Uri.parse("$baseUrl/identify");
    final request = http.MultipartRequest("POST", uri);

    for (final img in images) {
      request.files.add(
        await http.MultipartFile.fromPath("images", img.path),
      );
    }

    final streamed = await request.send();
    final body     = await streamed.stream.bytesToString();
    final decoded  = jsonDecode(body);

    if (streamed.statusCode != 200) {
      throw Exception(decoded["detail"] ?? "Server error");
    }

    return decoded;
  }

  static Future<Map<String, dynamic>> detectDisease(File image) async {
    final uri     = Uri.parse("$baseUrl/disease/detect");
    final request = http.MultipartRequest("POST", uri);

    request.files.add(
      await http.MultipartFile.fromPath("file", image.path),
    );

    final streamed = await request.send();
    final body     = await streamed.stream.bytesToString();
    final decoded  = jsonDecode(body);

    if (streamed.statusCode != 200) {
      throw Exception(decoded["detail"] ?? "Disease detection failed");
    }

    return decoded;
  }
}