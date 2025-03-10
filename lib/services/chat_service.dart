import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatService {
  static Stream<String> fetchResponseStream(String query) async* {
    final url = Uri.parse('http://127.0.0.1:8080/?query=${Uri.encodeComponent(query)}');
    final request = http.Request('GET', url);
    final response = await request.send();
    print(response);

    if (response.statusCode == 200) {
      await for (var chunk in response.stream.transform(utf8.decoder)) {
        yield chunk;
      }
    } else {
      throw Exception('Failed to load response');
    }
  }
}
