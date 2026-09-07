#!/usr/bin/env python3
"""
Sends an email to Intelsa (via Brevo's transactional API) with the client's
confirmed interview decisions for the SM Digital Intake Specialist shortlist.

Usage:
    export BREVO_API_KEY="xkeysib-..."
    python3 send_decision_notification.py SM_Digital_Intake_Specialist_Decisions.txt
    python3 send_decision_notification.py decisions.txt --to someone@intelsa.co

Get your Brevo API key at: https://app.brevo.com/settings/keys/api
The decisions file is the .txt downloaded from the report's "Export selections" button.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
DEFAULT_SENDER = {"name": "Oscar Barrera | Intelsa BPO", "email": "mdigital@intelsa.co"}
DEFAULT_RECIPIENT = "mdigital@intelsa.co"

COLORS = {
    "orange": "#ff9345",
    "green": "#a9d944",
    "dark": "#414c4c",
    "border": "#e5e7e7",
    "muted_bg": "#f7f7f7",
}


def parse_counts(text):
    counts = {}
    for label, key in [
        ("ADVANCE TO ENGLISH INTERVIEW", "advance"),
        ("ON HOLD", "hold"),
        ("NOT THIS ROUND", "reject"),
    ]:
        match = re.search(rf"=== {re.escape(label)} \((\d+)\) ===", text)
        counts[key] = int(match.group(1)) if match else 0
    return counts


def build_html(text, counts):
    body_html = (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return f"""
<div style="font-family: 'Poppins', Arial, sans-serif; background: #fff; color: {COLORS['dark']}; max-width: 640px; margin: 0 auto;">
  <div style="background: {COLORS['orange']}; padding: 20px 28px; border-radius: 3px 3px 0 0;">
    <div style="color: #fff; font-size: 12px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">Intelsa BPO &amp; CX</div>
    <div style="color: #fff; font-size: 20px; font-weight: 600; margin-top: 4px;">Decisiones de entrevista confirmadas</div>
  </div>
  <div style="border: 1px solid {COLORS['border']}; border-top: none; padding: 24px 28px; border-radius: 0 0 3px 3px;">
    <p style="font-size: 14px;">El cliente de <strong>SM Digital</strong> confirm&oacute; su selecci&oacute;n para el proceso de <strong>Skilled Intake Specialist</strong>:</p>
    <div style="display: flex; gap: 12px; margin: 20px 0; flex-wrap: wrap;">
      <div style="background: {COLORS['muted_bg']}; border-radius: 3px; padding: 12px 18px; flex: 1; min-width: 120px;">
        <div style="font-size: 24px; font-weight: 600; color: {COLORS['green']};">{counts['advance']}</div>
        <div style="font-size: 11px; font-weight: 500; color: {COLORS['dark']}; text-transform: uppercase;">Avanzan</div>
      </div>
      <div style="background: {COLORS['muted_bg']}; border-radius: 3px; padding: 12px 18px; flex: 1; min-width: 120px;">
        <div style="font-size: 24px; font-weight: 600; color: {COLORS['orange']};">{counts['hold']}</div>
        <div style="font-size: 11px; font-weight: 500; color: {COLORS['dark']}; text-transform: uppercase;">En espera</div>
      </div>
      <div style="background: {COLORS['muted_bg']}; border-radius: 3px; padding: 12px 18px; flex: 1; min-width: 120px;">
        <div style="font-size: 24px; font-weight: 600; color: #c0392b;">{counts['reject']}</div>
        <div style="font-size: 11px; font-weight: 500; color: {COLORS['dark']}; text-transform: uppercase;">Descartados</div>
      </div>
    </div>
    <pre style="background: {COLORS['muted_bg']}; border-radius: 3px; padding: 16px; font-size: 12px; white-space: pre-wrap; font-family: 'Courier New', monospace;">{body_html}</pre>
  </div>
</div>
""".strip()


def send_email(api_key, recipient, subject, html_content, text_content):
    payload = {
        "sender": DEFAULT_SENDER,
        "to": [{"email": recipient}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content,
    }
    request = urllib.request.Request(
        BREVO_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("decisions_file", help="Path to the exported decisions .txt file")
    parser.add_argument("--to", default=DEFAULT_RECIPIENT, help=f"Recipient email (default: {DEFAULT_RECIPIENT})")
    args = parser.parse_args()

    api_key = os.environ.get("BREVO_API_KEY")
    if not api_key:
        sys.exit("Error: set the BREVO_API_KEY environment variable first (https://app.brevo.com/settings/keys/api)")

    with open(args.decisions_file, "r", encoding="utf-8") as f:
        text = f.read()

    counts = parse_counts(text)
    subject = f"SM Digital · Intake Specialist — {counts['advance']} candidato(s) confirmado(s) para entrevista"
    html_content = build_html(text, counts)

    try:
        result = send_email(api_key, args.to, subject, html_content, text)
    except urllib.error.HTTPError as e:
        sys.exit(f"Brevo API error {e.code}: {e.read().decode('utf-8')}")

    print(f"Email sent to {args.to} — messageId: {result.get('messageId')}")


if __name__ == "__main__":
    main()
