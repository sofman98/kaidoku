import 'package:flutter/material.dart';
import 'chat_bubble.dart';
import 'chat_message.dart';

class ChatScreen extends StatefulWidget {
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<ChatMessage> _messages = [];
  final TextEditingController _controller = TextEditingController();

  void _handleSubmitted(String text) async {
    if (text.trim().isEmpty) return;
    _controller.clear();
    setState(() {
      // Add user's message
      _messages.insert(0, ChatMessage(message: text, isUser: true));
    });

    // Simulate an API call to your backend.
    String response = await _getAIResponse(text);
    setState(() {
      // Add AI's response
      _messages.insert(0, ChatMessage(message: response, isUser: false));
    });
  }

  Future<String> _getAIResponse(String query) async {
    // Replace this with your real API call logic.
    await Future.delayed(Duration(seconds: 1));
    return "Simulated response for: \"$query\"";
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Kaidoku"),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              reverse: true,
              padding: EdgeInsets.all(8.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                return ChatBubble(
                  message: _messages[index].message,
                  isUser: _messages[index].isUser,
                );
              },
            ),
          ),
          Divider(height: 1.0),
          Container(
            color: Colors.white,
            padding: EdgeInsets.symmetric(horizontal: 8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    onSubmitted: _handleSubmitted,
                    decoration: InputDecoration.collapsed(
                      hintText: "Type your message...",
                    ),
                  ),
                ),
                IconButton(
                  icon: Icon(Icons.send),
                  onPressed: () => _handleSubmitted(_controller.text),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
