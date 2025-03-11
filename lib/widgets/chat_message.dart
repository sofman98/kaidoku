import 'package:flutter/material.dart';
import '../models/message.dart';
import 'custom_linkify_text.dart';

class ChatMessage extends StatelessWidget {
  final Message message;

  ChatMessage({required this.message});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: EdgeInsets.symmetric(vertical: 5, horizontal: 10),
        padding: EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: message.isUser ? Colors.blue : Colors.grey[300],
          borderRadius: BorderRadius.circular(8),
        ),
        child: CustomLinkifyText(
          text: message.text,
          style: TextStyle(color: message.isUser ? Colors.white : Colors.black),
          linkStyle: TextStyle(
            color: Colors.lightBlueAccent,
            decoration: TextDecoration.underline,
          ),
        ),
      ),
    );
  }
}
