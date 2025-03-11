import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class CustomLinkifyText extends StatelessWidget {
  final String text;
  final TextStyle? style;
  final TextStyle? linkStyle;

  CustomLinkifyText({required this.text, this.style, this.linkStyle});

  @override
  Widget build(BuildContext context) {
    // Simple regex for detecting URLs. You can adjust this regex as needed.
    final regex = RegExp(
      r'((https?:\/\/)?([\w-]+\.)+[\w-]+(\/[\w- ./?%&=]*)?)',
      caseSensitive: false,
    );

    final matches = regex.allMatches(text);
    if (matches.isEmpty) {
      return Text(text, style: style);
    }

    List<TextSpan> spans = [];
    int lastMatchEnd = 0;
    for (final match in matches) {
      if (match.start > lastMatchEnd) {
        spans.add(
          TextSpan(
            text: text.substring(lastMatchEnd, match.start),
            style: style,
          ),
        );
      }
      final url = text.substring(match.start, match.end);
      spans.add(
        TextSpan(
          text: url,
          style: linkStyle ?? style?.copyWith(color: Colors.blue),
          recognizer: TapGestureRecognizer()
            ..onTap = () async {
              // Ensure the URL has a scheme. If not, add http://
              final Uri uri = Uri.parse(url.startsWith('http') ? url : 'http://$url');
              if (await canLaunchUrl(uri)) {
                await launchUrl(uri);
              } else {
                debugPrint('Could not launch $uri');
              }
            },
        ),
      );
      lastMatchEnd = match.end;
    }
    if (lastMatchEnd < text.length) {
      spans.add(TextSpan(text: text.substring(lastMatchEnd), style: style));
    }
    return RichText(text: TextSpan(children: spans));
  }
}
