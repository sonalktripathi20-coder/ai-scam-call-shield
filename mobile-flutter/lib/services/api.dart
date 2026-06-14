import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String defaultBaseUrl = "https://slick-emus-hammer.loca.lt"; // Live production Railway URL

  static Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('backend_url') ?? defaultBaseUrl;
  }

  static Future<void> saveBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('backend_url', url);
  }

  // Get App Settings
  static Future<Map<String, dynamic>> getSettings() async {
    try {
      final baseUrl = await getBaseUrl();
      final response = await http.get(Uri.parse('$baseUrl/api/settings'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print("[API] Error fetching settings: $e");
    }
    return {};
  }

  // Update App Settings
  static Future<bool> updateSettings(Map<String, dynamic> settings) async {
    try {
      final baseUrl = await getBaseUrl();
      final response = await http.post(
        Uri.parse('$baseUrl/api/settings'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(settings),
      );
      return response.statusCode == 200;
    } catch (e) {
      print("[API] Error updating settings: $e");
    }
    return false;
  }

  // Sync Phone Contacts
  static Future<bool> syncContacts(List<Map<String, String>> contacts) async {
    try {
      final baseUrl = await getBaseUrl();
      final response = await http.post(
        Uri.parse('$baseUrl/api/contacts/sync'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"contacts": contacts}),
      );
      return response.statusCode == 200;
    } catch (e) {
      print("[API] Error syncing contacts: $e");
    }
    return false;
  }

  // Decline an Active Call
  static Future<bool> declineCall(String callSid) async {
    try {
      final baseUrl = await getBaseUrl();
      final response = await http.post(
        Uri.parse('$baseUrl/api/calls/$callSid/decline'),
      );
      return response.statusCode == 200;
    } catch (e) {
      print("[API] Error declining call: $e");
    }
    return false;
  }

  // Get Active Calls Monitored on Twilio
  static Future<List<dynamic>> getActiveCalls() async {
    try {
      final baseUrl = await getBaseUrl();
      final response = await http.get(Uri.parse('$baseUrl/api/calls/active'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print("[API] Error fetching active calls: $e");
    }
    return [];
  }
}
