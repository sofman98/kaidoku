import 'package:flutter/material.dart';
import 'package:flutter_linkify/flutter_linkify.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/message.dart';

class ChatMessage extends StatelessWidget {
  final Message message;

  ChatMessage({required this.message});

  Future<void> _onOpen(LinkableElement link) async {
    final url = link.url;
    if (await canLaunch(url)) {
      await launch(url);
    } else {
      throw 'Could not launch $url';
    }
  }

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
        child: Linkify(
          onOpen: _onOpen,
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
